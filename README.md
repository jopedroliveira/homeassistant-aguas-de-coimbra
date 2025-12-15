# Águas de Coimbra - Home Assistant Integration

This is a Home Assistant custom integration for monitoring water consumption from the Águas de Coimbra digital portal.

## Features

- Real-time water consumption monitoring
- Five sensors:
  - Latest Reading: Most recent consumption value
  - Cumulative Total: Total cumulative consumption (for Energy dashboard)
  - Daily Consumption: Total consumption for today
  - Weekly Consumption: Total consumption for the last 7 days
  - Monthly Consumption: Total consumption for the current month
- Automatic updates every 15 minutes
- Secure credential storage
- Properly configured for Home Assistant Energy Dashboard

## Installation

### Prerequisites

- Home Assistant installation (version 2024.1.0 or higher)
- Águas de Coimbra portal account

### Option 1: Download from GitHub Releases (Recommended)

1. **Download the latest release**

   - Go to [Releases](https://github.com/jopedroliveira/homeassistant-aguas-de-coimbra/releases)
   - Download either `aguas_coimbra-x.x.x.tar.gz` or `aguas_coimbra-x.x.x.zip`

2. **Extract to Home Assistant**

   ```bash
   # Navigate to your Home Assistant config directory
   cd /config/custom_components/

   # Extract the downloaded file
   tar -xzf /path/to/aguas_coimbra-x.x.x.tar.gz
   # OR
   unzip /path/to/aguas_coimbra-x.x.x.zip
   ```

### Option 2: Manual Installation

1. **Copy Integration to Home Assistant**

   ```bash
   # Navigate to your Home Assistant config directory
   cd /path/to/homeassistant/config

   # Create custom_components directory if it doesn't exist
   mkdir -p custom_components

   # Copy the integration (adjust the source path to your actual location)
   cp -r /path/to/aguas-api/custom_components/aguas_coimbra custom_components/
   ```

2. **Restart Home Assistant**

   - Go to Settings → System → Restart
   - Wait for Home Assistant to fully restart

3. **Add the Integration**

   - Go to Settings → Devices & Services
   - Click "+ ADD INTEGRATION"
   - Search for "Águas de Coimbra"
   - Enter your information:
     - **Email**: Your Águas de Coimbra portal email
     - **Password**: Your portal password
     - **Meter Number**: Your water meter number (found on your bill or meter)
     - **Subscription ID** (optional): Leave blank to auto-discover, or enter manually if known

   > **Note**: The integration will attempt to automatically discover your subscription ID. If auto-discovery fails, you'll be prompted to enter it manually in a second step.

### Finding Your Meter Number and Subscription ID

**Meter Number (Required)**

- Found on your water bill
- Visible on the physical water meter
- Format: Usually alphanumeric (e.g., "ABC123456")

**Subscription ID (Auto-Discovered)**

The integration automatically attempts to discover this. If auto-discovery fails, you can find it manually:

**Method: Check browser network tab**

1. Log into https://bdigital.aguasdecoimbra.pt
2. Open Browser DevTools (F12)
3. Go to Network tab
4. Navigate to "Leituras" section
5. Look for requests to `/leituras/getContadores` or `/History/consumo/carga`
6. Check the query parameters for your IDs

## Troubleshooting

### Check Logs

If the integration doesn't work, check the Home Assistant logs:

1. Go to Settings → System → Logs
2. Look for entries containing "aguas_coimbra"

### Common Issues

**Authentication Failed**

- Verify your username and password are correct
- Try logging into the portal manually first

**Cannot Connect**

- Check your internet connection
- Verify the Águas de Coimbra portal is accessible

**Invalid Response**

- Double-check your subscription ID and meter number
- Ensure they match the ones from the portal

### Enable Debug Logging

Add this to your `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.aguas_coimbra: debug
```

## Sensors

After successful setup, you'll have these sensors:

- `sensor.aguas_coimbra_latest_reading` - Latest consumption reading (L)
- `sensor.aguas_coimbra_cumulative_total` - Cumulative total consumption (L) - Use this for Energy Dashboard
- `sensor.aguas_coimbra_daily_consumption` - Today's total (L)
- `sensor.aguas_coimbra_weekly_consumption` - Last 7 days total (L)
- `sensor.aguas_coimbra_monthly_consumption` - Current month total (L)

## Energy Dashboard Integration

The sensors are configured to work with Home Assistant's Energy Dashboard:

- **Latest Reading**: Individual consumption reading (state_class: measurement)
- **Cumulative Total**: Total cumulative consumption (state_class: total_increasing) - **Recommended for Energy Dashboard**
- **Daily Consumption**: Today's consumption total (state_class: total)
- **Weekly Consumption**: Last 7 days consumption (state_class: total)
- **Monthly Consumption**: Current month consumption (state_class: total)

To add to the Energy Dashboard:

1. Go to Settings → Dashboards → Energy
2. Click "Add Consumption"
3. Select `sensor.aguas_de_coimbra_<your_meter>_cumulative_total` for long-term tracking

### Important Notes on Sensor Configuration

- **Use Cumulative Total for Energy Dashboard**: This sensor uses `state_class: total_increasing` which is the correct configuration for tracking cumulative consumption over time. It will never decrease, preventing negative values in statistics.
- **Daily/Weekly/Monthly sensors**: These use `state_class: total` and reset at period boundaries. They're useful for monitoring specific time periods but not recommended for the main Energy Dashboard tracking.
- **Latest Reading**: This shows individual consumption readings and uses `state_class: measurement` for informational purposes only.

## Development Status

This is version 1.0.2 - fixed negative consumption issue and improved energy dashboard support.

### Recent Updates

- ✅ Fixed negative water consumption in Energy Dashboard
- ✅ Added Cumulative Total sensor with proper `state_class: total_increasing`
- ✅ Fixed state_class configuration for all sensors
- ✅ Daily/Weekly/Monthly sensors now use `state_class: total`
- ✅ Latest Reading sensor changed to `state_class: measurement`
- ✅ Auto-discovery of subscription ID (when possible)
- ✅ Simplified setup process (email, password, and meter number required)

### Known Limitations

- Single meter support only (one integration instance per meter)
- Subscription ID auto-discovery may not work for all account types (manual entry available as fallback)
- Meter number must be entered manually (visible on bill or meter)

### Planned Features

- Multi-meter support for accounts with multiple meters
- Historical data charts and visualization
- Cost calculations based on water rates
- Leak detection alerts based on unusual consumption patterns
- Support for other Portuguese water utilities

## Support

For issues or questions:

- **GitHub Issues**: [https://github.com/jopedroliveira/homeassistant-aguas-de-coimbra/issues](https://github.com/jopedroliveira/homeassistant-aguas-de-coimbra/issues)
- Check Home Assistant logs for error messages
- Verify network connectivity to Águas de Coimbra portal
- Ensure credentials and meter information are correct

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request at:
[https://github.com/jopedroliveira/homeassistant-aguas-de-coimbra](https://github.com/jopedroliveira/homeassistant-aguas-de-coimbra)

## License

MIT License
