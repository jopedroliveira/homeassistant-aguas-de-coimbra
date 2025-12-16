#!/usr/bin/env python3
"""Simple test of cumulative sensor logic with mock data."""
from datetime import datetime, timedelta


def simulate_cumulative_sensor(readings_list, initial_cumulative=0, initial_last_date=None):
    """Simulate the cumulative sensor logic."""
    _cumulative_value = initial_cumulative
    _last_processed_date = initial_last_date

    print(f"\n{'='*60}")
    print(f"INITIAL STATE:")
    print(f"  Cumulative: {_cumulative_value} L")
    print(f"  Last processed: {_last_processed_date}")
    print(f"  Readings to process: {len(readings_list)}")
    print(f"{'='*60}")

    # Calculate incremental consumption from NEW readings only
    incremental = 0.0
    most_recent_date = _last_processed_date
    processed = 0
    skipped = 0

    for reading in readings_list:
        reading_date_str = reading.get("date", "")
        if not reading_date_str:
            continue

        # Normalize the date string
        reading_date_str_clean = reading_date_str.replace("+00:00", "").replace("+01:00", "")

        # If we have a last processed date, only count readings newer than it
        if _last_processed_date:
            if reading_date_str_clean <= _last_processed_date:
                skipped += 1
                continue  # Skip already processed readings

        # Add this reading's consumption
        consumption = reading.get("consumption", 0)
        incremental += consumption
        processed += 1

        # Track the most recent reading date
        if most_recent_date is None or reading_date_str_clean > most_recent_date:
            most_recent_date = reading_date_str_clean

    print(f"\nPROCESSING:")
    print(f"  Processed: {processed} readings")
    print(f"  Skipped: {skipped} readings")
    print(f"  Incremental: {incremental} L")

    # Update cumulative value and last processed date (FIXED VERSION)
    # Important: Update last_processed_date even if incremental is 0
    if most_recent_date is not None and most_recent_date != _last_processed_date:
        if incremental > 0:
            _cumulative_value += incremental
            print(f"\nUPDATED:")
            print(f"  ✅ Cumulative: {_cumulative_value} L")
            print(f"  ✅ Last processed: {most_recent_date}")
        else:
            print(f"\nUPDATED (no consumption but marking readings as processed):")
            print(f"  ✅ Last processed: {most_recent_date}")
        _last_processed_date = most_recent_date
    else:
        print(f"\n⚠️  NO UPDATE (no new readings)")

    # This is what native_value returns (FIXED VERSION)
    # Only return None if we've truly never processed any data
    if _last_processed_date is None and _cumulative_value == 0:
        result = None
    else:
        result = _cumulative_value

    print(f"\nRETURN VALUE: {result}")
    if result is None:
        print("  ⚠️  Sensor will show as UNAVAILABLE in Home Assistant!")
    elif result == 0:
        print("  ✅ Sensor will show 0 L (available but no consumption yet)")

    return _cumulative_value, _last_processed_date, result


def test_scenario_1():
    """Test: First run with real consumption data."""
    print("\n\n" + "="*70)
    print("SCENARIO 1: First run - Fresh install with real data")
    print("="*70)

    # Mock readings (sorted by date, most recent first)
    readings = [
        {"date": "2024-12-15T10:00:00+00:00", "consumption": 150},
        {"date": "2024-12-14T10:00:00+00:00", "consumption": 200},
        {"date": "2024-12-13T10:00:00+00:00", "consumption": 180},
        {"date": "2024-12-12T10:00:00+00:00", "consumption": 220},
        {"date": "2024-12-11T10:00:00+00:00", "consumption": 190},
    ]

    cumulative, last_date, result = simulate_cumulative_sensor(readings)

    print(f"\n{'='*70}")
    print(f"RESULT: Should see {result} L in Home Assistant")
    print(f"{'='*70}")

    return cumulative, last_date


def test_scenario_2(prev_cumulative, prev_last_date):
    """Test: Second update - Same data (no new readings)."""
    print("\n\n" + "="*70)
    print("SCENARIO 2: Second update (15 min later) - Same data")
    print("="*70)

    # Same readings as before (no new data)
    readings = [
        {"date": "2024-12-15T10:00:00+00:00", "consumption": 150},
        {"date": "2024-12-14T10:00:00+00:00", "consumption": 200},
        {"date": "2024-12-13T10:00:00+00:00", "consumption": 180},
        {"date": "2024-12-12T10:00:00+00:00", "consumption": 220},
        {"date": "2024-12-11T10:00:00+00:00", "consumption": 190},
    ]

    cumulative, last_date, result = simulate_cumulative_sensor(
        readings,
        initial_cumulative=prev_cumulative,
        initial_last_date=prev_last_date
    )

    print(f"\n{'='*70}")
    print(f"RESULT: Should still see {result} L in Home Assistant")
    print(f"{'='*70}")

    return cumulative, last_date


def test_scenario_3():
    """Test: First run with ZERO consumption."""
    print("\n\n" + "="*70)
    print("SCENARIO 3: First run - All readings have 0 consumption")
    print("="*70)

    # Mock readings with zero consumption
    readings = [
        {"date": "2024-12-15T10:00:00+00:00", "consumption": 0},
        {"date": "2024-12-14T10:00:00+00:00", "consumption": 0},
        {"date": "2024-12-13T10:00:00+00:00", "consumption": 0},
        {"date": "2024-12-12T10:00:00+00:00", "consumption": 0},
        {"date": "2024-12-11T10:00:00+00:00", "consumption": 0},
    ]

    cumulative, last_date, result = simulate_cumulative_sensor(readings)

    print(f"\n{'='*70}")
    if result is None:
        print(f"❌ PROBLEM: Sensor shows as UNAVAILABLE even with valid readings!")
        print(f"   This might be why you're seeing 0 data in the dashboard.")
    else:
        print(f"RESULT: Should see {result} L in Home Assistant")
    print(f"{'='*70}")


def main():
    """Run all test scenarios."""
    print("\n" + "="*70)
    print("CUMULATIVE SENSOR LOGIC DIAGNOSTIC TEST")
    print("="*70)

    # Scenario 1: First run with data
    cumulative, last_date = test_scenario_1()

    # Scenario 2: Second update (no new data)
    test_scenario_2(cumulative, last_date)

    # Scenario 3: Zero consumption case
    test_scenario_3()

    print("\n\n" + "="*70)
    print("DIAGNOSIS:")
    print("="*70)
    print("""
If you're seeing 0 data in the Energy Dashboard after 30 minutes:

1. Check Home Assistant logs for the cumulative sensor:
   Settings → System → Logs → Search for "cumulative"

2. Check the sensor state in Developer Tools → States:
   Look for sensor.aguas_coimbra_cumulative_total

3. Possible causes:
   a) Sensor state is "unavailable" (shows as None)
   b) Sensor value is 0 but should be higher
   c) Sensor isn't updating (check last_processed_date attribute)
   d) All consumption values from API are 0

4. Check the sensor attributes:
   - last_processed_date: Should update with each new reading
   - If this is None or not updating, sensor isn't processing readings

5. Enable debug logging in configuration.yaml:
   logger:
     logs:
       custom_components.aguas_coimbra: debug
""")


if __name__ == "__main__":
    main()
