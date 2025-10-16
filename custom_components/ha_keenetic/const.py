"""Constants for the Keenetic integration."""
from datetime import timedelta

DOMAIN = "ha_keenetic_mk"
MANUFACTURER = "Keenetic"

# Configuration
CONF_HOST = "host"
CONF_PORT = "port"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

# Defaults
DEFAULT_HOST = "192.168.1.1"
DEFAULT_PORT = 81
DEFAULT_USERNAME = "admin"
DEFAULT_SCAN_INTERVAL = 30

# Error messages
ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_INVALID_AUTH = "invalid_auth"
ERROR_UNKNOWN = "unknown"

# API endpoints
API_SYSTEM = "/rci/show/system"
API_VERSION = "/rci/show/version"
API_INTERFACE = "/rci/show/interface"
API_MESH = "/rci/show/mws/member"

# Update interval
UPDATE_INTERVAL = timedelta(seconds=30)

# Interface types
INTERFACE_TYPE_WAN = "wan"
INTERFACE_TYPE_PORT = "port"
INTERFACE_TYPE_BRIDGE = "bridge"

# Interface traits
TRAIT_ETHERNET = "EthernetPort"
TRAIT_GIGABIT = "GigabitEthernetPort"

# State attributes
ATTR_INTERFACE_ID = "interface_id"
ATTR_INTERFACE_TYPE = "type"
ATTR_INTERFACE_DESCRIPTION = "description"
ATTR_INTERFACE_TRAITS = "traits"
ATTR_INTERFACE_ATTRIBUTES = "attributes"

# Mesh constants
MESH_NODE_PREFIX = "mesh_node_"

# Platforms
PLATFORMS = ["sensor", "switch"]


CONF_ENABLE_MESH = "enable_mesh"
CONF_UPDATE_INTERVAL = "update_interval"

DEFAULT_ENABLE_MESH = True
DEFAULT_UPDATE_INTERVAL = 30
