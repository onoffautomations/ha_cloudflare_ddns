"""Constants for the Cloudflare DDNS integration."""

DOMAIN = "cloudflare_ddns"

# Configuration keys
CONF_WHAT_IP = "what_ip"
CONF_DNS_RECORD = "dns_record"
CONF_ZONE_ID = "zone_id"
CONF_API_TOKEN = "api_token"
CONF_PROXIED = "proxied"
CONF_TTL = "ttl"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_DEVICE_NAME = "device_name"
CONF_AUTO_UPDATE = "auto_update"
CONF_NOTIFY_TELEGRAM = "notify_telegram"
CONF_TELEGRAM_CHAT_ID = "telegram_chat_id"
CONF_TELEGRAM_BOT_TOKEN = "telegram_bot_token"
CONF_NOTIFY_DISCORD = "notify_discord"
CONF_DISCORD_WEBHOOK_URL = "discord_webhook_url"

# Defaults
DEFAULT_WHAT_IP = "external"
DEFAULT_PROXIED = False
DEFAULT_TTL = 120
DEFAULT_UPDATE_INTERVAL = 60
DEFAULT_AUTO_UPDATE = True
DEFAULT_NOTIFY_TELEGRAM = False
DEFAULT_NOTIFY_DISCORD = False

# IP type options
IP_TYPE_EXTERNAL = "external"
IP_TYPE_INTERNAL = "internal"

# Update interval in seconds
MIN_UPDATE_INTERVAL = 10
MAX_UPDATE_INTERVAL = 3600

# TTL range
MIN_TTL = 120
MAX_TTL = 7200
AUTO_TTL = 1

# API URLs
CLOUDFLARE_API_BASE = "https://api.cloudflare.com/client/v4"
EXTERNAL_IP_URL = "https://checkip.amazonaws.com"

# Sensor types
SENSOR_SYNCED = "synced"
SENSOR_LAST_SYNC = "last_sync"
SENSOR_DOMAIN = "domain"
SENSOR_CURRENT_IP = "current_ip"
