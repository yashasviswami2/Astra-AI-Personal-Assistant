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

// ==========================================
// ASTRA INTERACTIVE COMMANDS
// ==========================================

document.querySelectorAll(".command-card").forEach(button => {

    button.addEventListener("click", async () => {

        let command = button.dataset.command;

        const action = button.dataset.action;

        // WEB SEARCH
        if (action === "search") {

            const query = prompt("What would you like to search for?");

            if (!query || !query.trim()) return;

            command = "Search the web for " + query.trim();
        }

        // PDF SUMMARIZATION
        if (action === "pdf") {

            const path = prompt("Enter the full path of your PDF file:");

            if (!path || !path.trim()) return;

            command = "Summarize the PDF file located at: " + path.trim();
        }

        if (!command) return;

        // Prevent overlapping requests
        if (sendBtn.disabled) {
            alert("ASTRA is processing another request.");
            return;
        }

        // Switch to AI Chat
        document.querySelector(
            '.nav-btn[data-page="chat"]'
        ).click();

        // Execute command through existing backend
        await sendMessage(command);

    });

});

// ==========================================
// ASTRA SMART REMINDER NOTIFICATIONS
// ==========================================

const shownReminders = new Set();

function showAstraNotification(title, message) {

    const notification = document.createElement("div");

    notification.className = "astra-notification";

    const heading = document.createElement("strong");

    heading.textContent = title;

    const content = document.createElement("p");

    content.textContent = message;

    const closeButton = document.createElement("button");

    closeButton.textContent = "Dismiss";

    closeButton.onclick = () => notification.remove();

    notification.append(
        heading,
        content,
        closeButton
    );

    document.body.appendChild(notification);

    setTimeout(() => {

        notification.remove();

    }, 15000);
}


async function checkAcademicReminders() {

    try {

        const response = await fetch(
            "/api/student/reminders"
        );

        if (!response.ok) return;

        const data = await response.json();

        const newReminders = data.reminders.filter(
            reminder => !shownReminders.has(
                reminder.id + reminder.priority
            )
        );

        if (!newReminders.length) return;

        newReminders.forEach(reminder => {

            shownReminders.add(
                reminder.id + reminder.priority
            );

        });

        showAstraNotification(
            "🔔 ASTRA Academic Reminder",
            newReminders.map(
                reminder => reminder.message
            ).join("\n")
        );

    } catch (error) {

        console.error("Reminder error:", error);

    }
}


// Check shortly after startup

setTimeout(checkAcademicReminders, 2000);


// Check automatically every minute

setInterval(checkAcademicReminders, 60000);

// ==========================================
// ASTRA PDF STUDY ASSISTANT
// ==========================================

pageTitles.materials = "Study Materials";

const studyPdfInput =
    document.getElementById("study-pdf");

const analyzePdfButton =
    document.getElementById("analyze-pdf");

const pdfResult =
    document.getElementById("pdf-result");

const pdfStatus =
    document.getElementById("pdf-status");


studyPdfInput.addEventListener("change", () => {

    const file = studyPdfInput.files[0];

    document.getElementById(
        "pdf-file-name"
    ).textContent = file
        ? file.name
        : "No file selected";

});


analyzePdfButton.addEventListener("click", async () => {

    const file = studyPdfInput.files[0];

    if (!file) {

        alert("Please select a PDF first.");

        return;
    }

    if (file.size > 20 * 1024 * 1024) {

        alert("Maximum PDF size is 20 MB.");

        return;
    }

    const formData = new FormData();

    formData.append("pdf", file);

    formData.append(
        "mode",
        document.getElementById("pdf-mode").value
    );

    formData.append(
        "question",
        document.getElementById("pdf-question").value
    );

    analyzePdfButton.disabled = true;

    analyzePdfButton.textContent =
        "⏳ ASTRA is analyzing...";

    pdfStatus.textContent =
        "Reading your study material...";

    pdfResult.textContent =
        "Generating personalized study material...";

    try {

        const response = await fetch(
            "/api/student/pdf",
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.error || "PDF analysis failed."
            );
        }

        pdfStatus.textContent =
            `Analyzed ${data.pages_processed} of ` +
            `${data.pages} pages successfully.` +
            (data.limited
                ? " Document exceeds the analysis limit."
                : "");

        pdfResult.textContent = data.response;

    } catch (error) {

        pdfStatus.textContent = "Analysis failed.";

        pdfResult.textContent = error.message;

    } finally {

        analyzePdfButton.disabled = false;

        analyzePdfButton.textContent =
            "✨ Analyze with ASTRA";

    }

});


document.getElementById(
    "copy-pdf-result"
).addEventListener("click", async () => {

    try {

        await navigator.clipboard.writeText(
            pdfResult.textContent
        );

        alert("Study material copied!");

    } catch (error) {

        alert("Could not copy study material.");

    }

});

// ==========================================
// ASTRA PRODUCTIVITY HUB
// ==========================================

pageTitles.productivity = "Productivity Hub";


