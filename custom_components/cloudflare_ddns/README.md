# Cloudflare DDNS Home Assistant Integration

This Home Assistant custom integration automatically updates your Cloudflare DNS records with your current IP address (either external or internal).

## Features

- **Config Flow**: Easy setup through the Home Assistant UI
- **Automatic Updates**: Regularly checks and updates your DNS record (default: every 60 seconds)
- **Multiple Sensors**:
  - `Synced`: Shows if your DNS is currently synced
  - `Last Sync`: Timestamp of the last successful sync
  - `Domain`: Your DDNS domain name
  - `Current IP`: Your current IP address
- **Notifications**: Optional Telegram and Discord notifications when DNS is updated
- **Flexible Configuration**: Support for both external and internal IP addresses
- **Cloudflare Proxy**: Optional support for Cloudflare's proxy feature

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/cloudflare_ddns` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Cloudflare DDNS**
4. Fill in the required information:

### Required Settings

- **DNS Record**: Your DNS A record (e.g., `ddns.example.com`)
- **Zone ID**: Your Cloudflare Zone ID (found in your Cloudflare dashboard)
- **API Token**: Your Cloudflare API token with DNS edit permissions

### Optional Settings

- **IP Type**: Choose `external` or `internal` (default: `external`)
- **Enable Cloudflare Proxy**: Route traffic through Cloudflare (default: `false`)
  - Note: Internal IPs cannot be proxied
- **TTL**: Time to live in seconds (120-7200, or 1 for automatic) (default: `120`)
- **Update Interval**: How often to check for IP changes in seconds (default: `60`)

### Notification Settings (Optional)

#### Telegram
- **Enable Telegram Notifications**: Turn on Telegram alerts
- **Telegram Chat ID**: Your Telegram chat ID
- **Telegram Bot Token**: Your Telegram bot API token

#### Discord
- **Enable Discord Notifications**: Turn on Discord alerts
- **Discord Webhook URL**: Your Discord webhook URL

## Sensors

The integration creates the following sensors:

### sensor.cloudflare_ddns_[domain]_synced
Shows whether your DNS record is currently synced with your IP address.
- State: `Yes` or `No`
- Attributes: `dns_record_ip`, `current_ip`

### sensor.cloudflare_ddns_[domain]_last_sync
Timestamp of the last successful update check.
- Device Class: `timestamp`

### sensor.cloudflare_ddns_[domain]_domain
Your DDNS domain name.
- Category: `diagnostic`

### sensor.cloudflare_ddns_[domain]_current_ip
Your current IP address.
- Category: `diagnostic`

## Getting Cloudflare Credentials

### Zone ID
1. Log in to your Cloudflare dashboard
2. Select your domain
3. Scroll down on the Overview page to find your Zone ID

### API Token
1. Go to [Cloudflare API Tokens](https://dash.cloudflare.com/profile/api-tokens)
2. Click "Create Token"
3. Use the "Edit zone DNS" template
4. Select your specific zone
5. Create the token and copy it

## Examples

### Automation Example
```yaml
automation:
  - alias: "Notify when DDNS updates"
    trigger:
      - platform: state
        entity_id: sensor.cloudflare_ddns_ddns_example_com_synced
        to: "Yes"
    action:
      - service: notify.mobile_app
        data:
          message: "DDNS updated to {{ state_attr('sensor.cloudflare_ddns_ddns_example_com_synced', 'current_ip') }}"
```

### Dashboard Card Example
```yaml
type: entities
title: Cloudflare DDNS
entities:
  - entity: sensor.cloudflare_ddns_ddns_example_com_synced
  - entity: sensor.cloudflare_ddns_ddns_example_com_last_sync
  - entity: sensor.cloudflare_ddns_ddns_example_com_domain
  - entity: sensor.cloudflare_ddns_ddns_example_com_current_ip
```

## Troubleshooting

### Integration not updating
- Check your API token has the correct permissions
- Verify your Zone ID is correct
- Check the Home Assistant logs for error messages

### Internal IP detection not working
Internal IP detection in the async version requires additional implementation. If you need internal IP support, please open an issue.

## Support

For issues, feature requests, or questions, please open an issue on GitHub.

## License

MIT License
