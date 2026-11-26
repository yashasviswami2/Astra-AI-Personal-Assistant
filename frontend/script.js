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
        if (localStorage.getItem("astra-voice-enabled") === "true") fetch("/api/speak", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:data.response})}).catch(console.error);



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



        document.getElementById(targetPage)?.classList.add("active");



        document.getElementById("page-title")

            .textContent = pageTitles[targetPage] || button.textContent.trim();



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



/* ==================================
   ASTRA INTELLIGENT HOME DASHBOARD
================================== */
pageTitles.home = "Home Dashboard";



let homeStudentName = "";



function updateHomeClock() {

    const now = new Date();

    const hour = now.getHours();



    let greeting = "Good evening";



    if (hour < 12) {

        greeting = "Good morning";

    } else if (hour < 17) {

        greeting = "Good afternoon";

    }



    document.getElementById("home-greeting").textContent =

        `${greeting}, ${homeStudentName || "Student"}`;



    document.getElementById("home-clock").textContent =

        now.toLocaleTimeString("en-IN");



    document.getElementById("home-date").textContent =

        now.toLocaleDateString("en-IN", {

            weekday: "long",

            day: "numeric",

            month: "long",

            year: "numeric"

        });

}



async function loadHomeDashboard() {



    try {

        const response = await fetch("/api/student/dashboard");



        if (!response.ok) {

            throw new Error("Dashboard unavailable");

        }



        const data = await response.json();



        const profile = data.profile || {};

        const stats = data.stats || {};

        const assignments = data.assignments || [];



        homeStudentName = profile.name || "";



        updateHomeClock();



        document.getElementById("home-subjects").textContent =

            stats.subjects || 0;



        document.getElementById("home-pending").textContent =

            stats.pending || 0;



        document.getElementById("home-completed").textContent =

            stats.completed || 0;



        document.getElementById("home-overdue").textContent =

            stats.overdue || 0;



        // Academic progress
        const total = stats.total || 0;

        const completed = stats.completed || 0;



        const progress = total > 0

            ? Math.round((completed / total) * 100)

            : 0;



        document.getElementById("home-progress").textContent =

            `${progress}%`;



        document.getElementById("home-progress-bar").style.width =

            `${progress}%`;



        // Today's priorities
        const priorities = assignments.filter(item =>

            item.status === "Pending" &&

            ["Overdue", "Urgent"].includes(item.urgency)

        );



        const priorityContainer =

            document.getElementById("home-priorities");



        if (priorities.length === 0) {



            priorityContainer.innerHTML = `

                <p>🎉 No urgent or overdue assignments.</p>

                <p>You can focus on revision and learning.</p>

            `;



        } else {



            priorityContainer.innerHTML = priorities.map(item => `

                <div class="home-priority-item">

                    <strong>${escapeHTML(item.title)}</strong>

                    <p>${escapeHTML(item.deadline)}</p>

                    <p>${escapeHTML(item.urgency)}</p>

                </div>

            `).join("");



        }



    } catch (error) {



        console.error("Home dashboard error:", error);



        document.getElementById("home-priorities").textContent =

            "Unable to load academic records.";



    }

}





/* NEXT EXAMINATION */
async function loadHomeExam() {



    const container =

        document.getElementById("home-next-exam");



    try {



        const response = await fetch("/api/student/exams");



        if (!response.ok) {

            throw new Error("Examination API unavailable");

        }



        const data = await response.json();



        const now = new Date();



        const today = Date.UTC(

            now.getFullYear(),

            now.getMonth(),

            now.getDate()

        );



        const exams = (data.exams || [])

            .filter(exam =>

                Date.parse(exam.exam_date) >= today

            )

            .sort((a, b) =>

                a.exam_date.localeCompare(b.exam_date)

            );



        if (exams.length === 0) {



            container.innerHTML = `

                <p>📅 No upcoming examinations registered.</p>

                <p>Add examinations in Student Workspace.</p>

            `;



            return;

        }



        const exam = exams[0];



        const daysRemaining = Math.ceil(

            (Date.parse(exam.exam_date) - today) / 86400000

        );



        container.innerHTML = `

            <h2>${escapeHTML(

                exam.subject || exam.subject_name || "Examination"

            )}</h2>



            <p>Exam Date: ${escapeHTML(exam.exam_date)}</p>



            <h2 style="color:#818cf8;">

                ${daysRemaining === 0

                    ? "Exam Today!"

                    : `${daysRemaining} Days Remaining`}

            </h2>



            <p>${escapeHTML(

                exam.syllabus || "No syllabus registered."

            )}</p>

        `;



    } catch (error) {



        container.textContent =

            "Unable to load examinations.";



        console.error(error);



    }

}





