# # Devin/modules/robotics/path_planning.py
# # Purpose: Provides path planning capabilities for a robot to navigate in a 2D environment.
# #          Implements the A* (A-star) search algorithm on an occupancy grid.

# import logging
# import heapq # Efficient priority queue for A* open set
# from typing import List, Tuple, Dict, Optional, Set
# from dataclasses import dataclass, field
# import numpy as np

# # Configure basic logging
# logger = logging.getLogger("PathPlanner")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# # Type hint for a location on the grid (row, col)
# GridLocation = Tuple[int, int]
# # Type hint for a path
# PathType = List[GridLocation]

# @dataclass(order=True)
# class PriorityNode:
#     """A node used in the A* priority queue for sorting."""
#     priority: float # The f-score (g_score + h_score)
#     # The item itself needs a __lt__ method if priorities are equal, or just use another sortable field
#     item: Any=field(compare=False)

# class PathPlanner:
#     """
#     Finds an optimal path on a 2D occupancy grid using the A* algorithm.
#     """

#     def __init__(self, occupancy_grid: np.ndarray):
#         """
#         Initializes the PathPlanner with a map of the environment.

#         Args:
#             occupancy_grid (np.ndarray): A 2D numpy array where:
#                 - 0 represents free, traversable space.
#                 - 1 (or any non-zero value) represents an occupied, non-traversable obstacle.
#         """
#         if not isinstance(occupancy_grid, np.ndarray) or occupancy_grid.ndim != 2:
#             raise ValueError("occupancy_grid must be a 2D NumPy array.")
        
#         self.grid = occupancy_grid
#         self.height, self.width = occupancy_grid.shape
#         logger.info(f"PathPlanner initialized with a {self.width}x{self.height} grid.")

#     def _is_valid_location(self, loc: GridLocation) -> bool:
#         """Checks if a location is within grid boundaries and is not an obstacle."""
#         r, c = loc
#         return (0 <= r < self.height and 0 <= c < self.width) and (self.grid[r, c] == 0)

#     def _get_neighbors(self, current_loc: GridLocation) -> List[GridLocation]:
#         """
#         Gets the valid, traversable neighbors of a grid location.
#         Considers 8-directional movement (including diagonals).
#         """
#         r, c = current_loc
#         neighbors = []
#         # Possible moves: [dr, dc, move_cost]
#         # Straight moves cost 1.0, diagonal moves cost sqrt(2) ~= 1.414
#         possible_moves = [
#             (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1), # Straight
#             (r - 1, c - 1), (r - 1, c + 1), (r + 1, c - 1), (r + 1, c + 1) # Diagonal
#         ]
        
#         for next_loc in possible_moves:
#             if self._is_valid_location(next_loc):
#                 neighbors.append(next_loc)
#         return neighbors

#     def _heuristic(self, loc_a: GridLocation, loc_b: GridLocation) -> float:
#         """
#         Calculates the heuristic (estimated distance) between two points.
#         Uses Euclidean distance for a more accurate estimate than Manhattan distance.
#         """
#         (r1, c1) = loc_a
#         (r2, c2) = loc_b
#         return np.sqrt((r1 - r2)**2 + (c1 - c2)**2)
#         # Alternative: Manhattan distance (faster but less accurate for diagonal movement)
#         # return abs(r1 - r2) + abs(c1 - c2)

#     def _reconstruct_path(self, came_from: Dict[GridLocation, GridLocation], current: GridLocation) -> PathType:
#         """Traces the path backwards from the goal to the start."""
#         total_path = [current]
#         while current in came_from:
#             current = came_from[current]
#             total_path.append(current)
#         return total_path[::-1] # Reverse to get path from start to goal

#     def plan_path_astar(self, start: GridLocation, goal: GridLocation) -> Optional[PathType]:
#         """
#         Finds a path from start to goal using the A* search algorithm.

#         Args:
#             start (GridLocation): The starting coordinates (row, col).
#             goal (GridLocation): The goal coordinates (row, col).

#         Returns:
#             Optional[PathType]: A list of (row, col) tuples representing the path,
#                                 or None if no path is found.
#         """
#         logger.info(f"Planning path from {start} to {goal} using A* algorithm...")

#         if not self._is_valid_location(start):
#             logger.error(f"Start location {start} is invalid (out of bounds or on an obstacle).")
#             return None
#         if not self._is_valid_location(goal):
#             logger.error(f"Goal location {goal} is invalid (out of bounds or on an obstacle).")
#             return None
#         if start == goal:
#             return [start] # Path is just the start point

