# Devin/xr_env/metaverse/unity_integration.py
# Purpose: Provides a real-time bridge to the Unity 3D engine, enabling
#          programmatic control over a 3D world via WebSockets.

import logging
import asyncio
import websockets
import json
import threading
from typing import Dict, Any, List, Optional

# Configure basic logging
logger = logging.getLogger("UnityIntegration")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False

class UnityClient:
    """
    A WebSocket client for sending commands to a Unity server.
    """
    def __init__(self, uri="ws://localhost:8080"):
        self.uri = uri
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()

    def _run_event_loop(self):
        """Runs the asyncio event loop in a dedicated thread."""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def _connect(self):
        """Coroutine to establish the WebSocket connection."""
        try:
            self.websocket = await websockets.connect(self.uri)
            logger.info(f"Successfully connected to Unity WebSocket server at {self.uri}")
        except ConnectionRefusedError:
            logger.error(f"Connection refused. Is the Unity server running at {self.uri}?")
            self.websocket = None
        except Exception as e:
            logger.error(f"Failed to connect to Unity: {e}")
            self.websocket = None
            
    def connect(self):
        """Establishes the connection to the Unity server."""
        if self.websocket and self.websocket.open:
            logger.warning("Already connected.")
            return
        future = asyncio.run_coroutine_threadsafe(self._connect(), self._loop)
        future.result(timeout=5) # Wait for connection to establish

    async def _send_command(self, command: str, params: Dict[str, Any]):
        """Coroutine to send a JSON command to Unity."""
        if not self.websocket or not self.websocket.open:
            logger.error("Cannot send command: Not connected to Unity.")
            return
        
        message = json.dumps({"command": command, "params": params})
        await self.websocket.send(message)
        logger.debug(f"Sent command: {message}")

    def send_command(self, command: str, params: Dict[str, Any]):
        """Sends a command to Unity from a synchronous context."""
        asyncio.run_coroutine_threadsafe(self._send_command(command, params), self._loop)

    # --- High-Level API for 3D World Building ---
    def create_primitive(self, shape: str, name: str, position: List[float], color: List[float]):
        """Creates a primitive shape (Cube, Sphere, etc.) in the Unity scene."""
        self.send_command("CREATE_PRIMITIVE", {
            "shape": shape, "name": name, "position": position, "color": color
        })
        
    def move_object(self, name: str, position: List[float]):
        """Moves an existing object in the scene."""
        self.send_command("MOVE_OBJECT", {"name": name, "position": position})
        
    def delete_object(self, name: str):
        """Deletes an object from the scene."""
        self.send_command("DELETE_OBJECT", {"name": name})

    def stop(self):
        """Stops the asyncio event loop."""
        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

