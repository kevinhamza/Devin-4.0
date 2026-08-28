import os


class StyleManager:
    """
    A utility class for managing UI styles and themes in the application.
    Provides functions for dynamic style generation and application.
    """

    def __init__(self):
        self.default_theme = {
            "background_color": "#1E1E1E",
            "text_color": "#FFFFFF",
            "highlight_color": "#007ACC",
            "error_color": "#FF5555",
            "success_color": "#22C55E",
            "font_family": "Arial",
            "font_size": 14,
        }

    def apply_theme(self, component, theme=None):
        """
        Apply a style theme to a UI component.
        :param component: UI component object.
        :param theme: Dictionary defining the theme.
        """
        try:
            theme = theme or self.default_theme
            component.configure(bg=theme["background_color"], fg=theme["text_color"])
            print(f"Applied theme: {theme}")
        except AttributeError as e:
            print(f"Error: Invalid component passed. {e}")
        except Exception as e:
            print(f"An error occurred while applying theme: {e}")

    def generate_css_file(self, theme=None, file_path="assets/style/theme.css"):
        """
        Generate a CSS file for the specified theme.
        :param theme: Dictionary defining the theme.
        :param file_path: Path where the CSS file will be saved.
        """
        try:
            theme = theme or self.default_theme
            css_content = f"""
            body {{
                background-color: {theme['background_color']};
                color: {theme['text_color']};
                font-family: {theme['font_family']};
                font-size: {theme['font_size']}px;
            }}
            .highlight {{
                color: {theme['highlight_color']};
            }}
            .error {{
                color: {theme['error_color']};
            }}
            .success {{
                color: {theme['success_color']};
            }}
            """
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as css_file:
                css_file.write(css_content)
            print(f"CSS file generated at: {file_path}")
        except Exception as e:
            print(f"An error occurred while generating CSS file: {e}")

    def get_color_scheme(self, dark_mode=True):
        """
        Retrieve a color scheme based on the mode.
        :param dark_mode: Boolean indicating dark or light mode.
        :return: Dictionary defining the color scheme.
        """
        try:
            if dark_mode:
                scheme = {
                    "background_color": "#1E1E1E",
                    "text_color": "#FFFFFF",
                    "highlight_color": "#007ACC",
                }
            else:
                scheme = {
                    "background_color": "#FFFFFF",
                    "text_color": "#000000",
                    "highlight_color": "#005BBB",
                }
            print(f"Color scheme: {scheme}")
            return scheme
        except Exception as e:
            print(f"An error occurred while retrieving color scheme: {e}")

    def load_custom_theme(self, file_path="config/custom_theme.json"):
        """
        Load a custom theme from a JSON file.
        :param file_path: Path to the JSON file.
        :return: Dictionary containing the theme.
        """
        try:
            import json

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Theme file not found: {file_path}")

            with open(file_path, "r") as theme_file:
                theme = json.load(theme_file)
            print(f"Loaded custom theme from {file_path}")
            return theme
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
        except Exception as e:
            print(f"An error occurred while loading custom theme: {e}")


if __name__ == "__main__":
    style_manager = StyleManager()

    # Example: Generate a CSS file
    style_manager.generate_css_file()

    # Example: Retrieve color scheme for light mode
    light_scheme = style_manager.get_color_scheme(dark_mode=False)

    # Example: Apply theme to a UI component
    mock_component = type("MockComponent", (), {"configure": lambda self, bg, fg: print(f"Set bg: {bg}, fg: {fg}")})()
    style_manager.apply_theme(mock_component, light_scheme)
