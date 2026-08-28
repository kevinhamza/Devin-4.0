// assets/scripts/script_dark_light.js
// Unified script for handling both dark mode and light mode functionality

document.addEventListener("DOMContentLoaded", () => {
    console.log("Dark and Light mode script loaded.");

    // Function to apply dark theme
    const applyDarkTheme = () => {
        document.body.classList.add("dark-theme");
        document.body.classList.remove("light-theme");
        document.querySelectorAll(".theme-toggle-element").forEach((element) => {
            element.style.backgroundColor = "#121212";
            element.style.color = "#ffffff";
        });
        console.log("Dark theme applied.");
    };

    // Function to apply light theme
    const applyLightTheme = () => {
        document.body.classList.add("light-theme");
        document.body.classList.remove("dark-theme");
        document.querySelectorAll(".theme-toggle-element").forEach((element) => {
            element.style.backgroundColor = "#ffffff";
            element.style.color = "#000000";
        });
        console.log("Light theme applied.");
    };

    // Function to toggle themes
    const toggleTheme = () => {
        if (document.body.classList.contains("dark-theme")) {
            applyLightTheme();
            localStorage.setItem("theme", "light");
        } else {
            applyDarkTheme();
            localStorage.setItem("theme", "dark");
        }
    };

    // Theme toggle button
    const themeToggleButton = document.getElementById("themeToggle");
    if (themeToggleButton) {
        themeToggleButton.addEventListener("click", toggleTheme);
    }

    // Apply saved theme on page load
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
        applyDarkTheme();
    } else {
        applyLightTheme();
    }

    // Dynamic element adjustment
    const adjustDynamicElements = () => {
        document.querySelectorAll(".dynamic-content").forEach((element) => {
            if (document.body.classList.contains("dark-theme")) {
                element.style.borderColor = "#444";
                element.style.boxShadow = "0 0 5px #333";
            } else {
                element.style.borderColor = "#ddd";
                element.style.boxShadow = "0 0 5px #aaa";
            }
        });
    };

    // Adjust elements dynamically on theme change
    document.body.addEventListener("classChange", adjustDynamicElements);

    console.log("Dark and Light mode script initialized.");
});