/* LIVE SYSTEM HEALTH */
async function loadHomeSystemHealth() {



    try {



        const response = await fetch("/api/system/status");



        if (!response.ok) {

            throw new Error("System API unavailable");

        }



        const data = await response.json();



        document.getElementById("home-cpu").textContent =

            `${data.cpu}%`;



        document.getElementById("home-ram").textContent =

            `${data.ram}%`;



        document.getElementById("home-disk").textContent =

            `${data.disk}%`;



        const batteryElement =

            document.getElementById("home-battery");



        batteryElement.textContent =

            data.battery == null

                ? "Not available"

                : `${data.battery}%${data.charging ? " (Charging)" : ""}`;



        batteryElement.style.color =

            data.battery != null && data.battery <= 20

                ? "#ef4444"

                : "#22c55e";



    } catch (error) {



        console.error("System monitoring error:", error);



    }

}





/* QUICK ACTION BUTTONS */
document.querySelectorAll("[data-home-page]")

    .forEach(button => {



        button.addEventListener("click", () => {



            const page = button.dataset.homePage;



            document.querySelector(

                `.nav-btn[data-page="${page}"]`

            )?.click();



        });



    });





/* AI DAILY BRIEFING */
document.getElementById("home-briefing-btn")

    .addEventListener("click", async () => {



        if (sendBtn.disabled) {

            return;

        }



        document.querySelector(

            '.nav-btn[data-page="chat"]'

        )?.click();



        await sendMessage(

            "Generate my personalized daily briefing. " +

            "Retrieve my student profile, registered subjects, " +

            "pending assignments, upcoming deadlines and exams. " +

            "Use my actual academic records. " +

            "Recommend today's top three priorities, " +

            "a realistic study schedule, revision topics, " +

            "and one productivity tip. " +

            "Do not invent assignments or examination dates."

        );



    });





/* DASHBOARD REFRESH */
async function refreshHomeDashboard() {



    await Promise.all([

        loadHomeDashboard(),

        loadHomeExam(),

        loadHomeSystemHealth()

    ]);



}



document.querySelector('.nav-btn[data-page="home"]')

    .addEventListener("click", refreshHomeDashboard);





// Update clock every second
updateHomeClock();



setInterval(updateHomeClock, 1000);





// Refresh academic information every 30 seconds
setInterval(() => {



    if (document.getElementById("home")

        .classList.contains("active")) {



        loadHomeDashboard();

        loadHomeExam();



    }



}, 30000);





// Refresh system information every 5 seconds
setInterval(() => {



    if (document.getElementById("home")

        .classList.contains("active")) {



        loadHomeSystemHealth();



    }



}, 5000);





// Make Home Dashboard the default landing page
document.querySelector(

    '.nav-btn[data-page="home"]'

)?.click();





/* =====================================
   ASTRA PERSONAL MEMORY WORKSPACE
===================================== */
pageTitles.memory = "Personal Memory";



let astraMemories = [];





/* LOAD SAVED MEMORIES */
async function loadPersonalMemories() {



    try {



        const response = await fetch("/api/memory");



        if (!response.ok) {

            throw new Error("Unable to load memories.");

        }



        const data = await response.json();



        astraMemories = data.memories || [];



        document.getElementById("memory-total").textContent =

            astraMemories.length;



        const categories = new Set(

            astraMemories.map(memory => memory.category)

        );



        document.getElementById("memory-categories").textContent =

            categories.size;



        renderPersonalMemories();



    } catch (error) {



        document.getElementById("memory-list").textContent =

            "Unable to load personal memories.";



        console.error(error);



    }

}





