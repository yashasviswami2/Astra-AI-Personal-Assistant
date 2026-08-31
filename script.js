// ==========================================
// JARVIS AI ASSISTANT
// ==========================================


// ==========================================
// ELEMENTS
// ==========================================

const state = document.getElementById('state');
const trans = document.getElementById('transcript');
const resp = document.getElementById('response');
const log = document.getElementById('log');
const orb = document.getElementById('orb');

const voiceBtn = document.getElementById('voiceBtn');
const aiChatBtn = document.getElementById('aiChatBtn');
const commandsBtn = document.getElementById('commandsBtn');
const aboutBtn = document.getElementById('aboutBtn');

const voicePanel = document.getElementById('voicePanel');
const aiChatPanel = document.getElementById('aiChatPanel');
const commandCenter = document.getElementById('commandCenter');
const aboutPanel = document.getElementById('aboutPanel');

const chatInput = document.getElementById('chatInput');
const chatSendBtn = document.getElementById('chatSendBtn');
const chatBox = document.getElementById('chatBox');


// ==========================================
// BACKEND
// ==========================================

const API_URL = 'http://127.0.0.1:5000';


// ==========================================
// VARIABLES
// ==========================================

let last = 'Hello! I am JARVIS.';
let rec = null;


// ==========================================
// LOGGING
// ==========================================

function addLog(title, message) {

    if (!log) return;

    log.insertAdjacentHTML(
        'afterbegin',
        `<p><b>${title}</b> — ${message}</p>`
    );
}


// ==========================================
// TEXT TO SPEECH
// ==========================================

function speak(text) {

    if (!('speechSynthesis' in window)) {
        return;
    }

    speechSynthesis.cancel();

    const utterance =
        new SpeechSynthesisUtterance(text);

    utterance.lang = 'en-IN';
    utterance.rate = 1;
    utterance.pitch = 1;

    speechSynthesis.speak(utterance);

    addLog(
        'Speech Output',
        'JARVIS is speaking the response.'
    );
}


// ==========================================
// RESPONSE
// ==========================================

function answer(text) {

    last = text;

    if (resp) {
        resp.textContent = text;
    }

    if (state) {
        state.textContent = 'RESPONSE READY';
    }

    addLog(
        'Response Ready',
        'JARVIS generated a response.'
    );
}


// ==========================================
// BACKEND COMMAND
// ==========================================

async function command(raw) {

    if (!raw || !raw.trim()) {
        return;
    }

    if (trans) {
        trans.textContent = raw;
    }

    if (state) {
        state.textContent = 'PROCESSING...';
    }

    addLog(
        'Command',
        `"${raw}"`
    );


    try {

        const response = await fetch(
            `${API_URL}/ask`,
            {
                method: 'POST',

                headers: {
                    'Content-Type': 'application/json'
                },

                body: JSON.stringify({
                    query: raw
                })
            }
        );


        if (!response.ok) {

            throw new Error(
                `Server returned ${response.status}`
            );

        }


        const data = await response.json();


        console.log(
            'JARVIS Backend Response:',
            data
        );


        if (data.response) {

            answer(data.response);

            speak(data.response);

            addLog(
                'Command Processed',
                'Request handled by JARVIS backend.'
            );

        } else {

            const message =
                'JARVIS received the request but returned no response.';

            answer(message);

            speak(message);

        }


    } catch (error) {

        console.error(
            'JARVIS Backend Error:',
            error
        );


        if (state) {
            state.textContent = 'BACKEND OFFLINE';
        }


        const message =
            'I cannot connect to my JARVIS backend. Please make sure the JARVIS server is running.';


        answer(message);

        speak(message);

    }

}


// ==========================================
// VIEW SWITCHING
// ==========================================

function hideAllPanels() {

    voicePanel.style.display = 'none';

    aiChatPanel.style.display = 'none';

    commandCenter.style.display = 'none';

    aboutPanel.style.display = 'none';


    voiceBtn.classList.remove('active');

    aiChatBtn.classList.remove('active');

    commandsBtn.classList.remove('active');

    aboutBtn.classList.remove('active');

}


