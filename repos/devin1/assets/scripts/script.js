// assets/scripts/script.js
// Main script for handling frontend interactivity and functionality

document.addEventListener("DOMContentLoaded", () => {
    console.log("Script loaded successfully.");

    // Global variables
    const themeToggle = document.getElementById("themeToggle");
    const notificationBell = document.getElementById("notificationBell");
    const sidebarToggle = document.getElementById("sidebarToggle");

    // Theme toggle functionality
    if (themeToggle) {
        themeToggle.addEventListener("click", () => {
            document.body.classList.toggle("dark-theme");
            const currentTheme = document.body.classList.contains("dark-theme") ? "dark" : "light";
            localStorage.setItem("theme", currentTheme);
            console.log(`Theme switched to ${currentTheme}`);
        });

        // Set theme on load
        const savedTheme = localStorage.getItem("theme");
        if (savedTheme === "dark") {
            document.body.classList.add("dark-theme");
        }
    }

    // Notification bell handler
    if (notificationBell) {
        notificationBell.addEventListener("click", () => {
            alert("You have new notifications!");
            console.log("Notification bell clicked.");
        });
    }

    // Sidebar toggle functionality
    if (sidebarToggle) {
        sidebarToggle.addEventListener("click", () => {
            const sidebar = document.getElementById("sidebar");
            if (sidebar) {
                sidebar.classList.toggle("visible");
                console.log("Sidebar toggled.");
            }
        });
    }

    // Form validation
    const forms = document.querySelectorAll(".needs-validation");
    forms.forEach((form) => {
        form.addEventListener("submit", (event) => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                console.error("Form validation failed.");
            }
            form.classList.add("was-validated");
        });
    });

    // AJAX example (fetch API)
    async function fetchData(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log("Data fetched:", data);
            return data;
        } catch (error) {
            console.error("Error fetching data:", error);
        }
    }

    // Example usage
    fetchData("/api/example-endpoint");
});
