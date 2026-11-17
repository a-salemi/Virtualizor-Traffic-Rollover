import logging
import requests
import urllib3
from typing import Dict, Any, Optional
from backend.config import (
    VIRTUALIZOR_IP,
    VIRTUALIZOR_PORT,
    VIRTUALIZOR_API_KEY,
    VIRTUALIZOR_API_PASS
)

# Suppress self-signed certificate warnings for local Virtualizor node
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("virturoll.api")

class VirtualizorClient:
    def __init__(self):
        self.base_url = f"https://{VIRTUALIZOR_IP}:{VIRTUALIZOR_PORT}/index.php"
        self.api_key = VIRTUALIZOR_API_KEY
        self.api_pass = VIRTUALIZOR_API_PASS

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_pass)

    def _request(self, params: Dict[str, Any], data: Optional[Dict[str, Any]] = None, method: str = "POST") -> Optional[Dict[str, Any]]:
        if not self.is_configured():
            logger.warning("Virtualizor API is not configured yet with API_KEY and API_PASS.")
            return None

        # Build standard Virtualizor API authentication parameters
        req_params = {
            "api": "json",
            "adminindex": 1,
            "apikey": self.api_key,
            "apipass": self.api_pass,
        }
        req_params.update(params)

        try:
            if method.upper() == "POST":
                res = requests.post(
                    self.base_url,
                    params=req_params,
                    data=data or {},
                    verify=False,
                    timeout=25
                )
            else:
                res = requests.get(
                    self.base_url,
                    params=req_params,
                    verify=False,
                    timeout=25
                )

            res.raise_for_status()
            return res.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Virtualizor API connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while parsing Virtualizor API response: {e}")
            return None

    def get_all_vps(self) -> Dict[str, Any]:
        """Fetch all virtual machines from Virtualizor node"""
        res = self._request({"act": "vs"}, method="GET")
        if res and isinstance(res, dict) and "vs" in res:
            return res["vs"]
        return {}

    def get_vps(self, vpsid: str) -> Optional[Dict[str, Any]]:
        """Fetch a single VPS details"""
        all_vps = self.get_all_vps()
        return all_vps.get(str(vpsid))

    def update_vps_bandwidth(self, vpsid: str, new_bandwidth_gb: float) -> bool:
        """Update VPS total bandwidth limit via Virtualizor API"""
        payload = {
            "act": "editvs",
            "vpsid": str(vpsid),
            "bandwidth": round(float(new_bandwidth_gb), 2)
        }
        res = self._request(payload, method="POST")
        if res and isinstance(res, dict):
            if res.get("done") or not res.get("error"):
                logger.info(f"Successfully updated VPS {vpsid} bandwidth to {new_bandwidth_gb} GB.")
                return True
            else:
                logger.error(f"Virtualizor API returned error for editvs {vpsid}: {res.get('error')}")
        return False

    def suspend_vps(self, vpsid: str) -> bool:
        """Suspend VPS when traffic is exhausted"""
        payload = {"act": "suspend", "vpsid": str(vpsid)}
        res = self._request(payload, method="POST")
        return bool(res and not res.get("error"))

    def unsuspend_vps(self, vpsid: str) -> bool:
        """Unsuspend VPS after traffic top-up"""
        payload = {"act": "unsuspend", "vpsid": str(vpsid)}
        res = self._request(payload, method="POST")
        return bool(res and not res.get("error"))

virtualizor_client = VirtualizorClient()
