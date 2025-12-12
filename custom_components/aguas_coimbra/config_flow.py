"""Config flow for Águas de Coimbra integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AguasCoimbraAPI, LoginError, ConnectionError as APIConnectionError
from .const import (
    CONF_METER_NUMBER,
    CONF_SUBSCRIPTION_ID,
    DOMAIN,
    ERROR_AUTH_FAILED,
    ERROR_CANNOT_CONNECT,
    ERROR_UNKNOWN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_METER_NUMBER): str,
        vol.Optional(CONF_SUBSCRIPTION_ID): str,
    }
)

STEP_SUBSCRIPTION_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SUBSCRIPTION_ID): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    api = AguasCoimbraAPI(session, data[CONF_USERNAME], data[CONF_PASSWORD])

    # Validate credentials by attempting login
    await api.login()

    # Return info to be stored in the config entry
    meter_number = data.get(CONF_METER_NUMBER, "Unknown")
    return {"title": f"Águas de Coimbra {meter_number}"}


class AguasCoimbraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Águas de Coimbra."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._username: str | None = None
        self._password: str | None = None
        self._subscription_id: str | None = None
        self._meter_number: str | None = None
        self._discovered_contracts: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate credentials
                session = async_get_clientsession(self.hass)
                api = AguasCoimbraAPI(
                    session, user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                )
                await api.login()

                # Store credentials and meter number
                self._username = user_input[CONF_USERNAME]
                self._password = user_input[CONF_PASSWORD]
                self._meter_number = user_input[CONF_METER_NUMBER]

                # If user provided subscription_id, use it directly
                if user_input.get(CONF_SUBSCRIPTION_ID):
                    self._subscription_id = user_input[CONF_SUBSCRIPTION_ID]

                    # Check if already configured
                    await self.async_set_unique_id(
                        f"{self._subscription_id}_{self._meter_number}"
                    )
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=f"Águas de Coimbra {self._meter_number}",
                        data={
                            CONF_USERNAME: self._username,
                            CONF_PASSWORD: self._password,
                            CONF_SUBSCRIPTION_ID: self._subscription_id,
                            CONF_METER_NUMBER: self._meter_number,
                        },
                    )

                # Try to auto-discover subscription ID
                _LOGGER.debug("Attempting to auto-discover subscription ID")
                subscriptions = await api.get_user_subscriptions()

                if subscriptions:
                    _LOGGER.info("Found %d subscription(s)", len(subscriptions))

                    # Extract subscription ID from first subscription
                    first_subscription = subscriptions[0]
                    subscription_id = first_subscription.get("subscriptionId")

                    if subscription_id:
                        self._subscription_id = str(subscription_id)
                        _LOGGER.info("Auto-discovered subscription ID: %s", self._subscription_id)

                        # Check if already configured
                        await self.async_set_unique_id(
                            f"{self._subscription_id}_{self._meter_number}"
                        )
                        self._abort_if_unique_id_configured()

                        return self.async_create_entry(
                            title=f"Águas de Coimbra {self._meter_number}",
                            data={
                                CONF_USERNAME: self._username,
                                CONF_PASSWORD: self._password,
                                CONF_SUBSCRIPTION_ID: self._subscription_id,
                                CONF_METER_NUMBER: self._meter_number,
                            },
                        )

                # If auto-discovery failed, ask for subscription ID manually
                _LOGGER.info("Auto-discovery failed, requesting subscription ID manually")
                return await self.async_step_subscription()

            except LoginError:
                errors["base"] = ERROR_AUTH_FAILED
            except APIConnectionError:
                errors["base"] = ERROR_CANNOT_CONNECT
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = ERROR_UNKNOWN

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_subscription(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual input of subscription ID."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._subscription_id = user_input[CONF_SUBSCRIPTION_ID]

            # Check if already configured
            await self.async_set_unique_id(
                f"{self._subscription_id}_{self._meter_number}"
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Águas de Coimbra {self._meter_number}",
                data={
                    CONF_USERNAME: self._username,
                    CONF_PASSWORD: self._password,
                    CONF_SUBSCRIPTION_ID: self._subscription_id,
                    CONF_METER_NUMBER: self._meter_number,
                },
            )

        return self.async_show_form(
            step_id="subscription",
            data_schema=STEP_SUBSCRIPTION_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "meter_number": self._meter_number or "your meter",
                "info": "Could not automatically find your subscription ID. Please enter it manually. You can find this in the browser network tab when accessing the Águas de Coimbra portal.",
            },
        )
