"""Diagnostic script to identify negative consumption values."""
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from test_api import AguasCoimbraAPI
import aiohttp

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)


async def diagnose_consumption(username: str, password: str, meter_number: str, subscription_id: str):
    """Diagnose consumption data for negative values."""

    async with aiohttp.ClientSession() as session:
        api = AguasCoimbraAPI(session, username, password)

        try:
            # Login
            _LOGGER.info("Logging in...")
            await api.login()

            # Get consumption data for last 30 days
            _LOGGER.info("Fetching consumption data...")
            data = await api.get_consumption(meter_number, subscription_id, days=30)

            if not data:
                _LOGGER.error("No data returned from API")
                return

            # Sort by date
            sorted_data = sorted(
                data,
                key=lambda x: datetime.fromisoformat(x["date"].replace("+00:00", "").replace("+01:00", "")),
                reverse=True,
            )

            # Analyze the data
            _LOGGER.info(f"\n{'='*80}")
            _LOGGER.info(f"CONSUMPTION DATA ANALYSIS (Last 30 days)")
            _LOGGER.info(f"{'='*80}\n")

            now = datetime.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday_start = today_start - timedelta(days=1)

            total_readings = len(sorted_data)
            negative_count = 0
            positive_count = 0
            zero_count = 0

            today_total = 0
            yesterday_total = 0
            all_time_total = 0

            negative_readings = []

            _LOGGER.info("Recent readings (newest first):")
            _LOGGER.info(f"{'Date':<25} {'Consumption (L)':<20} {'Status':<15}")
            _LOGGER.info("-" * 60)

            for i, reading in enumerate(sorted_data[:10]):  # Show last 10 readings
                date_str = reading["date"]
                reading_date = datetime.fromisoformat(
                    date_str.replace("+00:00", "").replace("+01:00", "")
                )
                consumption = reading.get("consumption", 0)

                status = "✓ POSITIVE" if consumption > 0 else ("✗ NEGATIVE" if consumption < 0 else "ZERO")
                _LOGGER.info(f"{date_str:<25} {consumption:<20.2f} {status:<15}")

                if consumption < 0:
                    negative_readings.append((date_str, consumption))

            _LOGGER.info("\n" + "-" * 60)
            _LOGGER.info("\nFull data analysis:")
            _LOGGER.info("-" * 60)

            # Analyze all readings
            for reading in sorted_data:
                date_str = reading["date"]
                reading_date = datetime.fromisoformat(
                    date_str.replace("+00:00", "").replace("+01:00", "")
                )
                consumption = reading.get("consumption", 0)

                # Count by type
                if consumption < 0:
                    negative_count += 1
                    negative_readings.append((date_str, consumption))
                elif consumption > 0:
                    positive_count += 1
                else:
                    zero_count += 1

                # Calculate totals
                all_time_total += consumption

                if reading_date >= today_start:
                    today_total += consumption

                if reading_date >= yesterday_start and reading_date < today_start:
                    yesterday_total += consumption

            # Print summary
            _LOGGER.info(f"\nTotal readings: {total_readings}")
            _LOGGER.info(f"Positive values: {positive_count}")
            _LOGGER.info(f"Negative values: {negative_count} ⚠️")
            _LOGGER.info(f"Zero values: {zero_count}")

            _LOGGER.info(f"\n{'='*60}")
            _LOGGER.info("CONSUMPTION TOTALS:")
            _LOGGER.info(f"{'='*60}")
            _LOGGER.info(f"Today's total:     {today_total:>10.2f} L")
            _LOGGER.info(f"Yesterday's total: {yesterday_total:>10.2f} L")
            _LOGGER.info(f"All-time total:    {all_time_total:>10.2f} L")

            if negative_count > 0:
                _LOGGER.warning(f"\n{'='*60}")
                _LOGGER.warning(f"⚠️  FOUND {negative_count} NEGATIVE VALUES!")
                _LOGGER.warning(f"{'='*60}")
                _LOGGER.warning("\nAll negative readings:")
                for date_str, value in negative_readings[:20]:  # Show up to 20
                    _LOGGER.warning(f"  {date_str:<25} {value:>10.2f} L")

                if len(negative_readings) > 20:
                    _LOGGER.warning(f"\n  ... and {len(negative_readings) - 20} more negative values")

                _LOGGER.warning("\n" + "="*60)
                _LOGGER.warning("RECOMMENDATION:")
                _LOGGER.warning("="*60)
                _LOGGER.warning("""
These negative values are likely meter reading corrections or adjustments
from Águas de Coimbra.

Options to handle this:
1. Filter out negative values (treat as corrections)
2. Keep negative values but add warnings
3. Create separate sensor for 'adjustments/corrections'
4. Contact Águas de Coimbra to understand these corrections
                """)
            else:
                _LOGGER.info("\n✓ No negative values found")

        except Exception as e:
            _LOGGER.error(f"Error during diagnosis: {e}", exc_info=True)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python diagnose_negative_values.py <email> <password> <meter_number> <subscription_id>")
        print("\nExample:")
        print("  python diagnose_negative_values.py user@example.com mypassword ABC123 sub456")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]
    meter_number = sys.argv[3]
    subscription_id = sys.argv[4]

    asyncio.run(diagnose_consumption(username, password, meter_number, subscription_id))
