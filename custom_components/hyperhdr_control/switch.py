"""Switch platform for HyperHDR Control integration."""
from __future__ import annotations

import json
import logging
from typing import Any
from urllib.parse import urlencode

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

# Define component names as constants
COMP_VIDEOGRABBER = "VIDEOGRABBER"
COMP_LEDDEVICE = "LEDDEVICE"

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the HyperHDR Control switches."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    
    async_add_entities([
        HyperHDRSwitch(entry.entry_id, host, port, COMP_VIDEOGRABBER, "USB Capture"),
        HyperHDRSwitch(entry.entry_id, host, port, COMP_LEDDEVICE, "LED Output")
    ], True)

class HyperHDRSwitch(SwitchEntity):
    """Representation of a HyperHDR Control switch."""

    def __init__(self, entry_id: str, host: str, port: int, component: str, name: str) -> None:
        """Initialize the switch."""
        self._entry_id = entry_id
        self._host = host
        self._port = port
        self._component = component
        self._attr_name = f"HyperHDR {name}"
        self._attr_unique_id = f"hyperhdr_{component.lower()}_{host}_{port}"
        self._attr_is_on = False

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

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self._set_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self._set_state(False)

    async def _set_state(self, state: bool) -> None:
        """Set the state of the component."""
        request_data = {
            "command": "componentstate",
            "componentstate": {
                "component": self._component,
                "state": state
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self._host}:{self._port}/json-rpc"
                params = {"request": json.dumps(request_data, separators=(',', ':'))}
                _LOGGER.debug("Sending request to %s with params: %s", url, params)
                
                async with async_timeout.timeout(10):
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            self._attr_is_on = state
                            _LOGGER.debug("Successfully set %s state to %s", self._component, state)
                        else:
                            _LOGGER.error("Failed to set state for %s: %s", self._component, response.status)
                            response_text = await response.text()
                            _LOGGER.error("Response: %s", response_text)
        except (aiohttp.ClientError, TimeoutError) as error:
            _LOGGER.error("Error setting state for %s: %s", self._component, error)

    async def async_update(self) -> None:
        """Update the state of the switch."""
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
                            components = data.get("info", {}).get("components", [])
                            for component in components:
                                if component.get("name") == self._component:
                                    self._attr_is_on = component.get("enabled", False)
                                    break
        except (aiohttp.ClientError, TimeoutError) as error:
            _LOGGER.error("Error updating state: %s", error) 