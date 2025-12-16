"""Test script for Águas de Coimbra integration."""
import asyncio
import sys
import os
from datetime import datetime, timedelta

import aiohttp

# Import the standalone test API (no Home Assistant dependencies)
from .test_api import AguasCoimbraAPI, LoginError, ConnectionError as APIConnectionError


async def test_login(username: str, password: str):
    """Test login functionality."""
    print("\n" + "=" * 60)
    print("TEST 1: Authentication")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        api = AguasCoimbraAPI(session, username, password)

        try:
            token = await api.login()
            print(f"✅ Login successful!")
            print(f"   X-Auth-Token: {token[:20]}...{token[-20:]}")
            return api
        except LoginError as e:
            print(f"❌ Login failed: {e}")
            return None
        except APIConnectionError as e:
            print(f"❌ Connection error: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None


async def test_get_meters(api: AguasCoimbraAPI, subscription_id: str):
    """Test fetching available meters."""
    print("\n" + "=" * 60)
    print("TEST 2: Get Available Meters")
    print("=" * 60)

    try:
        meters = await api.get_meters(subscription_id)
        print(f"✅ Successfully retrieved {len(meters)} meter(s)")

        for i, meter in enumerate(meters, 1):
            print(f"\n   Meter {i}:")
            for key, value in meter.items():
                print(f"      {key}: {value}")

        return meters
    except Exception as e:
        print(f"❌ Failed to get meters: {e}")
        return []


async def test_get_consumption(
    api: AguasCoimbraAPI,
    meter_number: str,
    subscription_id: str,
    days: int = 30
):
    """Test fetching consumption data."""
    print("\n" + "=" * 60)
    print(f"TEST 3: Get Consumption Data (Last {days} days)")
    print("=" * 60)

    try:
        consumption_data = await api.get_consumption(
            meter_number,
            subscription_id,
            days
        )
        print(f"✅ Successfully retrieved {len(consumption_data)} readings")

        if consumption_data:
            # Show first 5 readings
            print("\n   First 5 readings:")
            for i, reading in enumerate(consumption_data[:5], 1):
                date = reading.get('date', 'N/A')
                consumption = reading.get('consumption', 'N/A')
                cil = reading.get('cil', 'N/A')
                print(f"      {i}. {date[:19]} - {consumption}L (CIL: {cil})")

            if len(consumption_data) > 5:
                print(f"   ... and {len(consumption_data) - 5} more readings")

        return consumption_data
    except Exception as e:
        print(f"❌ Failed to get consumption: {e}")
        import traceback
        traceback.print_exc()
        return []


async def test_data_processing(consumption_data: list):
    """Test the coordinator's data processing."""
    print("\n" + "=" * 60)
    print("TEST 4: Data Processing & Aggregation")
    print("=" * 60)

    if not consumption_data:
        print("⚠️  No data to process")
        return

    # Sort by date (most recent first)
    sorted_data = sorted(
        consumption_data,
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

    for reading in sorted_data:
        try:
            reading_date = datetime.fromisoformat(
                reading["date"].replace("+00:00", "").replace("+01:00", "")
            )
            consumption = reading.get("consumption", 0)

            if reading_date >= today_start:
                daily_total += consumption
            if reading_date >= week_start:
                weekly_total += consumption
            if reading_date >= month_start:
                monthly_total += consumption
        except (ValueError, KeyError):
            continue

    print(f"✅ Data processed successfully")
    print(f"\n   Latest Reading:")
    print(f"      Value: {latest_reading} L")
    print(f"      Date: {last_reading_date}")
    print(f"      CIL: {cil}")
    print(f"\n   Aggregated Totals:")
    print(f"      Daily (today): {daily_total} L")
    print(f"      Weekly (last 7 days): {weekly_total} L")
    print(f"      Monthly (current month): {monthly_total} L")
    print(f"\n   Total readings in dataset: {len(consumption_data)}")


async def main():
    """Main test function."""
    print("\n" + "=" * 60)
    print("Águas de Coimbra Integration - Local Test")
    print("=" * 60)

    # Get credentials from .envrc or prompt
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

        if username and password:
            print(f"\n✓ Found credentials in .envrc")
    except FileNotFoundError:
        pass

    if not username:
        username = input("\nEnter username (email): ").strip()
    if not password:
        password = input("Enter password: ").strip()

    subscription_id = input("\nEnter subscription ID (e.g., 12345): ").strip()
    meter_number = input("Enter meter number (e.g., ABC123456): ").strip()

    if not all([username, password, subscription_id, meter_number]):
        print("\n❌ Missing required information")
        return

    print(f"\nTesting with:")
    print(f"   Username: {username}")
    print(f"   Subscription ID: {subscription_id}")
    print(f"   Meter Number: {meter_number}")

    # Run tests
    async with aiohttp.ClientSession() as session:
        api = AguasCoimbraAPI(session, username, password)

        # Test 1: Login
        if not await test_login(username, password):
            print("\n❌ Cannot continue - login failed")
            return

        # Re-create API with session
        api = AguasCoimbraAPI(session, username, password)
        await api.login()

        # Test 2: Get meters (optional, might fail if endpoint needs discovery)
        print("\n⚠️  Attempting to fetch meters (may fail - this is optional)")
        await test_get_meters(api, subscription_id)

        # Test 3: Get consumption
        consumption_data = await test_get_consumption(
            api,
            meter_number,
            subscription_id,
            days=30
        )

        # Test 4: Process data
        if consumption_data:
            await test_data_processing(consumption_data)

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print("\n✨ If all tests passed, the integration is ready to use!")
    print("   Next step: Install in Home Assistant\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