/* DISPLAY AND SEARCH MEMORIES */
function renderPersonalMemories() {



    const search = document

        .getElementById("memory-search")

        .value.toLowerCase().trim();



    const container =

        document.getElementById("memory-list");



    const filtered = astraMemories.filter(memory =>



        memory.memory_key.toLowerCase().includes(search) ||



        memory.memory_value.toLowerCase().includes(search) ||



        memory.category.toLowerCase().includes(search)



    );



    if (filtered.length === 0) {



        container.innerHTML = `

            <div class="empty-state">

                No matching memories found.

                Add a memory to personalize ASTRA.

            </div>

        `;



        return;

    }



    container.innerHTML = filtered.map(memory => `



        <div class="memory-card">



            <span class="memory-category">

                ${escapeHTML(memory.category)}

            </span>



            <h3>

                ${escapeHTML(memory.memory_key)}

            </h3>



            <p>

                ${escapeHTML(memory.memory_value)}

            </p>



            <p>

                Last updated:

                ${escapeHTML(memory.updated_at || "")}

            </p>



            <div class="memory-actions">



                <button

                    class="academic-btn"

                    onclick="editPersonalMemory(${Number(memory.id)})"

                >

                    ✏️ Edit

                </button>



                <button

                    class="memory-delete"

                    onclick="deletePersonalMemory(${Number(memory.id)})"

                >

                    🗑 Delete

                </button>



            </div>



        </div>



    `).join("");



}





/* SAVE OR UPDATE MEMORY */
document.getElementById("memory-form")

    .addEventListener("submit", async event => {



        event.preventDefault();



        const status =

            document.getElementById("memory-status");



        const key =

            document.getElementById("memory-key").value.trim();



        const value =

            document.getElementById("memory-value").value.trim();



        const category =

            document.getElementById("memory-category").value;



        if (!key || !value) {



            status.textContent =

                "Please enter a memory name and value.";



            return;

        }



        status.textContent = "Saving memory...";



        try {



            const response = await fetch("/api/memory", {



                method: "POST",



                headers: {

                    "Content-Type": "application/json"

                },



                body: JSON.stringify({

                    key,

                    value,

                    category

                })



            });



            const data = await response.json();



            if (!response.ok || !data.success) {



                throw new Error(

                    data.error || "Unable to save memory."

                );



            }



            status.textContent =

                "Memory saved successfully!";



            status.style.color = "#22c55e";



            document.getElementById("memory-form").reset();



            document.getElementById("memory-key").readOnly = false;



            await loadPersonalMemories();



        } catch (error) {



            status.textContent = error.message;



            status.style.color = "#ef4444";



        }



    });





/* EDIT EXISTING MEMORY */
function editPersonalMemory(id) {



    const memory = astraMemories.find(

        item => item.id === id

    );



    if (!memory) {

        return;

    }



    const keyInput =

        document.getElementById("memory-key");



    keyInput.value = memory.memory_key;



    keyInput.readOnly = true;



    document.getElementById("memory-value").value =

        memory.memory_value;



    const categoryInput =

        document.getElementById("memory-category");



    if (![...categoryInput.options].some(

        option => option.value === memory.category

    )) {

        categoryInput.add(

            new Option(memory.category, memory.category)

        );

    }



    categoryInput.value = memory.category;



    document.getElementById("memory-status").textContent =

        "Editing existing memory. Click Save Memory to update.";



    document.getElementById("memory-form").scrollIntoView({

        behavior: "smooth",

        block: "center"

    });



}





/* DELETE MEMORY */
async function deletePersonalMemory(id) {



    const confirmed = confirm(

        "Are you sure you want to delete this memory?"

    );



    if (!confirmed) {

        return;

    }



    try {



        const response = await fetch(

            `/api/memory/${id}`,

            { method: "DELETE" }

        );



        const data = await response.json();



        if (!response.ok || !data.success) {



            throw new Error(

                data.error || "Unable to delete memory."

            );



        }



        document.getElementById("memory-form").reset();



        document.getElementById("memory-key").readOnly = false;



        await loadPersonalMemories();



    } catch (error) {



        alert(error.message);



    }



}





/* LIVE MEMORY SEARCH */
document.getElementById("memory-search")

    .addEventListener("input", renderPersonalMemories);





/* AI PERSONALIZATION */
document.getElementById("memory-ai-btn")

    .addEventListener("click", async () => {



        if (sendBtn.disabled) {

            return;

        }



        document.querySelector(

            '.nav-btn[data-page="chat"]'

        )?.click();



        await sendMessage(

            "Retrieve my relevant saved personal memories " +

            "and academic profile. Based on my actual " +

            "preferences, goals and routine, provide " +

            "personalized academic, career and productivity " +

            "recommendations. Do not invent personal information."

        );



    });





