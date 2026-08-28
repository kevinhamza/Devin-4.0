// assets/scripts/script_dark.js
// Dedicated script for handling dark mode functionality

document.addEventListener("DOMContentLoaded", () => {
    console.log("Dark mode script loaded.");

    // Function to apply dark theme
    const applyDarkTheme = () => {
        document.body.classList.add("dark-theme");
        document.querySelectorAll(".dark-mode-element").forEach((element) => {
            element.style.backgroundColor = "#1e1e2f";
            element.style.color = "#ffffff";
        });
        console.log("Dark theme applied.");
    };

    // Function to remove dark theme
    const removeDarkTheme = () => {
        document.body.classList.remove("dark-theme");
        document.querySelectorAll(".dark-mode-element").forEach((element) => {
            element.style.backgroundColor = "";
            element.style.color = "";
        });
        console.log("Dark theme removed.");
    };

    // Theme toggle button
    const themeToggleButton = document.getElementById("themeToggleDark");
    if (themeToggleButton) {
        themeToggleButton.addEventListener("click", () => {
            if (document.body.classList.contains("dark-theme")) {
                removeDarkTheme();
                localStorage.setItem("theme", "light");
            } else {
                applyDarkTheme();
                localStorage.setItem("theme", "dark");
            }
        });
    }

    // Apply saved theme on page load
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
        applyDarkTheme();
    }

    // Dynamic element adjustment
    const adjustDynamicElements = () => {
        document.querySelectorAll(".dynamic-content").forEach((element) => {
            if (document.body.classList.contains("dark-theme")) {
                element.style.borderColor = "#444";
                element.style.boxShadow = "0 0 5px #222";
            } else {
                element.style.borderColor = "";
                element.style.boxShadow = "";
            }
        });
    };

    // Adjust elements dynamically on theme change
    document.body.addEventListener("classChange", adjustDynamicElements);

    console.log("Dark mode script initialized.");
});
