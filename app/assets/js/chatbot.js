// ============================================================
// SAKUBOT CHATBOT
// ============================================================

const API_BASE_URL = "http://127.0.0.1:8000";


// ============================================================
// CHAT STATE
// ============================================================

let chatHistory = [];

let totalMessages = 1;

let userMessages = 0;

let botMessages = 1;


// ============================================================
// DOM READY
// ============================================================

document.addEventListener("DOMContentLoaded", function () {

    const input =
        document.getElementById("chatInput");

    const button =
        document.getElementById("sendChat");


    if (!input || !button) {
        return;
    }


    // ==========================================
    // SEND BUTTON
    // ==========================================

    button.addEventListener(
        "click",
        sendMessage
    );


    // ==========================================
    // ENTER KEY
    // ==========================================

    input.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                sendMessage();

            }

        }
    );


    // ==========================================
    // RESET CHAT
    // ==========================================

    const resetButton =
        document.getElementById("resetChat");


    if (resetButton) {

        resetButton.addEventListener(
            "click",
            resetChat
        );

    }


    // ==========================================
    // EXPORT CHAT
    // ==========================================

    const exportButton =
        document.getElementById("exportChat");


    if (exportButton) {

        exportButton.addEventListener(
            "click",
            exportChat
        );

    }


    // ==========================================
    // EXAMPLE TOGGLE
    // ==========================================

    const exampleToggle =
        document.getElementById("exampleToggle");


    if (exampleToggle) {

        exampleToggle.addEventListener(
            "click",
            toggleExamples
        );

    }


    // ==========================================
    // EXAMPLE QUESTIONS
    // ==========================================

    const exampleButtons =
        document.querySelectorAll(
            ".example-question"
        );


    exampleButtons.forEach(function (button) {

        button.addEventListener(
            "click",
            function () {

                const message =
                    button.dataset.message;


                input.value =
                    message;


                input.focus();

            }
        );

    });


    // ==========================================
    // INITIAL STATISTICS
    // ==========================================

    updateStatistics();

});


// ============================================================
// SEND MESSAGE
// ============================================================

async function sendMessage() {

    const input =
        document.getElementById("chatInput");

    const button =
        document.getElementById("sendChat");


    if (!input || !button) {
        return;
    }


    const message =
        input.value.trim();


    // Jangan kirim pesan kosong
    if (!message) {
        return;
    }


    // ==========================================
    // TAMPILKAN PESAN USER
    // ==========================================

    addMessage(
        message,
        "user"
    );


    // ==========================================
    // UPDATE HISTORY
    // ==========================================

    chatHistory.push({
        role: "user",
        content: message
    });


    userMessages++;

    totalMessages++;


    updateStatistics();


    // ==========================================
    // CLEAR INPUT
    // ==========================================

    input.value = "";


    input.focus();


    // ==========================================
    // DISABLE INPUT
    // ==========================================

    input.disabled = true;

    button.disabled = true;


    // ==========================================
    // LOADING
    // ==========================================

    const loadingId =
        addLoadingMessage();


    try {

        // ======================================
        // REQUEST KE FASTAPI
        // ======================================

        const response =
            await fetch(
                `${API_BASE_URL}/api/chat`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        message: message,

                        chat_history:
                            chatHistory.slice(0, -1)
                    })
                }
            );


        // ======================================
        // HTTP ERROR
        // ======================================

        if (!response.ok) {

            throw new Error(
                `Server error (${response.status})`
            );

        }


        const data =
            await response.json();


        // ======================================
        // REMOVE LOADING
        // ======================================

        removeLoadingMessage(
            loadingId
        );


        // ======================================
        // AMBIL RESPONSE
        // ======================================

        const botResponse =
            data.response ||
            "Maaf, SakuBot tidak memberikan respons.";


        // ======================================
        // TAMPILKAN RESPONSE
        // ======================================

        addMessage(
            botResponse,
            "bot"
        );


        // ======================================
        // SIMPAN RESPONSE
        // ======================================

        chatHistory.push({
            role: "assistant",
            content: botResponse
        });


        botMessages++;

        totalMessages++;


        updateStatistics();


    } catch (error) {

        // ======================================
        // REMOVE LOADING
        // ======================================

        removeLoadingMessage(
            loadingId
        );


        console.error(
            "SakuBot error:",
            error
        );


        // ======================================
        // ERROR MESSAGE
        // ======================================

        const errorMessage =
            `
            ⚠️ Maaf, SakuBot sedang mengalami
            masalah saat menghubungi server.

            <br><br>

            Pastikan FastAPI sedang berjalan
            di <strong>http://127.0.0.1:8000</strong>.
            `;


        addMessage(
            errorMessage,
            "bot",
            true
        );


        botMessages++;

        totalMessages++;


        updateStatistics();

    } finally {

        // ======================================
        // ENABLE INPUT
        // ======================================

        input.disabled = false;

        button.disabled = false;

        input.focus();

    }

}