/* LOAD MEMORY WORKSPACE */
document.querySelector('.nav-btn[data-page="memory"]')

    .addEventListener("click", loadPersonalMemories);



/* =====================================
   ASTRA INTELLIGENT STUDY PLANNER
===================================== */
pageTitles.planner = "AI Study Planner";



const plannerDate = document.getElementById("planner-date");



const plannerNow = new Date();



plannerDate.value =

    `${plannerNow.getFullYear()}-` +

    `${String(plannerNow.getMonth() + 1).padStart(2, "0")}-` +

    `${String(plannerNow.getDate()).padStart(2, "0")}`;





/* FORMAT STUDY DURATION */
function formatStudyDuration(minutes) {



    const hours = Math.floor(minutes / 60);

    const remaining = minutes % 60;



    return `${hours}h ${remaining}m`;

}





/* LOAD STUDY PLANNER */
async function loadStudyPlanner() {



    const container =

        document.getElementById("planner-sessions");



    try {



        const response = await fetch(

            `/api/study/sessions?date=${encodeURIComponent(plannerDate.value)}`

        );



        if (!response.ok) {

            throw new Error("Unable to load study planner.");

        }



        const data = await response.json();



        const stats = data.stats;



        document.getElementById("planner-total").textContent =

            stats.total;



        document.getElementById("planner-completed").textContent =

            stats.completed;



        document.getElementById("planner-planned").textContent =

            formatStudyDuration(stats.planned_minutes);



        document.getElementById("planner-studied").textContent =

            formatStudyDuration(stats.completed_minutes);



        document.getElementById("planner-progress").textContent =

            `${stats.progress}%`;



        document.getElementById("planner-progress-bar").style.width =

            `${stats.progress}%`;



        if (!data.sessions.length) {



            container.innerHTML = `

                <div class="empty-state">

                    <h3>No study sessions scheduled.</h3>

                    <p>Generate an AI timetable to get started.</p>

                </div>

            `;



            return;

        }



        container.innerHTML = data.sessions.map(session => `



            <div class="study-session-card

                ${session.status === "Completed" ? "completed" : ""}">



                <div class="study-session-time">

                    ${escapeHTML(session.start_time)}

                </div>



                <div class="study-session-info">



                    <span class="study-priority

                        priority-${escapeHTML(session.priority.toLowerCase())}">

                        ${escapeHTML(session.priority)} Priority

                    </span>



                    <h3>${escapeHTML(session.subject)}</h3>



                    <p>${escapeHTML(session.topic)}</p>



                    <p>

                        ⏱ ${Number(session.duration_minutes)} minutes

                        | ${escapeHTML(session.status)}

                    </p>



                </div>



                <div class="study-session-actions">



                    ${session.status === "Pending" ? `

                        <button class="complete-btn"

                            onclick="completePlannerSession(${Number(session.id)})">

                            ✓ Complete

                        </button>

                    ` : "✅ Completed"}



                    <button class="memory-delete"

                        onclick="deletePlannerSession(${Number(session.id)})">

                        Delete

                    </button>



                </div>



            </div>



        `).join("");



    } catch (error) {



        container.textContent = error.message;



        console.error(error);



    }

}





/* COMPLETE STUDY SESSION */
async function completePlannerSession(id) {



    try {



        const response = await fetch(

            `/api/study/session/${id}/complete`,

            { method: "POST" }

        );



        if (!response.ok) {

            throw new Error("Unable to complete session.");

        }



        await loadStudyPlanner();



    } catch (error) {



        alert(error.message);



    }

}





/* DELETE STUDY SESSION */
async function deletePlannerSession(id) {



    if (!confirm("Delete this study session?")) {

        return;

    }



    try {



        const response = await fetch(

            `/api/study/session/${id}`,

            { method: "DELETE" }

        );



        if (!response.ok) {

            throw new Error("Unable to delete session.");

        }



        await loadStudyPlanner();



    } catch (error) {



        alert(error.message);



    }

}





