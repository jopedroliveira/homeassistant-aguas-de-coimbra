"""Test the listSubscriptions endpoint."""
import asyncio
import aiohttp
from .test_api import AguasCoimbraAPI

BASE_URL = "https://bdigital.aguasdecoimbra.pt/uPortal2/coimbra"
API_KEY = "fj894y82-h351-5f11-89f3-u2389ru893n1"


async def test_list_subscriptions(api: AguasCoimbraAPI):
    """Test the /Subscription/listSubscriptions endpoint."""
    print("\n" + "=" * 70)
    print("TEST: List Subscriptions Endpoint")
    print("=" * 70)
    print(f"Endpoint: GET {BASE_URL}/Subscription/listSubscriptions")

    if not api._auth_token:
        await api.login()

    headers = {
        "api-key": API_KEY,
        "X-Auth-Token": api._auth_token,
        "Accept": "application/json",
    }

    try:
        async with api._session.get(
            f"{BASE_URL}/Subscription/listSubscriptions",
            headers=headers,
        ) as response:
            print(f"\nStatus: {response.status}")

            if response.status == 200:
                data = await response.json()
                print(f"✅ SUCCESS! Received data")
                print(f"   Response type: {type(data)}")

                if isinstance(data, list):
                    print(f"   Number of subscriptions: {len(data)}")

                    for i, sub in enumerate(data, 1):
                        print(f"\n   Subscription {i}:")
                        for key, value in sub.items():
                            if isinstance(value, (str, int, float, bool)):
                                print(f"      {key}: {value}")
                            else:
                                print(f"      {key}: {type(value).__name__}")

                        # Look for subscription ID
                        sub_id = sub.get('subscriptionId') or sub.get('id') or sub.get('idSubscription')
                        if sub_id:
                            print(f"\n      ⭐ Subscription ID: {sub_id}")

                elif isinstance(data, dict):
                    print(f"\n   Data:")
                    for key, value in data.items():
                        print(f"      {key}: {value}")

                return data
            else:
                text = await response.text()
                print(f"❌ FAILED with status {response.status}")
                print(f"   Response: {text[:500]}")
                return None

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main test function."""
    print("\n" + "=" * 70)
    print("List Subscriptions Endpoint Test")
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

    if not all([username, password]):
        print("\n❌ Missing credentials")
        return

    print(f"\nTesting with:")
    print(f"   Username: {username}")

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

        # Test listSubscriptions
        subscriptions = await test_list_subscriptions(api)

        if subscriptions:
            print("\n" + "=" * 70)
            print("🎉 SUCCESS!")
            print("=" * 70)
            print("\nThe /Subscription/listSubscriptions endpoint works!")
            print("This can be used for auto-discovery in the integration.")

            # Try to extract subscription ID
            if isinstance(subscriptions, list) and len(subscriptions) > 0:
                first_sub = subscriptions[0]
                sub_id = first_sub.get('subscriptionId') or first_sub.get('id') or first_sub.get('idSubscription')
                if sub_id:
                    print(f"\n✓ Can auto-discover subscription ID: {sub_id}")
        else:
            print("\n" + "=" * 70)
            print("❌ ENDPOINT NOT AVAILABLE")
            print("=" * 70)
            print("\nThe /Subscription/listSubscriptions endpoint doesn't work.")
            print("We'll need to use manual entry or find another method.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
