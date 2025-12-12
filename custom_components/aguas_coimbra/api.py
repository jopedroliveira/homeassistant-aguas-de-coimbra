"""API client for Águas de Coimbra."""
import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from .const import (
    API_KEY,
    DEFAULT_BRAND_CODE,
    DEFAULT_PRODUCT_CODE,
    ENDPOINT_CONSUMPTION,
    ENDPOINT_SUBSCRIPTIONS,
    ENDPOINT_LOGIN,
    ENDPOINT_METERS,
    HEADER_ACCEPT,
    HEADER_API_KEY,
    HEADER_AUTH_TOKEN,
    HEADER_CONTENT_TYPE,
)

_LOGGER = logging.getLogger(__name__)


class AguasCoimbraAPIError(Exception):
    """Base exception for API errors."""


class LoginError(AguasCoimbraAPIError):
    """Exception for login failures."""


class ConnectionError(AguasCoimbraAPIError):
    """Exception for connection failures."""


class InvalidResponseError(AguasCoimbraAPIError):
    """Exception for invalid API responses."""


class AguasCoimbraAPI:
    """API client for Águas de Coimbra digital portal."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._username = username
        self._password = password
        self._auth_token: str | None = None

    async def login(self) -> str:
        """Authenticate and obtain X-Auth-Token."""
        headers = {
            HEADER_CONTENT_TYPE: "application/json;charset=utf-8",
            HEADER_API_KEY: API_KEY,
            HEADER_ACCEPT: "application/json, text/plain, */*",
        }

        payload = {
            "username": self._username,
            "password": self._password,
        }

        try:
            async with self._session.post(
                ENDPOINT_LOGIN,
                json=payload,
                headers=headers,
                allow_redirects=True,
            ) as response:
                # X-Auth-Token is in response headers
                auth_token = response.headers.get(HEADER_AUTH_TOKEN)

                if not auth_token:
                    _LOGGER.error("No X-Auth-Token in login response headers")
                    raise LoginError("Authentication failed - no token received")

                if response.status != 200:
                    _LOGGER.error(
                        "Login failed with status %s: %s",
                        response.status,
                        await response.text(),
                    )
                    raise LoginError(f"Login failed with status {response.status}")

                self._auth_token = auth_token
                _LOGGER.debug("Successfully authenticated with Águas de Coimbra")
                return auth_token

        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error during login: %s", err)
            raise ConnectionError("Failed to connect to Águas de Coimbra") from err

    async def get_user_subscriptions(self) -> list[dict[str, Any]]:
        """Get user subscriptions after login."""
        if not self._auth_token:
            await self.login()

        headers = {
            HEADER_API_KEY: API_KEY,
            HEADER_AUTH_TOKEN: self._auth_token,
            HEADER_ACCEPT: "application/json",
        }

        try:
            async with self._session.get(
                ENDPOINT_SUBSCRIPTIONS,
                headers=headers,
            ) as response:
                if response.status == 401:
                    # Token expired, re-authenticate
                    _LOGGER.warning("Auth token expired, re-authenticating")
                    await self.login()
                    return await self.get_user_subscriptions()

                if response.status != 200:
                    _LOGGER.warning(
                        "Failed to get subscriptions with status %s: %s",
                        response.status,
                        await response.text(),
                    )
                    # Return empty list if endpoint doesn't exist
                    return []

                data = await response.json()
                _LOGGER.debug("Retrieved %d subscription(s)", len(data) if isinstance(data, list) else 0)
                return data if isinstance(data, list) else []

        except aiohttp.ClientError as err:
            _LOGGER.warning("Connection error getting subscriptions: %s", err)
            # Return empty list on error - this is optional functionality
            return []

    async def get_meters(self, subscription_id: str) -> list[dict[str, Any]]:
        """Get available water meters for the account."""
        if not self._auth_token:
            await self.login()

        headers = {
            HEADER_API_KEY: API_KEY,
            HEADER_AUTH_TOKEN: self._auth_token,
            HEADER_ACCEPT: "application/json",
        }

        params = {"subscriptionId": subscription_id}

        try:
            async with self._session.get(
                ENDPOINT_METERS,
                headers=headers,
                params=params,
            ) as response:
                if response.status == 401:
                    # Token expired, re-authenticate
                    _LOGGER.warning("Auth token expired, re-authenticating")
                    await self.login()
                    return await self.get_meters(subscription_id)

                if response.status != 200:
                    _LOGGER.error(
                        "Failed to get meters with status %s: %s",
                        response.status,
                        await response.text(),
                    )
                    raise InvalidResponseError(
                        f"Failed to get meters: HTTP {response.status}"
                    )

                data = await response.json()
                _LOGGER.debug("Retrieved %d meters", len(data) if isinstance(data, list) else 0)
                return data if isinstance(data, list) else []

        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error getting meters: %s", err)
            raise ConnectionError("Failed to get meters") from err

    async def get_consumption(
        self,
        meter_number: str,
        subscription_id: str,
        days: int = 90,
    ) -> list[dict[str, Any]]:
        """Get consumption data for a water meter."""
        if not self._auth_token:
            await self.login()

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        headers = {
            HEADER_API_KEY: API_KEY,
            HEADER_AUTH_TOKEN: self._auth_token,
            HEADER_ACCEPT: "application/json",
        }

        params = {
            "codigoMarca": DEFAULT_BRAND_CODE,
            "codigoProduto": DEFAULT_PRODUCT_CODE,
            "numeroContador": meter_number,
            "subscriptionId": subscription_id,
            "initialDate": start_date.strftime("%Y-%m-%d"),
            "finalDate": end_date.strftime("%Y-%m-%d"),
        }

        try:
            async with self._session.get(
                ENDPOINT_CONSUMPTION,
                headers=headers,
                params=params,
            ) as response:
                if response.status == 401:
                    # Token expired, re-authenticate
                    _LOGGER.warning("Auth token expired, re-authenticating")
                    await self.login()
                    return await self.get_consumption(meter_number, subscription_id, days)

                if response.status != 200:
                    _LOGGER.error(
                        "Failed to get consumption with status %s: %s",
                        response.status,
                        await response.text(),
                    )
                    raise InvalidResponseError(
                        f"Failed to get consumption: HTTP {response.status}"
                    )

                data = await response.json()

                if not isinstance(data, list):
                    _LOGGER.error("Unexpected response format: %s", type(data))
                    raise InvalidResponseError("Invalid response format")

                _LOGGER.debug("Retrieved %d consumption readings", len(data))
                return data

        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error getting consumption: %s", err)
            raise ConnectionError("Failed to get consumption data") from err

    async def validate_credentials(self) -> bool:
        """Validate credentials by attempting login."""
        try:
            await self.login()
            return True
        except (LoginError, ConnectionError):
            return False