/* GENERATE AI TIMETABLE */
document.getElementById("generate-timetable")

    .addEventListener("click", async () => {



        if (sendBtn.disabled) return;



        const date = plannerDate.value;



        const hours =

            document.getElementById("planner-hours").value;



        const start =

            document.getElementById("planner-start").value;



        if (!date || !start) {

            alert("Please select a date and start time.");

            return;

        }



        document.querySelector(

            '.nav-btn[data-page="chat"]'

        )?.click();



        await sendMessage(

            `Create a personalized study timetable for ${date}. ` +

            `I have ${hours} hours available including breaks, ` +

            `starting at ${start}. ` +

            `Retrieve my registered subjects, upcoming exams, ` +

            `assignments, existing study sessions and relevant ` +

            `personal study preferences. ` +

            `Prioritize urgent academic work. ` +

            `Do not schedule sessions past midnight. ` +

            `Present the proposed timetable and ask for my ` +

            `approval before saving it to the database.`

        );



    });





/* ADD MANUAL SESSION THROUGH AI */
document.getElementById("add-study-session")

    .addEventListener("click", async () => {



        if (sendBtn.disabled) return;



        if (!plannerDate.value) {

            alert("Please select a date.");

            return;

        }



        document.querySelector(

            '.nav-btn[data-page="chat"]'

        )?.click();



        await sendMessage(

            `Help me add a study session for ${plannerDate.value}. ` +

            `Ask me for the subject, topic, start time, ` +

            `duration and priority.`

        );



    });





/* REFRESH EVENTS */
plannerDate.addEventListener(

    "change", loadStudyPlanner

);



document.getElementById("refresh-planner")

    .addEventListener("click", loadStudyPlanner);



document.querySelector('.nav-btn[data-page="planner"]')

    .addEventListener("click", loadStudyPlanner);





    /* =====================================
   ASTRA QUIZ AND PERFORMANCE ANALYTICS
===================================== */
pageTitles.analytics = "Quiz & Analytics";





/* LOAD REGISTERED SUBJECTS */
async function loadQuizSubjects() {



    try {



        const response = await fetch("/api/student/dashboard");



        if (!response.ok) {

            throw new Error("Unable to load subjects.");

        }



        const data = await response.json();



        const select = document.getElementById("quiz-subject");



        const previousValue = select.value;



        select.replaceChildren(

            new Option("Select subject", "")

        );



        (data.subjects || []).forEach(subject => {



            const option = new Option(

                `${subject.name} — Semester ${subject.semester}`,

                String(subject.id)

            );



            option.dataset.subject = subject.name;

            option.dataset.semester = subject.semester;



            select.add(option);



        });



        if ([...select.options].some(

            option => option.value === previousValue

        )) {

            select.value = previousValue;

        }



    } catch (error) {



        console.error(error);



    }

}





/* PERFORMANCE COLOR */
function quizPerformanceClass(accuracy) {



    if (accuracy >= 80) {

        return "performance-good";

    }



    if (accuracy >= 60) {

        return "performance-average";

    }



    return "performance-weak";

}