function showVoiceAssistant() {

    hideAllPanels();

    voicePanel.style.display = 'block';

    voiceBtn.classList.add('active');

}


function showAIChat() {

    hideAllPanels();

    aiChatPanel.style.display = 'block';

    aiChatBtn.classList.add('active');

    chatInput.focus();

}


function showCommands() {

    hideAllPanels();

    commandCenter.style.display = 'block';

    commandsBtn.classList.add('active');

}


function showAbout() {

    hideAllPanels();

    aboutPanel.style.display = 'block';

    aboutBtn.classList.add('active');

}


// ==========================================
// SIDEBAR BUTTONS
// ==========================================

voiceBtn.addEventListener(
    'click',
    showVoiceAssistant
);


aiChatBtn.addEventListener(
    'click',
    showAIChat
);


commandsBtn.addEventListener(
    'click',
    showCommands
);


aboutBtn.addEventListener(
    'click',
    showAbout
);


// ==========================================
// AI CHAT VOICE INPUT
// ==========================================

const chatMicBtn =
    document.getElementById('chatMicBtn');


if (chatMicBtn) {

    chatMicBtn.addEventListener(
        'click',
        () => {

            const SpeechRecognition =
                window.SpeechRecognition ||
                window.webkitSpeechRecognition;


            if (!SpeechRecognition) {

                alert(
                    'Voice input requires Google Chrome.'
                );

                return;
            }


            const chatRecognition =
                new SpeechRecognition();


            chatRecognition.lang =
                'en-IN';


            chatRecognition.continuous =
                false;


            chatRecognition.interimResults =
                false;


            chatMicBtn.classList.add(
                'listening'
            );


            chatInput.placeholder =
                'Listening...';


            chatRecognition.onstart =
                () => {

                    chatMicBtn.classList.add(
                        'listening'
                    );

                    chatInput.placeholder =
                        'Listening...';

                };


            chatRecognition.onresult =
                (event) => {

                    const text =
                        event
                            .results[0][0]
                            .transcript;


                    chatInput.value =
                        text;


                    chatInput.placeholder =
                        'Ask JARVIS anything...';


                    chatMicBtn.classList.remove(
                        'listening'
                    );


                    chatInput.focus();


                    // ==================================
                    // AUTOMATICALLY SEND VOICE QUERY
                    // ==================================

                    setTimeout(
                        () => {

                            sendChatMessage();

                        },
                        300
                    );

                };


            chatRecognition.onerror =
                (event) => {

                    console.error(
                        'AI Chat voice error:',
                        event.error
                    );


                    chatMicBtn.classList.remove(
                        'listening'
                    );


                    chatInput.placeholder =
                        'Ask JARVIS anything...';

                };


            chatRecognition.onend =
                () => {

                    chatMicBtn.classList.remove(
                        'listening'
                    );


                    chatInput.placeholder =
                        'Ask JARVIS anything...';

                };


            try {

                chatRecognition.start();

            } catch (error) {

                console.error(
                    'Could not start chat recognition:',
                    error
                );

                chatMicBtn.classList.remove(
                    'listening'
                );

                chatInput.placeholder =
                    'Ask JARVIS anything...';

            }

        }
    );

}


// ==========================================
// MICROPHONE
// ==========================================

const micButton =
    document.getElementById('micBtn');


if (micButton) {

    micButton.onclick = () => {

        const SpeechRecognition =
            window.SpeechRecognition ||
            window.webkitSpeechRecognition;


        if (!SpeechRecognition) {

            state.textContent =
                'USE GOOGLE CHROME';

            trans.textContent =
                'Speech recognition requires Google Chrome.';

            return;

        }


        rec =
            new SpeechRecognition();


        rec.lang =
            'en-IN';


        rec.continuous =
            false;


        rec.interimResults =
            false;


        rec.onstart = () => {

            state.textContent =
                'LISTENING...';


            orb.classList.add(
                'listening'
            );


            addLog(
                'Listening',
                'Waiting for your voice command.'
            );

        };


        rec.onresult = (event) => {

            const text =
                event
                    .results[0][0]
                    .transcript;


            command(text);

        };


        rec.onerror = (event) => {

            console.error(
                'Speech recognition error:',
                event.error
            );


            state.textContent =
                'VOICE ERROR';


            orb.classList.remove(
                'listening'
            );

        };


        rec.onend = () => {

            orb.classList.remove(
                'listening'
            );


            if (
                state.textContent ===
                'LISTENING...'
            ) {

                state.textContent =
                    'READY';

            }

        };


        try {

            rec.start();

        } catch (error) {

            console.error(
                'Could not start microphone:',
                error
            );

        }

    };

}


