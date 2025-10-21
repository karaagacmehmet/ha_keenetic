"""Switch platform for Keenetic integration."""
from __future__ import annotations
from dataclasses import dataclass
import logging
from typing import Any, Final

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)


from .const import DOMAIN, MANUFACTURER
from .icons import ICON_MOBILE, ICON_MOBILE_OFF, ICON_WIFI, ICON_WIFI_OFF

_LOGGER = logging.getLogger(__name__)

@dataclass
class KeeneticSwitchEntityDescription(SwitchEntityDescription):
    """Class describing Keenetic switch entities."""
    ap_id: str = None
    value_fn: callable = lambda x: x
    available_fn: callable = lambda x: True

SWITCH_TYPES: Final[tuple[KeeneticSwitchEntityDescription, ...]] = (
    KeeneticSwitchEntityDescription(
        key="wifi_main",
        name="WiFi Main",
        icon="mdi:wifi",
        ap_id="AccessPoint0",
        value_fn=lambda x: x.get("link") == "up",
    ),
    KeeneticSwitchEntityDescription(
        key="wifi_guest",
        name="WiFi Guest",
        icon="mdi:wifi",
        ap_id="AccessPoint1",
        value_fn=lambda x: x.get("link") == "up",
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Keenetic switches."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []
    
    _LOGGER.debug("Setting up Keenetic switches")
    
    if not coordinator.data:
        _LOGGER.error("No data in coordinator")
        return
        
    _LOGGER.debug("Coordinator data: %s", coordinator.data)
    
    if "interface" not in coordinator.data:
        _LOGGER.error("No interface data in coordinator data")
        return
        

    wifi_interfaces = {
        k: v for k, v in coordinator.data["interface"].items()
        if k.startswith("WifiMaster") and "AccessPoint" in k
    }
    
    _LOGGER.debug("Found WiFi interfaces: %s", wifi_interfaces)
    
    for interface_id, interface_data in wifi_interfaces.items():
        _LOGGER.debug("Processing WiFi interface: %s = %s", interface_id, interface_data)
        
        if interface_data.get("ssid") or interface_data.get("description"):
            _LOGGER.debug("Creating switch for interface: %s", interface_id)
            entities.append(
                KeeneticWiFiSwitch(
                    coordinator,
                    interface_id,
                    config_entry,
                    api
                )
            )
        else:
            _LOGGER.debug(
                "Skipping interface %s: No SSID or description", 
                interface_id
            )

    if not entities:
        _LOGGER.warning(
            "No WiFi switches were created. Full interface data: %s",
            coordinator.data.get("interface", {})
        )
    

    mobile_interfaces = {
        k: v for k, v in coordinator.data["interface"].items()
        if k.startswith("UsbLte")
    }

    _LOGGER.debug("Found Mobile interfaces: %s", mobile_interfaces)

    for interface_id, interface_data in mobile_interfaces.items():
     _LOGGER.debug("Processing Mobile interface: %s = %s", interface_id, interface_data)
        
     if interface_data.get("ssid") or interface_data.get("description"):
        _LOGGER.debug("Creating switch for interface: %s", interface_id)
        entities.append(
            KeeneticMobileSwitch(
                coordinator,
                interface_id,
                config_entry,
                api
            )
        )
     else:
        _LOGGER.debug(
            "Skipping interface %s: No SSID or description", 
            interface_id
        )

    _LOGGER.debug("Created %d switch entities", len(entities))



    usb_modem_interfaces = {
        k: v for k, v in coordinator.data["interface"].items()
        if k.startswith("UsbModem")
    }

    _LOGGER.debug("Found Usb Modem interfaces: %s", usb_modem_interfaces)

    for interface_id, interface_data in usb_modem_interfaces.items():
     _LOGGER.debug("Processing Usb Modem  interface: %s = %s", interface_id, interface_data)
        
     if interface_data.get("ssid") or interface_data.get("description"):
        _LOGGER.debug("Creating switch for interface: %s", interface_id)
        entities.append(
            KeeneticMobileSwitch(
                coordinator,
                interface_id,
                config_entry,
                api
            )
        )
     else:
        _LOGGER.debug(
            "Skipping interface %s: No SSID or description", 
            interface_id
        )

    async_add_entities(entities)

class KeeneticWiFiSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Keenetic WiFi switch."""

    def __init__(
            self,
            coordinator: DataUpdateCoordinator,
            ap_id: str,
            config_entry: ConfigEntry,
            api,
        ) -> None:
            """Initialize the WiFi switch."""
            super().__init__(coordinator)
            self._ap_id = ap_id
            self._config_entry = config_entry
            self._api = api
            
            ap_data = self.coordinator.data["interface"][ap_id]
            ssid = ap_data.get("ssid", "")
            
            is_5ghz = "WifiMaster1" in ap_id
            is_guest = "AccessPoint1" in ap_id
            is_iot = "AccessPoint2" in ap_id
            
            prefix = "5GHz" if is_5ghz else "2.4GHz"
            self._attr_name = f"{ssid} ({prefix})"
                
            self._attr_unique_id = f"{config_entry.entry_id}_wifi_{ap_id}"
            self.entity_id = f"switch.keenetic_wifi_{ap_id.lower().replace('/', '_')}"
            
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, config_entry.entry_id)},
                name=f"Keenetic {coordinator.data.get('device', 'Router')}",
                manufacturer=coordinator.data.get('manufacturer', MANUFACTURER),
                model=coordinator.data.get('model', 'Router'),
                sw_version=coordinator.data.get('firmware_version', ''),
                hw_version=coordinator.data.get('hardware_version', ''),
            )
    
    @property
    def is_on(self) -> bool:
        """Return true if WiFi network is enabled."""
        if self.coordinator.data is None:
            return False
            
        ap_data = self.coordinator.data["interface"].get(self._ap_id, {})
        return ap_data.get("up", False)
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if self.coordinator.data is None:
            return {}
            
        ap_data = self.coordinator.data["interface"].get(self._ap_id, {})
        
        wifi_password = (
            ap_data.get("authentication", {})
            .get("wpa-psk", {})
            .get("psk", "")
        )
        
        return {
            "mac": ap_data.get("mac", ""),
            "ssid": ap_data.get("ssid", ""),
            "encryption": ap_data.get("encryption", ""),
            "interface_name": ap_data.get("interface-name", ""),
            "description": ap_data.get("description", ""),
            "connected": ap_data.get("connected", "no"),
            "type": ap_data.get("type", ""),
            "password": ap_data.get("password", ""),
        }

    @property
    def is_on(self) -> bool:
        """Return true if WiFi network is enabled."""
        if self.coordinator.data is None:
            return False
            
        ap_data = self.coordinator.data["interface"].get(self._ap_id, {})
        return ap_data.get("up", False) is True

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        return ICON_WIFI if self.is_on else ICON_WIFI_OFF

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the WiFi network."""
        try:
            await self._api.enable_wifi(self._ap_id)
            await self.coordinator.async_request_refresh()
        except Exception as ex:
            _LOGGER.error("Failed to turn on WiFi network %s: %s", self._ap_id, str(ex))

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the WiFi network."""
        try:
            await self._api.disable_wifi(self._ap_id)
            await self.coordinator.async_request_refresh()
        except Exception as ex:
            _LOGGER.error("Failed to turn off WiFi network %s: %s", self._ap_id, str(ex))


class KeeneticMobileSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Keenetic Mobile switch."""

    def __init__(
            self,
            coordinator: DataUpdateCoordinator,
            ap_id: str,
            config_entry: ConfigEntry,
            api,
        ) -> None:
            """Initialize the Mobile switch."""
            super().__init__(coordinator)
            self._ap_id = ap_id
            self._config_entry = config_entry
            self._api = api
        
            ap_data = self.coordinator.data["interface"][ap_id]
       
            self._attr_name = f"{ap_data.get("description","")}"
                
            self._attr_unique_id = f"{config_entry.entry_id}_mobile_{ap_id}"
            self.entity_id = f"switch.keenetic_mobile_{ap_id.lower().replace('/', '_')}"
            
            # self._attr_device_info = DeviceInfo(
            #     identifiers={(DOMAIN, config_entry.entry_id)},
            #     name=f"{ap_data.get("description","")}",
            #     manufacturer=coordinator.data.get('manufacturer', MANUFACTURER),
            #     model=coordinator.data.get('model', 'Router'),
            #     sw_version=coordinator.data.get('firmware_version', ''),
            #     hw_version=coordinator.data.get('hardware_version', ''),
            # )

            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, config_entry.entry_id)},
                name=f"Keenetic {coordinator.data.get('device', 'Router')}",
                manufacturer=coordinator.data.get('manufacturer', MANUFACTURER),
                model=coordinator.data.get('model', 'Router'),
                sw_version=coordinator.data.get('firmware_version', ''),
                hw_version=coordinator.data.get('hardware_version', ''),
            )
    
    @property
    def is_on(self) -> bool:
        """Return true if Mobile network is enabled."""
        if self.coordinator.data is None:
            return False
            
        ap_data = self.coordinator.data["interface"].get(self._ap_id, {})
        return ap_data.get("up", False)
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if self.coordinator.data is None:
            return {}
            
        ap_data = self.coordinator.data["interface"].get(self._ap_id, {})    
        
        return {                    
            "interface_name": ap_data.get("interface-name", ""),
            "description": ap_data.get("description", ""),
            "connected": ap_data.get("connected", "no"),
            "type": ap_data.get("type", ""),         
            "mac": ap_data.get("mac", ""),
            "mobile": ap_data.get("mobile", ""),
            "operator": ap_data.get("operator", ""),     
            "connection-state" : ap_data.get("connection-state",""),
            "state" : ap_data.get("state",""),         
            "sim": ap_data.get("sim"),
            "up": True if  ap_data.get("connected") == "yes" else False,
            "link": ap_data.get("link"),
            "temperature": ap_data.get("temperature"),         
        }

    @property
    def is_on(self) -> bool:
        """Return true if Mobile network is enabled."""
        if self.coordinator.data is None:
            return False
            
        ap_data = self.coordinator.data["interface"].get(self._ap_id, {})
        return ap_data.get("up", False) is True

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        return ICON_MOBILE if self.is_on else ICON_MOBILE_OFF

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the Mobile network."""
        try:
            await self._api.enable_wifi(self._ap_id)
            await self.coordinator.async_request_refresh()
        except Exception as ex:
            _LOGGER.error("Failed to turn on Mobile network %s: %s", self._ap_id, str(ex))

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the Mobile network."""
        try:
            await self._api.disable_wifi(self._ap_id)
            await self.coordinator.async_request_refresh()
        except Exception as ex:
            _LOGGER.error("Failed to turn off Mobile network %s: %s", self._ap_id, str(ex))