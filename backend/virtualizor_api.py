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

# Suppress self-signed certificate warnings for Virtualizor nodes
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("virturoll.api")

def clean_host_and_port(ip: str, port: int = 4085):
    """Clean user input: strip https://, http://, trailing slashes, and extract embedded port"""
    if not ip:
        return "127.0.0.1", int(port)
    
    cleaned = str(ip).strip()
    if cleaned.startswith("https://"):
        cleaned = cleaned[8:]
    elif cleaned.startswith("http://"):
        cleaned = cleaned[7:]
    
    # Strip paths like /index.php or /
    cleaned = cleaned.split("/")[0].strip()

    # Extract port if user entered host:port
    if ":" in cleaned and not cleaned.startswith("["):
        parts = cleaned.split(":", 1)
        cleaned = parts[0].strip()
        try:
            port = int(parts[1].strip())
        except ValueError:
            pass

    return cleaned, int(port)

class VirtualizorClient:
    def __init__(self):
        self.ip, self.port = clean_host_and_port(VIRTUALIZOR_IP, VIRTUALIZOR_PORT)
        self.api_key = VIRTUALIZOR_API_KEY
        self.api_pass = VIRTUALIZOR_API_PASS
        self.base_url = f"https://{self.ip}:{self.port}/index.php"

    def update_credentials(self, ip: str, port: int, api_key: str, api_pass: str):
        self.ip, self.port = clean_host_and_port(ip, port)
        self.api_key = api_key.strip()
        if api_pass and api_pass.strip():
            self.api_pass = api_pass.strip()
        self.base_url = f"https://{self.ip}:{self.port}/index.php"
        logger.info(f"Virtualizor credentials updated: target={self.base_url}")

    def load_from_db(self, db):
        from backend.database import get_setting
        ip = get_setting(db, "virtualizor_ip", VIRTUALIZOR_IP)
        port = int(get_setting(db, "virtualizor_port", str(VIRTUALIZOR_PORT)))
        api_key = get_setting(db, "virtualizor_api_key", VIRTUALIZOR_API_KEY)
        api_pass = get_setting(db, "virtualizor_api_pass", VIRTUALIZOR_API_PASS)
        self.update_credentials(ip, port, api_key, api_pass)

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_pass and self.ip)

    def _request(self, params: Dict[str, Any], data: Optional[Dict[str, Any]] = None, method: str = "POST", timeout: int = 15) -> Optional[Dict[str, Any]]:
        if not self.is_configured():
            logger.warning("Virtualizor API is not configured yet with API_KEY and API_PASS.")
            return None

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
                    timeout=timeout
                )
            else:
                res = requests.get(
                    self.base_url,
                    params=req_params,
                    verify=False,
                    timeout=timeout
                )

            res.raise_for_status()
            data = res.json()
            if isinstance(data, dict) and "error" in data and data["error"]:
                logger.error(f"Virtualizor API error returned: {data['error']}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Virtualizor API connection error to {self.base_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while parsing Virtualizor API response: {e}")
            return None

    def test_connection_params(self, ip: str, port: int, api_key: str, api_pass: str) -> dict:
        """Test explicit credentials without altering current client state"""
        clean_ip, clean_port = clean_host_and_port(ip, port)
        if not api_pass or not api_pass.strip():
            api_pass = self.api_pass

        test_url = f"https://{clean_ip}:{clean_port}/index.php"
        req_params = {
            "act": "vs",
            "api": "json",
            "adminindex": 1,
            "apikey": api_key.strip(),
            "apipass": api_pass.strip(),
        }
        try:
            res = requests.get(test_url, params=req_params, verify=False, timeout=12)
            res.raise_for_status()
            data = res.json()
            if isinstance(data, dict):
                if "error" in data and data["error"]:
                    err = data["error"]
                    if isinstance(err, list):
                        err = ", ".join(err)
                    return {"success": False, "error": f"Virtualizor rejected API request: {err}"}
                
                vps_dict = data.get("vs", {})
                vps_count = len(vps_dict) if isinstance(vps_dict, dict) else 0
                return {
                    "success": True,
                    "vps_count": vps_count,
                    "message": f"Successfully connected to {clean_ip}:{clean_port}! Found {vps_count} virtual machines."
                }
            return {"success": False, "error": f"Invalid JSON response received from {test_url}"}
        except requests.exceptions.ConnectTimeout:
            return {"success": False, "error": f"Connection timed out to {clean_ip}:{clean_port}. Ensure port {clean_port} is open in firewall."}
        except requests.exceptions.SSLError as e:
            return {"success": False, "error": f"SSL Error communicating with {test_url}: {e}"}
        except requests.exceptions.ConnectionError as e:
            return {"success": False, "error": f"Connection refused or unreachable for {clean_ip}:{clean_port}. Check IP/Domain and firewall."}
        except Exception as e:
            return {"success": False, "error": str(e)}

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
        payload = {"act": "suspend", "vpsid": str(vpsid)}
        res = self._request(payload, method="POST")
        return bool(res and not res.get("error"))

    def unsuspend_vps(self, vpsid: str) -> bool:
        payload = {"act": "unsuspend", "vpsid": str(vpsid)}
        res = self._request(payload, method="POST")
        return bool(res and not res.get("error"))

virtualizor_client = VirtualizorClient()
