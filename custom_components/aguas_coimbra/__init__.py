"""The Águas de Coimbra integration."""
from __future__ import annotations

import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AguasCoimbraAPI
from .const import (
    CONF_HISTORY_DAYS,
    CONF_METER_NUMBER,
    CONF_SUBSCRIPTION_ID,
    CONF_UPDATE_INTERVAL,
    DEFAULT_HISTORY_DAYS,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)
from .coordinator import AguasCoimbraDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Águas de Coimbra from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Get configuration
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    meter_number = entry.data[CONF_METER_NUMBER]
    subscription_id = entry.data[CONF_SUBSCRIPTION_ID]

    update_interval = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    history_days = entry.options.get(CONF_HISTORY_DAYS, DEFAULT_HISTORY_DAYS)

    # Create API client
    session = async_get_clientsession(hass)
    api = AguasCoimbraAPI(session, username, password)

    # Create coordinator
    coordinator = AguasCoimbraDataUpdateCoordinator(
        hass,
        api,
        meter_number,
        subscription_id,
        update_interval,
        history_days,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info(
        "Águas de Coimbra integration set up successfully for meter %s",
        meter_number,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