// LIVE SYSTEM MONITOR

async function loadSystemStatus() {

    try {

        const response = await fetch("/api/system/status");

        if (!response.ok) {
            throw new Error("System monitor unavailable");
        }

        const data = await response.json();

        ["cpu", "ram", "disk", "battery"].forEach(key => {

            document.getElementById(
                `${key}-value`
            ).textContent =
                data[key] === null
                ? "N/A"
                : `${data[key]}%`;

            document.getElementById(
                `${key}-bar`
            ).value = data[key] ?? 0;

        });

        document.getElementById(
            "system-details"
        ).textContent =
            `${data.os} • ${data.cores} CPU threads • ` +
            `${data.ram_available} GB available RAM • ` +
            `${data.disk_free} GB free storage`;

    } catch (error) {

        document.getElementById(
            "system-details"
        ).textContent = error.message;

    }

}


document.querySelector(
    '.nav-btn[data-page="productivity"]'
).addEventListener("click", loadSystemStatus);


setInterval(() => {

    if (
        document.getElementById("productivity")
        .classList.contains("active")
    ) {
        loadSystemStatus();
    }

}, 5000);


// POMODORO FOCUS TIMER

let focusMinutes = 25;
let focusSeconds = 25 * 60;
let focusInterval = null;
let focusEndTime = null;

let focusSessions = Number(
    localStorage.getItem("astra-focus-sessions") || 0
);

document.getElementById(
    "focus-sessions"
).textContent = focusSessions;


function updateFocusDisplay() {

    const minutes = Math.floor(focusSeconds / 60);
    const seconds = focusSeconds % 60;

    document.getElementById(
        "focus-timer"
    ).textContent =
        `${String(minutes).padStart(2, "0")}:` +
        `${String(seconds).padStart(2, "0")}`;

}


function stopFocusTimer() {

    clearInterval(focusInterval);

    focusInterval = null;

}


function finishFocusSession() {

    stopFocusTimer();

    if (focusMinutes === 25) {

        focusSessions++;

        localStorage.setItem(
            "astra-focus-sessions",
            focusSessions
        );

        document.getElementById(
            "focus-sessions"
        ).textContent = focusSessions;

    }

    document.getElementById(
        "focus-status"
    ).textContent = "Session completed!";

    showAstraNotification(
        "🎯 ASTRA Focus Timer",
        focusMinutes === 25
            ? "Great work! Time to take a short break."
            : "Break completed. Ready to study again?"
    );

}


document.querySelectorAll(
    ".focus-mode"
).forEach(button => {

    button.addEventListener("click", () => {

        stopFocusTimer();

        focusMinutes = Number(button.dataset.minutes);

        focusSeconds = focusMinutes * 60;

        updateFocusDisplay();

        document.getElementById(
            "focus-status"
        ).textContent = "Ready to start";

    });

});


document.getElementById(
    "focus-start"
).addEventListener("click", () => {

    if (focusInterval) return;

    if (focusSeconds <= 0) {
        focusSeconds = focusMinutes * 60;
    }

    focusEndTime = Date.now() + focusSeconds * 1000;

    updateFocusDisplay();

    document.getElementById(
        "focus-status"
    ).textContent = "Session in progress";

    focusInterval = setInterval(() => {

        focusSeconds = Math.max(
            0,
            Math.ceil((focusEndTime - Date.now()) / 1000)
        );

        updateFocusDisplay();

        if (focusSeconds === 0) {
            finishFocusSession();
        }

    }, 250);

});


document.getElementById(
    "focus-pause"
).addEventListener("click", () => {

    if (focusInterval) {

        focusSeconds = Math.max(
            0,
            Math.ceil((focusEndTime - Date.now()) / 1000)
        );

        stopFocusTimer();

        updateFocusDisplay();

        document.getElementById(
            "focus-status"
        ).textContent = "Session paused";

    }

});


document.getElementById(
    "focus-reset"
).addEventListener("click", () => {

    stopFocusTimer();

    focusSeconds = focusMinutes * 60;

    updateFocusDisplay();

    document.getElementById(
        "focus-status"
    ).textContent = "Timer reset";

});


// ==========================================
// ASTRA VISUAL EXAM PLANNER
// ==========================================

