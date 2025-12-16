#!/usr/bin/env python3
"""Test script for cumulative sensor logic."""
import asyncio
from datetime import datetime
import aiohttp

# Import the API
from .test_api import AguasCoimbraAPI


class MockCoordinatorData:
    """Mock coordinator data for testing."""
    def __init__(self, readings):
        self.data = {
            "all_readings": readings,
            "latest_reading": readings[0]["consumption"] if readings else None,
            "last_reading_date": readings[0]["date"] if readings else None,
        }


class TestCumulativeSensor:
    """Test the cumulative sensor logic."""

    def __init__(self):
        self._cumulative_value = 0.0
        self._last_processed_date = None

    def process_readings(self, all_readings):
        """Process readings like the real sensor does."""
        if not all_readings:
            return self._cumulative_value if self._cumulative_value > 0 else None

        # Calculate incremental consumption from NEW readings only
        incremental = 0.0
        most_recent_date = self._last_processed_date
        processed_count = 0
        skipped_count = 0

        print(f"\n   Current state:")
        print(f"      Cumulative value: {self._cumulative_value} L")
        print(f"      Last processed date: {self._last_processed_date}")
        print(f"      Total readings to process: {len(all_readings)}")

        for reading in all_readings:
            try:
                reading_date_str = reading.get("date", "")
                if not reading_date_str:
                    continue

                # Normalize the date string
                reading_date_str_clean = reading_date_str.replace("+00:00", "").replace("+01:00", "")

                # If we have a last processed date, only count readings newer than it
                if self._last_processed_date:
                    if reading_date_str_clean <= self._last_processed_date:
                        skipped_count += 1
                        continue  # Skip already processed readings

                # Add this reading's consumption
                consumption = reading.get("consumption", 0)
                incremental += consumption
                processed_count += 1

                # Track the most recent reading date
                if most_recent_date is None or reading_date_str_clean > most_recent_date:
                    most_recent_date = reading_date_str_clean

            except (ValueError, KeyError, TypeError) as err:
                print(f"      ⚠️  Error processing reading: {err}")
                continue

        print(f"\n   Processing results:")
        print(f"      New readings processed: {processed_count}")
        print(f"      Readings skipped (already counted): {skipped_count}")
        print(f"      Incremental consumption: {incremental} L")

        # Update cumulative value and last processed date
        if incremental > 0:
            self._cumulative_value += incremental
            self._last_processed_date = most_recent_date
            print(f"      ✅ Updated cumulative: {self._cumulative_value} L")
            print(f"      ✅ Updated last processed date: {self._last_processed_date}")
        else:
            print(f"      ⚠️  No new consumption to add (incremental = 0)")

        result = self._cumulative_value if self._cumulative_value > 0 else None
        print(f"\n   Sensor would return: {result}")

        return result


async def test_cumulative_logic():
    """Test the cumulative sensor logic with real API data."""
    print("\n" + "=" * 60)
    print("Cumulative Sensor Logic Test")
    print("=" * 60)

    # Get credentials
    username = ""
    password = ""

    try:
        with open('.envrc', 'r') as f:
            lines = f.readlines()
            credentials = {}
            for line in lines:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    credentials[key] = value.strip("'\"")

        username = credentials.get('LOGIN_USERNAME', '')
        password = credentials.get('LOGIN_PASSWORD', '')
    except FileNotFoundError:
        pass

    if not username:
        username = input("\nEnter username (email): ").strip()
    if not password:
        password = input("Enter password: ").strip()

    subscription_id = input("\nEnter subscription ID: ").strip()
    meter_number = input("Enter meter number: ").strip()

    if not all([username, password, subscription_id, meter_number]):
        print("\n❌ Missing required information")
        return

    # Fetch real data
    async with aiohttp.ClientSession() as session:
        api = AguasCoimbraAPI(session, username, password)

        try:
            await api.login()
            print("✅ Logged in successfully")

            consumption_data = await api.get_consumption(
                meter_number,
                subscription_id,
                days=90
            )

            print(f"✅ Retrieved {len(consumption_data)} readings from API")

            if not consumption_data:
                print("❌ No consumption data available")
                return

            # Sort by date (same as coordinator does)
            sorted_data = sorted(
                consumption_data,
                key=lambda x: datetime.fromisoformat(x["date"].replace("+00:00", "").replace("+01:00", "")),
                reverse=True,
            )

            # Show sample of data
            print(f"\n   Sample readings (first 5):")
            for i, reading in enumerate(sorted_data[:5], 1):
                date = reading.get('date', 'N/A')
                consumption = reading.get('consumption', 'N/A')
                print(f"      {i}. {date} - {consumption}L")

            # Test cumulative sensor logic
            sensor = TestCumulativeSensor()

            print("\n" + "=" * 60)
            print("SIMULATION 1: First coordinator update (initial state)")
            print("=" * 60)
            result1 = sensor.process_readings(sorted_data[:100])  # First 100 readings

            print("\n" + "=" * 60)
            print("SIMULATION 2: Second coordinator update (15 min later)")
            print("   Simulating same readings (no new data)")
            print("=" * 60)
            result2 = sensor.process_readings(sorted_data[:100])

            print("\n" + "=" * 60)
            print("SUMMARY")
            print("=" * 60)
            print(f"   After 1st update: {result1}")
            print(f"   After 2nd update: {result2}")

            if result1 is None:
                print("\n   ⚠️  PROBLEM: Sensor returns None after first update!")
                print("   This means it will show as unavailable in Home Assistant.")
                print("\n   Possible causes:")
                print("   1. All consumption values are 0")
                print("   2. No readings were processed")
                print("   3. cumulative_value is 0 (returns None)")
            elif result1 == result2:
                print(f"\n   ✅ Cumulative total is stable: {result1} L")
            else:
                print(f"\n   ⚠️  Cumulative total changed: {result1} → {result2}")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(test_cumulative_logic())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
