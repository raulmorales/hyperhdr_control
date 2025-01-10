"""Number platform for HyperHDR Control integration."""
from __future__ import annotations

import json
import logging
from typing import Any

import aiohttp
import async_timeout
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the HyperHDR Control number entities."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    
    async_add_entities([
        HyperHDRBrightnessNumber(entry.entry_id, host, port)
    ], True)

class HyperHDRBrightnessNumber(NumberEntity):
    """Representation of a HyperHDR brightness control."""

    def __init__(self, entry_id: str, host: str, port: int) -> None:
        """Initialize the number entity."""
        self._entry_id = entry_id
        self._host = host
        self._port = port
        self._attr_name = "HyperHDR Brightness"
        self._attr_unique_id = f"hyperhdr_brightness_{host}_{port}"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_mode = NumberMode.SLIDER
        self._attr_native_unit_of_measurement = PERCENTAGE

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this HyperHDR instance."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._host}:{self._port}")},
            manufacturer="HyperHDR",
            name=f"HyperHDR ({self._host})",
            model="HyperHDR LED Controller",
            sw_version="1.2.0",
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set the brightness value."""
        request_data = {
            "command": "adjustment",
            "adjustment": {
                "classic_config": False,
                "brightness": int(value)
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self._host}:{self._port}/json-rpc"
                async with async_timeout.timeout(10):
                    async with session.get(url, params={"request": json.dumps(request_data)}) as response:
                        if response.status == 200:
                            self._attr_native_value = value
                        else:
                            _LOGGER.error("Failed to set brightness: %s", response.status)
        except (aiohttp.ClientError, TimeoutError) as error:
            _LOGGER.error("Error setting brightness: %s", error)

    async def async_update(self) -> None:
        """Update the current brightness value."""
        request_data = {
            "command": "serverinfo"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self._host}:{self._port}/json-rpc"
                async with async_timeout.timeout(10):
                    async with session.get(url, params={"request": json.dumps(request_data)}) as response:
                        if response.status == 200:
                            data = await response.json()
                            adjustment = data.get("info", {}).get("adjustment", {})
                            self._attr_native_value = float(adjustment.get("brightness", 100))
        except (aiohttp.ClientError, TimeoutError) as error:
            _LOGGER.error("Error updating brightness: %s", error) 