/* LOAD ANALYTICS DASHBOARD */
async function loadQuizAnalytics() {



    try {



        const response = await fetch("/api/quiz/analytics");



        if (!response.ok) {

            throw new Error("Unable to load analytics.");

        }



        const data = await response.json();



        const stats = data.stats;



        document.getElementById("quiz-total").textContent =

            stats.total_quizzes;



        document.getElementById("quiz-questions").textContent =

            stats.total_questions;



        document.getElementById("quiz-accuracy").textContent =

            stats.total_quizzes ? `${stats.accuracy}%` : "N/A";



        document.getElementById("quiz-weak-count").textContent =

            stats.weak_topics;





        /* SUBJECT PERFORMANCE */
        const performanceContainer =

            document.getElementById("subject-performance");



        if (!data.performance.length) {



            performanceContainer.innerHTML = `

                <div class="empty-state">

                    Complete your first quiz to see performance.

                </div>

            `;



        } else {



            performanceContainer.innerHTML =

                data.performance.map(item => `



                    <div class="performance-card">



                        <div class="performance-header">



                            <h3>

                                ${escapeHTML(item.subject)}

                                — Sem ${Number(item.semester)}

                            </h3>



                            <strong>

                                ${Number(item.accuracy)}%

                            </strong>



                        </div>



                        <div class="performance-track">



                            <div class="performance-fill

                                ${quizPerformanceClass(item.accuracy)}"

                                style="width:

                                ${Math.max(0, Math.min(100, Number(item.accuracy)))}%">

                            </div>



                        </div>



                        <p>

                            ${Number(item.quizzes)} quizzes |

                            ${Number(item.correct)}/

                            ${Number(item.questions)} correct

                        </p>



                    </div>



                `).join("");



        }





        /* WEAK TOPICS */
        const weakContainer =

            document.getElementById("weak-topics-list");



        if (!data.weak_topics.length) {



            weakContainer.innerHTML = `

                <div class="empty-state">

                    No recorded topics below 60% accuracy.

                    More assessments may be needed.

                </div>

            `;



        } else {



            weakContainer.innerHTML =

                data.weak_topics.map(item => `



                    <div class="weak-topic-card">



                        <h3>${escapeHTML(item.topic)}</h3>



                        <p>${escapeHTML(item.subject)}

                           — Sem ${Number(item.semester)}</p>



                        <p>

                            Accuracy: ${Number(item.accuracy)}%

                        </p>



                        <p>

                            Attempts: ${Number(item.attempts)}

                        </p>



                    </div>



                `).join("");



        }





        /* QUIZ HISTORY */
        const historyContainer =

            document.getElementById("quiz-history");



        if (!data.history.length) {



            historyContainer.innerHTML = `

                <div class="empty-state">

                    No quiz history available.

                </div>

            `;



        } else {



            historyContainer.innerHTML =

                data.history.map(item => `



                    <div class="quiz-history-card">



                        <h3>${escapeHTML(item.topic)}</h3>



                        <p>

                            ${escapeHTML(item.subject)}

                            | ${escapeHTML(item.difficulty)}

                        </p>



                        <div class="quiz-score">



                            ${Number(item.correct_answers)}/

                            ${Number(item.total_questions)}



                            — ${Number(item.percentage)}%



                        </div>



                        <p>

                            ${escapeHTML(item.feedback || "")}

                        </p>



                        <p>

                            ${escapeHTML(item.created_at)}

                        </p>



                        <button class="memory-delete"

                            onclick="deleteQuizResult(${Number(item.id)})">

                            Delete Result

                        </button>



                    </div>



                `).join("");



        }



    } catch (error) {



        document.getElementById("quiz-history").textContent =

            "Unable to load quiz analytics.";



        console.error(error);



    }

}





/* START AI QUIZ */
document.getElementById("start-ai-quiz")

    .addEventListener("click", async () => {



        if (sendBtn.disabled) return;



        const select =

            document.getElementById("quiz-subject");



        const selected = select.selectedOptions[0];



        const topic =

            document.getElementById("quiz-topic").value.trim();



        const difficulty =

            document.getElementById("quiz-difficulty").value;



        const count =

            document.getElementById("quiz-count").value;



        const type =

            document.getElementById("quiz-type").value;



        if (!select.value || !topic) {



            alert("Please select a subject and enter a topic.");



            return;



        }



        document.querySelector(

            '.nav-btn[data-page="chat"]'

        )?.click();



        await sendMessage(

            `Conduct a ${count}-question ${type} quiz ` +

            `on ${topic} from ${selected.dataset.subject}, ` +

            `semester ${selected.dataset.semester}. ` +

            `Difficulty: ${difficulty}. ` +

            `Ask one question at a time. ` +

            `Evaluate my answers and explain mistakes. ` +

            `At the end calculate my score and ask ` +

            `permission to save the result.`

        );



    });





/* PERSONALIZED REVISION */
document.getElementById("quiz-revision-btn")

    .addEventListener("click", async () => {



        if (sendBtn.disabled) return;



        document.querySelector(

            '.nav-btn[data-page="chat"]'

        )?.click();



        await sendMessage(

            "Retrieve my actual academic performance, " +

            "quiz history and weak topics. Create a " +

            "personalized revision strategy with subject " +

            "priorities, important concepts, practice " +

            "questions and a realistic study schedule. " +

            "Do not invent assessment records."

        );



    });





/* DELETE QUIZ RESULT */
async function deleteQuizResult(id) {



    if (!confirm("Delete this quiz result?")) {

        return;

    }



    try {



        const response = await fetch(

            `/api/quiz/result/${id}`,

            { method: "DELETE" }

        );



        if (!response.ok) {

            throw new Error("Unable to delete result.");

        }



        await loadQuizAnalytics();



    } catch (error) {



        alert(error.message);



    }

}





