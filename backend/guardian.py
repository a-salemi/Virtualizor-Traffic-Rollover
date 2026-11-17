from __future__ import annotations
from datetime import datetime
import json
import logging
import threading
from typing import Tuple
from sqlalchemy.orm import Session
from backend.config import (
    ROLLOVER_WINDOW_START_DAY,
    ROLLOVER_WINDOW_END_DAY
)
from backend.database import VPSTraffic, AuditLog, VirtualizorPanel
from backend.virtualizor_api import virtualizor_client, VirtualizorClient
from backend.telegram_notifier import telegram_notifier

logger = logging.getLogger("virturoll.guardian")

class TrafficGuardian:
    def _sync_single_client(self, db: Session, client: VirtualizorClient, is_rollover_window: bool, current_month_tag: str) -> Tuple[int, int]:
        """
        Syncs VPS instances from a single Virtualizor client.
        Virtualizor is treated as the strict, single source of truth for all current limits and usage counters.
        """
        raw_res = client._request({"act": "vs"}, method="GET")
        if not raw_res or not isinstance(raw_res, dict):
            logger.warning(f"Could not reach Virtualizor node at {client.base_url}")
            return 0, 0

        if "error" in raw_res and raw_res["error"]:
            err = raw_res["error"]
            if isinstance(err, list):
                err = ", ".join(err)
            logger.error(f"Virtualizor node {client.base_url} returned error: {err}")
            return 0, 0

        vps_dict = raw_res.get("vs", {})
        if not isinstance(vps_dict, dict):
            return 0, 0

        synced_count = 0
        rollover_count = 0

        for vpsid_raw, data in vps_dict.items():
            vpsid = str(vpsid_raw)
            hostname = data.get("hostname", f"vps-{vpsid}")
            
            ips = data.get("ips", {})
            ip_str = ""
            if isinstance(ips, dict) and ips:
                ip_str = next(iter(ips.values()), "")
            elif isinstance(ips, list) and ips:
                ip_str = str(ips[0])
            elif isinstance(ips, str):
                ip_str = ips

            try:
                virt_limit = float(data.get("bandwidth", 0.0))
                virt_used = float(data.get("used_bandwidth", 0.0))
            except (ValueError, TypeError):
                continue

            rec = db.query(VPSTraffic).filter(VPSTraffic.vpsid == vpsid).first()

            if not rec:
                # First discovery of this VPS
                is_unl = bool(virt_limit <= 0)
                rec = VPSTraffic(
                    vpsid=vpsid,
                    hostname=hostname,
                    ip=ip_str,
                    total_purchased_gb=virt_limit,
                    current_virtualizor_limit_gb=virt_limit,
                    current_month_used_gb=virt_used,
                    last_known_used_gb=virt_used,
                    remaining_gb=0.0 if is_unl else max(0.0, round(virt_limit - virt_used, 2)),
                    last_rollover_period=current_month_tag,
                    is_suspended=bool(data.get("status") == 0)
                )
                db.add(rec)
                synced_count += 1
                continue

            # Existing VPS record
            rec.hostname = hostname
            rec.ip = ip_str
            rec.is_suspended = bool(data.get("status") == 0)

            prev_limit = rec.current_virtualizor_limit_gb
            prev_used = rec.last_known_used_gb
            last_rollover = rec.last_rollover_period
            is_unlimited = (prev_limit <= 0 or virt_limit <= 0)

            # Monthly reset detection:
            # 1. Inside rollover date window (end/start of calendar month)
            # 2. Not yet processed for the current month
            # 3. Usage dropped drastically (Virtualizor reset month counter to 0)
            traffic_dropped = (prev_used > 0.5 and virt_used < prev_used * 0.3) or (prev_used > 0.05 and virt_used == 0)
            not_yet_rolled_over = (last_rollover != current_month_tag)

            if is_rollover_window and traffic_dropped and not_yet_rolled_over:
                if is_unlimited:
                    logger.info(f"[ROLLOVER SKIPPED] VPS {vpsid} ({hostname}) is UNLIMITED. Limit stays 0.")
                    rec.current_virtualizor_limit_gb = 0.0
                    rec.current_month_used_gb = virt_used
                    rec.last_known_used_gb = virt_used
                    rec.remaining_gb = 0.0
                    rec.last_rollover_period = current_month_tag
                else:
                    remaining = max(0.0, round(prev_limit - prev_used, 2))
                    new_limit = max(0.05, remaining)

                    logger.info(
                        f"[ROLLOVER DETECTED] VPS {vpsid} ({hostname}): "
                        f"Previous Limit: {prev_limit}GB, Consumed: {prev_used}GB. "
                        f"New Rollover Limit: {new_limit}GB"
                    )

                    success, api_msg = client.update_vps_bandwidth(vpsid, new_limit, hostname=hostname)

                    audit = AuditLog(
                        event_type="ROLLOVER",
                        vpsid=vpsid,
                        message=f"Automatic rollover applied. Remaining bandwidth set to {new_limit} GB (Was: {prev_limit} GB, Used: {prev_used} GB). Result: {api_msg}",
                        details=json.dumps({
                            "prev_limit_gb": prev_limit,
                            "prev_used_gb": prev_used,
                            "new_limit_gb": new_limit,
                            "api_success": success,
                            "api_msg": api_msg
                        })
                    )
                    db.add(audit)

                    rec.current_virtualizor_limit_gb = new_limit
                    rec.current_month_used_gb = virt_used
                    rec.last_known_used_gb = virt_used
                    rec.remaining_gb = new_limit
                    rec.last_rollover_period = current_month_tag
                    rollover_count += 1

                    try:
                        telegram_notifier.notify_rollover(vpsid, hostname, prev_limit, prev_used, new_limit)
                    except Exception as te:
                        logger.error(f"Failed to send rollover telegram alert: {te}")
            else:
                # Normal ongoing operation: Strictly mirror Virtualizor node's metrics
                rec.current_month_used_gb = virt_used
                if virt_used >= rec.last_known_used_gb:
                    rec.last_known_used_gb = virt_used

                if is_unlimited:
                    rec.remaining_gb = 0.0
                    rec.current_virtualizor_limit_gb = 0.0
                else:
                    rec.current_virtualizor_limit_gb = virt_limit
                    rec.remaining_gb = max(0.0, round(virt_limit - virt_used, 2))
                    if virt_limit > rec.total_purchased_gb:
                        rec.total_purchased_gb = virt_limit

            synced_count += 1

        return synced_count, rollover_count

    def sync_and_check(self, db: Session) -> dict:
        """
        Polls Virtualizor node(s), tracks usage deltas, detects monthly reset events,
        and applies persistent bandwidth rollover automatically.
        """
        current_month_tag = datetime.utcnow().strftime("%Y-%m")
        day_of_month = datetime.utcnow().day
        is_rollover_window = (day_of_month >= ROLLOVER_WINDOW_START_DAY or day_of_month <= ROLLOVER_WINDOW_END_DAY)

        panels = db.query(VirtualizorPanel).filter(VirtualizorPanel.is_active == True).all()

        total_synced = 0
        total_rollovers = 0

        if panels:
            for panel in panels:
                p_client = VirtualizorClient(panel.ip, panel.port, panel.api_key, panel.api_pass)
                s_count, r_count = self._sync_single_client(db, p_client, is_rollover_window, current_month_tag)
                total_synced += s_count
                total_rollovers += r_count
                panel.last_sync = datetime.utcnow()
                panel.last_status = "online" if s_count > 0 or panel.last_status == "online" else "error"
                if s_count > 0:
                    panel.vps_count = s_count
        elif virtualizor_client.is_configured():
            s_count, r_count = self._sync_single_client(db, virtualizor_client, is_rollover_window, current_month_tag)
            total_synced += s_count
            total_rollovers += r_count
        else:
            return {"status": "unconfigured", "message": "No Virtualizor node or panel credentials configured."}

        db.commit()
        return {
            "status": "success",
            "total_vps": total_synced,
            "rollovers_applied": total_rollovers,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _resolve_client_for_vps(self, db: Session, vpsid: str) -> VirtualizorClient:
        """Find the corresponding Virtualizor client for a given VPS ID"""
        panels = db.query(VirtualizorPanel).filter(VirtualizorPanel.is_active == True).all()
        if len(panels) == 1:
            p = panels[0]
            return VirtualizorClient(p.ip, p.port, p.api_key, p.api_pass)
        elif len(panels) > 1:
            for p in panels:
                client = VirtualizorClient(p.ip, p.port, p.api_key, p.api_pass)
                res = client._request({"act": "vs"}, method="GET")
                if res and isinstance(res, dict) and "vs" in res:
                    if str(vpsid) in res["vs"]:
                        return client
        return virtualizor_client

    def add_bandwidth(self, db: Session, vpsid: str, extra_gb: float) -> dict:
        """
        Top up bandwidth package for a customer.
        Virtualizor node is the sole authority: the database is NEVER updated unless the node confirms success.
        """
        rec = db.query(VPSTraffic).filter(VPSTraffic.vpsid == str(vpsid)).first()
        if not rec:
            return {"success": False, "message": "VPS not found in database."}

        new_total_purchased = round(rec.total_purchased_gb + extra_gb, 2)
        new_limit = round(rec.current_virtualizor_limit_gb + extra_gb, 2)

        client = self._resolve_client_for_vps(db, vpsid)
        if not client.is_configured():
            return {"success": False, "message": "Virtualizor node credentials not configured."}

        # Update Virtualizor node
        success, api_msg = client.update_vps_bandwidth(vpsid, new_limit, hostname=rec.hostname)
        if not success:
            logger.error(f"Failed to update bandwidth on Virtualizor node for VPS {vpsid}: {api_msg}")
            return {
                "success": False,
                "message": f"Virtualizor node rejected update: {api_msg}"
            }

        # Node confirmed success -> Strictly update local database metrics
        rec.total_purchased_gb = new_total_purchased
        rec.current_virtualizor_limit_gb = new_limit
        rec.remaining_gb = max(0.0, round(new_limit - rec.current_month_used_gb, 2))

        audit = AuditLog(
            event_type="ADD_TRAFFIC",
            vpsid=str(vpsid),
            message=f"Added {extra_gb} GB traffic to VPS #{vpsid} ({rec.hostname}). New limit: {new_limit} GB. (Node confirmed: {api_msg})",
            details=json.dumps({
                "added_gb": extra_gb,
                "new_limit_gb": new_limit,
                "total_purchased_gb": new_total_purchased,
                "api_response": api_msg
            })
        )
        db.add(audit)
        db.commit()

        # Trigger real-time Telegram top-up alert in background daemon thread
        try:
            threading.Thread(
                target=telegram_notifier.notify_topup,
                args=(vpsid, rec.hostname, extra_gb, new_limit),
                daemon=True
            ).start()
        except Exception as te:
            logger.error(f"Failed to launch topup telegram alert thread: {te}")

        return {
            "success": True,
            "vpsid": vpsid,
            "added_gb": extra_gb,
            "new_limit_gb": new_limit,
            "remaining_gb": rec.remaining_gb,
            "virtualizor_synced": True,
            "message": f"Successfully added {extra_gb} GB to VPS #{vpsid}."
        }

guardian = TrafficGuardian()