// ============================================================
// ADD MESSAGE
// ============================================================

function addMessage(
    message,
    sender,
    allowHTML = false
) {

    const container =
        document.getElementById("chatMessages");


    if (!container) {
        return;
    }


    const wrapper =
        document.createElement("div");


    wrapper.className =
        `chat-message ${sender}`;


    // ==========================================
    // BOT AVATAR
    // ==========================================

    let avatar = "";


    if (sender === "bot") {

        avatar = `
            <div class="chat-avatar">
                <i class="fa-solid fa-robot"></i>
            </div>
        `;

    }


    // ==========================================
    // BUBBLE
    // ==========================================

    const bubble =
        document.createElement("div");


    bubble.className =
        "chat-bubble";


    if (allowHTML) {

        bubble.innerHTML =
            message;

    } else {

        bubble.innerHTML =
            formatMessage(message);

    }


    wrapper.innerHTML =
        avatar;


    wrapper.appendChild(
        bubble
    );


    container.appendChild(
        wrapper
    );


    // ==========================================
    // SCROLL
    // ==========================================

    scrollToBottom();

}


// ============================================================
// FORMAT MESSAGE
// ============================================================

// ============================================================
// FORMAT MESSAGE
// ============================================================

function formatMessage(message) {

    if (!message) {
        return "";
    }


    let text = String(message);


    // ========================================================
    // NORMALISASI LINE BREAK
    // ========================================================

    text = text.replace(/\r\n/g, "\n");


    // ========================================================
    // ESCAPE HTML
    // ========================================================

    text = escapeHTML(text);


    // ========================================================
    // CODE BLOCK
    // ========================================================

    const codeBlocks = [];

    text = text.replace(
        /```(?:\w+)?\n?([\s\S]*?)```/g,
        function (_, code) {

            const index =
                codeBlocks.length;

            codeBlocks.push(code.trim());

            return `@@CODEBLOCK_${index}@@`;

        }
    );


    // ========================================================
    // MARKDOWN TABLE
    // ========================================================

    text = parseMarkdownTables(text);


    // ========================================================
    // HEADINGS
    // ========================================================

    text = text.replace(
        /^### (.+)$/gm,
        "<h6>$1</h6>"
    );

    text = text.replace(
        /^## (.+)$/gm,
        "<h5>$1</h5>"
    );

    text = text.replace(
        /^# (.+)$/gm,
        "<h4>$1</h4>"
    );


    // ========================================================
    // BOLD
    // ========================================================

    text = text.replace(
        /\*\*(.*?)\*\*/g,
        "<strong>$1</strong>"
    );


    // ========================================================
    // ITALIC
    // ========================================================

    text = text.replace(
        /(?<!\*)\*([^*\n]+)\*(?!\*)/g,
        "<em>$1</em>"
    );


    // ========================================================
    // INLINE CODE
    // ========================================================

    text = text.replace(
        /`([^`\n]+)`/g,
        "<code>$1</code>"
    );


    // ========================================================
    // NUMBERED LIST
    // ========================================================

    text = parseNumberedLists(text);


    // ========================================================
    // BULLET LIST
    // ========================================================

    text = parseBulletLists(text);


    // ========================================================
    // HORIZONTAL LINE
    // ========================================================

    text = text.replace(
        /^---+$/gm,
        "<hr>"
    );


    // ========================================================
    // LINE BREAK
    // ========================================================

    text = text.replace(
        /\n/g,
        "<br>"
    );


    // ========================================================
    // RESTORE CODE BLOCK
    // ========================================================

    codeBlocks.forEach(
        function (code, index) {

            const placeholder =
                `@@CODEBLOCK_${index}@@`;

            const html = `
                <pre class="chat-code-block"><code>${code}</code></pre>
            `;

            text = text.replace(
                placeholder,
                html
            );

        }
    );


    return text;

}


// ============================================================
// MARKDOWN TABLE
// ============================================================

function parseMarkdownTables(text) {

    const lines =
        text.split("\n");

    const result = [];

    let i = 0;


    while (i < lines.length) {

        const current =
            lines[i].trim();


        const next =
            lines[i + 1]
                ?.trim();


        // ====================================================
        // CEK APAKAH INI TABLE
        // ====================================================

        const isTable =
            current.includes("|") &&
            next &&
            /^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?$/.test(
                next
            );


        if (!isTable) {

            result.push(lines[i]);

            i++;

            continue;

        }


        // ====================================================
        // HEADER
        // ====================================================

        const headers =
            parseTableRow(current);


        i += 2;


        // ====================================================
        // DATA ROWS
        // ====================================================

        const rows = [];


        while (i < lines.length) {

            const line =
                lines[i].trim();


            if (
                !line ||
                !line.includes("|")
            ) {
                break;
            }


            rows.push(
                parseTableRow(line)
            );


            i++;

        }


        // ====================================================
        // BUILD TABLE
        // ====================================================

        let tableHTML = `
            <div class="chat-table-wrapper">
                <table class="chat-table">
                    <thead>
                        <tr>
        `;


        headers.forEach(
            function (header) {

                tableHTML += `
                    <th>${header}</th>
                `;

            }
        );


        tableHTML += `
                        </tr>
                    </thead>

                    <tbody>
        `;


        rows.forEach(
            function (row) {

                tableHTML += "<tr>";


                headers.forEach(
                    function (_, index) {

                        tableHTML += `
                            <td>
                                ${row[index] || ""}
                            </td>
                        `;

                    }
                );


                tableHTML += "</tr>";

            }
        );


        tableHTML += `
                    </tbody>
                </table>
            </div>
        `;


        result.push(
            tableHTML
        );

    }


    return result.join("\n");

}


// ============================================================
// PARSE TABLE ROW
// ============================================================

function parseTableRow(row) {

    let value =
        row.trim();


    // Hilangkan | di awal
    if (value.startsWith("|")) {
        value = value.substring(1);
    }


    // Hilangkan | di akhir
    if (value.endsWith("|")) {
        value = value.substring(
            0,
            value.length - 1
        );
    }


    return value
        .split("|")
        .map(
            cell => cell.trim()
        );

}


// ============================================================
// NUMBERED LIST
// ============================================================

function parseNumberedLists(text) {

    const lines =
        text.split("\n");

    const result = [];

    let inList = false;


    lines.forEach(
        function (line) {

            const match =
                line.match(
                    /^\s*\d+\.\s+(.+)$/
                );


            if (match) {

                if (!inList) {

                    result.push(
                        '<ol class="chat-list">'
                    );

                    inList = true;

                }


                result.push(
                    `<li>${match[1]}</li>`
                );


            } else {

                if (inList) {

                    result.push("</ol>");

                    inList = false;

                }


                result.push(line);

            }

        }
    );


    if (inList) {

        result.push("</ol>");

    }


    return result.join("\n");

}


// ============================================================
// BULLET LIST
// ============================================================

function parseBulletLists(text) {

    const lines =
        text.split("\n");

    const result = [];

    let inList = false;


    lines.forEach(
        function (line) {

            const match =
                line.match(
                    /^\s*(?:[-*]|•)\s+(.+)$/
                );


            if (match) {

                if (!inList) {

                    result.push(
                        '<ul class="chat-list">'
                    );

                    inList = true;

                }


                result.push(
                    `<li>${match[1]}</li>`
                );


            } else {

                if (inList) {

                    result.push("</ul>");

                    inList = false;

                }


                result.push(line);

            }

        }
    );


    if (inList) {

        result.push("</ul>");

    }


    return result.join("\n");

}

// ============================================================
// ESCAPE HTML
// ============================================================

function escapeHTML(text) {

    const div =
        document.createElement("div");


    div.textContent =
        text;


    return div.innerHTML;

}


// ============================================================
// LOADING MESSAGE
// ============================================================

function addLoadingMessage() {

    const container =
        document.getElementById("chatMessages");


    if (!container) {
        return null;
    }


    const id =
        `loading-${Date.now()}`;


    const wrapper =
        document.createElement("div");


    wrapper.className =
        "chat-message bot";


    wrapper.id =
        id;


    wrapper.innerHTML = `
        <div class="chat-avatar">
            <i class="fa-solid fa-robot"></i>
        </div>

        <div class="chat-bubble">

            <span class="chat-loading">

                SakuBot sedang berpikir

                <span class="loading-dots">
                    <span>.</span>
                    <span>.</span>
                    <span>.</span>
                </span>

            </span>

        </div>
    `;


    container.appendChild(
        wrapper
    );


    scrollToBottom();


    return id;

}


// ============================================================
// REMOVE LOADING
// ============================================================

function removeLoadingMessage(id) {

    if (!id) {
        return;
    }


    const loading =
        document.getElementById(id);


    if (loading) {

        loading.remove();

    }

}


// ============================================================
// RESET CHAT
// ============================================================

function resetChat() {

    const confirmed =
        confirm(
            "Apakah kamu yakin ingin menghapus riwayat chat?"
        );


    if (!confirmed) {
        return;
    }


    const container =
        document.getElementById("chatMessages");


    if (!container) {
        return;
    }


    // ==========================================
    // RESET HISTORY
    // ==========================================

    chatHistory = [];


    // ==========================================
    // RESET STATISTICS
    // ==========================================

    totalMessages = 1;

    userMessages = 0;

    botMessages = 1;


    // ==========================================
    // RESET UI
    // ==========================================

    container.innerHTML = `

        <div class="chat-message bot">

            <div class="chat-avatar">

                <i class="fa-solid fa-robot"></i>

            </div>


            <div class="chat-bubble">

                Halo! Aku SAKU Assistant 👋

                <br><br>

                Kamu bisa mencatat pengeluaran,
                pemasukan, hutang, atau bertanya
                tentang kondisi bisnis kamu.

                <br><br>

                Mau mulai dari mana?

            </div>

        </div>

    `;


    updateStatistics();

}


// ============================================================
// EXPORT CHAT
// ============================================================

function exportChat() {

    const messages =
        [];


    // ==========================================
    // INITIAL MESSAGE
    // ==========================================

    messages.push({
        role: "assistant",
        content:
            "Halo! Aku SAKU Assistant 👋"
    });


    // ==========================================
    // CHAT HISTORY
    // ==========================================

    chatHistory.forEach(function (message) {

        messages.push({
            role: message.role,
            content: message.content
        });

    });


    // ==========================================
    // EXPORT DATA
    // ==========================================

    const exportData = {

        diekspor_pada:
            new Date().toLocaleString(
                "id-ID"
            ),

        jumlah_pesan:
            messages.length,

        percakapan:
            messages

    };


    const json =
        JSON.stringify(
            exportData,
            null,
            2
        );


    // ==========================================
    // DOWNLOAD
    // ==========================================

    const blob =
        new Blob(
            [json],
            {
                type: "application/json"
            }
        );


    const url =
        URL.createObjectURL(
            blob
        );


    const link =
        document.createElement("a");


    link.href =
        url;


    const timestamp =
        getTimestamp();


    link.download =
        `saku_chat_${timestamp}.json`;


    document.body.appendChild(
        link
    );


    link.click();


    document.body.removeChild(
        link
    );


    URL.revokeObjectURL(
        url
    );

}


// ============================================================
// TIMESTAMP
// ============================================================

function getTimestamp() {

    const now =
        new Date();


    const year =
        now.getFullYear();


    const month =
        String(
            now.getMonth() + 1
        ).padStart(2, "0");


    const day =
        String(
            now.getDate()
        ).padStart(2, "0");


    const hours =
        String(
            now.getHours()
        ).padStart(2, "0");


    const minutes =
        String(
            now.getMinutes()
        ).padStart(2, "0");


    return `${year}${month}${day}_${hours}${minutes}`;

}


// ============================================================
// UPDATE STATISTICS
// ============================================================

function updateStatistics() {

    const total =
        document.getElementById(
            "totalMessages"
        );


    const user =
        document.getElementById(
            "userMessages"
        );


    const bot =
        document.getElementById(
            "botMessages"
        );


    if (total) {

        total.textContent =
            totalMessages;

    }


    if (user) {

        user.textContent =
            userMessages;

    }


    if (bot) {

        bot.textContent =
            botMessages;

    }

}


// ============================================================
// EXAMPLE QUESTIONS TOGGLE
// ============================================================

function toggleExamples() {

    const content =
        document.getElementById(
            "exampleContent"
        );


    const chevron =
        document.getElementById(
            "exampleChevron"
        );


    if (!content || !chevron) {
        return;
    }


    const isHidden =
        content.style.display === "none";


    if (isHidden) {

        content.style.display =
            "block";


        chevron.classList.remove(
            "fa-chevron-down"
        );


        chevron.classList.add(
            "fa-chevron-up"
        );

    } else {

        content.style.display =
            "none";


        chevron.classList.remove(
            "fa-chevron-up"
        );


        chevron.classList.add(
            "fa-chevron-down"
        );

    }

}


// ============================================================
// SCROLL CHAT
// ============================================================

function scrollToBottom() {

    const container =
        document.getElementById(
            "chatMessages"
        );


    if (!container) {
        return;
    }


    setTimeout(
        function () {

            container.scrollTop =
                container.scrollHeight;

        },
        50
    );

}