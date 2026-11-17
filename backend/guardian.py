from datetime import datetime
import json
import logging
from sqlalchemy.orm import Session
from backend.config import (
    ROLLOVER_WINDOW_START_DAY,
    ROLLOVER_WINDOW_END_DAY
)
from backend.database import VPSTraffic, AuditLog
from backend.virtualizor_api import virtualizor_client

logger = logging.getLogger("virturoll.guardian")

class TrafficGuardian:
    def sync_and_check(self, db: Session) -> dict:
        """
        Polls Virtualizor node, tracks usage deltas, detects monthly reset events,
        and applies persistent bandwidth rollover automatically.
        """
        if not virtualizor_client.is_configured():
            return {"status": "unconfigured", "message": "Virtualizor API credentials not set. Please configure in Node Settings."}

        raw_res = virtualizor_client._request({"act": "vs"}, method="GET")
        if not raw_res or not isinstance(raw_res, dict):
            return {"status": "error", "message": f"Could not connect to {virtualizor_client.base_url}. Check if node is online and port {virtualizor_client.port} is open."}

        if "error" in raw_res and raw_res["error"]:
            err = raw_res["error"]
            if isinstance(err, list):
                err = ", ".join(err)
            return {"status": "error", "message": f"Virtualizor rejected API: {err}"}

        vps_dict = raw_res.get("vs", {})

        current_month_tag = datetime.utcnow().strftime("%Y-%m")
        day_of_month = datetime.utcnow().day
        is_rollover_window = (day_of_month >= ROLLOVER_WINDOW_START_DAY or day_of_month <= ROLLOVER_WINDOW_END_DAY)

        synced_count = 0
        rollover_count = 0

        for vpsid_raw, data in vps_dict.items():
            vpsid = str(vpsid_raw)
            hostname = data.get("hostname", f"vps-{vpsid}")
            
            # Extract primary IP
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
                # First time seeing this VPS -> Register in system
                rec = VPSTraffic(
                    vpsid=vpsid,
                    hostname=hostname,
                    ip=ip_str,
                    total_purchased_gb=virt_limit,
                    current_virtualizor_limit_gb=virt_limit,
                    current_month_used_gb=virt_used,
                    last_known_used_gb=virt_used,
                    remaining_gb=max(0.0, virt_limit - virt_used),
                    last_rollover_period=current_month_tag,
                    is_suspended=bool(data.get("status") == 0)
                )
                db.add(rec)
                synced_count += 1
                continue

            # Existing record in database
            rec.hostname = hostname
            rec.ip = ip_str
            rec.is_suspended = bool(data.get("status") == 0)

            prev_limit = rec.current_virtualizor_limit_gb
            prev_used = rec.last_known_used_gb
            last_rollover = rec.last_rollover_period
            is_unlimited = (prev_limit <= 0 or virt_limit <= 0)

            # RESET DETECTION LOGIC:
            # 1. Inside rollover date window (end/start of month)
            # 2. Not yet processed for the current month
            # 3. Usage dropped drastically (Virtualizor wiped the monthly counter to 0)
            traffic_dropped = (prev_used > 0.5 and virt_used < prev_used * 0.3) or (prev_used > 0.05 and virt_used == 0)
            not_yet_rolled_over = (last_rollover != current_month_tag)

            if is_rollover_window and traffic_dropped and not_yet_rolled_over:
                if is_unlimited:
                    # Unlimited server: Do NOT modify bandwidth limit! Keep at 0 (Unlimited)
                    logger.info(f"[ROLLOVER SKIPPED] VPS {vpsid} ({hostname}) is UNLIMITED. Limit remains 0.")
                    rec.current_virtualizor_limit_gb = 0.0
                    rec.current_month_used_gb = virt_used
                    rec.last_known_used_gb = virt_used
                    rec.remaining_gb = 0.0
                    rec.last_rollover_period = current_month_tag
                else:
                    # Metered/Prepaid server: Calculate actual remaining bandwidth:
                    remaining = max(0.0, round(prev_limit - prev_used, 2))
                    new_limit = max(0.05, remaining) # Safety floor

                    logger.info(
                        f"[ROLLOVER DETECTED] VPS {vpsid} ({hostname}): "
                        f"Previous Limit: {prev_limit}GB, Consumed: {prev_used}GB. "
                        f"New Rollover Limit: {new_limit}GB"
                    )

                    # Push updated limit to Virtualizor node
                    success = virtualizor_client.update_vps_bandwidth(vpsid, new_limit)

                    audit = AuditLog(
                        event_type="ROLLOVER",
                        vpsid=vpsid,
                        message=f"Automatic rollover applied. Remaining bandwidth set to {new_limit} GB (Was: {prev_limit} GB, Used: {prev_used} GB).",
                        details=json.dumps({
                            "prev_limit_gb": prev_limit,
                            "prev_used_gb": prev_used,
                            "new_limit_gb": new_limit,
                            "api_success": success
                        })
                    )
                    db.add(audit)

                    rec.current_virtualizor_limit_gb = new_limit
                    rec.current_month_used_gb = virt_used
                    rec.last_known_used_gb = virt_used
                    rec.remaining_gb = new_limit
                    rec.last_rollover_period = current_month_tag
                    rollover_count += 1
            else:
                # Normal ongoing operation: Keep used metrics synchronized
                rec.current_month_used_gb = virt_used
                if virt_used >= rec.last_known_used_gb:
                    rec.last_known_used_gb = virt_used
                
                if is_unlimited:
                    rec.remaining_gb = 0.0
                    rec.current_virtualizor_limit_gb = 0.0
                else:
                    rec.remaining_gb = max(0.0, round(rec.current_virtualizor_limit_gb - virt_used, 2))

                # If admin manually modified limit in Virtualizor panel, sync it
                if abs(virt_limit - rec.current_virtualizor_limit_gb) > 0.1 and not not_yet_rolled_over:
                    rec.current_virtualizor_limit_gb = virt_limit

            synced_count += 1

        db.commit()
        return {
            "status": "success",
            "total_vps": synced_count,
            "rollovers_applied": rollover_count,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }

    def add_bandwidth(self, db: Session, vpsid: str, extra_gb: float) -> dict:
        """Top up bandwidth package for a customer"""
        rec = db.query(VPSTraffic).filter(VPSTraffic.vpsid == str(vpsid)).first()
        if not rec:
            return {"success": False, "message": "VPS not found in database."}

        new_total_purchased = round(rec.total_purchased_gb + extra_gb, 2)
        new_limit = round(rec.current_virtualizor_limit_gb + extra_gb, 2)

        # Update Virtualizor
        api_res = virtualizor_client.update_vps_bandwidth(vpsid, new_limit)

        rec.total_purchased_gb = new_total_purchased
        rec.current_virtualizor_limit_gb = new_limit
        rec.remaining_gb = max(0.0, round(new_limit - rec.current_month_used_gb, 2))

        audit = AuditLog(
            event_type="ADD_TRAFFIC",
            vpsid=str(vpsid),
            message=f"Added {extra_gb} GB traffic to VPS {vpsid} ({rec.hostname}). New limit: {new_limit} GB.",
            details=json.dumps({
                "added_gb": extra_gb,
                "new_limit_gb": new_limit,
                "total_purchased_gb": new_total_purchased
            })
        )
        db.add(audit)
        db.commit()

        return {
            "success": True,
            "vpsid": vpsid,
            "added_gb": extra_gb,
            "new_limit_gb": new_limit,
            "remaining_gb": rec.remaining_gb,
            "virtualizor_synced": api_res
        }

guardian = TrafficGuardian()
