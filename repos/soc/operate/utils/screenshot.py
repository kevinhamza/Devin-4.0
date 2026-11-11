import os
import platform
import subprocess
import glob
import time
from PIL import Image


def capture_screen_with_cursor(file_path):
    user_platform = platform.system()

    if user_platform == "Windows":
        import pyautogui
        screenshot = pyautogui.screenshot()
        screenshot.save(file_path)
    elif user_platform == "Linux":
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        if "wayland" in session_type:
            # GNOME Wayland: use gdbus XDG Portal screenshot
            _capture_wayland_gdbus(file_path)
        else:
            # X11: use scrot
            result = subprocess.run(["scrot", file_path], capture_output=True)
            if result.returncode != 0:
                subprocess.run(["import", "-window", "root", file_path])
    elif user_platform == "Darwin":  # (Mac OS)
        subprocess.run(["screencapture", "-C", file_path])
    else:
        print(f"The platform you're using ({user_platform}) is not currently supported")


def _capture_wayland_gdbus(dest_path):
    """Capture screenshot on GNOME Wayland via gdbus XDG Portal, then copy to dest_path."""
    pictures_dir = os.path.expanduser("~/Pictures")
    before = set(glob.glob(os.path.join(pictures_dir, "Screenshot*.png")))

    subprocess.Popen([
        "gdbus", "call", "--session",
        "--dest", "org.gnome.Shell.Screenshot",
        "--object-path", "/org/gnome/Shell/Screenshot",
        "--method", "org.gnome.Shell.Screenshot.Screenshot",
        "true", "false",
        os.path.join(pictures_dir, "screenshot_tmp.png")
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Wait up to 6s for new file
    new_file = None
    for _ in range(60):
        time.sleep(0.1)
        after = set(glob.glob(os.path.join(pictures_dir, "Screenshot*.png")))
        diff = after - before
        if diff:
            new_file = max(diff, key=os.path.getmtime)
            break

    if new_file and os.path.exists(new_file):
        import shutil
        shutil.copy2(new_file, dest_path)
    else:
        raise RuntimeError("gdbus screenshot timed out — no new file appeared in ~/Pictures")


def compress_screenshot(raw_screenshot_filename, screenshot_filename):
    with Image.open(raw_screenshot_filename) as img:
        # Check if the image has an alpha channel (transparency)
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            # Create a white background image
            background = Image.new('RGB', img.size, (255, 255, 255))
            # Paste the image onto the background, using the alpha channel as mask
            background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
            # Save the result as JPEG
            background.save(screenshot_filename, 'JPEG', quality=85)  # Adjust quality as needed
        else:
            # If no alpha channel, simply convert and save
            img.convert('RGB').save(screenshot_filename, 'JPEG', quality=85)
