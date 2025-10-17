"""API client for Keenetic routers."""
import base64
import logging
import aiohttp
from typing import Dict, Any

from .const import (
    API_SYSTEM,
    API_VERSION,
    API_INTERFACE,
    API_MESH,
    MANUFACTURER
)
from .ethernet_processor import EthernetProcessor
from .wifi_processor import WiFiProcessor
from .mesh_processor import MeshProcessor
from .mobile_processor import MobileProcessor

_LOGGER = logging.getLogger(__name__)

class KeeneticAPI:
    """Keenetic API client."""

    def __init__(self, host: str, username: str, password: str, port: int = 81) -> None:
        """Initialize the API client."""
        self._host = host
        self._username = username
        self._password = password
        self._port = port
        self._session = None
        self._auth_token = None
        self._base_url = f"http://{self._host}:{self._port}"

    async def authenticate(self) -> bool:
        """Authenticate with the router."""
        try:
            auth_string = base64.b64encode(
                f"{self._username}:{self._password}".encode()
            ).decode()

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._base_url}/rci/",
                    headers={"Authorization": f"Basic {auth_string}"},
                ) as response:
                    if response.status == 200:
                        self._auth_token = auth_string
                        return True
                    return False
        except Exception as ex:
            _LOGGER.error("Authentication failed: %s", str(ex))
            return False

    async def _get_system_info(self) -> dict:
        """Get system information."""
        if not self._auth_token:
            if not await self.authenticate():
                return {}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._base_url}{API_SYSTEM}",
                    headers={"Authorization": f"Basic {self._auth_token}"},
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        memory_total = int(data.get("memtotal", 0))
                        memory_free = int(data.get("memfree", 0))
                        memory_usage = round((memory_total - memory_free) / memory_total * 100, 1) if memory_total > 0 else 0

                        return {
                            "cpu_usage": data.get("cpuload", 0),
                            "uptime": data.get("uptime", 0),
                            "memory_usage": memory_usage,
                            "memory_free": memory_free,
                            "hostname": data.get("hostname", ""),
                            "domainname": data.get("domainname", ""),
                        }
                    return {}
        except Exception as ex:
            _LOGGER.error("Error getting system info: %s", str(ex))
            return {}

    async def _get_version_info(self) -> dict:
        """Get version information."""
        if not self._auth_token:
            if not await self.authenticate():
                return {}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._base_url}{API_VERSION}",
                    headers={"Authorization": f"Basic {self._auth_token}"},
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "firmware_version": data.get("title", ""),
                            "firmware_branch": data.get("sandbox", ""),
                            "model": data.get("model", ""),
                            "device": data.get("device", ""),
                            "manufacturer": data.get("manufacturer", MANUFACTURER),
                            "hardware_version": data.get("hw_version", ""),
                        }
                    return {}
        except Exception as ex:
            _LOGGER.error("Error getting version info: %s", str(ex))
            return {}

    async def _get_interface_status(self) -> dict:
        """Get interface status."""
        if not self._auth_token:
            if not await self.authenticate():
                return {}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._base_url}{API_INTERFACE}",
                    headers={"Authorization": f"Basic {self._auth_token}"},
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    return {}
        except Exception as ex:
            _LOGGER.error("Error getting interface status: %s", str(ex))
            return {}

    async def _get_interface_statistics(self, interface_name: str) -> dict:
        """Get interface statistics."""
        if not self._auth_token:
            if not await self.authenticate():
                return {}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._base_url}/rci/show/interface/stat?name={interface_name}",
                    headers={"Authorization": f"Basic {self._auth_token}"},
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return {}
        except Exception as ex:
            _LOGGER.error("Error getting interface statistics: %s", str(ex))
            return {}

    async def _get_mesh_info(self) -> list:
        """Get mesh network information."""
        if not self._auth_token:
            if not await self.authenticate():
                return []

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self._base_url}{API_MESH}"
                _LOGGER.debug("Requesting mesh info from: %s", url)
                async with session.get(
                    url,
                    headers={"Authorization": f"Basic {self._auth_token}"},
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        _LOGGER.debug("Raw mesh data received: %s", data)
                        if isinstance(data, list):
                            return data
                        elif isinstance(data, dict) and "member" in data:
                            return data["member"]
                        return []
                    return []
        except Exception as ex:
            _LOGGER.error("Error getting mesh info: %s", str(ex))
            return []

    async def get_system_info(self) -> dict:
        """Get system information for config flow."""
        try:
            data = await self.get_data()
            
            if not data:
                raise Exception("Failed to get system information")
    
            return {
                "device": data.get("device", "Router"),
                "manufacturer": data.get("manufacturer", "Keenetic"),
                "model": data.get("model", "Router"),
                "firmware_version": data.get("firmware_version", ""),
                "hardware_version": data.get("hardware_version", ""),
                "cpu_usage": data.get("cpu_usage", 0)
            }
        except Exception as ex:
            _LOGGER.error("Error in get_system_info: %s", str(ex))
            raise

    async def get_data(self) -> Dict[str, Any]:
        """Get all required data from router."""
        try:
            async with aiohttp.ClientSession() as session:
                system_info = await self._get_system_info()
                version_info = await self._get_version_info()
                interface_info = await self._get_interface_status()
                mesh_info = await self._get_mesh_info()

                ethernet_interfaces = await EthernetProcessor.process_ethernet_ports(
                    interface_info,
                    self._get_interface_statistics
                )

                wifi_interfaces = await WiFiProcessor.process_wifi_interfaces(session,self._base_url,self._auth_token)

                mobile_interfaces = await MobileProcessor.process_interfaces(session,self._base_url,self._auth_token)

                all_interfaces = {
                    **ethernet_interfaces,
                    **wifi_interfaces,
                    **mobile_interfaces
                }
                
                _LOGGER.debug("All interfaces: %s", all_interfaces)

                processed_mesh = MeshProcessor.process_mesh_nodes(mesh_info)

                return {
                    **system_info,
                    **version_info,
                    "interface": all_interfaces,
                    "mesh": processed_mesh
                }

        except Exception as ex:
            _LOGGER.error("Error getting data: %s", str(ex))
            return {}

    async def _get_wifi_interface_info(self, interface_name: str) -> dict:
        """Get detailed information about specific WiFi interface."""
        if not self._auth_token:
            if not await self.authenticate():
                return {}
    
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._base_url}/rci/interface/{interface_name}",
                    headers={"Authorization": f"Basic {self._auth_token}"},
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        _LOGGER.debug("WiFi interface data for %s: %s", interface_name, data)
                        return data
                    return {}
        except Exception as ex:
            _LOGGER.error("Error getting WiFi interface info: %s", str(ex))
            return {}

    async def enable_wifi(self, ap_id: str) -> bool:
        """Enable WiFi network."""
        if not self._auth_token:
            if not await self.authenticate():
                return False
    
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self._base_url}/rci/interface/{ap_id}",
                    headers={
                        "Authorization": f"Basic {self._auth_token}",
                        "Content-Type": "application/json"
                    },
                    json={"up": "true"}
                ) as response:
                    return response.status == 200
        except Exception as ex:
            _LOGGER.error("Error enabling WiFi network: %s", str(ex))
            return False
    
    async def disable_wifi(self, ap_id: str) -> bool:
        """Disable WiFi network."""
        if not self._auth_token:
            if not await self.authenticate():
                return False
    
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self._base_url}/rci/interface/{ap_id}",
                    headers={
                        "Authorization": f"Basic {self._auth_token}",
                        "Content-Type": "application/json"
                    },
                    json={"down": "true"}
                ) as response:
                    return response.status == 200
        except Exception as ex:
            _LOGGER.error("Error disabling WiFi network: %s", str(ex))
            return False
