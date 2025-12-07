"""The Cloudflare DDNS integration."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CLOUDFLARE_API_BASE,
    CONF_API_TOKEN,
    CONF_AUTO_UPDATE,
    CONF_DEVICE_NAME,
    CONF_DISCORD_WEBHOOK_URL,
    CONF_DNS_RECORD,
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
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    EXTERNAL_IP_URL,
    IP_TYPE_EXTERNAL,
    IP_TYPE_INTERNAL,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Cloudflare DDNS from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Get configuration
    config = {**entry.data, **entry.options}
    update_interval = config.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

    # Create coordinator
    coordinator = CloudflareDDNSCoordinator(
        hass,
        entry,
        config,
        timedelta(seconds=update_interval),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


class CloudflareDDNSCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Cloudflare DDNS data."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        config: dict,
        update_interval: timedelta,
    ) -> None:
        """Initialize."""
        self.config = config
        self.dns_record = config[CONF_DNS_RECORD]
        self.zone_id = config[CONF_ZONE_ID]
        self.api_token = config[CONF_API_TOKEN]
        self.what_ip = config[CONF_WHAT_IP]
        self.proxied = config.get(CONF_PROXIED, False)
        self.ttl = config.get(CONF_TTL, 120)
        self.auto_update_enabled = config.get(CONF_AUTO_UPDATE, DEFAULT_AUTO_UPDATE)
        self.session = async_get_clientsession(hass)
        self.last_sync_time: Optional[datetime] = None
        self._manual_sync_requested = False

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
            config_entry=entry,
        )

    async def _async_update_data(self) -> dict:
        """Update data via Cloudflare API."""
        try:
            # Check if this is a manual sync
            is_manual_sync = self._manual_sync_requested
            self._manual_sync_requested = False  # Reset flag

            # Get current IP
            current_ip = await self._get_current_ip()
            if not current_ip:
                raise UpdateFailed("Failed to get current IP address")

            # Get DNS record info
            dns_record_info = await self._get_dns_record_info()
            if not dns_record_info:
                raise UpdateFailed("Failed to get DNS record information")

            dns_record_id = dns_record_info.get("id")
            dns_record_ip = dns_record_info.get("content")
            is_proxied = dns_record_info.get("proxied")

            synced = (dns_record_ip == current_ip) and (is_proxied == self.proxied)

            # Update DNS if: manual sync requested OR (not synced and auto-update is enabled)
            if is_manual_sync or (not synced and self.auto_update_enabled):
                if not synced:
                    _LOGGER.info(
                        "DNS record %s is %s, updating to %s%s",
                        self.dns_record,
                        dns_record_ip,
                        current_ip,
                        " (manual sync)" if is_manual_sync else "",
                    )
                    success = await self._update_dns_record(dns_record_id, current_ip)
                    if success:
                        await self._send_notifications(current_ip, dns_record_ip)
                        synced = True
                        # Update last sync time after any successful DNS update
                        self.last_sync_time = dt_util.now()
                    else:
                        raise UpdateFailed("Failed to update DNS record")
                else:
                    # Already synced but manual sync was requested
                    _LOGGER.info("DNS record %s already synced (manual sync)", self.dns_record)
                    # Update last sync time for manual sync even if already synced
                    if is_manual_sync:
                        self.last_sync_time = dt_util.now()
            elif not synced and not self.auto_update_enabled:
                _LOGGER.debug(
                    "DNS record %s needs update but auto-update is disabled",
                    self.dns_record,
                )

            # Update last sync time on every check if auto update is enabled
            if self.auto_update_enabled and not is_manual_sync:
                self.last_sync_time = dt_util.now()

            return {
                "synced": synced,
                "current_ip": current_ip,
                "dns_record_ip": dns_record_ip,
                "domain": self.dns_record,
            }

        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timeout connecting to Cloudflare API") from err
        except Exception as err:
            raise UpdateFailed(f"Error updating data: {err}") from err

    async def _get_current_ip(self) -> str | None:
        """Get the current IP address."""
        try:
            if self.what_ip == IP_TYPE_EXTERNAL:
                # Get external IP
                async with self.session.get(EXTERNAL_IP_URL) as response:
                    if response.status == 200:
                        ip = (await response.text()).strip()
                        _LOGGER.debug("External IP: %s", ip)
                        return ip
            else:
                # For internal IP, we need to use local network detection
                # This is simplified - in a real implementation you'd use socket
                # or another method to get the local IP
                _LOGGER.warning(
                    "Internal IP detection not fully implemented in async context"
                )
                return None
        except Exception as err:
            _LOGGER.error("Error getting current IP: %s", err)
            return None

    async def _get_dns_record_info(self) -> dict | None:
        """Get DNS record information from Cloudflare."""
        try:
            url = f"{CLOUDFLARE_API_BASE}/zones/{self.zone_id}/dns_records"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
            params = {"name": self.dns_record}

            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success") and data.get("result"):
                        return data["result"][0]
        except Exception as err:
            _LOGGER.error("Error getting DNS record info: %s", err)
        return None

    async def _update_dns_record(self, record_id: str, ip: str) -> bool:
        """Update DNS record on Cloudflare."""
        try:
            url = f"{CLOUDFLARE_API_BASE}/zones/{self.zone_id}/dns_records/{record_id}"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
            data = {
                "type": "A",
                "name": self.dns_record,
                "content": ip,
                "ttl": self.ttl,
                "proxied": self.proxied,
            }

            async with self.session.put(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        _LOGGER.info(
                            "Successfully updated %s to %s", self.dns_record, ip
                        )
                        return True
        except Exception as err:
            _LOGGER.error("Error updating DNS record: %s", err)
        return False

    async def _send_notifications(self, new_ip: str, old_ip: str) -> None:
        """Send notifications if configured."""
        message = f"{self.dns_record} DNS Record Updated To: {new_ip} (was {old_ip})"

        # Telegram notification
        if self.config.get(CONF_NOTIFY_TELEGRAM):
            chat_id = self.config.get(CONF_TELEGRAM_CHAT_ID)
            bot_token = self.config.get(CONF_TELEGRAM_BOT_TOKEN)
            if chat_id and bot_token:
                try:
                    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    params = {"chat_id": chat_id, "text": message}
                    async with self.session.get(url, params=params) as response:
                        if response.status == 200:
                            _LOGGER.info("Telegram notification sent")
                except Exception as err:
                    _LOGGER.error("Error sending Telegram notification: %s", err)

        # Discord notification
        if self.config.get(CONF_NOTIFY_DISCORD):
            webhook_url = self.config.get(CONF_DISCORD_WEBHOOK_URL)
            if webhook_url:
                try:
                    payload = {"content": message}
                    headers = {"Content-Type": "application/json"}
                    async with self.session.post(
                        webhook_url, json=payload, headers=headers
                    ) as response:
                        if response.status in (200, 204):
                            _LOGGER.info("Discord notification sent")
                except Exception as err:
                    _LOGGER.error("Error sending Discord notification: %s", err)
