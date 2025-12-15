"""Sensor platform for Águas de Coimbra."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    SENSOR_CUMULATIVE_TOTAL,
    SENSOR_DAILY_CONSUMPTION,
    SENSOR_LATEST_READING,
    SENSOR_MONTHLY_CONSUMPTION,
    SENSOR_TYPES,
    SENSOR_WEEKLY_CONSUMPTION,
)
from .coordinator import AguasCoimbraDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Águas de Coimbra sensors based on a config entry."""
    coordinator: AguasCoimbraDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        AguasCoimbraLatestReadingSensor(coordinator, entry),
        AguasCoimbraCumulativeSensor(coordinator, entry),
        AguasCoimbraDailySensor(coordinator, entry),
        AguasCoimbraWeeklySensor(coordinator, entry),
        AguasCoimbraMonthlySensor(coordinator, entry),
    ]

    async_add_entities(entities)


class AguasCoimbraSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Águas de Coimbra sensors."""

    def __init__(
        self,
        coordinator: AguasCoimbraDataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"
        self._sensor_type = sensor_type

        sensor_config = SENSOR_TYPES[sensor_type]
        self._attr_name = sensor_config["name"]
        self._attr_icon = sensor_config["icon"]
        self._attr_native_unit_of_measurement = sensor_config["unit"]
        self._attr_device_class = sensor_config.get("device_class")
        self._attr_state_class = sensor_config.get("state_class")

        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Águas de Coimbra {coordinator.meter_number}",
            "manufacturer": "Águas de Coimbra",
            "model": "Water Meter",
            "sw_version": "1.0.0",
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self.coordinator.data is not None


class AguasCoimbraLatestReadingSensor(AguasCoimbraSensorBase):
    """Sensor for the latest water consumption reading."""

    def __init__(
        self,
        coordinator: AguasCoimbraDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, SENSOR_LATEST_READING)

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("latest_reading")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}

        return {
            "last_reading_date": self.coordinator.data.get("last_reading_date"),
            "cil": self.coordinator.data.get("cil"),
            "meter_number": self.coordinator.data.get("meter_number"),
        }


class AguasCoimbraCumulativeSensor(AguasCoimbraSensorBase):
    """Sensor for cumulative water consumption total."""

    def __init__(
        self,
        coordinator: AguasCoimbraDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, SENSOR_CUMULATIVE_TOTAL)

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("cumulative_total")
        return None


class AguasCoimbraDailySensor(AguasCoimbraSensorBase):
    """Sensor for daily water consumption total."""

    def __init__(
        self,
        coordinator: AguasCoimbraDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, SENSOR_DAILY_CONSUMPTION)

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("daily_total")
        return None


class AguasCoimbraWeeklySensor(AguasCoimbraSensorBase):
    """Sensor for weekly water consumption total."""

    def __init__(
        self,
        coordinator: AguasCoimbraDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, SENSOR_WEEKLY_CONSUMPTION)

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("weekly_total")
        return None


class AguasCoimbraMonthlySensor(AguasCoimbraSensorBase):
    """Sensor for monthly water consumption total."""

    def __init__(
        self,
        coordinator: AguasCoimbraDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, SENSOR_MONTHLY_CONSUMPTION)

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("monthly_total")
        return None