/* REFRESH ANALYTICS */
async function refreshQuizWorkspace() {



    await Promise.all([

        loadQuizSubjects(),

        loadQuizAnalytics()

    ]);



}



document.getElementById("refresh-analytics")

    .addEventListener("click", refreshQuizWorkspace);



document.querySelector('.nav-btn[data-page="analytics"]')

    .addEventListener("click", refreshQuizWorkspace);



    /* =====================================
   ASTRA MULTIMODAL VISION INTELLIGENCE
===================================== */
pageTitles.vision = "Vision Intelligence";



let astraVisionResult = "";



const visionButton =

    document.getElementById("analyze-screen-btn");



const visionStatus =

    document.getElementById("vision-status");



const visionResult =

    document.getElementById("vision-result");





async function runVisionAnalysis(question) {



    if (visionButton.disabled) return;



    const approved = confirm(

        "ASTRA will capture your screen and send it " +

        "to Gemini for analysis. Continue?"

    );



    if (!approved) return;



    visionButton.disabled = true;



    astraVisionResult = "";



    const delay = Number(

        document.getElementById("vision-delay").value

    );



    try {



        for (let seconds = delay; seconds > 0; seconds--) {



            visionStatus.textContent =

                `Switch to your target window. ` +

                `Capturing in ${seconds} seconds...`;



            await new Promise(

                resolve => setTimeout(resolve, 1000)

            );



        }



        visionStatus.textContent =

            "👁️ ASTRA is analyzing your screen...";



        visionResult.textContent =

            "Processing visual information...";



        const response = await fetch(

            "/api/vision/analyze",

            {

                method: "POST",



                headers: {

                    "Content-Type": "application/json"

                },



                body: JSON.stringify({

                    question: question

                })

            }

        );



        if (!response.ok) {



            throw new Error(

                "Unable to analyze the screen."

            );



        }



        const data = await response.json();



        astraVisionResult = data.response || "";



        if (window.marked && window.DOMPurify) {



            visionResult.innerHTML =

                DOMPurify.sanitize(

                    marked.parse(astraVisionResult)

                );



        } else {



            visionResult.textContent =

                astraVisionResult;



        }



        visionStatus.textContent =

            "Screen analysis request finished.";



    } catch (error) {



        visionStatus.textContent =

            "❌ Screen analysis failed.";



        visionResult.textContent =

            error.message;



    } finally {



        visionButton.disabled = false;



    }



}





/* CUSTOM SCREEN ANALYSIS */
visionButton.addEventListener("click", () => {



    const question =

        document.getElementById("vision-question")

            .value.trim();



    runVisionAnalysis(

        question ||

        "Explain what is currently visible on my screen."

    );



});





/* QUICK ANALYSIS BUTTONS */
document.querySelectorAll("[data-vision]")

    .forEach(button => {



        button.addEventListener("click", () => {



            const question = button.dataset.vision;



            document.getElementById(

                "vision-question"

            ).value = question;



            runVisionAnalysis(question);



        });



    });





/* COPY ANALYSIS */
document.getElementById("copy-vision-result")

    .addEventListener("click", async () => {



        if (!astraVisionResult) {



            alert("No analysis available.");



            return;



        }



        try {



            await navigator.clipboard.writeText(

                astraVisionResult

            );



            visionStatus.textContent =

                "✓ Analysis copied successfully.";



        } catch (error) {



            alert("Unable to copy analysis.");



        }



    });



    /* ASTRA INTELLIGENT AUTOMATION */
pageTitles.automation = "Smart Automation";



document.querySelectorAll("[data-workflow]")

    .forEach(button => {



        button.addEventListener("click", async () => {



            if (sendBtn.disabled) return;



            const command = button.dataset.workflow;



            document.querySelector(

                '.nav-btn[data-page="chat"]'

            )?.click();



            await sendMessage(command);



        });



    });



