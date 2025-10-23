"""Config flow for Keenetic integration."""
from typing import Any
import logging
from urllib.parse import urlparse

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo
import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_ENABLE_MESH,
    CONF_UPDATE_INTERVAL,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_USERNAME,
    DEFAULT_ENABLE_MESH,
    DEFAULT_UPDATE_INTERVAL,
    ERROR_CANNOT_CONNECT,
    ERROR_INVALID_AUTH,
    ERROR_UNKNOWN,
    MANUFACTURER,
)
from .api import KeeneticAPI

_LOGGER = logging.getLogger(__name__)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class KeeneticConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Keenetic."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.discovered_host: str | None = None

    async def async_validate_input(self, data: dict) -> bool:
        """Validate the user input allows us to connect."""
        try:
            api = KeeneticAPI(
                host=data[CONF_HOST],
                username=data[CONF_USERNAME],
                password=data[CONF_PASSWORD],
                port=data[CONF_PORT],
            )

            if not await api.authenticate():
                raise InvalidAuth

            system_info = await api.get_system_info()
            if not system_info:
                raise CannotConnect

            return True

        except InvalidAuth:
            # Re-raise to be caught by caller
            raise
        except Exception as error:
            _LOGGER.exception("Unexpected exception during validation")
            raise CannotConnect from error

    async def async_step_ssdp(self, discovery_info: SsdpServiceInfo) -> FlowResult:
        """Handle a discovered Keenetic router."""
        hostname = urlparse(discovery_info.ssdp_location).hostname
        if not hostname:
            return self.async_abort(reason="no_host")

        await self.async_set_unique_id(discovery_info.upnp.get("serialNumber", hostname))
        self._abort_if_unique_id_configured(updates={CONF_HOST: hostname})

        self.discovered_host = hostname

        self.context["title_placeholders"] = {
            "name": discovery_info.upnp.get("friendlyName", "Keenetic Router"),
            "host": hostname,
        }

        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                user_input[CONF_HOST] = self.discovered_host or user_input[CONF_HOST]

                await self.async_validate_input(user_input)

                user_input[CONF_ENABLE_MESH] = DEFAULT_ENABLE_MESH
                user_input[CONF_UPDATE_INTERVAL] = DEFAULT_UPDATE_INTERVAL

                return self.async_create_entry(
                    title=f"Keenetic ({user_input[CONF_HOST]})",
                    data=user_input,
                )

            except CannotConnect:
                errors["base"] = ERROR_CANNOT_CONNECT
            except InvalidAuth:
                errors["base"] = ERROR_INVALID_AUTH
            except Exception:
                _LOGGER.exception("Unexpected exception in user step")
                errors["base"] = ERROR_UNKNOWN

        default_host = self.discovered_host or DEFAULT_HOST

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=default_host): str,
                    vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=1, max=65535),
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        # Do not pass config_entry; Core injects it after instantiation.
        return KeeneticOptionsFlow()


class KeeneticOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self) -> None:
        """Initialize options flow."""
        # Do not set self.config_entry here; Core will inject it.
        pass

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options  # Injected by Cor_
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ENABLE_MESH,
                        default=options.get(CONF_ENABLE_MESH, DEFAULT_ENABLE_MESH),
                    ): bool,
                    vol.Required(
                        CONF_UPDATE_INTERVAL,
                        default=options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=10, max=300)
                    ),
                }
            ),
        )