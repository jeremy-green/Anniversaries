"""The Anniversaries Integration."""
import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.config_validation import CONFIG_SCHEMA

from .const import (
    CONF_SENSORS,
    DOMAIN,
    ISSUE_URL,
    CC_STARTUP_VERSION,
    VERSION,
    CONFIG_SCHEMA,
)
from . import services

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    if config.get(DOMAIN) is None:
        # We get here if the integration is set up using config flow
        return True

    hass.async_create_task(
        CC_STARTUP_VERSION.format(name=DOMAIN, version=VERSION, issue_link=ISSUE_URL)
    )

    # Register services
    await services.async_register_services(hass)

    platform_config = config[DOMAIN].get(CONF_SENSORS, {})

    # If no platform is enabled, skip setup
    if not platform_config:
        return True

    # Skip setup if already configured
    if hass.data.get(DOMAIN):
        return True

    # Set up global data
    hass.data[DOMAIN] = {}

    # Load the platform from YAML config
    if platform_config:
        hass.async_create_task(
            hass.helpers.discovery.async_load_platform(
                "sensor", DOMAIN, platform_config, config
            )
        )
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data[DOMAIN] = {}

    hass.async_create_task(
        CC_STARTUP_VERSION.format(name=DOMAIN, version=VERSION, issue_link=ISSUE_URL)
    )

    # Register services
    await services.async_register_services(hass)

    # Safely update entry options if needed
    hass.config_entries.async_update_entry(
        config_entry, options=config_entry.data
    )

    try:
        # Load the platform again
        await hass.config_entries.async_forward_entry_setup(config_entry, "sensor")

        # Add update listener
        config_entry.add_update_listener(update_listener)

        return True
    except Exception as error:
        raise ConfigEntryNotReady from error


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle removal of an entry."""
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")
        _LOGGER.info(
            "Successfully removed sensor from the %s integration", DOMAIN,
        )
        return True
    except ValueError:
        _LOGGER.error("Failed to remove sensor from the %s integration", DOMAIN)
        return False


async def update_listener(hass, entry):
    """Update listener."""
    _LOGGER.debug("Updating listener")

    # Unload and reload platform to apply new settings
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)