"""Test subscription ID discovery methods."""
import asyncio
import sys
from datetime import datetime

import aiohttp

from .test_api import AguasCoimbraAPI

# Constants
BASE_URL = "https://bdigital.aguasdecoimbra.pt/uPortal2/coimbra"
API_KEY = "fj894y82-h351-5f11-89f3-u2389ru893n1"


async def test_meters_no_subscription(api: AguasCoimbraAPI):
    """Test calling meters endpoint WITHOUT subscription ID."""
    print("\n" + "=" * 70)
    print("TEST 1: Get Meters WITHOUT Subscription ID")
    print("=" * 70)
    print("Endpoint: GET /leituras/getContadores")
    print("Parameters: NONE")

    if not api._auth_token:
        await api.login()

    headers = {
        "api-key": API_KEY,
        "X-Auth-Token": api._auth_token,
        "Accept": "application/json",
    }

    try:
        async with api._session.get(
            f"{BASE_URL}/leituras/getContadores",
            headers=headers,
        ) as response:
            print(f"\nStatus: {response.status}")

            if response.status == 200:
                data = await response.json()
                print(f"✅ SUCCESS! Received data")
                print(f"   Response type: {type(data)}")

                if isinstance(data, list):
                    print(f"   Number of meters: {len(data)}")

                    for i, meter in enumerate(data, 1):
                        print(f"\n   Meter {i}:")
                        print(f"      Keys: {list(meter.keys())}")

                        # Look for subscription ID in various possible locations
                        sub_id = None
                        if 'subscriptionId' in meter:
                            sub_id = meter['subscriptionId']
                        elif 'idSubscription' in meter:
                            sub_id = meter['idSubscription']
                        elif 'subscription' in meter and isinstance(meter['subscription'], dict):
                            sub_id = meter['subscription'].get('id')

                        if sub_id:
                            print(f"      ⭐ FOUND SUBSCRIPTION ID: {sub_id}")

                        # Show meter number
                        meter_num = None
                        if 'chaveContador' in meter and isinstance(meter['chaveContador'], dict):
                            meter_num = meter['chaveContador'].get('numeroContador')
                        elif 'numeroContador' in meter:
                            meter_num = meter['numeroContador']

                        if meter_num:
                            print(f"      Meter Number: {meter_num}")

                        # Show first few keys and values
                        for key in list(meter.keys())[:5]:
                            value = meter[key]
                            if isinstance(value, (str, int, float, bool)):
                                print(f"      {key}: {value}")

                return data
            else:
                text = await response.text()
                print(f"❌ FAILED with status {response.status}")
                print(f"   Response: {text[:200]}")
                return None

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_meters_with_meter_number(api: AguasCoimbraAPI, meter_number: str):
    """Test calling meters endpoint WITH meter number parameter."""
    print("\n" + "=" * 70)
    print("TEST 2: Get Meters WITH Meter Number Parameter")
    print("=" * 70)
    print(f"Endpoint: GET /leituras/getContadores?numeroContador={meter_number}")

    if not api._auth_token:
        await api.login()

    headers = {
        "api-key": API_KEY,
        "X-Auth-Token": api._auth_token,
        "Accept": "application/json",
    }

    params = {"numeroContador": meter_number}

    try:
        async with api._session.get(
            f"{BASE_URL}/leituras/getContadores",
            headers=headers,
            params=params,
        ) as response:
            print(f"\nStatus: {response.status}")

            if response.status == 200:
                data = await response.json()
                print(f"✅ SUCCESS! Received data")
                print(f"   Response type: {type(data)}")

                if isinstance(data, list):
                    print(f"   Number of meters: {len(data)}")

                    for i, meter in enumerate(data, 1):
                        print(f"\n   Meter {i}:")

                        # Look for subscription ID
                        sub_id = None
                        for key in ['subscriptionId', 'idSubscription', 'subscription_id']:
                            if key in meter:
                                sub_id = meter[key]
                                break

                        if sub_id:
                            print(f"      ⭐ FOUND SUBSCRIPTION ID: {sub_id}")

                        # Show all keys
                        print(f"      All keys: {list(meter.keys())}")

                return data
            else:
                text = await response.text()
                print(f"❌ FAILED with status {response.status}")
                print(f"   Response: {text[:200]}")
                return None

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_extract_subscription_from_meter_data(meter_data: list, meter_number: str):
    """Test extracting subscription ID from meter data."""
    print("\n" + "=" * 70)
    print("TEST 3: Extract Subscription ID from Meter Data")
    print("=" * 70)

    if not meter_data:
        print("⚠️  No meter data to analyze")
        return None

    print(f"Looking for meter: {meter_number}")

    for meter in meter_data:
        # Get meter number from data
        current_meter = None

        if 'chaveContador' in meter and isinstance(meter['chaveContador'], dict):
            current_meter = meter['chaveContador'].get('numeroContador')
        elif 'numeroContador' in meter:
            current_meter = meter['numeroContador']

        print(f"\nChecking meter: {current_meter}")

        if current_meter == meter_number:
            print(f"✅ Found matching meter!")

            # Try to find subscription ID
            subscription_id = None

            # Check various possible locations
            if 'subscriptionId' in meter:
                subscription_id = meter['subscriptionId']
                print(f"   Found subscriptionId: {subscription_id}")

            if 'idSubscription' in meter:
                subscription_id = meter['idSubscription']
                print(f"   Found idSubscription: {subscription_id}")

            if 'subscription' in meter:
                if isinstance(meter['subscription'], dict):
                    subscription_id = meter['subscription'].get('id') or meter['subscription'].get('subscriptionId')
                    print(f"   Found in subscription object: {subscription_id}")
                elif isinstance(meter['subscription'], (str, int)):
                    subscription_id = str(meter['subscription'])
                    print(f"   Found subscription: {subscription_id}")

            # Check in chaveContador
            if 'chaveContador' in meter and isinstance(meter['chaveContador'], dict):
                chave = meter['chaveContador']
                if 'subscriptionId' in chave:
                    subscription_id = chave['subscriptionId']
                    print(f"   Found in chaveContador: {subscription_id}")

            if subscription_id:
                print(f"\n⭐ SUCCESSFULLY EXTRACTED SUBSCRIPTION ID: {subscription_id}")
                return str(subscription_id)
            else:
                print(f"\n❌ Could not find subscription ID in meter data")
                print(f"   Available keys: {list(meter.keys())}")
                return None

    print(f"\n❌ Meter {meter_number} not found in data")
    return None


