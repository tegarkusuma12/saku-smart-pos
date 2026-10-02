// Konfigurasi otomatis environment
const URL_LOCAL = "http://127.0.0.1:8000";

// NANTI: Ganti URL di bawah ini dengan URL asli dari Render.com
const URL_PRODUCTION = "https://saku-smart-pos.onrender.com"; 

// Otomatis mengecek apakah dibuka dari localhost atau Vercel
const isLocal = window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost";
const API_BASE_URL = isLocal ? URL_LOCAL : URL_PRODUCTION;