"""Button platform for HyperHDR Control integration."""
from __future__ import annotations

import json
import logging
from typing import Any

import aiohttp
import async_timeout
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import AVAILABLE_EFFECTS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the HyperHDR Control buttons."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    
    entities = []
    for effect in AVAILABLE_EFFECTS:
        entities.append(HyperHDREffectButton(host, port, effect))
    
    async_add_entities(entities, True)

class HyperHDREffectButton(ButtonEntity):
    """Representation of a HyperHDR Effect button."""

    def __init__(self, host: str, port: int, effect_name: str) -> None:
        """Initialize the button."""
        self._host = host
        self._port = port
        self._effect_name = effect_name
        self._attr_name = f"HyperHDR Effect {effect_name}"
        self._attr_unique_id = f"hyperhdr_effect_{host}_{port}_{effect_name.lower().replace(' ', '_')}"

    async def async_press(self) -> None:
        """Handle the button press."""
        request_data = {
            "command": "effect",
            "effect": {
                "name": self._effect_name
            },
            "duration": 0,
            "priority": 64,
            "origin": "Home Assistant"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self._host}:{self._port}/json-rpc"
                async with async_timeout.timeout(10):
                    async with session.get(url, params={"request": json.dumps(request_data)}) as response:
                        if response.status != 200:
                            _LOGGER.error("Failed to activate effect: %s", response.status)
        except (aiohttp.ClientError, TimeoutError) as error:
            _LOGGER.error("Error activating effect: %s", error) 