async def main():
    """Main test function."""
    print("\n" + "=" * 70)
    print("Subscription ID Discovery Test Suite")
    print("=" * 70)

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

        if username and password:
            print(f"\n✓ Found credentials in .envrc")
    except FileNotFoundError:
        username = input("\nEnter username (email): ").strip()
        password = input("Enter password: ").strip()

    meter_number = input("Enter meter number (e.g., ABC123456): ").strip()

    if not all([username, password, meter_number]):
        print("\n❌ Missing required information")
        return

    print(f"\nTesting with:")
    print(f"   Username: {username}")
    print(f"   Meter Number: {meter_number}")

    async with aiohttp.ClientSession() as session:
        api = AguasCoimbraAPI(session, username, password)

        # Login
        print("\n" + "=" * 70)
        print("Authenticating...")
        print("=" * 70)
        try:
            token = await api.login()
            print(f"✅ Login successful!")
            print(f"   Token: {token[:30]}...")
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return

        # Test 1: Meters without subscription ID
        meter_data = await test_meters_no_subscription(api)

        # Test 2: Meters with meter number
        if not meter_data:
            meter_data = await test_meters_with_meter_number(api, meter_number)

        # Test 3: Extract subscription ID
        if meter_data:
            subscription_id = await test_extract_subscription_from_meter_data(meter_data, meter_number)

            if subscription_id:
                print("\n" + "=" * 70)
                print("🎉 DISCOVERY SUCCESSFUL!")
                print("=" * 70)
                print(f"\nDiscovered Subscription ID: {subscription_id}")
                print(f"\nThis method can be used in the integration to auto-discover")
                print(f"the subscription ID without requiring user input!")
            else:
                print("\n" + "=" * 70)
                print("⚠️  DISCOVERY FAILED")
                print("=" * 70)
                print("\nCould not extract subscription ID from meter data.")
                print("Manual entry will still be required as fallback.")
        else:
            print("\n" + "=" * 70)
            print("❌ ALL TESTS FAILED")
            print("=" * 70)
            print("\nCould not retrieve meter data without subscription ID.")
            print("The current implementation with /Subscription/listSubscriptions")
            print("or manual entry is the best option.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
