"""Sensor platform for Cloudflare DDNS integration."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Cloudflare DDNS sensors from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        CloudflareDDNSSyncedSensor(coordinator, config_entry),
        CloudflareDDNSLastSyncSensor(coordinator, config_entry),
        CloudflareDDNSDomainSensor(coordinator, config_entry),
        CloudflareDDNSCurrentIPSensor(coordinator, config_entry),
    ]

    async_add_entities(entities)


class CloudflareDDNSBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Cloudflare DDNS sensors."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
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


class CloudflareDDNSSyncedSensor(CloudflareDDNSBaseSensor):
    """Sensor showing if DNS is synced."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = "Synced"
        self._attr_unique_id = f"{config_entry.entry_id}_synced"
        self._attr_icon = "mdi:sync"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return "Yes" if self.coordinator.data.get("synced") else "No"
        return "Unknown"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        if self.coordinator.data:
            return {
                "dns_record_ip": self.coordinator.data.get("dns_record_ip"),
                "current_ip": self.coordinator.data.get("current_ip"),
            }
        return {}


class CloudflareDDNSLastSyncSensor(CloudflareDDNSBaseSensor):
    """Sensor showing last sync time."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = "Last Sync"
        self._attr_unique_id = f"{config_entry.entry_id}_last_sync"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_icon = "mdi:clock-outline"

    @property
    def native_value(self) -> datetime | None:
        """Return the state of the sensor."""
        return self.coordinator.last_sync_time


class CloudflareDDNSDomainSensor(CloudflareDDNSBaseSensor):
    """Sensor showing the DDNS domain."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = "Domain"
        self._attr_unique_id = f"{config_entry.entry_id}_domain"
        self._attr_icon = "mdi:web"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("domain", self.coordinator.dns_record)
        return self.coordinator.dns_record


class CloudflareDDNSCurrentIPSensor(CloudflareDDNSBaseSensor):
    """Sensor showing the current IP address."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = "Current IP"
        self._attr_unique_id = f"{config_entry.entry_id}_current_ip"
        self._attr_icon = "mdi:ip"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("current_ip")
        return None
