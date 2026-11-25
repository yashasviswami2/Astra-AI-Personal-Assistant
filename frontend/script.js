// ==========================================
// ASTRA - MAIN JAVASCRIPT
// ==========================================

const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const chatMessages = document.getElementById("chat-messages");
const sendBtn = document.getElementById("send-btn");
const micBtn = document.getElementById("mic-btn");


// ==========================================
// ADD MESSAGE TO CHAT
// ==========================================

function addMessage(message, sender) {

    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${sender}`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = sender === "bot" ? "A" : "Y";

    const content = document.createElement("div");
    content.className = "message-content";
    content.textContent = message;

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageDiv;
}


// ==========================================
// SEND MESSAGE TO GEMINI
// ==========================================

async function sendMessage(message) {

    if (!message.trim()) return;

    addMessage(message, "user");

    userInput.value = "";

    sendBtn.disabled = true;
    micBtn.disabled = true;

    sendBtn.textContent = "...";

    const loadingMessage = addMessage(
        "ASTRA is thinking...",
        "bot"
    );

    try {

        const response = await fetch("/api/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: message
            })

        });

        const data = await response.json();

        loadingMessage.remove();

        if (!response.ok) {
            throw new Error(data.error || "Something went wrong.");
        }

        addMessage(data.response, "bot");

        // Voice output will be connected through Flask.
        // The /api/speak endpoint will be added in the backend step.

    }

    catch (error) {

        loadingMessage.remove();

        addMessage(
            "Sorry! " + error.message,
            "bot"
        );

    }

    finally {

        sendBtn.disabled = false;
        micBtn.disabled = false;

        sendBtn.textContent = "➤";

        userInput.focus();

    }
}


// ==========================================
// CHAT FORM
// ==========================================

chatForm.addEventListener("submit", async (event) => {

    event.preventDefault();

    const message = userInput.value.trim();

    if (!message) return;

    await sendMessage(message);

});


// ==========================================
// MICROPHONE / SPEECH INPUT
// ==========================================

micBtn.addEventListener("click", async () => {

    try {

        micBtn.disabled = true;
        micBtn.classList.add("listening");

        micBtn.textContent = "🔴";
        micBtn.title = "Listening...";

        const response = await fetch("/api/listen", {
            method: "POST"
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Microphone error.");
        }

        if (data.transcript && data.transcript.trim()) {

            userInput.value = data.transcript;

            await sendMessage(data.transcript);

        } else {

            addMessage(
                "I couldn't understand that. Please try again.",
                "bot"
            );

        }

    }

    catch (error) {

        addMessage(
            "Microphone error: " + error.message,
            "bot"
        );

    }

    finally {

        micBtn.disabled = false;
        micBtn.classList.remove("listening");

        micBtn.textContent = "🎙️";
        micBtn.title = "Speak to ASTRA";

    }

});


// ==========================================
// SIDEBAR NAVIGATION
// ==========================================

const navButtons = document.querySelectorAll(".nav-btn");
const pages = document.querySelectorAll(".page");

const pageTitles = {

    voice: "Voice Assistant",
    chat: "AI Chat",
    commands: "Commands",
    about: "About ASTRA"

};

navButtons.forEach(button => {

    button.addEventListener("click", () => {

        const targetPage = button.dataset.page;

        navButtons.forEach(btn =>
            btn.classList.remove("active")
        );

        pages.forEach(page =>
            page.classList.remove("active")
        );

        button.classList.add("active");

        document.getElementById(targetPage)
            .classList.add("active");

        document.getElementById("page-title")
            .textContent = pageTitles[targetPage];

    });

});


// ==========================================
// CHECK BACKEND STATUS
// ==========================================

async function checkBackend() {

    try {

        const response = await fetch("/api/health");

        const data = await response.json();

        console.log("ASTRA Backend:", data);

        if (!data.gemini_configured) {

            console.warn(
                "Gemini API key is not configured."
            );

        }

    }

    catch (error) {

        console.error(
            "Backend connection failed:",
            error
        );

    }

}

checkBackend();