"""WiFi data processor for Keenetic integration."""
import logging
from typing import Dict, Any

_LOGGER = logging.getLogger(__name__)

class WiFiProcessor:
    """Process WiFi data from Keenetic router."""

    @staticmethod
    async def process_wifi_interfaces(session, base_url, auth_token) -> Dict[str, Any]:
        """Process WiFi interfaces and return formatted data."""
        wifi_data = {}
        try:
            for band in ["WifiMaster0", "WifiMaster1"]:
                async with session.get(
                    f"{base_url}/rci/interface/{band}",
                    headers={"Authorization": f"Basic {auth_token}"},
                ) as response:
                    if response.status == 200:
                        master_data = await response.json()
                        _LOGGER.debug("%s data: %s", band, master_data)
                        
                        for i in range(7):
                            ap_id = f"{band}/AccessPoint{i}"
                            async with session.get(
                                f"{base_url}/rci/interface/{ap_id}",
                                headers={"Authorization": f"Basic {auth_token}"},
                            ) as ap_response:
                                if ap_response.status == 200:
                                    ap_data = await ap_response.json()
                                    _LOGGER.debug("AP data for %s: %s", ap_id, ap_data)
                                    if ap_data.get("ssid"):
                                        wifi_password = (
                                            ap_data.get("authentication", {})
                                            .get("wpa-psk", {})
                                            .get("psk", "")
                                        )
                                        wifi_data[ap_id] = {
                                            "id": ap_id,
                                            "type": "AccessPoint",
                                            "description": ap_data.get("description", ""),
                                            "ssid": ap_data.get("ssid"),
                                            "up": ap_data.get("up", False),
                                            "encryption": ap_data.get("encryption", {}),
                                            "link": "up" if ap_data.get("up") else "down",
                                            "mac": ap_data.get("mac", ""),
                                            "interface-name": ap_data.get("interface-name", ""),
                                            "connected": ap_data.get("connected", "no"),
                                            "state": ap_data.get("state", "down"),
                                            "password": wifi_password
                                        }
                                        
            _LOGGER.debug("Processed WiFi interfaces: %s", wifi_data)
            return wifi_data
            
        except Exception as ex:
            _LOGGER.error("Error processing WiFi interfaces: %s", str(ex))
            return {}