// Devin/assets/scripts/script_dark.js
// Handles theme switching (dark/light/system) and persistence.

document.addEventListener('DOMContentLoaded', function() {
    console.log("Theme Controller Initialized (script_dark.js).");

    // --- Configuration ---
    const themePreferenceKey = 'devinThemePreference'; // Key for localStorage
    const darkModeClass = 'dark-mode'; // CSS class to toggle on body/html
    const themeToggleButton = document.getElementById('theme-toggle-btn'); // ID of the toggle button
    const rootElement = document.documentElement; // Apply class to <html> for broader scope, or document.body

    // --- Core Theme Functions ---

    /**
     * Applies the specified theme by adding/removing the dark mode class
     * and saving the preference.
     * @param {('dark' | 'light' | 'system')} theme - The theme to apply ('system' resolves based on OS).
     */
    function applyTheme(theme) {
        let themeToApply = theme;

        if (theme === 'system') {
            // Check system preference if 'system' is chosen
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            themeToApply = prefersDark ? 'dark' : 'light';
            console.log(`System preference detected: ${themeToApply}`);
        }

        console.log(`Applying theme: ${themeToApply}`);
        if (themeToApply === 'dark') {
            rootElement.classList.add(darkModeClass);
            if(themeToggleButton) themeToggleButton.setAttribute('aria-pressed', 'true'); // Indicate button state
        } else {
            rootElement.classList.remove(darkModeClass);
             if(themeToggleButton) themeToggleButton.setAttribute('aria-pressed', 'false'); // Indicate button state
        }

        // Save the explicit user choice ('dark', 'light', or 'system')
        try {
            localStorage.setItem(themePreferenceKey, theme);
             console.log(`Saved theme preference to localStorage: ${theme}`);
        } catch (e) {
             console.error("Could not save theme preference to localStorage:", e);
        }
    }

    /**
     * Gets the current theme preference, checking localStorage first, then system preference.
     * @returns {'dark' | 'light' | 'system'} - The preferred theme setting.
     */
    function getStoredThemePreference() {
        let preference = 'system'; // Default to system preference
        try {
             const storedPref = localStorage.getItem(themePreferenceKey);
             if (storedPref && ['dark', 'light', 'system'].includes(storedPref)) {
                 preference = storedPref;
                 console.log(`Found stored theme preference: ${preference}`);
             } else {
                  console.log("No valid stored theme preference found, defaulting to 'system'.");
             }
        } catch (e) {
             console.error("Could not read theme preference from localStorage:", e);
        }
        return preference;
    }


    // --- Initialization ---

    // Apply the theme as soon as the page loads based on stored preference or system setting
    const initialTheme = getStoredThemePreference();
    applyTheme(initialTheme); // Apply 'dark', 'light', or resolve 'system'

    // Optional: Listen for system preference changes if user selected 'system'
    // This updates the theme automatically if the OS theme changes mid-session
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
        const currentPreference = getStoredThemePreference();
        if (currentPreference === 'system') {
            console.log("System color scheme changed, reapplying theme...");
            applyTheme('system'); // Re-evaluate and apply based on new system setting
        }
    });


    // --- Event Listener for Toggle Button ---

    if (themeToggleButton) {
        themeToggleButton.addEventListener('click', () => {
            console.log("Theme toggle button clicked.");
            // Determine the *next* theme state to cycle through (e.g., light -> dark -> system -> light)
            // Or simpler: just toggle between light/dark and ignore 'system' for toggle action
            const currentAppliedThemeIsDark = rootElement.classList.contains(darkModeClass);
            const nextTheme = currentAppliedThemeIsDark ? 'light' : 'dark'; // Simple light/dark toggle

            // More complex cycling including 'system' (optional):
            // const currentPreference = getStoredThemePreference();
            // let nextTheme;
            // if (currentPreference === 'light') nextTheme = 'dark';
            // else if (currentPreference === 'dark') nextTheme = 'system';
            // else nextTheme = 'light'; // Cycle system -> light

            applyTheme(nextTheme);
        });
         console.log("Attached click listener to theme toggle button.");
    } else {
        console.warn("Theme toggle button (#theme-toggle-btn) not found.");
    }

}); // End DOMContentLoaded