/* ASTRA LIVE BACKEND MONITORING */
async function updateAstraLiveStatus() {



    const dot = document.getElementById(

        "astra-status-dot"

    );



    const status = document.getElementById(

        "astra-status-text"

    );



    const engine = document.getElementById(

        "astra-engine-status"

    );



    if (!dot || !status || !engine) return;



    try {



        const response = await fetch("/api/health", {

            cache: "no-store",

            signal: AbortSignal.timeout(5000)

        });



        if (!response.ok) {

            throw new Error("Backend unavailable");

        }



        const data = await response.json();



        if (data.status !== "online") {

            throw new Error("Backend unhealthy");

        }



        if (data.gemini_configured) {



            dot.className = "astra-status-dot online";



            status.textContent = "ASTRA Online";



            engine.textContent = "Gemini Configured";



        } else {



            dot.className = "astra-status-dot warning";



            status.textContent = "Limited Mode";



            engine.textContent = "AI Configuration Required";



        }



    } catch (error) {



        dot.className = "astra-status-dot offline";



        status.textContent = "ASTRA Offline";



        engine.textContent = "Backend Disconnected";



    }



}



updateAstraLiveStatus();



setInterval(updateAstraLiveStatus, 10000);
// Student workspace restoration
function escapeHTML(value) {
    return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
pageTitles.student = 'Student Workspace';
async function loadStudentDashboard() {
    const subjects = document.getElementById('student-subjects');
    const assignments = document.getElementById('student-assignments');
    try {
        const response = await fetch('/api/student/dashboard', {cache:'no-store'});
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Academic data unavailable');
        document.getElementById('student-greeting').textContent = data.profile ? `Welcome, ${data.profile.name}!` : 'Welcome, Student!';
        document.getElementById('student-profile-text').textContent = data.profile ? [data.profile.course,data.profile.branch,`Semester ${data.profile.semester}`,data.profile.university].filter(Boolean).join(' • ') : 'Set up your academic profile to get started.';
        for (const key of ['subjects','pending','completed','overdue']) document.getElementById('stat-'+key).textContent = data.stats[key];
        subjects.replaceChildren();
        for (const item of data.subjects) {
            const card = document.createElement('div'); card.className='subject-card';
            card.textContent = `${item.name} • Semester ${item.semester}`; subjects.append(card);
        }
        if (!data.subjects.length) subjects.textContent='No subjects registered yet.';
        assignments.replaceChildren();
        for (const item of data.assignments) {
            const card=document.createElement('div'); card.className='assignment-card';
            const title=document.createElement('strong'); title.textContent=item.title;
            const details=document.createElement('p'); details.textContent=`${item.subject} • ${item.deadline} • ${item.urgency}`;
            card.append(title,details);
            if (item.status !== 'Completed') {
                const button=document.createElement('button'); button.className='academic-btn'; button.textContent='Mark completed';
                button.onclick=async()=>{ if(!confirm('Mark this assignment completed?')) return; button.disabled=true; try { const r=await fetch(`/api/student/assignment/${Number(item.id)}/complete`,{method:'POST'}); if(!r.ok) throw new Error('Could not complete assignment'); await loadStudentDashboard(); } catch(e){alert(e.message);button.disabled=false;} };
                card.append(button);
            }
            assignments.append(card);
        }
        if (!data.assignments.length) assignments.textContent='No assignments registered yet.';
    } catch(error) { subjects.textContent=assignments.textContent=error.message; for(const key of ['subjects','pending','completed','overdue']) document.getElementById('stat-'+key).textContent='—'; }
}
document.querySelector('.nav-btn[data-page="student"]').addEventListener('click',loadStudentDashboard);
document.getElementById('refresh-student').addEventListener('click',loadStudentDashboard);
document.querySelectorAll('#student [data-prompt]').forEach(button=>button.addEventListener('click',async()=>{
    if(sendBtn.disabled){alert('ASTRA is processing another request.');return;}
    document.querySelector('.nav-btn[data-page="chat"]').click();
    await sendMessage(button.dataset.prompt);
}));

const voiceToggle = document.getElementById("voice-toggle");
function updateVoiceToggle(){voiceToggle.textContent=localStorage.getItem("astra-voice-enabled")==="true"?"🔊 Voice Output: ON":"🔇 Voice Output: OFF";}
voiceToggle.addEventListener("click",()=>{localStorage.setItem("astra-voice-enabled",String(localStorage.getItem("astra-voice-enabled")!=="true"));updateVoiceToggle();});
updateVoiceToggle();
