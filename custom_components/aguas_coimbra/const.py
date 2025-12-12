"""Constants for the Águas de Coimbra integration."""
from datetime import timedelta
from typing import Final

# Integration domain
DOMAIN: Final = "aguas_coimbra"

# API Configuration
BASE_URL: Final = "https://bdigital.aguasdecoimbra.pt/uPortal2/coimbra"
API_KEY: Final = "fj894y82-h351-5f11-89f3-u2389ru893n1"

# API Endpoints
ENDPOINT_LOGIN: Final = f"{BASE_URL}/login"
ENDPOINT_SUBSCRIPTIONS: Final = f"{BASE_URL}/Subscription/listSubscriptions"
ENDPOINT_METERS: Final = f"{BASE_URL}/leituras/getContadores"
ENDPOINT_CONSUMPTION: Final = f"{BASE_URL}/History/consumo/carga"

# Default Configuration
DEFAULT_UPDATE_INTERVAL: Final = timedelta(minutes=15)
DEFAULT_HISTORY_DAYS: Final = 90
DEFAULT_PRODUCT_CODE: Final = "AG"  # Water (Água)
DEFAULT_BRAND_CODE: Final = "AF"

# Configuration Keys
CONF_METER_NUMBER: Final = "meter_number"
CONF_SUBSCRIPTION_ID: Final = "subscription_id"
CONF_UPDATE_INTERVAL: Final = "update_interval"
CONF_HISTORY_DAYS: Final = "history_days"

# Sensor Types
SENSOR_LATEST_READING: Final = "latest_reading"
SENSOR_DAILY_CONSUMPTION: Final = "daily_consumption"
SENSOR_WEEKLY_CONSUMPTION: Final = "weekly_consumption"
SENSOR_MONTHLY_CONSUMPTION: Final = "monthly_consumption"

# Sensor Configuration
SENSOR_TYPES: Final = {
    SENSOR_LATEST_READING: {
        "name": "Latest Reading",
        "icon": "mdi:water",
        "unit": "L",
        "device_class": "water",
        "state_class": "total_increasing",
    },
    SENSOR_DAILY_CONSUMPTION: {
        "name": "Daily Consumption",
        "icon": "mdi:water",
        "unit": "L",
        "device_class": "water",
        "state_class": "total",
    },
    SENSOR_WEEKLY_CONSUMPTION: {
        "name": "Weekly Consumption",
        "icon": "mdi:water-outline",
        "unit": "L",
        "device_class": "water",
        "state_class": "total",
    },
    SENSOR_MONTHLY_CONSUMPTION: {
        "name": "Monthly Consumption",
        "icon": "mdi:water-circle",
        "unit": "L",
        "device_class": "water",
        "state_class": "total",
    },
}

# HTTP Headers
HEADER_CONTENT_TYPE: Final = "Content-Type"
HEADER_API_KEY: Final = "api-key"
HEADER_AUTH_TOKEN: Final = "X-Auth-Token"
HEADER_ACCEPT: Final = "Accept"

# Error Messages
ERROR_AUTH_FAILED: Final = "auth_failed"
ERROR_CANNOT_CONNECT: Final = "cannot_connect"
ERROR_INVALID_RESPONSE: Final = "invalid_response"
ERROR_UNKNOWN: Final = "unknown"

# Platforms
PLATFORMS: Final = ["sensor"]
