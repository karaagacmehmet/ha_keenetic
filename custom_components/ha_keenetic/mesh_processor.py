"""Mesh network data processor for Keenetic integration."""
import logging
from typing import Dict, Any

_LOGGER = logging.getLogger(__name__)

class MeshProcessor:
    """Process mesh network data from Keenetic router."""

    @staticmethod
    def process_mesh_nodes(mesh_info: list) -> Dict[str, Any]:
        """Process mesh nodes and return formatted data."""
        processed_mesh = {}
        try:
            if mesh_info and isinstance(mesh_info, list):
                for node in mesh_info:
                    node_id = node.get("mac", "")
                    if node_id:
                        processed_mesh[node_id] = {
                            "id": node_id,
                            "known_host": node.get("known-host", ""),
                            "hostname": node.get("hostname", ""),
                            "model": node.get("model", ""),
                            "status": "connected",
                            "attributes": {
                                "ip": node.get("ip", ""),
                                "mode": node.get("mode", ""),
                                "hw_id": node.get("hw_id", ""),
                                "firmware": node.get("fw", ""),
                                "firmware_available": node.get("fw-available", ""),
                                "memory": node.get("system", {}).get("memory", ""),
                                "uptime": node.get("system", {}).get("uptime", ""),
                                "ports": node.get("port", []),
                                "capabilities": node.get("capabilities", {}),
                                "cloud_agent_state": node.get("cloud-agent-state", ""),
                                "internet_available": node.get("internet-available", False),
                            }
                        }
            
            _LOGGER.debug("Processed mesh nodes: %s", processed_mesh)
            return processed_mesh
            
        except Exception as ex:
            _LOGGER.error("Error processing mesh nodes: %s", str(ex))
            return {}