"""Config flow for HyperHDR Control integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import device_registry as dr
import aiohttp
import async_timeout

from .const import DOMAIN, DEFAULT_PORT

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HyperHDR Control."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._host: str | None = None
        self._port: int | None = None
        self._name: str | None = None

    async def async_step_zeroconf(self, discovery_info) -> FlowResult:
        """Handle zeroconf discovery."""
        self._host = discovery_info.host
        self._port = discovery_info.port or DEFAULT_PORT
        self._name = discovery_info.name.replace("._hyperhdr-http._tcp.local.", "")

        # Check if already configured
        await self.async_set_unique_id(f"{self._host}:{self._port}")
        self._abort_if_unique_id_configured()

        # Set title for confirmation
        self.context["title_placeholders"] = {"name": self._name}
        
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input=None) -> FlowResult:
        """Handle user-confirmation of discovered node."""
        if user_input is not None:
            return await self._test_connection()

        return self.async_show_form(
            step_id="confirm",
            description_placeholders={
                "name": self._name,
                "host": self._host,
                "port": self._port,
            },
        )

    async def async_step_user(
        self, user_input: dict[str, any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._port = user_input[CONF_PORT]
            return await self._test_connection()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                }
            ),
            errors=errors,
        )

    async def _test_connection(self) -> FlowResult:
        """Test the connection to HyperHDR."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://{self._host}:{self._port}/json-rpc"
                test_request = {
                    "command": "serverinfo"
                }
                async with async_timeout.timeout(10):
                    async with session.get(url, params={"request": str(test_request)}) as response:
                        if response.status == 200:
                            await self.async_set_unique_id(
                                f"{self._host}:{self._port}", raise_on_progress=False
                            )
                            return self.async_create_entry(
                                title=self._name or f"HyperHDR ({self._host})",
                                data={
                                    CONF_HOST: self._host,
                                    CONF_PORT: self._port,
                                }
                            )
        except (aiohttp.ClientError, TimeoutError):
            pass

        return self.async_abort(reason="cannot_connect") 