#         # The set of nodes already evaluated
#         closed_set: Set[GridLocation] = set()
        
#         # The set of discovered nodes that are not yet evaluated.
#         # Implemented as a priority queue (min-heap) for efficiency.
#         # Items are (f_score, node)
#         open_set: List[PriorityNode] = [PriorityNode(priority=self._heuristic(start, goal), item=start)]
        
#         # came_from[n] is the node immediately preceding it on the cheapest path from start to n.
#         came_from: Dict[GridLocation, GridLocation] = {}
        
#         # g_score[n] is the cost of the cheapest path from start to n currently known.
#         g_score: Dict[GridLocation, float] = defaultdict(lambda: float('inf'))
#         g_score[start] = 0.0
        
#         # f_score[n] represents our current best guess as to how cheap a path from start to goal
#         # can be if it goes through n. f_score[n] = g_score[n] + h(n).
#         f_score: Dict[GridLocation, float] = defaultdict(lambda: float('inf'))
#         f_score[start] = self._heuristic(start, goal)

#         # Map to keep track of items in the priority queue for efficient updates/removals
#         open_set_map = {start: open_set[0]}

#         while open_set:
#             # Get the node in open_set having the lowest f_score value
#             current_node = heapq.heappop(open_set).item
            
#             if current_node not in open_set_map: # If already removed (e.g., duplicate with higher f_score)
#                 continue
            
#             del open_set_map[current_node] # Remove from map as we process it

#             if current_node == goal:
#                 logger.info(f"Path found! Length: {len(self._reconstruct_path(came_from, current))} steps.")
#                 return self._reconstruct_path(came_from, current)

#             closed_set.add(current_node)

#             for neighbor in self._get_neighbors(current_node):
#                 if neighbor in closed_set:
#                     continue # Ignore neighbors already evaluated

#                 # The distance from start to a neighbor
#                 # d(current,neighbor) is the weight of the edge from current to neighbor
#                 # Here, straight moves cost 1, diagonal moves cost sqrt(2)
#                 move_cost = np.sqrt((current[0] - neighbor[0])**2 + (current[1] - neighbor[1])**2)
#                 tentative_g_score = g_score[current] + move_cost

#                 if tentative_g_score < g_score[neighbor]:
#                     # This path to neighbor is better than any previous one. Record it!
#                     came_from[neighbor] = current
#                     g_score[neighbor] = tentative_g_score
#                     f_score[neighbor] = tentative_g_score + self._heuristic(neighbor, goal)
                    
#                     if neighbor not in open_set_map:
#                         entry = PriorityNode(priority=f_score[neighbor], item=neighbor)
#                         heapq.heappush(open_set, entry)
#                         open_set_map[neighbor] = entry
#                     # If neighbor is already in open_set with a higher f_score,
#                     # a proper priority queue implementation would update its priority.
#                     # Since we are using a basic heapq and checking on pop, we just add the new, better path.
#                     # A more optimized version might use a structure that supports priority updates.

#         logger.warning(f"No path found from {start} to {goal}.")
#         return None # No path was found

# import logging
# import heapq
# from collections import defaultdict # Added for Part 1 logic
# from typing import List, Tuple, Dict, Optional, Set, Any
# from dataclasses import dataclass, field
# import numpy as np
# import math # For sqrt


#     def _smooth_path_conceptual(self, path: PathType) -> PathType:
#         """
#         Conceptually smooths a jagged grid-based path.
#         A simple approach is to remove unnecessary intermediate waypoints on straight lines.
#         More advanced methods use splines or other curve-fitting algorithms.
#         """
#         if not path or len(path) < 3:
#             return path # Nothing to smooth

#         logger.info("Smoothing the raw path...")
#         # Simple "shortcut" smoothing:
#         smoothed_path = [path[0]]
#         i = 0
#         while i < len(path) - 1:
#             # Check for line-of-sight from current point `i` to a future point `j`
#             # For this conceptual version, we'll just remove redundant points on straight axis-aligned lines
#             r1, c1 = path[i]
#             r2, c2 = path[i+1]
            
#             # This is a very basic smoother. A real one would use more advanced geometry.
#             # Look ahead to see if the direction changes.
#             if i < len(path) - 2:
#                 r3, c3 = path[i+2]
#                 # Vector from i to i+1
#                 dir1 = (r2 - r1, c2 - c1)
#                 # Vector from i+1 to i+2
#                 dir2 = (r3 - r2, c3 - c2)
                
