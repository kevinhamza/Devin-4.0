"""
scripts/robot_manager_ui.py
===========================
This script provides a user interface for managing robots. It allows real-time monitoring,
control, and configuration of robots through an intuitive GUI.
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from modules.robotics.robot_manager import RobotManager
from modules.robotics.diagnostic_tools import run_diagnostics

class RobotManagerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Manager UI")
        self.manager = RobotManager()

        # Initialize UI elements
        self.create_widgets()

    def create_widgets(self):
        # Title Label
        title_label = ttk.Label(self.root, text="Robot Manager", font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # Robot Selection Dropdown
        ttk.Label(self.root, text="Select Robot:").grid(row=1, column=0, padx=10, sticky="w")
        self.robot_selector = ttk.Combobox(self.root, values=self.get_robot_list(), state="readonly")
        self.robot_selector.grid(row=1, column=1, padx=10, sticky="w")
        self.robot_selector.bind("<<ComboboxSelected>>", self.update_robot_status)

        # Status Display
        ttk.Label(self.root, text="Status:").grid(row=2, column=0, padx=10, sticky="w")
        self.status_label = ttk.Label(self.root, text="No robot selected", font=("Arial", 12))
        self.status_label.grid(row=2, column=1, columnspan=2, sticky="w")

        # Control Buttons
        self.start_button = ttk.Button(self.root, text="Start", command=self.start_robot)
        self.start_button.grid(row=3, column=0, padx=10, pady=10)

        self.stop_button = ttk.Button(self.root, text="Stop", command=self.stop_robot)
        self.stop_button.grid(row=3, column=1, padx=10, pady=10)

        self.diagnostics_button = ttk.Button(self.root, text="Run Diagnostics", command=self.run_robot_diagnostics)
        self.diagnostics_button.grid(row=3, column=2, padx=10, pady=10)

    def get_robot_list(self):
        """Fetches the list of available robots."""
        return self.manager.list_robots()

    def update_robot_status(self, event):
        """Updates the status display when a robot is selected."""
        selected_robot = self.robot_selector.get()
        status = self.manager.get_robot_status(selected_robot)
        self.status_label.config(text=status)

    def start_robot(self):
        """Starts the selected robot."""
        selected_robot = self.robot_selector.get()
        if not selected_robot:
            messagebox.showwarning("Warning", "Please select a robot!")
            return
        success = self.manager.start_robot(selected_robot)
        messagebox.showinfo("Info", f"Robot {selected_robot} started successfully!" if success else f"Failed to start {selected_robot}.")
        self.update_robot_status(None)

    def stop_robot(self):
        """Stops the selected robot."""
        selected_robot = self.robot_selector.get()
        if not selected_robot:
            messagebox.showwarning("Warning", "Please select a robot!")
            return
        success = self.manager.stop_robot(selected_robot)
        messagebox.showinfo("Info", f"Robot {selected_robot} stopped successfully!" if success else f"Failed to stop {selected_robot}.")
        self.update_robot_status(None)

    def run_robot_diagnostics(self):
        """Runs diagnostics on the selected robot."""
        selected_robot = self.robot_selector.get()
        if not selected_robot:
            messagebox.showwarning("Warning", "Please select a robot!")
            return
        result = run_diagnostics(selected_robot)
        messagebox.showinfo("Diagnostics Result", result)

if __name__ == "__main__":
    root = tk.Tk()
    app = RobotManagerUI(root)
    root.mainloop()
