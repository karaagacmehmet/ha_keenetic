"""Sensor platform for Keenetic integration."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any, Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTime,
    UnitOfTemperature,
    UnitOfInformation,
    UnitOfDataRate,
)

from .const import DOMAIN, MANUFACTURER
from .icons import *

_LOGGER = logging.getLogger(__name__)

@dataclass
class KeeneticSensorEntityDescription(SensorEntityDescription):
    """Class describing Keenetic sensor entities."""
    value_fn: callable = lambda x: x
    available_fn: callable = lambda x: True
    use_full_data: bool = False

@dataclass
class InterfaceSensorEntityDescription(SensorEntityDescription):
    """Interface sensor entity description."""
    interface_id: str = None
    value_fn: callable = lambda x: x
    available_fn: callable = lambda x: True
    extra_attributes_fn: callable = lambda x: {}

@dataclass
class MeshNodeSensorEntityDescription(SensorEntityDescription):
    """Mesh node sensor entity description."""
    node_id: str = None
    value_fn: callable = lambda x: x
    available_fn: callable = lambda x: True


SENSOR_TYPES: tuple[KeeneticSensorEntityDescription, ...] = (

    KeeneticSensorEntityDescription(
        key="cpu_usage",
        name="CPU Usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_CPU,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    KeeneticSensorEntityDescription(
        key="uptime",
        name="Uptime",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_UPTIME,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    KeeneticSensorEntityDescription(
        key="memory_usage",
        name="Memory Usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_MEMORY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    KeeneticSensorEntityDescription(
        key="ram_usage",
        name="RAM Usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_MEMORY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    KeeneticSensorEntityDescription(
        key="memory_free",
        name="Memory Free",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon=ICON_MEMORY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda x: x * 1024,
    ),
    
    KeeneticSensorEntityDescription(
        key="hostname",
        name="Hostname",
        icon=ICON_ROUTER,
    ),
    KeeneticSensorEntityDescription(
        key="domainname",
        name="Domain Name",
        icon=ICON_DOMAIN,
    ),
    KeeneticSensorEntityDescription(
        key="firmware_version",
        name="Firmware Version",
        icon=ICON_FIRMWARE,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
    KeeneticSensorEntityDescription(
        key="firmware_branch",
        name="Firmware Branch",
        icon=ICON_FIRMWARE,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
    KeeneticSensorEntityDescription(
        key="model",
        name="Model",
        icon=ICON_ROUTER_WIRELESS,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
    KeeneticSensorEntityDescription(
        key="device",
        name="Device",
        icon=ICON_ROUTER_WIRELESS,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
    KeeneticSensorEntityDescription(
        key="manufacturer",
        name="Manufacturer",
        icon=ICON_FACTORY,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
    KeeneticSensorEntityDescription(
        key="hardware_version",
        name="Hardware Version",
        icon=ICON_CHIP,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
    KeeneticSensorEntityDescription(
        key="mesh_nodes_count",
        name="Mesh Nodes Count",
        icon="mdi:access-point-network",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda x: len(x.get("mesh", {})),
        use_full_data=True
    ),
)

INTERFACE_SENSORS: list[InterfaceSensorEntityDescription] = [
    InterfaceSensorEntityDescription(
        key="link",
        name="Link Status",
        icon=ICON_ETHERNET_ON,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda x: "up" if x.get("link") == "up" else "down",
        extra_attributes_fn=lambda x: {
            "rx_bytes": x.get("rxbytes", 0),
            "tx_bytes": x.get("txbytes", 0),
        },
    ),
    InterfaceSensorEntityDescription(
        key="speed",
        name="Speed",
        icon=ICON_SPEED,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda x: x.get("speed", 0),
        available_fn=lambda x: x.get("link") == "up",
    ),
    InterfaceSensorEntityDescription(
        key="rx_speed",
        name="Receive Speed",
        icon=ICON_DOWNLOAD,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DATA_RATE,
        value_fn=lambda x: x.get("rxspeed", 0),
    ),
    InterfaceSensorEntityDescription(
        key="tx_speed",
        name="Transmit Speed",
        icon=ICON_UPLOAD,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DATA_RATE,
        value_fn=lambda x: x.get("txspeed", 0),
    ),
]

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Keenetic sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    entities = []
    
    for description in SENSOR_TYPES:
        entities.append(KeeneticSensor(coordinator, description, config_entry))
    
    if coordinator.data and "interface" in coordinator.data:
        _LOGGER.debug("Found interfaces: %s", coordinator.data["interface"].keys())
        for interface_id, interface_data in coordinator.data["interface"].items():
            if interface_data.get("type") in ["wan", "port", "aaaaaa"]:
                entities.append(
                    KeeneticInterfaceSensor(
                        coordinator,
                        interface_id,
                        config_entry
                    )
                )

    if coordinator.data and "mesh" in coordinator.data:
        _LOGGER.debug("Found mesh nodes: %s", coordinator.data["mesh"].keys())
        for node_id, node_data in coordinator.data["mesh"].items():
            _LOGGER.debug("Adding mesh node: %s, data: %s", node_id, node_data)
            entities.append(
                KeeneticMeshNodeSensor(
                    coordinator,
                    node_id,
                    config_entry
                )
            )
    else:
        _LOGGER.debug("No mesh data found in coordinator data: %s", coordinator.data.keys())
    
    async_add_entities(entities)

class KeeneticSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Keenetic sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        description: KeeneticSensorEntityDescription,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._config_entry = config_entry
        
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_device_info = self._get_device_info()

    def _get_device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name=f"Keenetic {self.coordinator.data.get('device', 'Router')}",
            manufacturer=self.coordinator.data.get("manufacturer", MANUFACTURER),
            model=self.coordinator.data.get("model", "Router"),
            sw_version=self.coordinator.data.get("firmware_version", ""),
            hw_version=self.coordinator.data.get("hardware_version", ""),
        )

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
            
        if self.entity_description.use_full_data:
            return self.entity_description.value_fn(self.coordinator.data)
        else:
            value = self.coordinator.data.get(self.entity_description.key)
            if value is None:
                return None
            return self.entity_description.value_fn(value)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self.coordinator.data is not None
            and self.entity_description.available_fn(self.coordinator.data)
        )

class KeeneticMeshNodeSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Keenetic Mesh Node sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        node_id: str,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the mesh node sensor."""
        super().__init__(coordinator)
        self._node_id = node_id
        self._config_entry = config_entry
        
        node_data = self.coordinator.data["mesh"][node_id]
        model = node_data.get("model", "")
        known_host = node_data.get("known-host", "")
        self._attr_name = f"Mesh {model} ({known_host})" if known_host else f"Mesh {model}" or f"Mesh Node {node_id}"
        self._attr_unique_id = f"{config_entry.entry_id}_mesh_node_{node_id}"
        self.entity_id = f"sensor.keenetic_mesh_node_{node_id.replace(':', '_')}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
        )

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        if self.coordinator.data is None:
            return ICON_MESH_NODE_OFFLINE
            
        mesh_data = self.coordinator.data.get("mesh", {})
        node_data = mesh_data.get(self._node_id, {})
        return ICON_MESH_NODE if node_data.get("status") == "connected" else ICON_MESH_NODE_OFFLINE

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
            
        mesh_data = self.coordinator.data.get("mesh", {})
        node_data = mesh_data.get(self._node_id, {})
        return node_data.get("status", "unknown")

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self.coordinator.data is None:
            _LOGGER.debug("Coordinator data is None")
            return {}
            
        mesh_data = self.coordinator.data.get("mesh", {})
        _LOGGER.debug("Mesh data from coordinator: %s", mesh_data)
        
        node_data = mesh_data.get(self._node_id, {})
        _LOGGER.debug("Node data for %s: %s", self._node_id, node_data)
        
        attributes = node_data.get("attributes", {})
        _LOGGER.debug("Node attributes: %s", attributes)
        
        result = {
            "ip_address": attributes.get("ip", ""),
            "mode": attributes.get("mode", ""),
            "hw_id": attributes.get("hw_id", ""),
            "firmware": attributes.get("firmware", ""),
            "firmware_available": attributes.get("firmware_available", ""),
            "memory": attributes.get("memory", ""),
            "uptime": attributes.get("uptime", ""),
            "cloud_state": attributes.get("cloud_agent_state", ""),
            "internet_available": attributes.get("internet_available", False),
        }
        
        _LOGGER.debug("Returning attributes: %s", result)
        return result

class KeeneticInterfaceSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Keenetic interface sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        interface_id: str,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the interface sensor."""
        super().__init__(coordinator)
        self._interface_id = interface_id
        self._config_entry = config_entry
        
        interface_data = self.coordinator.data["interface"][interface_id]
        self._attr_name = interface_data['label']
        self._attr_unique_id = f"{config_entry.entry_id}_interface_{interface_id}"
        self.entity_id = f"sensor.keenetic_interface_{interface_id}"
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"Keenetic {coordinator.data.get('device', 'Router')}",
            manufacturer=coordinator.data.get("manufacturer", "Keenetic"),
            model=coordinator.data.get("model", "Router"),
            sw_version=coordinator.data.get("firmware_version", ""),
            hw_version=coordinator.data.get("hardware_version", ""),
        )

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
            
        interface_data = self.coordinator.data["interface"][self._interface_id]
        return interface_data["link"]

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self.coordinator.data is None:
            return {}
            
        interface_data = self.coordinator.data["interface"][self._interface_id]
        
        return {
            "interface_id": interface_data["id"],
            "type": interface_data.get("type"),
            "description": interface_data.get("description"),
            "speed": f"{interface_data.get('speed', 0)} Mbps",
            "rx_speed": f"{interface_data.get('rxspeed', 0)} B/s",
            "tx_speed": f"{interface_data.get('txspeed', 0)} B/s",
            "rx_bytes": interface_data.get("rxbytes", 0),
            "tx_bytes": interface_data.get("txbytes", 0),
            **interface_data.get("attributes", {})
        }

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_ETHERNET_ON if self.native_value == "up" else ICON_ETHERNET_OFF