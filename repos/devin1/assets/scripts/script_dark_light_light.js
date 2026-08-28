// assets/scripts/script_dark_light_light.js
// Script for handling dark mode, light mode, and light-enhanced mode functionality

document.addEventListener("DOMContentLoaded", () => {
    console.log("Dark, Light, and Light-Enhanced mode script loaded.");

    // Function to apply dark theme
    const applyDarkTheme = () => {
        document.body.classList.add("dark-theme");
        document.body.classList.remove("light-theme", "light-enhanced-theme");
        document.querySelectorAll(".theme-toggle-element").forEach((element) => {
            element.style.backgroundColor = "#121212";
            element.style.color = "#ffffff";
        });
        console.log("Dark theme applied.");
    };

    // Function to apply light theme
    const applyLightTheme = () => {
        document.body.classList.add("light-theme");
        document.body.classList.remove("dark-theme", "light-enhanced-theme");
        document.querySelectorAll(".theme-toggle-element").forEach((element) => {
            element.style.backgroundColor = "#ffffff";
            element.style.color = "#000000";
        });
        console.log("Light theme applied.");
    };

    // Function to apply light-enhanced theme
    const applyLightEnhancedTheme = () => {
        document.body.classList.add("light-enhanced-theme");
        document.body.classList.remove("dark-theme", "light-theme");
        document.querySelectorAll(".theme-toggle-element").forEach((element) => {
            element.style.backgroundColor = "#f0f8ff";
            element.style.color = "#002244";
            element.style.border = "1px solid #88c0d0";
        });
        console.log("Light-enhanced theme applied.");
    };

    // Function to toggle between themes
    const toggleTheme = () => {
        if (document.body.classList.contains("dark-theme")) {
            applyLightTheme();
            localStorage.setItem("theme", "light");
        } else if (document.body.classList.contains("light-theme")) {
            applyLightEnhancedTheme();
            localStorage.setItem("theme", "light-enhanced");
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
    } else if (savedTheme === "light-enhanced") {
        applyLightEnhancedTheme();
    } else {
        applyLightTheme();
    }

    // Dynamic adjustments
    const adjustDynamicElements = () => {
        document.querySelectorAll(".dynamic-content").forEach((element) => {
            if (document.body.classList.contains("dark-theme")) {
                element.style.boxShadow = "0 0 5px #333";
            } else if (document.body.classList.contains("light-enhanced-theme")) {
                element.style.boxShadow = "0 0 10px #88c0d0";
            } else {
                element.style.boxShadow = "0 0 5px #aaa";
            }
        });
    };

    // Adjust elements dynamically on theme change
    document.body.addEventListener("classChange", adjustDynamicElements);

    console.log("Dark, Light, and Light-Enhanced mode script initialized.");
});
