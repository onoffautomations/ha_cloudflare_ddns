"""Button platform for Cloudflare DDNS integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Cloudflare DDNS buttons from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        CloudflareDDNSSyncButton(coordinator, config_entry),
    ]

    async_add_entities(entities)


class CloudflareDDNSSyncButton(CoordinatorEntity, ButtonEntity):
    """Button to manually trigger a DNS sync."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_name = "Sync Now"
        self._attr_unique_id = f"{config_entry.entry_id}_sync_now"
        self._attr_icon = "mdi:refresh"
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information about this entity."""
        device_name = self._config_entry.data.get(
            "device_name", self.coordinator.dns_record
        )
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": f"Cloudflare DDNS {device_name}",
            "manufacturer": "Onoff automations",
            "model": "DDNS",
            "entry_type": "service",
        }

    async def async_press(self) -> None:
        """Handle the button press - trigger immediate sync."""
        _LOGGER.info("Manual sync triggered for %s", self.coordinator.dns_record)
        # Set manual sync flag before requesting refresh
        self.coordinator._manual_sync_requested = True
        await self.coordinator.async_request_refresh()