// ==========================================
// SPEAK BUTTON
// ==========================================

const speakButton =
    document.getElementById('speakBtn');


if (speakButton) {

    speakButton.onclick = () => {

        if (last) {

            speak(last);

        }

    };

}


// ==========================================
// QUICK COMMANDS
// ==========================================

document
    .querySelectorAll('[data-q]')
    .forEach(button => {

        button.onclick = () => {

            command(
                button.dataset.q
            );

        };

    });


// ==========================================
// COMMAND CENTER ACTIONS
// ==========================================

document
    .querySelectorAll('.command-action')
    .forEach(button => {

        button.addEventListener(
            'click',
            () => {

                const commandText =
                    button.dataset.command;


                if (commandText) {

                    command(
                        commandText
                    );

                }

            }
        );

    });


// ==========================================
// AI CHAT
// ==========================================

async function sendChatMessage() {

    const message =
        chatInput.value.trim();


    if (!message) {
        return;
    }


    // ==================================
    // USER MESSAGE
    // ==================================

    chatBox.insertAdjacentHTML(
        'beforeend',

        `
        <div class="chat-message user-message">

            <strong>YOU</strong>

            <p>${message}</p>

        </div>
        `
    );


    chatInput.value = '';


    // ==================================
    // THINKING MESSAGE
    // ==================================

    const thinking =
        document.createElement('div');


    thinking.className =
        'chat-message jarvis-message';


    thinking.innerHTML = `

        <strong>JARVIS</strong>

        <p>Thinking...</p>

    `;


    chatBox.appendChild(
        thinking
    );


    chatBox.scrollTop =
        chatBox.scrollHeight;


    try {

        const response =
            await fetch(

                `${API_URL}/ask`,

                {

                    method: 'POST',

                    headers: {

                        'Content-Type':
                            'application/json'

                    },

                    body: JSON.stringify({

                        query: message

                    })

                }

            );


        if (!response.ok) {

            throw new Error(
                `Server returned ${response.status}`
            );

        }


        const data =
            await response.json();


        thinking.remove();


        const reply =
            data.response ||
            'Sorry, I could not generate a response.';


        // ==================================
        // JARVIS MESSAGE
        // ==================================

        chatBox.insertAdjacentHTML(
            'beforeend',

            `
            <div class="chat-message jarvis-message">

                <strong>JARVIS</strong>

                <p>${reply}</p>

            </div>
            `
        );


        // ==================================
        // SPEAK RESPONSE
        // ==================================

        speak(reply);


        chatBox.scrollTop =
            chatBox.scrollHeight;


    } catch (error) {

    console.error(
        'AI Chat Error:',
        error
    );

    thinking.innerHTML = `

        <strong>JARVIS</strong>

        <p>
            Sorry, I could not process that request.
            Please check the JARVIS backend.
        </p>

    `;

    addLog(
        'AI Chat Error',
        error.message || 'Unknown backend error.'
    );

    chatBox.scrollTop =
        chatBox.scrollHeight;
}




// ==========================================
// CHAT SEND BUTTON
// ==========================================

chatSendBtn.addEventListener(
    'click',
    sendChatMessage
);


// ==========================================
// ENTER TO SEND
// ==========================================

chatInput.addEventListener(
    'keydown',
    event => {

        if (event.key === 'Enter') {

            event.preventDefault();

            sendChatMessage();

        }

    }
);


// ==========================================
// START WITH VOICE ASSISTANT
// ==========================================

// Start on AI Chat view
showAIChat();
}