async function loadExamPlanner() {

    const container = document.getElementById("exam-list");

    try {

        const response = await fetch("/api/student/exams");

        if (!response.ok) {
            throw new Error("Could not load examinations.");
        }

        const data = await response.json();

        if (!data.exams.length) {

            container.textContent =
                "No examinations registered yet.";

            return;
        }

        const today = new Date();

        const todayUTC = Date.UTC(
            today.getFullYear(),
            today.getMonth(),
            today.getDate()
        );

        container.innerHTML = data.exams.map(exam => {

            const examDate = Date.parse(
                exam.exam_date + "T00:00:00Z"
            );

            const days = Math.round(
                (examDate - todayUTC) / 86400000
            );

            let countdown = `${days} days remaining`;
            let urgency = "upcoming";

            if (days < 0) {

                countdown = "Exam date passed";
                urgency = "completed";

            } else if (days === 0) {

                countdown = "EXAM TODAY";
                urgency = "overdue";

            } else if (days <= 3) {

                urgency = "urgent";

            }

            return `
                <div class="exam-card">

                    <div class="exam-header">

                        <h3>${escapeHTML(exam.subject)}</h3>

                        <span class="assignment-badge badge-${urgency}">
                            ${countdown}
                        </span>

                    </div>

                    <p>📅 Exam Date: ${escapeHTML(exam.exam_date)}</p>

                    <h4>Examination Syllabus</h4>

                    <p>${escapeHTML(
                        exam.syllabus || "Not provided"
                    )}</p>

                </div>
            `;

        }).join("");

    } catch (error) {

        container.textContent = error.message;

    }

}


document.getElementById(
    "refresh-exams"
).addEventListener("click", loadExamPlanner);


document.querySelector(
    '.nav-btn[data-page="student"]'
).addEventListener("click", loadExamPlanner);


document.getElementById(
    "add-exam-btn"
).addEventListener("click", async () => {

    if (sendBtn.disabled) return;

    document.querySelector(
        '.nav-btn[data-page="chat"]'
    ).click();

    await sendMessage(
        "Help me register a new examination with its subject, date and syllabus."
    );

});


document.getElementById(
    "exam-plan-btn"
).addEventListener("click", async () => {

    if (sendBtn.disabled) return;

    document.querySelector(
        '.nav-btn[data-page="chat"]'
    ).click();

    await sendMessage(
        "Retrieve my upcoming exams and saved syllabus, then create a prioritized study timetable."
    );

});

// ==========================================
// ASTRA PROFESSIONAL MESSAGE FORMATTING
// ==========================================

function formatAstraMessage(message) {

    const content = message.querySelector(".message-content");

    if (!content || content.dataset.formatted) return;

    if (typeof marked === "undefined" ||
        typeof DOMPurify === "undefined") return;

    const originalText = content.textContent.trim();

    if (!originalText) return;

    content.dataset.formatted = "true";

    content.innerHTML = DOMPurify.sanitize(
        marked.parse(originalText)
    );

    const actions = document.createElement("div");

    actions.className = "message-actions";

    const copyButton = document.createElement("button");

    copyButton.textContent = "📋 Copy";

    copyButton.onclick = async () => {

        try {

            await navigator.clipboard.writeText(originalText);

            copyButton.textContent = "✓ Copied";

            setTimeout(() => {
                copyButton.textContent = "📋 Copy";
            }, 1500);

        } catch {

            alert("Could not copy response.");

        }

    };

    const downloadButton = document.createElement("button");

    downloadButton.textContent = "⬇ Download";

    downloadButton.onclick = () => {

        const blob = new Blob(
            [originalText],
            { type: "text/plain;charset=utf-8" }
        );

        const url = URL.createObjectURL(blob);

        const link = document.createElement("a");

        link.href = url;
        link.download = "ASTRA_Response.txt";

        link.click();

        setTimeout(() => URL.revokeObjectURL(url), 1000);

    };

    actions.append(copyButton, downloadButton);

    content.appendChild(actions);

}


const astraChatObserver = new MutationObserver(() => {

    document.querySelectorAll(
        "#chat-messages .message.bot"
    ).forEach(formatAstraMessage);

});


astraChatObserver.observe(
    document.getElementById("chat-messages"),
    {
        childList: true,
        subtree: true
    }
);


document.querySelectorAll(
    "#chat-messages .message.bot"
).forEach(formatAstraMessage);

// ASTRA CHAT MANAGEMENT

document.getElementById(
    "export-chat"
).addEventListener("click", () => {

    const messages = document.querySelectorAll(
        "#chat-messages .message"
    );

    const transcript = Array.from(messages).map(message => {

        const role = message.classList.contains("bot")
            ? "ASTRA"
            : "USER";

        const content = message.querySelector(
            ".message-content"
        ).cloneNode(true);

        content.querySelectorAll(
            ".message-actions"
        ).forEach(element => element.remove());

        return `${role}:\n${content.innerText}\n`;

    }).join("\n------------------------\n\n");

    const blob = new Blob(
        [transcript],
        { type: "text/plain;charset=utf-8" }
    );

    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");

    link.href = url;

    link.download = "ASTRA_Conversation.txt";

    link.click();

    setTimeout(() => URL.revokeObjectURL(url), 1000);

});


document.getElementById(
    "clear-chat"
).addEventListener("click", () => {

    if (sendBtn.disabled) {

        alert("Wait for ASTRA to finish responding.");

        return;

    }

    if (!confirm("Clear the visible conversation?")) return;

    document.getElementById(
        "chat-messages"
    ).innerHTML = "";

    addMessage(
        "Hello! I'm ASTRA. What would you like to do next?",
        "bot"
    );

});