#                 if dir1 == dir2: # Still moving in the same direction, so skip the intermediate point
#                     i += 1
#                     continue

#             smoothed_path.append(path[i+1])
#             i += 1
            
#         logger.info(f"  Path smoothed from {len(path)} points to {len(smoothed_path)} points.")
#         return smoothed_path

#     def find_path(self, start: GridLocation, goal: GridLocation, smooth: bool = True) -> Optional[PathType]:
#         """
#         The main public method to find and optionally smooth a path.

#         Args:
#             start (GridLocation): The starting coordinates (row, col).
#             goal (GridLocation): The goal coordinates (row, col).
#             smooth (bool): If True, applies a conceptual smoothing algorithm to the path.

#         Returns:
#             Optional[PathType]: The final path, or None if no path is found.
#         """
#         raw_path = self.plan_path_astar(start, goal)
        
#         if not raw_path:
#             return None
            
#         if smooth:
#             return self._smooth_path_conceptual(raw_path)
#         else:
#             return raw_path

# # --- Helper function for visualization ---
# def visualize_path_on_grid(grid: np.ndarray, path: Optional[PathType] = None, start: Optional[GridLocation] = None, goal: Optional[GridLocation] = None):
#     """Prints a text-based visualization of the grid, obstacles, and path."""
#     # Create a copy to draw on
#     vis_grid = np.full(grid.shape, fill_value=".", dtype=str)
#     vis_grid[grid == 1] = "█" # Obstacles

#     if path:
#         for r, c in path:
#             vis_grid[r, c] = "*" # Path
            
#     if start:
#         vis_grid[start] = "S" # Start
    
#     if goal:
#         vis_grid[goal] = "G" # Goal
        
#     print("\n--- Path Visualization ---")
#     for row in vis_grid:
#         print(" ".join(row))
#     print("------------------------")
#     print("Legend: S=Start, G=Goal, █=Obstacle, *=Path")


# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Robotics Path Planner Prototype 🗺️ ===")
#     print("=========================================================")

#     # Create a 15x20 grid map with obstacles (1) and free space (0)
#     # Using NumPy for efficient array operations
#     grid_map = np.array([
#         [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
#         [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
#         [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
#         [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
#         [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
#         [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#         [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
#         [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#         [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#         [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#         [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
#         [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#         [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#         [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#         [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
#     ])
    
#     # Initialize the planner with the map
#     path_planner = PathPlanner(occupancy_grid=grid_map)
    
#     # --- Case 1: Find a valid path ---
#     print("\n--- Case 1: Finding a path from (0, 0) to (14, 19) ---")
#     start_pos = (0, 0)
#     goal_pos = (14, 19)
    
#     final_path = path_planner.find_path(start_pos, goal_pos, smooth=True)
    
#     visualize_path_on_grid(grid_map, final_path, start_pos, goal_pos)
#     if final_path:
#         print(f"\nSmoothed path found with {len(final_path)} waypoints.")
#         # print(f"Path waypoints: {final_path}")
    
#     # --- Case 2: No path available ---
#     print("\n--- Case 2: Trying to find a path to an unreachable goal (inside an obstacle) ---")
#     unreachable_goal = (7, 10)
    
#     no_path = path_planner.find_path(start_pos, unreachable_goal, smooth=True)
    
#     visualize_path_on_grid(grid_map, no_path, start_pos, unreachable_goal)
#     if not no_path:
#         print("\nAs expected, no path was found to the unreachable goal.")

#     print("\n=========================================================")
#     print("=== Path Planner Prototype Complete ===")
#     print("=========================================================")


# Devin/modules/robotics/path_planning.py
# Purpose: Provides advanced path planning, smoothing, and following for a robot
#          in a 2D environment. Implements A* and gradient-based smoothing.

import logging
import heapq
from collections import defaultdict
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass, field
import numpy as np

try:
    # This module now integrates with our robotics controller
    from modules.robotics_control_module import RoboticsControlModule
    DEVIN_CORE_AVAILABLE = True
except ImportError:
    DEVIN_CORE_AVAILABLE = False


# Configure basic logging
logger = logging.getLogger("PathPlanner")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

# Type hints
GridLocation = Tuple[int, int]
PathType = List[GridLocation]
Pose = Tuple[float, float, float] # (x, y, theta_degrees)

@dataclass(order=True)
class PriorityNode:
    priority: float
    item: Any=field(compare=False)

