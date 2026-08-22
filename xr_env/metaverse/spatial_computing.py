# Devin/xr_env/metaverse/spatial_computing.py
# Purpose: Provides spatial reasoning for 3D environments, including scene
#          analysis, spatial querying, and 3D pathfinding on a navmesh.

import logging
import json
import math
import heapq
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

try:
    import numpy as np
    from xr_env.metaverse.unity_integration import UnityClient
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("SpatialComputing")
# (Logger setup omitted for brevity, assumed to be configured)

@dataclass
class SceneObject:
    """Represents an object within the 3D scene."""
    name: str
    position: np.ndarray
    bounds_center: np.ndarray
    bounds_size: np.ndarray

@dataclass
class NavMeshNode:
    """Represents a node in the navigation mesh graph."""
    id: int
    position: np.ndarray
    neighbors: List[int] = field(default_factory=list)

class SpatialComputer:
    """Performs spatial analysis and pathfinding on a 3D scene graph."""
    def __init__(self, unity_client: UnityClient):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core Devin module is missing. Error: {_import_error}")

        self.unity_client = unity_client
        self.scene_graph: Dict[str, SceneObject] = {}
        self.nav_mesh: Dict[int, NavMeshNode] = {}
        
        # We need to add handlers to the unity client to receive data
        # This is a conceptual link; the client would need a callback system.
        logger.info("SpatialComputer initialized. Ready to receive scene data from Unity.")

    def update_scene_graph(self, scene_data: List[Dict]):
        """Processes and stores scene data received from Unity."""
        self.scene_graph.clear()
        for obj_data in scene_data:
            name = obj_data['name']
            self.scene_graph[name] = SceneObject(
                name=name,
                position=np.array(obj_data['position']),
                bounds_center=np.array(obj_data['bounds_center']),
                bounds_size=np.array(obj_data['bounds_size'])
            )
        logger.info(f"Scene graph updated with {len(self.scene_graph)} objects.")

    def find_nearest_object(self, point: List[float], ignore_name: Optional[str] = None) -> Optional[SceneObject]:
        """Finds the closest object in the scene to a given 3D point."""
        point_vec = np.array(point)
        min_dist = float('inf')
        nearest_obj = None
        for name, obj in self.scene_graph.items():
            if name == ignore_name: continue
            dist = np.linalg.norm(obj.position - point_vec)
            if dist < min_dist:
                min_dist = dist
                nearest_obj = obj
        return nearest_obj

    def find_path_3d_astar(self, start_pos: List[float], end_pos: List[float]) -> Optional[List[List[float]]]:
        """Calculates a path on the navmesh using the A* algorithm."""
        if not self.nav_mesh:
            logger.error("Cannot find path: Navigation mesh is empty.")
            return None
            
        start_vec, end_vec = np.array(start_pos), np.array(end_pos)
        
        # Find the closest navmesh nodes to the start and end points
        start_node = min(self.nav_mesh.values(), key=lambda n: np.linalg.norm(n.position - start_vec))
        end_node = min(self.nav_mesh.values(), key=lambda n: np.linalg.norm(n.position - end_vec))
        
        # A* implementation
        open_set = [(0, start_node.id)] # (priority, node_id)
        came_from = {}
        g_score = {node_id: float('inf') for node_id in self.nav_mesh}
        g_score[start_node.id] = 0
        
        while open_set:
            _, current_id = heapq.heappop(open_set)
            
            if current_id == end_node.id:
                # Reconstruct path
                path = []
                while current_id in came_from:
                    path.append(self.nav_mesh[current_id].position.tolist())
                    current_id = came_from[current_id]
                path.append(start_node.position.tolist())
                return path[::-1] # Reverse to get start -> end

            current_node = self.nav_mesh[current_id]
            for neighbor_id in current_node.neighbors:
                neighbor_node = self.nav_mesh[neighbor_id]
                tentative_g_score = g_score[current_id] + np.linalg.norm(current_node.position - neighbor_node.position)
                if tentative_g_score < g_score[neighbor_id]:
                    came_from[neighbor_id] = current_id
                    g_score[neighbor_id] = tentative_g_score
                    h_score = np.linalg.norm(neighbor_node.position - end_vec)
                    f_score = tentative_g_score + h_score
                    heapq.heappush(open_set, (f_score, neighbor_id))
        
        return None # No path found

