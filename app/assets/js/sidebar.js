document.addEventListener("DOMContentLoaded", async function () {

    const sidebarContainer = document.getElementById("sidebar-container");

    if (!sidebarContainer) {
        return;
    }


    try {

        const response = await fetch(
            getSidebarPath()
        );

        if (!response.ok) {
            throw new Error("Sidebar gagal dimuat.");
        }

        const sidebarHTML = await response.text();

        sidebarContainer.innerHTML = sidebarHTML;


        // Set menu aktif
        setActiveSidebar();


    } catch (error) {

        console.error("Error loading sidebar:", error);

    }

});



function getSidebarPath() {

    const currentPath = window.location.pathname;


    // Jika halaman berada di /pages/
    if (currentPath.includes("/pages/")) {

        return "../components/sidebar.html";

    }


    // Jika halaman berada di root /app/
    return "components/sidebar.html";

}



function setActiveSidebar() {

    const currentPath = window.location.pathname;


    let activePage = "";


    if (currentPath.includes("1_kasir")) {

        activePage = "kasir";

    }

    else if (currentPath.includes("2_chatbot")) {

        activePage = "chatbot";

    }

    else if (currentPath.includes("3_dashboard")) {

        activePage = "dashboard";

    }

    else if (currentPath.includes("4_inventaris")) {

        activePage = "inventaris";

    }

    else if (currentPath.includes("5_akuntansi")) {

        activePage = "akuntansi";

    }


    const activeMenu = document.querySelector(
        `.saku-nav-link[data-page="${activePage}"]`
    );


    if (activeMenu) {

        activeMenu.classList.add("active");

    }

}