# --- C# Server Script for Unity (`DevinListener.cs`) ---
UNITY_CSHARP_CODE = """
// DevinListener.cs: Attach this script to an empty GameObject in your Unity scene.
// PREREQUISITE: You must install a WebSocket package in Unity.
// A good option is NativeWebSocket: https://github.com/endel/NativeWebSocket
// Open Package Manager -> Add package from git URL... -> com.github.endel.nativewebsocket

using UnityEngine;
using NativeWebSocket;
using System.Collections.Generic;
using System.Collections.Concurrent;

// --- Data structures to parse JSON messages from Python ---
[System.Serializable]
public class CommandMessage {
    public string command;
    public Parameters params;
}

[System.Serializable]
public class Parameters {
    public string shape;
    public string name;
    public float[] position;
    public float[] color;
}

public class DevinListener : MonoBehaviour {
    WebSocket websocket;
    // Use a thread-safe queue to pass messages from the WebSocket thread to Unity's main thread
    private readonly ConcurrentQueue<CommandMessage> messageQueue = new ConcurrentQueue<CommandMessage>();

    async void Start() {
        websocket = new WebSocket("ws://localhost:8080");

        websocket.OnOpen += () => {
            Debug.Log("Connection open!");
        };

        websocket.OnError += (e) => {
            Debug.Log("Error! " + e);
        };



        websocket.OnClose += (e) => {
            Debug.Log("Connection closed!");
        };

        websocket.OnMessage += (bytes) => {
            var message = System.Text.Encoding.UTF8.GetString(bytes);
            Debug.Log("OnMessage! " + message);
            // Parse the message and add to the queue for processing in Update()
            CommandMessage cmd = JsonUtility.FromJson<CommandMessage>(message);
            messageQueue.Enqueue(cmd);
        };

        // Keep sending messages at every 0.3s
        InvokeRepeating("SendWebSocketMessage", 0.0f, 0.3f);

        await websocket.Connect();
    }

    void Update() {
        #if !UNITY_WEBGL || UNITY_EDITOR
            websocket.DispatchMessageQueue();
        #endif

        // Process all messages from the queue on the main thread
        while (messageQueue.TryDequeue(out CommandMessage cmd)) {
            ProcessCommand(cmd);
        }
    }
    
    // --- This is the core command processor ---
    private void ProcessCommand(CommandMessage cmd) {
        switch (cmd.command) {
            case "CREATE_PRIMITIVE":
                PrimitiveType type = (PrimitiveType)System.Enum.Parse(typeof(PrimitiveType), cmd.params.shape, true);
                GameObject obj = GameObject.CreatePrimitive(type);
                obj.name = cmd.params.name;
                obj.transform.position = new Vector3(cmd.params.position[0], cmd.params.position[1], cmd.params.position[2]);
                
                Material mat = obj.GetComponent<Renderer>().material;
                mat.color = new Color(cmd.params.color[0], cmd.params.color[1], cmd.params.color[2], cmd.params.color[3]);
                break;

            case "MOVE_OBJECT":
                GameObject objToMove = GameObject.Find(cmd.params.name);
                if (objToMove != null) {
                    objToMove.transform.position = new Vector3(cmd.params.position[0], cmd.params.position[1], cmd.params.position[2]);
                }
                break;
                
            case "DELETE_OBJECT":
                GameObject objToDelete = GameObject.Find(cmd.params.name);
                if (objToDelete != null) {
                    Destroy(objToDelete);
                }
                break;
        }
    }
    
    async void SendWebSocketMessage() {
        if (websocket.State == WebSocketState.Open) {
            await websocket.SendText("{\"status\": \"alive\"}");
        }
    }

    private async void OnApplicationQuit() {
        await websocket.Close();
    }
}
"""

# --- Example Usage ---
if __name__ == "__main__":
    import time
    print("=========================================================")
    print("=== Unity 3D Integration (Live Demo) 🧊🎮 ===")
    print("=========================================================")
    print("\n--- SETUP INSTRUCTIONS ---")
    print("1. Create a new 3D project in Unity Hub.")
    print("2. In Unity, go to Window -> Package Manager.")
    print("3. Click the '+' icon -> 'Add package from git URL...'")
    print("4. Enter 'com.github.endel.nativewebsocket' and click Add.")
    print("5. Create an empty GameObject in your scene (right-click in Hierarchy -> Create Empty).")
    print("6. Create a new C# Script named 'DevinListener.cs' in your Assets.")
    print("7. Copy the C# code from this script into 'DevinListener.cs'.")
    print("8. Drag the 'DevinListener.cs' script onto your empty GameObject in the Hierarchy.")
    print("9. Press the 'Play' button in the Unity Editor.")
    print("10. Run this Python script.")
    input("\nPress Enter to start the Python client...")

    client = None
    try:
        client = UnityClient()
        client.connect()
        
        if client.websocket is None:
            raise ConnectionError("Could not connect to Unity. Please follow setup instructions.")

        print("\n--- Sending commands to build a scene in Unity... ---")
        # Create a floor
        client.create_primitive("Cube", "Floor", [0, -0.5, 0], [0.5, 0.5, 0.5, 1])
        client.send_command("SCALE_OBJECT", {"name": "Floor", "scale": [20, 1, 20]}) # Assuming SCALE_OBJECT is implemented in C#
        time.sleep(1)

        # Create a moving sphere
        client.create_primitive("Sphere", "BouncingBall", [0, 2, 0], [1, 0, 0, 1]) # Red
        time.sleep(1)
        
        # Animate the sphere
        print("--- Animating the scene... ---")
        for i in range(50):
            y_pos = 2.0 + math.sin(time.time() * 5) * 1.5
            client.move_object("BouncingBall", [0, y_pos, 0])
            time.sleep(0.05)
            
        time.sleep(1)
        client.delete_object("BouncingBall")
        print("--- Animation complete. ---")

    except Exception as e:
        logger.error(f"Demo failed to run: {e}")
    finally:
        if client:
            client.stop()
    
    print("\n=========================================================")
    print("=== Unity Integration Demo Complete ===")
    print("=========================================================")