# --- C# Server Script for Unity (`DevinListener.cs`, UPDATED) ---
UPDATED_UNITY_CSHARP_CODE = """
// DevinListener.cs: Attach this script to an empty GameObject in your Unity scene.
// This is an UPDATED version that handles scene graph and navmesh requests.
// PREREQUISITE: Unity's AI Navigation package must be installed (Window -> AI -> Navigation).
// PREREQUISITE: You must install a WebSocket package (e.g., NativeWebSocket).

using UnityEngine;
using UnityEngine.AI; // Required for NavMesh
using NativeWebSocket;
using System.Collections.Generic;
using System.Collections.Concurrent;
using System.Linq; // Required for LINQ queries

// (CommandMessage and Parameters classes are the same as in unity_integration.py)

// --- New data structures for sending scene data to Python ---
[System.Serializable]
public class SceneObjectData {
    public string name;
    public float[] position;
    public float[] bounds_center;
    public float[] bounds_size;
}

[System.Serializable]
public class SceneGraphMessage {
    public string messageType = "SCENE_GRAPH_DATA";
    public List<SceneObjectData> objects;
}


public class DevinListener : MonoBehaviour {
    // ... (WebSocket setup and message queue are the same) ...

    private void ProcessCommand(CommandMessage cmd) {
        switch (cmd.command) {
            // ... (CREATE_PRIMITIVE, MOVE_OBJECT, DELETE_OBJECT are the same) ...

            case "GET_SCENE_GRAPH":
                // Find all objects with a renderer (i.e., visible objects)
                var renderers = FindObjectsOfType<MeshRenderer>();
                var sceneGraph = new SceneGraphMessage { objects = new List<SceneObjectData>() };
                foreach (var rend in renderers) {
                    sceneGraph.objects.Add(new SceneObjectData {
                        name = rend.gameObject.name,
                        position = new float[] { rend.transform.position.x, rend.transform.position.y, rend.transform.position.z },
                        bounds_center = new float[] { rend.bounds.center.x, rend.bounds.center.y, rend.bounds.center.z },
                        bounds_size = new float[] { rend.bounds.size.x, rend.bounds.size.y, rend.bounds.size.z }
                    });
                }
                string json = JsonUtility.ToJson(sceneGraph);
                // Send the scene graph data back to the Python client
                websocket.SendText(json);
                break;
        }
    }
    // ... (OnApplicationQuit is the same) ...
}
"""

# --- Example Usage ---
if __name__ == "__main__":
    import time
    print("=========================================================")
    print("=== Spatial Computing (Live Unity Demo) 🧠🧊 ===")
    print("=========================================================")
    print("\n--- SETUP INSTRUCTIONS (UPDATED) ---")
    print("1. Follow the setup from 'unity_integration.py'.")
    print("2. In Unity, open the Navigation window (Window -> AI -> Navigation).")
    print("3. In the 'Bake' tab, click the 'Bake' button to generate a NavMesh for your scene.")
    print("4. Update your 'DevinListener.cs' script with the NEW C# code from this file.")
    print("5. Press 'Play' in the Unity Editor, then run this script.")
    input("\nPress Enter to start the Python client...")
    
    # NOTE: The demo below is conceptual. A real implementation would require the UnityClient
    # to have a robust callback system to receive the SCENE_GRAPH_DATA message from Unity.
    print("\n--- CONCEPTUAL DEMO ---")
    print("This demo outlines the logic. A full implementation requires a bidirectional client.")
    
    # 1. Setup clients
    client = UnityClient()
    client.connect()
    computer = SpatialComputer(client)

    # 2. Build a scene
    print("1. Building a simple scene in Unity...")
    client.create_primitive("Cube", "Obstacle", [5, 0.5, 5], [0, 0, 1, 1])
    client.create_primitive("Sphere", "Agent", [0, 0.5, 0], [0, 1, 0, 1])
    
    # 3. Request scene data (conceptual)
    print("2. Requesting scene data from Unity...")
    # client.send_command("GET_SCENE_GRAPH", {})
    # In a real app, we'd wait here for the response. We will simulate it.
    simulated_scene_data = [
        {'name': 'Obstacle', 'position': [5, 0.5, 5], 'bounds_center': [5,0.5,5], 'bounds_size': [1,1,1]},
        {'name': 'Agent', 'position': [0, 0.5, 0], 'bounds_center': [0,0.5,0], 'bounds_size': [1,1,1]},
    ]
    computer.update_scene_graph(simulated_scene_data)
    
    # 4. Perform a spatial query
    print("3. Finding the nearest object to the Agent...")
    nearest = computer.find_nearest_object([0, 0.5, 0], ignore_name="Agent")
    print(f"   -> Nearest object is '{nearest.name}' at position {nearest.position.tolist()}")
    
    # 5. Perform 3D pathfinding (conceptual)
    print("4. Finding a 3D path from Agent to [9, 0.5, 9]...")
    # We simulate a simple navmesh graph
    computer.nav_mesh = {
        0: NavMeshNode(id=0, position=np.array([0,0,0]), neighbors=[1]),
        1: NavMeshNode(id=1, position=np.array([5,0,0]), neighbors=[0,2]),
        2: NavMeshNode(id=2, position=np.array([9,0,9]), neighbors=[1]),
    }
    path = computer.find_path_3d_astar([0,0.5,0], [9,0.5,9])
    
    if path:
        print(f"   -> Path found with {len(path)} waypoints: {path}")
        print("5. Animating agent along the path in Unity...")
        for waypoint in path:
            client.move_object("Agent", waypoint)
            time.sleep(0.5)
    
    client.stop()
    print("\n=========================================================")
    print("=== Spatial Computing Demo Complete ===")
    print("=========================================================")
