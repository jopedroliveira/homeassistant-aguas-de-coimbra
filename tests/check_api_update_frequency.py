#!/usr/bin/env python3
"""Check how frequently the Águas de Coimbra API provides new readings."""
import asyncio
from datetime import datetime
import aiohttp
from .test_api import AguasCoimbraAPI


async def check_api_updates():
    """Fetch data twice with a delay to see if new readings appear."""
    print("\n" + "="*70)
    print("API UPDATE FREQUENCY CHECK")
    print("="*70)

    # Get credentials
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
        print("❌ .envrc file not found")
        return

    subscription_id = input("\nEnter subscription ID: ").strip()
    meter_number = input("Enter meter number: ").strip()

    if not all([username, password, subscription_id, meter_number]):
        print("\n❌ Missing required information")
        return

    async with aiohttp.ClientSession() as session:
        api = AguasCoimbraAPI(session, username, password)

        try:
            await api.login()
            print("✅ Logged in successfully\n")

            # FIRST FETCH
            print("="*70)
            print("FETCH #1: Getting current data...")
            print("="*70)
            data1 = await api.get_consumption(meter_number, subscription_id, days=7)

            if not data1:
                print("❌ No data received")
                return

            # Sort by date (most recent first)
            sorted1 = sorted(
                data1,
                key=lambda x: x["date"],
                reverse=True
            )

            print(f"✅ Retrieved {len(data1)} readings")
            print(f"\n   Most recent 3 readings:")
            for i, reading in enumerate(sorted1[:3], 1):
                print(f"      {i}. {reading['date']} - {reading['consumption']}L")

            most_recent_date_1 = sorted1[0]["date"] if sorted1 else None
            print(f"\n   Most recent reading date: {most_recent_date_1}")

            # WAIT 2 MINUTES
            wait_seconds = 120
            print(f"\n{'='*70}")
            print(f"Waiting {wait_seconds} seconds to check for new readings...")
            print("(This simulates what happens between coordinator updates)")
            print(f"{'='*70}")
            await asyncio.sleep(wait_seconds)

            # SECOND FETCH
            print("\n" + "="*70)
            print("FETCH #2: Checking for new data after waiting...")
            print("="*70)
            data2 = await api.get_consumption(meter_number, subscription_id, days=7)

            sorted2 = sorted(
                data2,
                key=lambda x: x["date"],
                reverse=True
            )

            print(f"✅ Retrieved {len(data2)} readings")
            print(f"\n   Most recent 3 readings:")
            for i, reading in enumerate(sorted2[:3], 1):
                print(f"      {i}. {reading['date']} - {reading['consumption']}L")

            most_recent_date_2 = sorted2[0]["date"] if sorted2 else None
            print(f"\n   Most recent reading date: {most_recent_date_2}")

            # COMPARE
            print("\n" + "="*70)
            print("ANALYSIS")
            print("="*70)

            if most_recent_date_1 == most_recent_date_2:
                print("❌ NO NEW READINGS appeared in the last 2 minutes")
                print("\n   This means:")
                print("   - The API doesn't update every 15 minutes")
                print("   - Cumulative sensor only updates when API has new readings")
                print("   - Energy Dashboard only gets new data points when sensor updates")
                print("\n   Expected behavior:")
                print("   - If Águas de Coimbra only reads meters once/twice per day,")
                print("     you'll only see 1-2 data points per day in Energy Dashboard")
            else:
                print("✅ NEW READING appeared!")
                print(f"   Old: {most_recent_date_1}")
                print(f"   New: {most_recent_date_2}")
                print("\n   This means the API updates frequently")

            # Show all unique dates
            all_dates_1 = set(r["date"][:10] for r in data1)  # Just the date part
            print(f"\n   Unique reading dates in data (last 7 days): {len(all_dates_1)}")
            for date in sorted(all_dates_1, reverse=True):
                readings_on_date = [r for r in data1 if r["date"].startswith(date)]
                print(f"      {date}: {len(readings_on_date)} readings")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(check_api_updates())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
