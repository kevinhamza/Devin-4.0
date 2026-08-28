// assets/scripts/script_light.js
// Dedicated script for handling light mode functionality

document.addEventListener("DOMContentLoaded", () => {
    console.log("Light mode script loaded.");

    // Function to apply light theme
    const applyLightTheme = () => {
        document.body.classList.add("light-theme");
        document.querySelectorAll(".light-mode-element").forEach((element) => {
            element.style.backgroundColor = "#ffffff";
            element.style.color = "#000000";
        });
        console.log("Light theme applied.");
    };

    // Function to remove light theme
    const removeLightTheme = () => {
        document.body.classList.remove("light-theme");
        document.querySelectorAll(".light-mode-element").forEach((element) => {
            element.style.backgroundColor = "";
            element.style.color = "";
        });
        console.log("Light theme removed.");
    };

    // Theme toggle button
    const themeToggleButton = document.getElementById("themeToggleLight");
    if (themeToggleButton) {
        themeToggleButton.addEventListener("click", () => {
            if (document.body.classList.contains("light-theme")) {
                removeLightTheme();
                localStorage.setItem("theme", "dark");
            } else {
                applyLightTheme();
                localStorage.setItem("theme", "light");
            }
        });
    }

    // Apply saved theme on page load
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "light") {
        applyLightTheme();
    }

    // Dynamic element adjustment
    const adjustDynamicElements = () => {
        document.querySelectorAll(".dynamic-content").forEach((element) => {
            if (document.body.classList.contains("light-theme")) {
                element.style.borderColor = "#ddd";
                element.style.boxShadow = "0 0 5px #aaa";
            } else {
                element.style.borderColor = "";
                element.style.boxShadow = "";
            }
        });
    };

    // Adjust elements dynamically on theme change
    document.body.addEventListener("classChange", adjustDynamicElements);

    console.log("Light mode script initialized.");
});
