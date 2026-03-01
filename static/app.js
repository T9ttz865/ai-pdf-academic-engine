// ===============================
// Send Message to AI (Flask API)
// ===============================

async function sendMessage(mode) {

    const input = document.getElementById("userInput");
    const chatBox = document.getElementById("chatBox");

    if (!input || !chatBox) return;

    const message = input.value.trim();
    if (!message) return;

    // عرض رسالة المستخدم
    chatBox.innerHTML += `
        <div class="chat-message user">
            ${escapeHTML(message)}
        </div>
    `;

    input.value = "";
    scrollToBottom();

    // إنشاء عنصر تحميل
    const loadingId = "loading-" + Date.now();

    chatBox.innerHTML += `
        <div class="chat-message ai" id="${loadingId}">
            ⏳ Processing...
        </div>
    `;

    scrollToBottom();

    try {

        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message,
                mode: mode
            })
        });

        const data = await response.json();

        // إزالة loading إذا موجود
        const loadingElement = document.getElementById(loadingId);
        if (loadingElement) loadingElement.remove();

        if (!response.ok || !data.reply) {

            chatBox.innerHTML += `
                <div class="chat-message ai error">
                    ⚠ ${escapeHTML(data.error || "Server error")}
                </div>
            `;

        } else {

            chatBox.innerHTML += `
                <div class="chat-message ai">
                    ${escapeHTML(data.reply)}
                </div>
            `;

        }

        scrollToBottom();

    } catch (error) {

        const loadingElement = document.getElementById(loadingId);
        if (loadingElement) loadingElement.remove();

        chatBox.innerHTML += `
            <div class="chat-message ai error">
                ⚠ Connection error — check Flask server
            </div>
        `;

        scrollToBottom();
    }
}


// ===============================
// Helpers
// ===============================

// منع إدخال HTML خبيث
function escapeHTML(str) {
    return str.replace(/[&<>"']/g, function(m) {
        return ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        })[m];
    });
}

// Scroll تلقائي للأسفل
function scrollToBottom() {
    const chatBox = document.getElementById("chatBox");
    if (!chatBox) return;
    chatBox.scrollTop = chatBox.scrollHeight;
}