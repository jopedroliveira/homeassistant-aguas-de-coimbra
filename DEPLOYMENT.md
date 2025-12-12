# Deployment Instructions for Águas de Coimbra Integration

## Quick Deployment

### Option 1: Using the Deployment Package (Recommended)

1. Transfer the deployment package to your Home Assistant machine:

   ```bash
   scp aguas_coimbra_deployment.tar.gz user@ha-machine:/tmp/
   ```

2. On the Home Assistant machine, extract to custom_components:

   ```bash
   cd /config/custom_components/
   tar -xzf /tmp/aguas_coimbra_deployment.tar.gz
   ```

3. Restart Home Assistant:

   - Go to Settings → System → Restart
   - Or via command line: `ha core restart`

4. Add the integration:
   - Go to Settings → Devices & Services
   - Click "Add Integration"
   - Search for "Águas de Coimbra"
   - Follow the configuration flow

### Option 2: Using Git Clone

1. On the Home Assistant machine:

   ```bash
   cd /config/custom_components/
   git clone https://github.com/jopedroliveira/homeassistant-aguas-de-coimbra.git aguas_coimbra
   ```

2. Restart Home Assistant and add the integration as above.

### Option 3: Manual File Copy

If you have access to the Home Assistant file system (e.g., via Samba/SMB):

1. Copy the entire `custom_components/aguas_coimbra/` folder to:

   ```
   /config/custom_components/aguas_coimbra/
   ```

2. Restart Home Assistant and add the integration.

## Configuration

During setup, you'll need:

- **Username**: Your Águas de Coimbra portal email
- **Password**: Your portal password
- **Meter Number**: Your water meter number (e.g., ABC123456)
- **Subscription ID**: _(Optional)_ - Will be auto-discovered if not provided

The integration will automatically discover your subscription ID using the `/Subscription/listSubscriptions` endpoint. If auto-discovery fails, you'll be prompted to enter it manually.

## Post-Installation

After installation, you should see 4 new sensors:

- `sensor.aguas_coimbra_<meter>_latest_reading` - Latest meter reading
- `sensor.aguas_coimbra_<meter>_daily_consumption` - Today's consumption
- `sensor.aguas_coimbra_<meter>_weekly_consumption` - Last 7 days
- `sensor.aguas_coimbra_<meter>_monthly_consumption` - Last 30 days

## Troubleshooting

Check the Home Assistant logs if the integration doesn't appear:

```bash
tail -f /config/home-assistant.log | grep aguas_coimbra
```

Common issues:

- **Integration not showing**: Verify files are in `/config/custom_components/aguas_coimbra/`
- **Login failed**: Check credentials during config flow
- **No data**: Verify meter number is correct and matches your account

## Energy Dashboard Integration

To add water consumption to the Energy Dashboard:

1. Go to Settings → Dashboards → Energy
2. Click "Add Water Source"
3. Select `sensor.aguas_coimbra_<meter>_daily_consumption`

## Updates

To update the integration:

```bash
cd /config/custom_components/aguas_coimbra/
git pull
```

Then restart Home Assistant.
