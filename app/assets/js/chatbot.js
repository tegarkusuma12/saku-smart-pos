document.addEventListener("DOMContentLoaded", function () {

    const input = document.getElementById("chatInput");

    const button = document.getElementById("sendChat");


    if (!input || !button) {
        return;
    }


    button.addEventListener(
        "click",
        sendMessage
    );


    input.addEventListener(
        "keydown",
        function (event) {

            if (event.key === "Enter") {

                sendMessage();

            }

        }
    );

});


function sendMessage() {

    const input =
        document.getElementById("chatInput");

    const message =
        input.value.trim();


    if (!message) {
        return;
    }


    addMessage(
        message,
        "user"
    );


    input.value = "";


    setTimeout(function () {

        const response =
            generateResponse(message);


        addMessage(
            response,
            "bot"
        );

    }, 500);

}


function addMessage(message, sender) {

    const container =
        document.getElementById("chatMessages");


    const wrapper =
        document.createElement("div");


    wrapper.className =
        `chat-message ${sender}`;


    wrapper.innerHTML = `

        <div class="chat-bubble">

            ${message}

        </div>

    `;


    container.appendChild(wrapper);


    container.scrollTop =
        container.scrollHeight;

}


function generateResponse(message) {

    const text =
        message.toLowerCase();


    if (text.includes("penjualan")) {

        return `
            Total penjualan bulan ini
            mencapai <strong>Rp12.500.000</strong>.
            Jumlah transaksi sebanyak
            <strong>184 transaksi</strong>.
        `;

    }


    if (
        text.includes("stok") ||
        text.includes("inventaris")
    ) {

        return `
            Saat ini ada
            <strong>3 produk</strong>
            dengan stok menipis dan
            <strong>1 produk</strong>
            yang sudah habis.
        `;

    }


    if (
        text.includes("laba") ||
        text.includes("profit")
    ) {

        return `
            Laba bulan ini sekitar
            <strong>Rp5.150.000</strong>
            berdasarkan data transaksi saat ini.
        `;

    }


    return `
        Saya belum memahami pertanyaan tersebut.
        Coba tanyakan tentang
        <strong>penjualan</strong>,
        <strong>stok</strong>, atau
        <strong>laba</strong>.
    `;

}