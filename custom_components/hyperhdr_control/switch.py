"""Switch platform for HyperHDR Control integration."""
from __future__ import annotations

import json
import logging
from typing import Any

import aiohttp
import async_timeout
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
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
    """Set up the HyperHDR Control switch."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    
    async_add_entities([HyperHDRSwitch(entry.entry_id, host, port)], True)

class HyperHDRSwitch(SwitchEntity):
    """Representation of a HyperHDR Control switch."""

    def __init__(self, entry_id: str, host: str, port: int) -> None:
        """Initialize the switch."""
        self._entry_id = entry_id
        self._host = host
        self._port = port
        self._attr_name = "HyperHDR USB Capture"
        self._attr_unique_id = f"hyperhdr_videograbber_{host}_{port}"
        self._attr_is_on = False

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this HyperHDR instance."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._host}:{self._port}")},
            manufacturer="HyperHDR",
            name=f"HyperHDR ({self._host})",
            model="HyperHDR LED Controller",
            sw_version="1.0.0",
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self._set_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self._set_state(False)

    async def _set_state(self, state: bool) -> None:
        """Set the state of the video grabber."""
        request_data = {
            "command": "componentstate",
            "componentstate": {
                "component": "VIDEOGRABBER",
                "state": state
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self._host}:{self._port}/json-rpc"
                async with async_timeout.timeout(10):
                    async with session.get(url, params={"request": json.dumps(request_data)}) as response:
                        if response.status == 200:
                            self._attr_is_on = state
                        else:
                            _LOGGER.error("Failed to set state: %s", response.status)
        except (aiohttp.ClientError, TimeoutError) as error:
            _LOGGER.error("Error setting state: %s", error)

    async def async_update(self) -> None:
        """Update the state of the switch."""
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
                            components = data.get("info", {}).get("components", [])
                            for component in components:
                                if component.get("name") == "VIDEOGRABBER":
                                    self._attr_is_on = component.get("enabled", False)
                                    break
        except (aiohttp.ClientError, TimeoutError) as error:
            _LOGGER.error("Error updating state: %s", error) 