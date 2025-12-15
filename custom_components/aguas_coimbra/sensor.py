"""Sensor platform for Águas de Coimbra."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
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


class AguasCoimbraCumulativeSensor(AguasCoimbraSensorBase, RestoreEntity):
    """Sensor for cumulative water consumption total.

    This sensor maintains a monotonically increasing cumulative total by:
    - Restoring its last state value on startup
    - Tracking the last processed reading timestamp
    - Only adding consumption from new readings (not yet counted)
    - Never decreasing, even as old readings fall off the API's rolling window
    """

    def __init__(
        self,
        coordinator: AguasCoimbraDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, SENSOR_CUMULATIVE_TOTAL)
        self._cumulative_value: float = 0.0
        self._last_processed_date: str | None = None

    async def async_added_to_hass(self) -> None:
        """Restore last state when entity is added to hass."""
        await super().async_added_to_hass()

        # Restore the last cumulative value and last processed date
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                self._cumulative_value = float(last_state.state)
                _LOGGER.info(
                    "Restored cumulative total: %.2f L from previous state",
                    self._cumulative_value
                )

                # Only restore last processed date if cumulative value restoration succeeded
                # This prevents data loss from skipping readings while starting cumulative at 0
                if last_state.attributes:
                    self._last_processed_date = last_state.attributes.get("last_processed_date")
                    if self._last_processed_date:
                        _LOGGER.info(
                            "Restored last processed date: %s",
                            self._last_processed_date
                        )
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "Could not restore cumulative total, starting fresh from 0. "
                    "Last processed date will not be restored to avoid data loss."
                )
                self._cumulative_value = 0.0
                self._last_processed_date = None

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            # Return restored cumulative value even when coordinator data unavailable
            # This ensures the sensor displays the last known value after restart
            return self._cumulative_value if self._cumulative_value > 0 else None

        # Get all readings from coordinator
        all_readings = self.coordinator.data.get("all_readings", [])
        if not all_readings:
            return self._cumulative_value if self._cumulative_value > 0 else None

        # Calculate incremental consumption from NEW readings only
        incremental = 0.0
        most_recent_date = self._last_processed_date

        for reading in all_readings:
            try:
                reading_date_str = reading.get("date", "")
                if not reading_date_str:
                    continue

                # Normalize the date string (remove timezone offsets for consistent comparison)
                reading_date_str_clean = reading_date_str.replace("+00:00", "").replace("+01:00", "")

                # If we have a last processed date, only count readings newer than it
                if self._last_processed_date:
                    if reading_date_str_clean <= self._last_processed_date:
                        continue  # Skip already processed readings

                # Add this reading's consumption
                consumption = reading.get("consumption", 0)
                incremental += consumption

                # Track the most recent reading date (use normalized version)
                if most_recent_date is None or reading_date_str_clean > most_recent_date:
                    most_recent_date = reading_date_str_clean

            except (ValueError, KeyError, TypeError) as err:
                _LOGGER.warning("Error processing reading for cumulative total: %s", err)
                continue

        # Update cumulative value and last processed date
        if incremental > 0:
            self._cumulative_value += incremental
            self._last_processed_date = most_recent_date
            _LOGGER.debug(
                "Added %.2f L to cumulative total (new total: %.2f L, last date: %s)",
                incremental,
                self._cumulative_value,
                self._last_processed_date
            )

        return self._cumulative_value if self._cumulative_value > 0 else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        return {
            "last_processed_date": self._last_processed_date,
        }


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
