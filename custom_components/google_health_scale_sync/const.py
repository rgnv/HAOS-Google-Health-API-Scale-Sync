"""Constants for Google Health API Scale Sync."""

DOMAIN = "google_health_scale_sync"
DEFAULT_TITLE = "Google Health API Scale Sync"
OAUTH2_AUTHORIZE = "https://accounts.google.com/o/oauth2/v2/auth"
OAUTH2_TOKEN = "https://oauth2.googleapis.com/token"
WRITE_SCOPE = "https://www.googleapis.com/auth/googlehealth.health_metrics_and_measurements.writeonly"

SERVICE_LOG_BODY_MEASUREMENTS = "log_body_measurements"

# Profile and sync options are stored in the config entry, never in the repository.
CONF_HEIGHT_M = "height_m"
CONF_AGE = "age"
CONF_SEX = "sex"
CONF_BIRTH_DATE = "birth_date"
CONF_SYNC_BODY_FAT = "sync_body_fat"
DEFAULT_HEIGHT_M = 1.75
DEFAULT_AGE = 30
DEFAULT_SEX = "unspecified"
DEFAULT_SYNC_BODY_FAT = True

ATTR_WEIGHT_KG = "weight_kg"
ATTR_BODY_FAT_PERCENT = "body_fat_percent"
ATTR_MEASURED_AT = "measured_at"
ATTR_MEASUREMENT_ID = "measurement_id"
ATTR_ENTRY_ID = "entry_id"
