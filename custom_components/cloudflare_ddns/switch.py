"""Switch platform for Cloudflare DDNS integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_AUTO_UPDATE, DEFAULT_AUTO_UPDATE, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Cloudflare DDNS switches from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        CloudflareDDNSAutoUpdateSwitch(coordinator, config_entry),
    ]

    async_add_entities(entities)


class CloudflareDDNSAutoUpdateSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable automatic DDNS updates."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_name = "Automatic Updates"
        self._attr_unique_id = f"{config_entry.entry_id}_auto_update"
        self._attr_icon = "mdi:update"
        self._attr_entity_category = EntityCategory.CONFIG
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

    @property
    def is_on(self) -> bool:
        """Return true if automatic updates are enabled."""
        return self.coordinator.auto_update_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on automatic updates."""
        # Update the coordinator property immediately
        self.coordinator.auto_update_enabled = True

        # Persist the state to config entry options
        self.hass.config_entries.async_update_entry(
            self._config_entry,
            options={**self._config_entry.options, CONF_AUTO_UPDATE: True},
        )

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off automatic updates."""
        # Update the coordinator property immediately
        self.coordinator.auto_update_enabled = False

        # Persist the state to config entry options
        self.hass.config_entries.async_update_entry(
            self._config_entry,
            options={**self._config_entry.options, CONF_AUTO_UPDATE: False},
        )

        self.async_write_ha_state()