class PathPlanner:
    """Finds and smooths an optimal path on a 2D occupancy grid."""
    def __init__(self, occupancy_grid: np.ndarray):
        if not isinstance(occupancy_grid, np.ndarray) or occupancy_grid.ndim != 2:
            raise ValueError("occupancy_grid must be a 2D NumPy array.")
        self.grid = occupancy_grid
        self.height, self.width = occupancy_grid.shape
        logger.info(f"PathPlanner initialized with a {self.width}x{self.height} grid.")

    def _is_valid(self, loc: GridLocation) -> bool:
        """Checks if a location is within grid boundaries and is not an obstacle."""
        r, c = loc
        return (0 <= r < self.height and 0 <= c < self.width) and (self.grid[r, c] == 0)

    def _get_neighbors(self, loc: GridLocation) -> List[GridLocation]:
        """Gets valid, 8-directional neighbors."""
        r, c = loc
        possible_moves = [(r-1, c), (r+1, c), (r, c-1), (r, c+1), (r-1, c-1), (r-1, c+1), (r+1, c-1), (r+1, c+1)]
        return [move for move in possible_moves if self._is_valid(move)]

    def _heuristic(self, a: GridLocation, b: GridLocation) -> float:
        """Euclidean distance heuristic."""
        return np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

    def _reconstruct_path(self, came_from: Dict, current: GridLocation) -> PathType:
        """Traces the A* path backwards."""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return path[::-1]

    def _plan_path_astar(self, start: GridLocation, goal: GridLocation) -> Optional[PathType]:
        """The core A* search algorithm."""
        if not self._is_valid(start) or not self._is_valid(goal):
            logger.error("Start or goal location is invalid.")
            return None

        open_set = [PriorityNode(0, start)]
        came_from = {}
        g_score = defaultdict(lambda: float('inf'))
        g_score[start] = 0
        f_score = defaultdict(lambda: float('inf'))
        f_score[start] = self._heuristic(start, goal)

        while open_set:
            current = heapq.heappop(open_set).item
            if current == goal:
                return self._reconstruct_path(came_from, current)

            for neighbor in self._get_neighbors(current):
                move_cost = self._heuristic(current, neighbor)
                tentative_g_score = g_score[current] + move_cost
                if tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self._heuristic(neighbor, goal)
                    heapq.heappush(open_set, PriorityNode(f_score[neighbor], neighbor))
        return None

    def _smooth_path_gradient(self, path: PathType, alpha: float = 0.5, beta: float = 0.2, iterations: int = 100) -> PathType:
        """
        Smooths a path using gradient descent.
        - alpha: Weight for moving towards the average of neighbors (smoothness).
        - beta: Weight for moving away from the original path (maintaining shape).
        """
        smoothed_path = np.array(path, dtype=float)
        for _ in range(iterations):
            for i in range(1, len(path) - 1):
                # Gradient for smoothness (pulls point towards the midpoint of its neighbors)
                grad_smooth = (smoothed_path[i-1] + smoothed_path[i+1]) - 2 * smoothed_path[i]
                # Gradient for staying close to the original path
                grad_original = path[i] - smoothed_path[i]
                
                new_point = smoothed_path[i] + alpha * grad_smooth + beta * grad_original
                
                # Check for collisions. If the new point is invalid, don't update it.
                if self._is_valid(tuple(np.round(new_point).astype(int))):
                    smoothed_path[i] = new_point
        
        return [tuple(np.round(p).astype(int)) for p in smoothed_path]

    def find_path(self, start: GridLocation, goal: GridLocation, smooth: bool = True) -> Optional[PathType]:
        """Finds and optionally smooths a path."""
        raw_path = self._plan_path_astar(start, goal)
        if not raw_path: return None
        return self._smooth_path_gradient(raw_path) if smooth else raw_path

# --- Path Following Logic ---
class PathFollower:
    """Translates a path into a sequence of robot commands."""
    def __init__(self, robot_controller: RoboticsControlModule, planner: PathPlanner, map_resolution: float = 0.1):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError("RoboticsControlModule is required.")
        
        self.controller = robot_controller
        self.planner = planner
        self.map_resolution = map_resolution # meters per grid cell

    def world_to_grid(self, world_coord: Tuple[float, float]) -> GridLocation:
        """Converts real-world coordinates (meters) to grid coordinates."""
        return (int(world_coord[1] / self.map_resolution), int(world_coord[0] / self.map_resolution))

    def follow_path(self, start_pose: Pose, goal_pose: Pose):
        """Plans a path and generates a sequence of commands to follow it."""
        start_grid = self.world_to_grid((start_pose[0], start_pose[1]))
        goal_grid = self.world_to_grid((goal_pose[0], goal_pose[1]))
        
        path = self.planner.find_path(start_grid, goal_grid)
        if not path:
            logger.error("Could not find a path to follow.")
            return

        current_theta = start_pose[2]
        
        logger.warning("--- Beginning Path Following Sequence (Commands) ---")
        for i in range(len(path) - 1):
            current_point_grid = path[i]
            next_point_grid = path[i+1]
            
            # Calculate required angle and distance for the next move
            delta_y = (next_point_grid[0] - current_point_grid[0]) * self.map_resolution
            delta_x = (next_point_grid[1] - current_point_grid[1]) * self.map_resolution
            
            target_theta = np.degrees(np.arctan2(delta_y, delta_x))
            distance = np.sqrt(delta_x**2 + delta_y**2)
            
            # Calculate rotation needed
            rotation_needed = target_theta - current_theta
            
            # Normalize angle to -180 to 180
            if rotation_needed > 180: rotation_needed -= 360
            if rotation_needed < -180: rotation_needed += 360

            print(f"Step {i+1}: From {current_point_grid} to {next_point_grid}")
            if abs(rotation_needed) > 1.0: # Only rotate if significant
                print(f"  -> COMMAND: Rotate by {rotation_needed:.1f} degrees.")
                # self.controller.rotate_relative(delta_yaw=rotation_needed)
                # time.sleep(...) # Wait for rotation
                current_theta += rotation_needed
                
            print(f"  -> COMMAND: Move forward {distance:.2f} meters.")
            # self.controller.move_relative(dx=distance)
            # time.sleep(...) # Wait for movement
        logger.warning("--- Path Following Sequence Complete ---")


# --- Example Usage ---
if __name__ == "__main__":
    from modules.robotics_control_module import ROS2_RobotInterface
    
    print("=========================================================")
    print("=== Integrated Robotics Path Planner & Follower 🗺️🤖 ===")
    print("=========================================================")
    
    grid_map = np.array([
        [0, 0, 0, 1, 0, 0, 0],
        [0, 1, 0, 1, 0, 1, 0],
        [0, 1, 0, 0, 0, 1, 0],
        [0, 0, 0, 1, 1, 1, 0],
        [0, 1, 0, 0, 0, 0, 0],
        [0, 1, 0, 1, 0, 1, 0],
        [0, 0, 0, 1, 0, 0, 0],
    ])
    
    planner = PathPlanner(occupancy_grid=grid_map)
    start, goal = (0, 0), (6, 6)
    
    # --- 1. Find and visualize the raw A* path ---
    raw_path = planner.find_path(start, goal, smooth=False)
    print("\n--- 1. Raw A* Path ---")
    visualize_path_on_grid(grid_map, raw_path, start, goal)
    
    # --- 2. Find and visualize the smoothed path ---
    smoothed_path = planner.find_path(start, goal, smooth=True)
    print("\n--- 2. Smoothed Path (Gradient Descent) ---")
    visualize_path_on_grid(grid_map, smoothed_path, start, goal)
    
    # --- 3. Demonstrate the PathFollower ---
    print("\n\n--- 3. Demonstrating PathFollower Command Generation ---")
    if DEVIN_CORE_AVAILABLE:
        try:
            # We don't need a live connection for this demo, just the controller object
            # In a real run, this would connect to the ROS 2 server
            robot_controller = RoboticsControlModule(robot_interface=ROS2_RobotInterface())
            
            path_follower = PathFollower(robot_controller, planner, map_resolution=0.5) # 0.5 meters per grid cell
            
            start_pose: Pose = (0.25, 0.25, 0.0) # (x, y, theta) in meters and degrees
            goal_pose: Pose = (3.25, 3.25, 0.0)
            
            path_follower.follow_path(start_pose, goal_pose)
            
        except (ImportError, FileNotFoundError) as e:
            print(f"  [SKIPPED] PathFollower demo requires ROS 2 and its dependencies. Error: {e}")
    else:
        print("  [SKIPPED] PathFollower demo requires core modules.")

    print("\n=========================================================")
    print("=== Path Planner Prototype Complete ===")
    print("=========================================================")

def visualize_path_on_grid(grid, path, start, goal):
    vis = np.full(grid.shape, fill_value=".", dtype=str)
    vis[grid == 1] = "█"
    if path:
        for r, c in path:
            vis[r, c] = "*"
    if start: vis[start] = "S"
    if goal: vis[goal] = "G"
    for row in vis:
        print(" ".join(row))
        
