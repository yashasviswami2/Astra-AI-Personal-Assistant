# 🤖 JARVIS — AI-Powered Personal Assistant

> **A desktop-based AI personal assistant built with Python, Google Gemini, voice interaction, system automation, web tools, memory, and productivity features.**

JARVIS is an intelligent personal assistant designed to interact with users through **natural voice commands and AI-powered conversations**.

It combines **Generative AI, Speech Recognition, Text-to-Speech, Desktop Automation, Web Search, File Management, Screenshot Capture, PDF Processing, Memory, and a System Tray interface** into a single assistant.

The goal of this project is to create a practical AI assistant capable of understanding natural-language commands and performing useful tasks directly on a Windows computer.

---

## ✨ Features

### 🧠 Generative AI
- Powered by **Google Gemini**
- Natural-language conversations
- Context-aware responses
- AI-powered question answering
- Intelligent command interpretation
- Dynamic tool execution

### 🎤 Voice Interaction
- Speech-to-Text using `SpeechRecognition`
- Text-to-Speech responses
- Microphone detection and calibration
- Natural voice command interaction
- Configurable microphone selection

### 🖥️ Desktop Automation

JARVIS can interact with the user's computer and perform actions such as:

- 🚀 Launch applications
- 🌐 Open websites
- 🔎 Search the web
- 📁 Browse directories
- 📄 Read text files
- ✍️ Create and modify text files
- 🗑️ Safely delete files
- 📸 Capture screenshots
- 📋 Read clipboard contents
- 📋 Update clipboard contents
- 📑 Extract and summarize PDF text

### ⏰ Time & System Tools

JARVIS can access system information and respond to commands such as:

```text
"What time is it?"
"What is the current time?"

                         ┌─────────────────────┐
                         │       USER          │
                         └──────────┬──────────┘
                                    │
                           Voice / Text Command
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │       JARVIS        │
                         │      AI AGENT       │
                         └──────────┬──────────┘
                                    │
                         ┌──────────▼──────────┐
                         │    Google Gemini    │
                         │    Generative AI    │
                         └──────────┬──────────┘
                                    │
                         Command / Tool Selection
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
             ▼                      ▼                      ▼
       Desktop Tools           Web Tools              File Tools
             │                      │                      │
             ▼                      ▼                      ▼
       App Launcher          Web Search             File Manager
       Screenshot            URL Opening            PDF Reader
       Clipboard             Page Extraction        File Operations
             │                      │                      │
             └──────────────────────┼──────────────────────┘
                                    │
                                    ▼
                           ┌─────────────────┐
                           │     Response    │
                           │   Text + Voice  │
                           └─────────────────┘
