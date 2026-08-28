# Devin/monitoring/analytics_dashboard.py
# Purpose: A real-time, terminal-based analytics dashboard that visualizes
#          data from the CPU and Memory monitoring modules.

import logging
import curses
import time
import sys
from datetime import datetime

# --- Import other Devin modules ---
from monitoring.cpu_usage import CPU_Monitor, format_bytes
from monitoring.memory_tracker import MemoryTracker

# Configure basic logging to a file to not interfere with curses
# logging.basicConfig(filename='dashboard.log', level=logging.INFO)

def format_bytes_for_dashboard(byte_count: int) -> str:
    """A version of format_bytes that handles dashboard spacing."""
    if byte_count is None: return "N/A"
    power = 1024
    n = 0
    power_labels = {0: 'B', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while byte_count >= power and n < len(power_labels) -1:
        byte_count /= power
        n += 1
    return f"{byte_count:6.2f} {power_labels[n]}"

class AnalyticsDashboard:
    """
    Manages the curses-based TUI for system analytics.
    """
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.cpu_monitor = CPU_Monitor()
        self.memory_tracker = MemoryTracker()
        
        # Setup curses
        curses.curs_set(0) # Hide the cursor
        self.stdscr.nodelay(True) # Make getch non-blocking
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        
        self.run_dashboard()

    def _get_color_for_percent(self, percent: float):
        """Returns a color pair based on a percentage value."""
        if percent > 85.0:
            return curses.color_pair(3) | curses.A_BOLD # Red
        if percent > 60.0:
            return curses.color_pair(2) | curses.A_BOLD # Yellow
        return curses.color_pair(1) # Green

    def _draw_progress_bar(self, window, y, x, width, percent, label):
        """Draws a text-based progress bar."""
        filled_len = int(width * percent / 100)
        bar = '█' * filled_len + '-' * (width - filled_len)
        color = self._get_color_for_percent(percent)
        
        window.addstr(y, x, f"{label:<8} [{bar}] {percent:5.1f}%", color)

    def _draw_main_layout(self):
        """Draws the borders and titles for the dashboard."""
        h, w = self.stdscr.getmaxyx()
        self.stdscr.clear()
        
        # Title
        title = "DEVIN - SYSTEM ANALYTICS DASHBOARD (Press 'q' to quit)"
        self.stdscr.addstr(0, (w - len(title)) // 2, title, curses.A_REVERSE)
        
        # Draw boxes
        self.stdscr.box() # Outer box
        self.stdscr.vline(1, w // 2, '|', h - 2) # Vertical separator
        self.stdscr.hline(h // 2, 1, '-', w - 2) # Horizontal separator

        # Box titles
        self.stdscr.addstr(1, 3, "[ CPU Usage ]")
        self.stdscr.addstr(1, w // 2 + 3, "[ Memory Usage ]")
        self.stdscr.addstr(h // 2, 3, "[ Top Processes - CPU ]")
        self.stdscr.addstr(h // 2, w // 2 + 3, "[ Top Processes - Memory ]")

    def run_dashboard(self):
        """The main loop to fetch data and draw the dashboard."""
        
        while True:
            try:
                # Check for quit command
                if self.stdscr.getch() == ord('q'):
                    break
                
                h, w = self.stdscr.getmaxyx()
                self._draw_main_layout()
                
                # --- CPU Widget ---
                cpu_percent = self.cpu_monitor.get_system_cpu_usage(per_cpu=False)
                cpu_per_core = self.cpu_monitor.get_system_cpu_usage(per_cpu=True)
                bar_width = (w // 2) - 13
                self._draw_progress_bar(self.stdscr, 3, 2, bar_width, cpu_percent, "Total")
                for i, core_usage in enumerate(cpu_per_core):
                    if 5 + i < (h // 2 -1):
                        self._draw_progress_bar(self.stdscr, 5 + i, 2, bar_width, core_usage, f"Core {i}")

                # --- Memory Widget ---
                vmem = self.memory_tracker.get_virtual_memory_usage()
                swap = self.memory_tracker.get_swap_memory_usage()
                mem_bar_width = w - (w // 2) - 13
                self._draw_progress_bar(self.stdscr, 3, w // 2 + 2, mem_bar_width, vmem.percent, "RAM")
                self.stdscr.addstr(4, w//2 + 3, f"{format_bytes_for_dashboard(vmem.used)} / {format_bytes_for_dashboard(vmem.total)}")
                self._draw_progress_bar(self.stdscr, 6, w // 2 + 2, mem_bar_width, swap.percent, "Swap")
                self.stdscr.addstr(7, w//2 + 3, f"{format_bytes_for_dashboard(swap.used)} / {format_bytes_for_dashboard(swap.total)}")

                # --- Top Processes Widgets ---
                top_cpu = self.cpu_monitor.get_top_processes(count=h // 2 - 4)
                top_mem = self.memory_tracker.get_top_processes_by_memory(count=h // 2 - 4)
                
                # Draw CPU processes
                self.stdscr.addstr(h // 2 + 1, 2, f"{'PID':>5} {'%CPU':>5} {'Name'}", curses.A_UNDERLINE)
                for i, p in enumerate(top_cpu):
                     if h // 2 + 2 + i < h - 1:
                        self.stdscr.addstr(h // 2 + 2 + i, 2, f"{p['pid']:>5} {p['cpu_usage']:5.1f} {p['name']}")

                # Draw Memory processes
                self.stdscr.addstr(h // 2 + 1, w // 2 + 2, f"{'PID':>5} {'RSS':>10} {'Name'}", curses.A_UNDERLINE)
                for i, p in enumerate(top_mem):
                    if h // 2 + 2 + i < h - 1:
                        self.stdscr.addstr(h // 2 + 2 + i, w // 2 + 2, f"{p['pid']:>5} {format_bytes_for_dashboard(p['rss']):>10} {p['name']}")

                self.stdscr.refresh()
                time.sleep(2)

            except (KeyboardInterrupt, SystemExit):
                break
            except Exception as e:
                # Need to properly end curses mode on error
                raise e


# --- Main Entry Point ---
def main(stdscr):
    """Wrapper function to run the dashboard."""
    AnalyticsDashboard(stdscr)

if __name__ == "__main__":
    print("=========================================================")
    print("=== System Analytics Dashboard Prototype 📊🚀 ===")
    print("=========================================================")
    
    # Check for windows-curses if on Windows
    if sys.platform == "win32":
        try:
            import curses
        except ImportError:
            print("\nERROR: On Windows, the 'windows-curses' library is required.")
            print("Please run: pip install windows-curses")
            sys.exit(1)
    
    print("Initializing dashboard... (Your terminal will be cleared)")
    time.sleep(2)
    
    # curses.wrapper handles initialization and cleanup automatically
    curses.wrapper(main)
    
    print("Dashboard closed. Thank you for using Devin!")
