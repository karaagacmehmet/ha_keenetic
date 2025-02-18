"""Config flow for Keenetic integration."""
from typing import Any
import logging
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_ENABLE_MESH,  # Добавляем новые константы
    CONF_UPDATE_INTERVAL,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_USERNAME,
    DEFAULT_ENABLE_MESH,  # Добавляем значения по умолчанию
    DEFAULT_UPDATE_INTERVAL,
    ERROR_CANNOT_CONNECT,
    ERROR_INVALID_AUTH,
    ERROR_UNKNOWN,
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

            # Проверяем, что можем получить данные
            system_info = await api.get_system_info()
            if not system_info:
                raise CannotConnect

            return True

        except InvalidAuth:
            raise InvalidAuth
        except Exception as error:
            _LOGGER.exception("Unexpected exception")
            raise CannotConnect from error

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Проверка на уже существующую конфигурацию
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST]}_{user_input[CONF_PORT]}"
                )
                self._abort_if_unique_id_configured()

                # Проверка подключения
                await self.async_validate_input(user_input)

                # Добавляем значения по умолчанию для новых опций
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
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = ERROR_UNKNOWN

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
                    vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
                        vol.Coerce(int), 
                        vol.Range(min=1, max=65535)
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return KeeneticOptionsFlow(config_entry)


class KeeneticOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
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