# servers/__init__.py

# Import necessary modules
from .development import start_dev_server
from .production import start_prod_server
from .testing import start_test_server
from .dev_prod import start_dev_prod_server
from .dev_test import start_dev_test_server
from .prod_test import start_prod_test_server
from .dev_prod_test import start_dev_prod_test_server
from .dev_prod_test_all import start_dev_prod_test_all_server
from .docker_compose import start_multi_container_server
from .global_settings import load_global_settings
from .user_profiles import load_user_profiles
from .robotics_config import load_robotics_config
from .ai_config import load_ai_config
from .device_config import load_device_config
from .api_keys import load_api_keys
from .advanced_settings import load_advanced_settings
from .system_settings import load_system_settings
from .user_settings import load_user_settings
from .user_data import load_user_data
from .user_preferences import load_user_preferences
from .user_behavior import load_user_behavior
from .os_specific_linux import load_linux_config
from .os_specific_windows import load_windows_config
from .os_specific_macos import load_macos_config
from .os_specific_android import load_android_config
from .os_specific_other import load_other_os_config

# Initialize server modules
def init_servers():
    # Load settings and configurations
    load_global_settings()
    load_user_profiles()
    load_robotics_config()
    load_ai_config()
    load_device_config()
    load_api_keys()
    load_advanced_settings()
    load_system_settings()
    load_user_settings()
    load_user_data()
    load_user_preferences()
    load_user_behavior()
    load_linux_config()
    load_windows_config()
    load_macos_config()
    load_android_config()
    load_other_os_config()

    # Initialize each server module
    start_dev_server()
    start_prod_server()
    start_test_server()
    start_dev_prod_server()
    start_dev_test_server()
    start_prod_test_server()
    start_dev_prod_test_server()
    start_dev_prod_test_all_server()
    start_multi_container_server()

# Call the server initialization function
if __name__ == "__main__":
    init_servers()
