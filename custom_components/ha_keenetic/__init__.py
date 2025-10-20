"""The Keenetic integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import Platform
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import logging
from .const import DOMAIN, UPDATE_INTERVAL
from .api import KeeneticAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Keenetic from a config entry."""
    try:
        api = KeeneticAPI(
            host=entry.data["host"],
            username=entry.data["username"],
            password=entry.data["password"],
            port=entry.data["port"],
        )

        if not await api.authenticate():
            _LOGGER.error("Failed to authenticate with Keenetic router")
            raise ConfigEntryNotReady("Failed to authenticate")

        async def async_update_data():
            """Fetch data from API."""
            try:
                data = await api.get_data()
                _LOGGER.debug("Got data from API: %s", data)
                if not data or "interface" not in data:
                    _LOGGER.error("Invalid data received from API")
                    return None
                return data
            except Exception as ex:
                _LOGGER.error("Error getting data: %s", str(ex))
                raise

        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=async_update_data,
            update_interval=UPDATE_INTERVAL,
        )

        await coordinator.async_config_entry_first_refresh()
        
        if not coordinator.data:
            raise ConfigEntryNotReady("No data received from router")
            
        _LOGGER.debug("Initial coordinator data: %s", coordinator.data)

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {
            "coordinator": coordinator,
            "api": api,
        }
        
        _LOGGER.debug("Setting up platforms: %s", PLATFORMS)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        
        return True

    except Exception as ex:
        _LOGGER.error("Failed to setup Keenetic integration: %s", str(ex))
        raise ConfigEntryNotReady from ex

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok