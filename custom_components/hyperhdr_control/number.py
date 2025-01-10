"""Number platform for HyperHDR Control integration."""
from __future__ import annotations

import json
import logging
from typing import Any
import asyncio
from datetime import datetime, timedelta

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

THROTTLE_DELAY = 1.0  # Delay in seconds between API calls

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
        self._attr_native_value = 100  # Set initial value
        self._attr_available = True  # Explicitly set availability
        self._last_update = datetime.min
        self._pending_value = None
        self._update_lock = asyncio.Lock()
        self._update_task = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this HyperHDR instance."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._host}:{self._port}")},
            manufacturer="HyperHDR",
            name=f"HyperHDR ({self._host})",
            model="HyperHDR LED Controller",
            sw_version="1.3.3",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._attr_available

    async def _delayed_update(self) -> None:
        """Handle the delayed update of the brightness value."""
        try:
            while True:
                async with self._update_lock:
                    if self._pending_value is None:
                        self._update_task = None
                        return
                    
                    value = self._pending_value
                    self._pending_value = None
                
                await self._set_brightness(value)
                await asyncio.sleep(THROTTLE_DELAY)
        except Exception as error:
            _LOGGER.error("Error in delayed update: %s", error)
            self._update_task = None

    async def async_set_native_value(self, value: float) -> None:
        """Set the brightness value with throttling."""
        async with self._update_lock:
            self._pending_value = value
            self._attr_native_value = value
            
            if self._update_task is None:
                self._update_task = asyncio.create_task(self._delayed_update())

    async def _set_brightness(self, value: float) -> None:
        """Send the brightness value to HyperHDR."""
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
                params = {"request": json.dumps(request_data, separators=(',', ':'))}
                _LOGGER.debug("Sending brightness request to %s with params: %s", url, params)
                
                async with async_timeout.timeout(10):
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            self._attr_available = True
                        else:
                            self._attr_available = False
                            _LOGGER.error("Failed to set brightness: %s", response.status)
                            response_text = await response.text()
                            _LOGGER.error("Response: %s", response_text)
        except (aiohttp.ClientError, TimeoutError) as error:
            self._attr_available = False
            _LOGGER.error("Error setting brightness: %s", error)

    async def async_update(self) -> None:
        """Update the current brightness value."""
        request_data = {
            "command": "serverinfo"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self._host}:{self._port}/json-rpc"
                params = {"request": json.dumps(request_data, separators=(',', ':'))}
                
                async with async_timeout.timeout(10):
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            _LOGGER.debug("Received serverinfo response: %s", data)
                            
                            # Find the brightness in the adjustment array
                            adjustments = data.get("info", {}).get("adjustment", [])
                            if isinstance(adjustments, list) and adjustments:
                                # Take the first adjustment's brightness value
                                brightness = adjustments[0].get("brightness", 100)
                                self._attr_native_value = float(brightness)
                            
                            self._attr_available = True
                        else:
                            self._attr_available = False
        except (aiohttp.ClientError, TimeoutError) as error:
            self._attr_available = False
            _LOGGER.error("Error updating brightness: %s", error) 