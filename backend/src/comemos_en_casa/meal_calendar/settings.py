"""Static domain settings; process configuration is introduced with PR 3 access work."""

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# The IANA database names the Canary Islands zone Atlantic/Canary. Keep the
# product-facing name while resolving the valid system identifier.
CANARY_TIMEZONE_NAME = "Europe/Canary"
try:
    CANARY_TIMEZONE = ZoneInfo(CANARY_TIMEZONE_NAME)
except ZoneInfoNotFoundError:
    CANARY_TIMEZONE = ZoneInfo("Atlantic/Canary")
