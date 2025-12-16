"""Debug script to examine the actual API data structure."""
import asyncio
import logging
import sys
import json
from datetime import datetime, timedelta
from tests.test_api import AguasCoimbraAPI
import aiohttp

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)


async def debug_api_structure(username: str, password: str, meter_number: str, subscription_id: str):
    """Debug the actual structure of API consumption data."""

    async with aiohttp.ClientSession() as session:
        api = AguasCoimbraAPI(session, username, password)

        try:
            # Login
            _LOGGER.info("Logging in...")
            await api.login()

            # Get consumption data for last 7 days
            _LOGGER.info("Fetching consumption data (last 7 days)...")
            data = await api.get_consumption(meter_number, subscription_id, days=7)

            if not data:
                _LOGGER.error("No data returned from API")
                return

            # Sort by date
            sorted_data = sorted(
                data,
                key=lambda x: datetime.fromisoformat(x["date"].replace("+00:00", "").replace("+01:00", "")),
                reverse=True,
            )

            _LOGGER.info(f"\n{'='*80}")
            _LOGGER.info(f"RAW API DATA STRUCTURE ANALYSIS")
            _LOGGER.info(f"{'='*80}\n")

            # Show first reading structure
            if sorted_data:
                _LOGGER.info("First reading (most recent) - FULL STRUCTURE:")
                _LOGGER.info(json.dumps(sorted_data[0], indent=2, default=str))

            _LOGGER.info(f"\n{'='*80}")
            _LOGGER.info("ALL READINGS (Last 7 days):")
            _LOGGER.info(f"{'='*80}\n")

            # Analyze date ranges
            now = datetime.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday_start = today_start - timedelta(days=1)

            today_readings = []
            yesterday_readings = []
            other_readings = []

            _LOGGER.info(f"Current time: {now}")
            _LOGGER.info(f"Today starts at: {today_start}")
            _LOGGER.info(f"Yesterday starts at: {yesterday_start}\n")

            for reading in sorted_data:
                date_str = reading["date"]
                reading_date = datetime.fromisoformat(
                    date_str.replace("+00:00", "").replace("+01:00", "")
                )
                consumption = reading.get("consumption", 0)

                # Categorize by date
                if reading_date >= today_start:
                    today_readings.append((date_str, consumption, reading))
                elif reading_date >= yesterday_start:
                    yesterday_readings.append((date_str, consumption, reading))
                else:
                    other_readings.append((date_str, consumption, reading))

            # Show today's readings
            _LOGGER.info(f"📅 TODAY's readings ({len(today_readings)}):")
            _LOGGER.info("-" * 80)
            today_sum = 0
            for date_str, consumption, reading in today_readings:
                today_sum += consumption
                _LOGGER.info(f"  Date: {date_str}")
                _LOGGER.info(f"  Consumption: {consumption} L")
                _LOGGER.info(f"  All fields: {json.dumps(reading, indent=4, default=str)}")
                _LOGGER.info("-" * 80)
            _LOGGER.info(f"TODAY's TOTAL (sum): {today_sum} L\n")

            # Show yesterday's readings
            _LOGGER.info(f"📅 YESTERDAY's readings ({len(yesterday_readings)}):")
            _LOGGER.info("-" * 80)
            yesterday_sum = 0
            for date_str, consumption, reading in yesterday_readings:
                yesterday_sum += consumption
                _LOGGER.info(f"  Date: {date_str}")
                _LOGGER.info(f"  Consumption: {consumption} L")
                _LOGGER.info(f"  All fields: {json.dumps(reading, indent=4, default=str)}")
                _LOGGER.info("-" * 80)
            _LOGGER.info(f"YESTERDAY's TOTAL (sum): {yesterday_sum} L\n")

            # Show other readings
            if other_readings:
                _LOGGER.info(f"📅 OLDER readings ({len(other_readings)}):")
                _LOGGER.info("-" * 80)
                for date_str, consumption, _ in other_readings[:5]:  # Show first 5
                    _LOGGER.info(f"  {date_str}: {consumption} L")
                if len(other_readings) > 5:
                    _LOGGER.info(f"  ... and {len(other_readings) - 5} more")
                _LOGGER.info("")

            _LOGGER.info(f"\n{'='*80}")
            _LOGGER.info("COMPARISON WITH HOME ASSISTANT:")
            _LOGGER.info(f"{'='*80}")
            _LOGGER.info(f"Portal shows for yesterday: +525 L")
            _LOGGER.info(f"Home Assistant shows: -525 L")
            _LOGGER.info(f"API data sum for yesterday: {yesterday_sum} L")
            _LOGGER.info(f"API data sum for today: {today_sum} L")

            if abs(yesterday_sum - 525) < 0.01:
                _LOGGER.info("\n✓ API data matches portal (+525L)")
                _LOGGER.info("⚠️  Issue is in Home Assistant processing/calculation!")
            elif abs(yesterday_sum + 525) < 0.01:
                _LOGGER.error("\n✗ API is returning negative value (-525L)")
                _LOGGER.error("⚠️  Issue is from Águas de Coimbra API!")
            else:
                _LOGGER.warning(f"\n? API sum ({yesterday_sum}L) doesn't match portal or HA")
                _LOGGER.warning("⚠️  May need to check calculation method")

            # Check for any unusual fields
            _LOGGER.info(f"\n{'='*80}")
            _LOGGER.info("CHECKING FOR UNUSUAL PATTERNS:")
            _LOGGER.info(f"{'='*80}")

            # Check all available fields in the data
            if sorted_data:
                all_keys = set()
                for reading in sorted_data:
                    all_keys.update(reading.keys())

                _LOGGER.info(f"\nAll available fields in API response:")
                for key in sorted(all_keys):
                    _LOGGER.info(f"  - {key}")

                # Check if there are any fields that might affect calculation
                sample_values = {}
                for key in all_keys:
                    values = [str(r.get(key, 'N/A')) for r in sorted_data[:3]]
                    sample_values[key] = values

                _LOGGER.info(f"\nSample values (3 most recent readings):")
                for key, values in sample_values.items():
                    _LOGGER.info(f"  {key}: {', '.join(values)}")

        except Exception as e:
            _LOGGER.error(f"Error during diagnosis: {e}", exc_info=True)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python debug_data_structure.py <email> <password> <meter_number> <subscription_id>")
        print("\nExample:")
        print("  python debug_data_structure.py user@example.com mypassword ABC123 sub456")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]
    meter_number = sys.argv[3]
    subscription_id = sys.argv[4]

    asyncio.run(debug_api_structure(username, password, meter_number, subscription_id))
