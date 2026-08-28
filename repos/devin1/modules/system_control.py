import os
import subprocess
import platform
import psutil
import shutil
import ctypes

class SystemControl:
    """
    A class to handle system control tasks, including file management, process handling, 
    and system settings management.
    """

    @staticmethod
    def get_system_info():
        """
        Retrieves system information such as OS, architecture, and memory usage.
        """
        info = {
            "OS": platform.system(),
            "OS Version": platform.version(),
            "Architecture": platform.architecture()[0],
            "Processor": platform.processor(),
            "Total Memory": f"{psutil.virtual_memory().total // (1024 ** 3)} GB",
            "Available Memory": f"{psutil.virtual_memory().available // (1024 ** 3)} GB",
            "CPU Cores": psutil.cpu_count(logical=True),
        }
        return info

    @staticmethod
    def list_files_and_directories(path="."):
        """
        Lists all files and directories at a given path.
        """
        try:
            return os.listdir(path)
        except Exception as e:
            return str(e)

    @staticmethod
    def create_directory(path):
        """
        Creates a new directory at the specified path.
        """
        try:
            os.makedirs(path, exist_ok=True)
            return f"Directory created: {path}"
        except Exception as e:
            return str(e)

    @staticmethod
    def delete_file_or_directory(path):
        """
        Deletes a file or directory.
        """
        try:
            if os.path.isfile(path):
                os.remove(path)
                return f"File deleted: {path}"
            elif os.path.isdir(path):
                shutil.rmtree(path)
                return f"Directory deleted: {path}"
            else:
                return f"No such file or directory: {path}"
        except Exception as e:
            return str(e)

    @staticmethod
    def move_file(source, destination):
        """
        Moves a file or directory to a new location.
        """
        try:
            shutil.move(source, destination)
            return f"Moved {source} to {destination}"
        except Exception as e:
            return str(e)

    @staticmethod
    def execute_command(command):
        """
        Executes a system command and returns its output.
        """
        try:
            result = subprocess.run(command, shell=True, text=True, capture_output=True)
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return str(e)

    @staticmethod
    def kill_process(pid):
        """
        Kills a process by its process ID.
        """
        try:
            psutil.Process(pid).terminate()
            return f"Process {pid} terminated successfully."
        except Exception as e:
            return str(e)

    @staticmethod
    def restart_system():
        """
        Restarts the system.
        """
        try:
            if platform.system() == "Windows":
                os.system("shutdown /r /t 0")
            else:
                os.system("sudo reboot")
            return "System is restarting..."
        except Exception as e:
            return str(e)

    @staticmethod
    def shutdown_system():
        """
        Shuts down the system.
        """
        try:
            if platform.system() == "Windows":
                os.system("shutdown /s /t 0")
            else:
                os.system("sudo shutdown now")
            return "System is shutting down..."
        except Exception as e:
            return str(e)

    @staticmethod
    def lock_screen():
        """
        Locks the system screen.
        """
        try:
            if platform.system() == "Windows":
                ctypes.windll.user32.LockWorkStation()
            elif platform.system() == "Linux":
                os.system("gnome-screensaver-command -l")
            elif platform.system() == "Darwin":
                os.system("/System/Library/CoreServices/Menu\\ Extras/User.menu/Contents/Resources/CGSession -suspend")
            return "Screen locked."
        except Exception as e:
            return str(e)

    @staticmethod
    def monitor_cpu_usage():
        """
        Monitors and retrieves current CPU usage.
        """
        try:
            return f"CPU Usage: {psutil.cpu_percent(interval=1)}%"
        except Exception as e:
            return str(e)

    @staticmethod
    def monitor_memory_usage():
        """
        Monitors and retrieves current memory usage.
        """
        try:
            memory = psutil.virtual_memory()
            return f"Used Memory: {memory.used // (1024 ** 3)} GB / Total Memory: {memory.total // (1024 ** 3)} GB"
        except Exception as e:
            return str(e)

    @staticmethod
    def manage_power_settings(option):
        """
        Manages power settings like sleep or hibernate.
        """
        try:
            if platform.system() == "Windows":
                if option.lower() == "sleep":
                    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                elif option.lower() == "hibernate":
                    os.system("shutdown /h")
            elif platform.system() == "Linux":
                if option.lower() == "sleep":
                    os.system("systemctl suspend")
                elif option.lower() == "hibernate":
                    os.system("systemctl hibernate")
            elif platform.system() == "Darwin":
                if option.lower() == "sleep":
                    os.system("pmset sleepnow")
            return f"System set to {option.lower()} mode."
        except Exception as e:
            return str(e)

if __name__ == "__main__":
    # Example usage
    control = SystemControl()
    print("System Info:", control.get_system_info())
    print("Files in current directory:", control.list_files_and_directories())
    print(control.create_directory("test_dir"))
    print(control.delete_file_or_directory("test_dir"))
    print(control.execute_command("echo Hello, Devin!"))
