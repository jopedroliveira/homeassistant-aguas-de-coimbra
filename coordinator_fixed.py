"""Data update coordinator for Águas de Coimbra - IMPROVED VERSION with negative value handling."""
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AguasCoimbraAPI, AguasCoimbraAPIError
from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class AguasCoimbraDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Águas de Coimbra data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: AguasCoimbraAPI,
        meter_number: str,
        subscription_id: str,
        update_interval: timedelta = DEFAULT_UPDATE_INTERVAL,
        history_days: int = 90,
        filter_negative_values: bool = True,  # NEW: Option to filter negative values
    ) -> None:
        """Initialize the coordinator."""
        self.api = api
        self.meter_number = meter_number
        self.subscription_id = subscription_id
        self.history_days = history_days
        self.filter_negative_values = filter_negative_values

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{meter_number}",
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Águas de Coimbra API."""
        try:
            # Fetch consumption data
            consumption_data = await self.api.get_consumption(
                self.meter_number,
                self.subscription_id,
                self.history_days,
            )

            # Process and aggregate the data
            processed_data = self._process_consumption_data(consumption_data)

            _LOGGER.debug(
                "Successfully updated data for meter %s: %s",
                self.meter_number,
                processed_data,
            )

            return processed_data

        except AguasCoimbraAPIError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    def _process_consumption_data(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        """Process raw consumption data and calculate aggregates."""
        if not data:
            _LOGGER.warning("No consumption data received")
            return {
                "latest_reading": None,
                "daily_total": 0,
                "weekly_total": 0,
                "monthly_total": 0,
                "last_reading_date": None,
                "all_readings": [],
                "negative_values_found": 0,
                "adjustments_total": 0,
            }

        # Sort by date (most recent first)
        sorted_data = sorted(
            data,
            key=lambda x: datetime.fromisoformat(x["date"].replace("+00:00", "").replace("+01:00", "")),
            reverse=True,
        )

        # Get latest reading
        latest = sorted_data[0] if sorted_data else None
        latest_reading = latest["consumption"] if latest else None
        last_reading_date = latest["date"] if latest else None
        cil = latest.get("cil") if latest else None

        # Calculate date ranges
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Calculate totals
        daily_total = 0
        weekly_total = 0
        monthly_total = 0

        # NEW: Track negative values
        negative_values_count = 0
        adjustments_total = 0  # Sum of all negative values (corrections/adjustments)

        for reading in sorted_data:
            try:
                reading_date = datetime.fromisoformat(
                    reading["date"].replace("+00:00", "").replace("+01:00", "")
                )
                consumption = reading.get("consumption", 0)

                # NEW: Track negative values
                if consumption < 0:
                    negative_values_count += 1
                    adjustments_total += consumption
                    _LOGGER.warning(
                        "Negative consumption value detected: %s L on %s",
                        consumption,
                        reading["date"]
                    )

                    # NEW: Optionally skip negative values
                    if self.filter_negative_values:
                        _LOGGER.debug(
                            "Filtering out negative value (filter_negative_values=True)"
                        )
                        continue

                # Daily total (today only)
                if reading_date >= today_start:
                    daily_total += consumption

                # Weekly total (last 7 days)
                if reading_date >= week_start:
                    weekly_total += consumption

                # Monthly total (current month)
                if reading_date >= month_start:
                    monthly_total += consumption

            except (ValueError, KeyError) as err:
                _LOGGER.warning("Error processing reading: %s", err)
                continue

        # NEW: Log summary of negative values if found
        if negative_values_count > 0:
            _LOGGER.warning(
                "Found %d negative consumption values (total: %.2f L). "
                "These may be meter reading corrections or adjustments. "
                "filter_negative_values=%s",
                negative_values_count,
                adjustments_total,
                self.filter_negative_values,
            )

        return {
            "latest_reading": latest_reading,
            "daily_total": max(0, daily_total) if self.filter_negative_values else daily_total,
            "weekly_total": max(0, weekly_total) if self.filter_negative_values else weekly_total,
            "monthly_total": max(0, monthly_total) if self.filter_negative_values else monthly_total,
            "last_reading_date": last_reading_date,
            "cil": cil,
            "meter_number": self.meter_number,
            "all_readings": sorted_data[:100],  # Keep last 100 readings
            "negative_values_found": negative_values_count,  # NEW
            "adjustments_total": adjustments_total,  # NEW
        }
