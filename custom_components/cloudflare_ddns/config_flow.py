"""Config flow for Cloudflare DDNS integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_API_TOKEN,
    CONF_AUTO_UPDATE,
    CONF_DEVICE_NAME,
    CONF_DNS_RECORD,
    CONF_DISCORD_WEBHOOK_URL,
    CONF_NOTIFY_DISCORD,
    CONF_NOTIFY_TELEGRAM,
    CONF_PROXIED,
    CONF_TELEGRAM_BOT_TOKEN,
    CONF_TELEGRAM_CHAT_ID,
    CONF_TTL,
    CONF_UPDATE_INTERVAL,
    CONF_WHAT_IP,
    CONF_ZONE_ID,
    DEFAULT_AUTO_UPDATE,
    DEFAULT_NOTIFY_DISCORD,
    DEFAULT_NOTIFY_TELEGRAM,
    DEFAULT_PROXIED,
    DEFAULT_TTL,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_WHAT_IP,
    DOMAIN,
    IP_TYPE_EXTERNAL,
    IP_TYPE_INTERNAL,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    MIN_TTL,
    MAX_TTL,
    AUTO_TTL,
)

_LOGGER = logging.getLogger(__name__)


class CloudflareDDNSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cloudflare DDNS."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate TTL
            ttl = user_input.get(CONF_TTL, DEFAULT_TTL)
            if ttl != AUTO_TTL and (ttl < MIN_TTL or ttl > MAX_TTL):
                errors[CONF_TTL] = "invalid_ttl"

            # Validate internal IP cannot be proxied
            if (
                user_input.get(CONF_WHAT_IP) == IP_TYPE_INTERNAL
                and user_input.get(CONF_PROXIED, False)
            ):
                errors[CONF_PROXIED] = "internal_cannot_proxy"

            if not errors:
                # Create entry
                title = user_input.get(CONF_DEVICE_NAME, user_input[CONF_DNS_RECORD])
                return self.async_create_entry(title=title, data=user_input)

        # Build schema
        data_schema = vol.Schema(
            {
                vol.Required(CONF_DNS_RECORD): str,
                vol.Optional(CONF_DEVICE_NAME): str,
                vol.Required(CONF_ZONE_ID): str,
                vol.Required(CONF_API_TOKEN): str,
                vol.Required(
                    CONF_WHAT_IP, default=DEFAULT_WHAT_IP
                ): vol.In([IP_TYPE_EXTERNAL, IP_TYPE_INTERNAL]),
                vol.Optional(CONF_PROXIED, default=DEFAULT_PROXIED): bool,
                vol.Optional(CONF_TTL, default=DEFAULT_TTL): vol.Coerce(int),
                vol.Optional(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                ),
                vol.Optional(CONF_AUTO_UPDATE, default=DEFAULT_AUTO_UPDATE): bool,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_notifications(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle notification configuration step."""
        if user_input is not None:
            return self.async_create_entry(title="Cloudflare DDNS", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_NOTIFY_TELEGRAM, default=DEFAULT_NOTIFY_TELEGRAM
                ): bool,
                vol.Optional(CONF_TELEGRAM_CHAT_ID): str,
                vol.Optional(CONF_TELEGRAM_BOT_TOKEN): str,
                vol.Optional(CONF_NOTIFY_DISCORD, default=DEFAULT_NOTIFY_DISCORD): bool,
                vol.Optional(CONF_DISCORD_WEBHOOK_URL): str,
            }
        )

        return self.async_show_form(step_id="notifications", data_schema=data_schema)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> CloudflareDDNSOptionsFlowHandler:
        """Get the options flow for this handler."""
        return CloudflareDDNSOptionsFlowHandler(config_entry)


class CloudflareDDNSOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Cloudflare DDNS."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate TTL
            ttl = user_input.get(CONF_TTL, DEFAULT_TTL)
            if ttl != AUTO_TTL and (ttl < MIN_TTL or ttl > MAX_TTL):
                errors[CONF_TTL] = "invalid_ttl"

            # Validate internal IP cannot be proxied
            if (
                user_input.get(CONF_WHAT_IP) == IP_TYPE_INTERNAL
                and user_input.get(CONF_PROXIED, False)
            ):
                errors[CONF_PROXIED] = "internal_cannot_proxy"

            if not errors:
                return self.async_create_entry(title="", data=user_input)

        current_config = {**self.config_entry.data, **self.config_entry.options}

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_DNS_RECORD,
                    default=current_config.get(CONF_DNS_RECORD, ""),
                ): str,
                vol.Optional(
                    CONF_DEVICE_NAME,
                    description={"suggested_value": current_config.get(CONF_DEVICE_NAME)},
                ): str,
                vol.Required(
                    CONF_ZONE_ID,
                    default=current_config.get(CONF_ZONE_ID),
                ): str,
                vol.Required(
                    CONF_API_TOKEN,
                    default=current_config.get(CONF_API_TOKEN),
                ): str,
                vol.Required(
                    CONF_WHAT_IP,
                    default=current_config.get(CONF_WHAT_IP, DEFAULT_WHAT_IP),
                ): vol.In([IP_TYPE_EXTERNAL, IP_TYPE_INTERNAL]),
                vol.Optional(
                    CONF_PROXIED,
                    default=current_config.get(CONF_PROXIED, DEFAULT_PROXIED),
                ): bool,
                vol.Optional(
                    CONF_TTL,
                    default=current_config.get(CONF_TTL, DEFAULT_TTL),
                ): vol.Coerce(int),
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=current_config.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                    ),
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                ),
                vol.Optional(
                    CONF_AUTO_UPDATE,
                    default=current_config.get(CONF_AUTO_UPDATE, DEFAULT_AUTO_UPDATE),
                ): bool,
                vol.Optional(
                    CONF_NOTIFY_TELEGRAM,
                    default=current_config.get(CONF_NOTIFY_TELEGRAM, DEFAULT_NOTIFY_TELEGRAM),
                ): bool,
                vol.Optional(
                    CONF_TELEGRAM_CHAT_ID,
                    default=current_config.get(CONF_TELEGRAM_CHAT_ID, ""),
                ): str,
                vol.Optional(
                    CONF_TELEGRAM_BOT_TOKEN,
                    default=current_config.get(CONF_TELEGRAM_BOT_TOKEN, ""),
                ): str,
                vol.Optional(
                    CONF_NOTIFY_DISCORD,
                    default=current_config.get(CONF_NOTIFY_DISCORD, DEFAULT_NOTIFY_DISCORD),
                ): bool,
                vol.Optional(
                    CONF_DISCORD_WEBHOOK_URL,
                    default=current_config.get(CONF_DISCORD_WEBHOOK_URL, ""),
                ): str,
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=options_schema, errors=errors
        )
