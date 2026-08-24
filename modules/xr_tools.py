# Devin/modules/xr_tools.py
# Purpose: A high-level facade that orchestrates Devin's XR/metaverse tools --
#          a live bridge to a running Unity 3D engine instance, and pure-Python
#          3D spatial reasoning/pathfinding over the scene it reports -- into
#          one cohesive interface for the AGI.
#
# NOTE: xr_env/digital_identity/nft_generator.py was evaluated and deliberately
# NOT wrapped here: it uses MockIPFSUploader and MockBlockchainMinter, which
# only write local files and fabricate fake-looking IPFS hashes / tx hashes.
# There is no real IPFS upload or blockchain mint happening, so it has no
# genuine capability to expose as an agent tool.

import logging
from typing import Any, Dict, List, Optional

# --- Import the low-level XR tools this facade will manage ---
from xr_env.metaverse.unity_integration import UnityClient
from xr_env.metaverse.spatial_computing import SpatialComputer, NavMeshNode, DEVIN_CORE_AVAILABLE

# Configure basic logging
logger = logging.getLogger("XRFacade")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class XRFacade:
    """
    A single, simplified interface to Devin's XR/metaverse capabilities:

    - A live command bridge to a running Unity 3D engine instance
      (UnityClient), used to build/move/delete objects in a 3D scene.
    - Pure-Python spatial reasoning (SpatialComputer): nearest-object
      queries and A* pathfinding over a scene graph / navmesh graph that
      the caller supplies (e.g. as reported by Unity).

    UnityClient will simply fail to connect (and log a warning) if no Unity
    instance is running at the configured WebSocket URI -- that is expected
    in most environments and is not treated as a fatal error.
    """

    def __init__(self, unity_uri: str = "ws://localhost:8080"):
        """
        Initializes the Unity bridge and the spatial computer on top of it.

        Args:
            unity_uri (str): WebSocket URI of the Unity DevinListener bridge.
        """
        self.unity_client = UnityClient(uri=unity_uri)
        self._unity_connected = False

        self.spatial_computer: Optional[SpatialComputer] = None
        if DEVIN_CORE_AVAILABLE:
            try:
                self.spatial_computer = SpatialComputer(self.unity_client)
            except ImportError as e:
                logger.warning(f"SpatialComputer unavailable: {e}")
        else:
            logger.warning("SpatialComputer unavailable: numpy (or unity_integration) failed to import.")

        logger.info("XRFacade initialized.")

    # ------------------------------------------------------------------
    # Unity bridge
    # ------------------------------------------------------------------

    def connect_to_unity(self) -> bool:
        """
        Attempts to connect to the configured Unity WebSocket bridge.
        Fails gracefully (returns False, logs a warning) if no Unity
        instance is listening -- this is the expected case unless the
        user has a Unity Editor open and running the DevinListener script.

        Returns:
            bool: True if the connection was established, False otherwise.
        """
        try:
            self.unity_client.connect()
        except Exception as e:
            logger.warning(f"Could not connect to Unity at {self.unity_client.uri}: {e}")
            self._unity_connected = False
            return False
        self._unity_connected = bool(self.unity_client.websocket)
        return self._unity_connected

    def is_unity_connected(self) -> bool:
        """Returns whether the Unity WebSocket bridge is currently connected."""
        ws = self.unity_client.websocket
        return bool(ws and getattr(ws, "open", False))

    def create_scene_object(self, shape: str, name: str, position: List[float], color: List[float]) -> str:
        """
        Creates a primitive shape (e.g. "Cube", "Sphere") in the connected Unity scene.

        Args:
            shape (str): Unity primitive name ("Cube", "Sphere", "Cylinder", "Capsule", "Plane", "Quad").
            name (str): The GameObject name to assign.
            position (List[float]): [x, y, z] world position.
            color (List[float]): [r, g, b, a] color, each in 0.0-1.0.
        """
        if not self.is_unity_connected():
            return "Not connected to Unity. Call connect_to_unity() first (requires a running Unity instance with the DevinListener bridge script)."
        self.unity_client.create_primitive(shape, name, position, color)
        return f"Sent CREATE_PRIMITIVE for '{name}' ({shape}) at {position}."

    def move_scene_object(self, name: str, position: List[float]) -> str:
        """Moves an existing named object in the connected Unity scene to a new position."""
        if not self.is_unity_connected():
            return "Not connected to Unity. Call connect_to_unity() first."
        self.unity_client.move_object(name, position)
        return f"Sent MOVE_OBJECT for '{name}' to {position}."

    def delete_scene_object(self, name: str) -> str:
        """Deletes a named object from the connected Unity scene."""
        if not self.is_unity_connected():
            return "Not connected to Unity. Call connect_to_unity() first."
        self.unity_client.delete_object(name)
        return f"Sent DELETE_OBJECT for '{name}'."

    def disconnect_from_unity(self) -> str:
        """Stops the Unity bridge's background event loop and connection."""
        self.unity_client.stop()
        self._unity_connected = False
        return "Unity bridge stopped."

    # ------------------------------------------------------------------
    # Spatial reasoning (pure Python -- no external service required)
    # ------------------------------------------------------------------

    def update_scene_graph(self, scene_objects: List[Dict[str, Any]]) -> str:
        """
        Loads a 3D scene graph for spatial queries. Each object dict must have:
        {"name": str, "position": [x,y,z], "bounds_center": [x,y,z], "bounds_size": [x,y,z]}.
        This data can come from a live Unity GET_SCENE_GRAPH response, or be
        supplied directly by the caller for offline spatial reasoning.

        Returns:
            str: A status message with the number of objects loaded.
        """
        if not self.spatial_computer:
            return "SpatialComputer is unavailable (numpy not installed)."
        self.spatial_computer.update_scene_graph(scene_objects)
        return f"Scene graph updated with {len(self.spatial_computer.scene_graph)} object(s)."

    def find_nearest_scene_object(self, point: List[float], ignore_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Finds the object in the loaded scene graph closest to a given 3D point
        (requires update_scene_graph() to have been called first).

        Args:
            point (List[float]): [x, y, z] query point.
            ignore_name (Optional[str]): An object name to exclude from the search
                (e.g. the querying agent's own object).

        Returns:
            Optional[Dict[str, Any]]: {"name": str, "position": [x,y,z]}, or None if
                no objects are loaded or found.
        """
        if not self.spatial_computer:
            logger.error("find_nearest_scene_object called but SpatialComputer is unavailable.")
            return None
        obj = self.spatial_computer.find_nearest_object(point, ignore_name=ignore_name)
        if obj is None:
            return None
        return {"name": obj.name, "position": obj.position.tolist()}

    def set_navmesh(self, nodes: List[Dict[str, Any]]) -> str:
        """
        Defines the navigation-mesh graph used by find_path() for A* pathfinding.
        Each node dict must have: {"id": int, "position": [x,y,z], "neighbors": [int, ...]}
        where "neighbors" lists the ids of directly-connected nodes.

        Args:
            nodes (List[Dict[str, Any]]): The navmesh node list.

        Returns:
            str: A status message with the number of nodes loaded.
        """
        if not self.spatial_computer:
            return "SpatialComputer is unavailable (numpy not installed)."
        if not NUMPY_AVAILABLE:
            return "SpatialComputer is unavailable (numpy not installed)."

        nav_mesh: Dict[int, NavMeshNode] = {}
        for node in nodes:
            node_id = int(node["id"])
            nav_mesh[node_id] = NavMeshNode(
                id=node_id,
                position=np.array(node["position"], dtype=float),
                neighbors=list(node.get("neighbors", [])),
            )
        self.spatial_computer.nav_mesh = nav_mesh
        return f"Navmesh set with {len(nav_mesh)} node(s)."

    def find_path(self, start_pos: List[float], end_pos: List[float]) -> Optional[List[List[float]]]:
        """
        Computes a 3D path between two points using A* over the navmesh graph
        (requires set_navmesh() to have been called first).

        Args:
            start_pos (List[float]): [x, y, z] starting point.
            end_pos (List[float]): [x, y, z] destination point.

        Returns:
            Optional[List[List[float]]]: An ordered list of [x,y,z] waypoints from
                start to end, or None if no path was found / navmesh is empty.
        """
        if not self.spatial_computer:
            logger.error("find_path called but SpatialComputer is unavailable.")
            return None
        return self.spatial_computer.find_path_3d_astar(start_pos, end_pos)


# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== XR Facade Demo ===")
    print("=========================================================")

    xr = XRFacade()

    print("\n--- Attempting Unity connection (expected to fail without a running Unity instance) ---")
    connected = xr.connect_to_unity()
    print(f"Connected: {connected}")

    print("\n--- Offline spatial reasoning demo (no Unity required) ---")
    print(xr.update_scene_graph([
        {"name": "Obstacle", "position": [5, 0.5, 5], "bounds_center": [5, 0.5, 5], "bounds_size": [1, 1, 1]},
        {"name": "Agent", "position": [0, 0.5, 0], "bounds_center": [0, 0.5, 0], "bounds_size": [1, 1, 1]},
    ]))
    nearest = xr.find_nearest_scene_object([0, 0.5, 0], ignore_name="Agent")
    print(f"Nearest object to Agent: {nearest}")

    print(xr.set_navmesh([
        {"id": 0, "position": [0, 0, 0], "neighbors": [1]},
        {"id": 1, "position": [5, 0, 0], "neighbors": [0, 2]},
        {"id": 2, "position": [9, 0, 9], "neighbors": [1]},
    ]))
    path = xr.find_path([0, 0.5, 0], [9, 0.5, 9])
    print(f"Path: {path}")

    xr.disconnect_from_unity()
    print("\n=========================================================")
    print("=== XR Facade Demo Complete ===")
    print("=========================================================")
