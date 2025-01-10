"""Config flow for HyperHDR Control integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import aiohttp
import async_timeout

DOMAIN = "hyperhdr_control"

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HyperHDR Control."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Test the connection
                async with aiohttp.ClientSession() as session:
                    url = f"http://{user_input[CONF_HOST]}:{user_input[CONF_PORT]}/json-rpc"
                    test_request = {
                        "command": "serverinfo"
                    }
                    async with async_timeout.timeout(10):
                        async with session.get(url, params={"request": str(test_request)}) as response:
                            if response.status == 200:
                                return self.async_create_entry(
                                    title=f"HyperHDR Control ({user_input[CONF_HOST]})",
                                    data=user_input
                                )
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=8090): int,
                }
            ),
            errors=errors,
        ) 