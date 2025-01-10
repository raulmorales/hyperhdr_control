"""The HyperHDR Control integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.helpers import device_registry as dr
import asyncio

from .const import DOMAIN

# Define platforms to load
PLATFORMS = [
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.NUMBER,
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HyperHDR Control from a config entry."""
    # Store an instance of the "domain" that includes the host/port
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "host": entry.data[CONF_HOST],
        "port": entry.data[CONF_PORT],
    }

    # Register device
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, f"{entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}")},
        manufacturer="HyperHDR",
        name=f"HyperHDR ({entry.data[CONF_HOST]})",
        model="HyperHDR LED Controller",
        sw_version="1.3.2",
    )

    # Set up all platforms
    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok 