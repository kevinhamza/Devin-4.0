"""
Path Planning Module
====================
Implements A*, RRT, and Dijkstra algorithms for robotic navigation and pathfinding.
"""

import heapq
import math
import random
from collections import deque

# Node class for graph representation
class Node:
    def __init__(self, x, y, cost=float('inf'), parent=None):
        """
        Represents a node in the search space.

        Args:
            x (int): X-coordinate.
            y (int): Y-coordinate.
            cost (float): Cost to reach this node.
            parent (Node): Parent node for path reconstruction.
        """
        self.x = x
        self.y = y
        self.cost = cost
        self.parent = parent

    def __lt__(self, other):
        return self.cost < other.cost

# A* Algorithm
class AStar:
    @staticmethod
    def heuristic(node, goal):
        """
        Calculates the heuristic for A* (Euclidean distance).

        Args:
            node (Node): Current node.
            goal (Node): Goal node.

        Returns:
            float: Heuristic cost.
        """
        return math.sqrt((node.x - goal.x)**2 + (node.y - goal.y)**2)

    @staticmethod
    def search(grid, start, goal):
        """
        Executes the A* algorithm.

        Args:
            grid (list): 2D list representing the grid (0 for free space, 1 for obstacles).
            start (Node): Start node.
            goal (Node): Goal node.

        Returns:
            list: Path from start to goal.
        """
        open_list = []
        heapq.heappush(open_list, start)
        closed_set = set()

        while open_list:
            current = heapq.heappop(open_list)
            if (current.x, current.y) == (goal.x, goal.y):
                return AStar.reconstruct_path(current)

            closed_set.add((current.x, current.y))
            neighbors = AStar.get_neighbors(grid, current)

            for neighbor in neighbors:
                if (neighbor.x, neighbor.y) in closed_set:
                    continue

                tentative_cost = current.cost + 1  # Assuming uniform cost for simplicity
                if tentative_cost < neighbor.cost:
                    neighbor.cost = tentative_cost
                    neighbor.parent = current
                    total_cost = tentative_cost + AStar.heuristic(neighbor, goal)
                    heapq.heappush(open_list, neighbor)

        return []

    @staticmethod
    def reconstruct_path(node):
        """
        Reconstructs the path from start to goal.

        Args:
            node (Node): Goal node.

        Returns:
            list: Path as a list of (x, y) tuples.
        """
        path = []
        while node:
            path.append((node.x, node.y))
            node = node.parent
        return path[::-1]

    @staticmethod
    def get_neighbors(grid, node):
        """
        Finds valid neighbors for a node.

        Args:
            grid (list): 2D grid representation.
            node (Node): Current node.

        Returns:
            list: Neighboring nodes.
        """
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        neighbors = []
        for dx, dy in directions:
            nx, ny = node.x + dx, node.y + dy
            if 0 <= nx < len(grid) and 0 <= ny < len(grid[0]) and grid[nx][ny] == 0:
                neighbors.append(Node(nx, ny))
        return neighbors

# Rapidly-Exploring Random Trees (RRT)
class RRT:
    @staticmethod
    def generate_path(start, goal, grid, max_iter=1000, step_size=5):
        """
        Generates a path using RRT.

        Args:
            start (Node): Start node.
            goal (Node): Goal node.
            grid (list): 2D grid representation.
            max_iter (int): Maximum iterations.
            step_size (int): Maximum distance between nodes.

        Returns:
            list: Path from start to goal.
        """
        nodes = [start]
        for _ in range(max_iter):
            rand_node = Node(random.randint(0, len(grid) - 1), random.randint(0, len(grid[0]) - 1))
            nearest_node = RRT.get_nearest_node(nodes, rand_node)
            new_node = RRT.steer(nearest_node, rand_node, step_size)

            if RRT.is_collision_free(nearest_node, new_node, grid):
                nodes.append(new_node)
                if RRT.is_goal_reached(new_node, goal):
                    return RRT.reconstruct_path(new_node)

        return []

    @staticmethod
    def get_nearest_node(nodes, random_node):
        return min(nodes, key=lambda node: math.sqrt((node.x - random_node.x)**2 + (node.y - random_node.y)**2))

    @staticmethod
    def steer(from_node, to_node, step_size):
        dx, dy = to_node.x - from_node.x, to_node.y - from_node.y
        distance = math.sqrt(dx**2 + dy**2)
        ratio = min(1, step_size / distance)
        return Node(from_node.x + int(dx * ratio), from_node.y + int(dy * ratio), parent=from_node)

    @staticmethod
    def is_collision_free(from_node, to_node, grid):
        return grid[to_node.x][to_node.y] == 0

    @staticmethod
    def is_goal_reached(node, goal):
        return math.sqrt((node.x - goal.x)**2 + (node.y - goal.y)**2) < 1

# Dijkstra's Algorithm
class Dijkstra:
    @staticmethod
    def search(grid, start, goal):
        """
        Executes Dijkstra's algorithm.

        Args:
            grid (list): 2D grid representation.
            start (Node): Start node.
            goal (Node): Goal node.

        Returns:
            list: Path from start to goal.
        """
        queue = []
        heapq.heappush(queue, start)
        visited = set()

        while queue:
            current = heapq.heappop(queue)
            if (current.x, current.y) == (goal.x, goal.y):
                return AStar.reconstruct_path(current)

            visited.add((current.x, current.y))
            neighbors = AStar.get_neighbors(grid, current)

            for neighbor in neighbors:
                if (neighbor.x, neighbor.y) in visited:
                    continue

                tentative_cost = current.cost + 1
                if tentative_cost < neighbor.cost:
                    neighbor.cost = tentative_cost
                    neighbor.parent = current
                    heapq.heappush(queue, neighbor)

        return []

# Example Usage
if __name__ == "__main__":
    grid = [
        [0, 0, 0, 1, 0],
        [0, 1, 0, 1, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0],
        [1, 1, 0, 0, 0]
    ]
    start = Node(0, 0, cost=0)
    goal = Node(4, 4)

    print("A* Path:", AStar.search(grid, start, goal))
    print("RRT Path:", RRT.generate_path(start, goal, grid))
    print("Dijkstra Path:", Dijkstra.search(grid, start, goal))
