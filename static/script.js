// ==========================================
// APPLICATION STATE & HTML ELEMENTS
// ==========================================

const userInput = document.getElementById("userInput");
const chatMessages = document.getElementById("chatMessages");
const clearChatBtn = document.getElementById("clearChatBtn");
const micBtn = document.getElementById("micBtn");
const voiceIndicator = document.getElementById("voiceIndicator");
const languageSelect = document.getElementById("languageSelect");

let chatHistory = [];
let currentLanguage = "en";
let recognition = null;
let isRecording = false;

// ==========================================
// MULTILINGUAL I18N DICTIONARY
// ==========================================

const i18n = {
    en: {
        main_title: "Health Prediction & Hospital Assistant",
        main_subtitle: "Intelligent Patient Navigation & Symptom Assessment",
        assistant: "AI Assistant",
        symptom_checker: "Symptom Checker",
        floor_map: "Floor Map",
        departments: "Departments",
        medicines: "Pharmacy (Room 50)",
        appointments: "OPD Registration",
        emergency: "Emergency SOS",
        clear_chat: "Clear Chat",
        welcome_text: "Namaste! Welcome to **Government General Hospital (Pedda Hospital), Kurnool**. I am your Healthcare Information & Navigation Assistant. How can I guide you today?",
        card1_title: "Cold, Fever & Flu",
        card1_desc: "Find initial consultation rooms for general cold, cough or fever.",
        card2_title: "Medicine & Pharmacy",
        card2_desc: "Locate Room 50 Pharmacy, dispensing guidance and precautions.",
        card3_title: "Heart & Chest Care",
        card3_desc: "Cardiology (Room 25), ECG (Room 46), and heart evaluation.",
        card4_title: "Hospital Directory",
        card4_desc: "View all 8 verified department room numbers and contacts.",
        placeholder: "Ask about symptoms, departments, room numbers...",
        speaking: "🔊 Reading out loud...",
        listen_btn: "🔊 Listen",
        print_btn: "🖨️ Print Slip"
    },
    te: {
        main_title: "ఆరోగ్య సహాయకుడు & ఆసుపత్రి నావిగేషన్",
        main_subtitle: "ప్రభుత్వ సాధారణ ఆసుపత్రి (పెద్ద ఆసుపత్రి), కర్నూలు",
        assistant: "AI సహాయకుడు",
        symptom_checker: "లక్షణాల పరీక్ష",
        floor_map: "ఆసుపత్రి మ్యాప్",
        departments: "విభాగాలు",
        medicines: "ఫార్మసీ (రూమ్ 50)",
        appointments: "OPD రిజిస్ట్రేషన్",
        emergency: "అత్యవసర SOS",
        clear_chat: "చాట్ క్లియర్",
        welcome_text: "నమస్కారం! **ప్రభుత్వ జనరల్ ఆసుపత్రి (పెద్ద ఆసుపత్రి), కర్నూలు** కి స్వాగతం. నేను మీ ఆసుపత్రి మార్గదర్శక సహాయకుడిని. మీకు ఎలా సహాయపడగలను?",
        card1_title: "జలుబు, జ్వరం & దగ్గు",
        card1_desc: "జలుబు మరియు జ్వరానికి జనరల్ మెడిసిన్ (రూమ్ 12) వివరాలు.",
        card2_title: "మందులు & ఫార్మసీ",
        card2_desc: "రూమ్ 50 ఫార్మసీ మందుల పంపిణీ వివరాలు.",
        card3_title: "గుండె & ఛాతీ సంరక్షణ",
        card3_desc: "కార్డియాలజీ (రూమ్ 25), ECG (రూమ్ 46) వివరాలు.",
        card4_title: "ఆసుపత్రి గదుల వివరాలు",
        card4_desc: "అన్ని 8 విభాగాల గదుల నంబర్లు మరియు ఫోన్ నంబర్లు.",
        placeholder: "లక్షణాలు, గది నంబర్లు లేదా సేవల గురించి అడగండి...",
        speaking: "🔊 చదువుతోంది...",
        listen_btn: "🔊 వినండి",
        print_btn: "🖨️ స్లిప్ ప్రింట్"
    },
    hi: {
        main_title: "स्वास्थ्य सहायक एवं अस्पताल मार्गदर्शन",
        main_subtitle: "राजकीय सामान्य चिकित्सालय (बड़ा अस्पताल), कुरनूल",
        assistant: "AI सहायक",
        symptom_checker: "लक्षण जांच",
        floor_map: "अस्पताल का नक्शा",
        departments: "विभाग",
        medicines: "दवाखाना (कमरा 50)",
        appointments: "ओपीडी पंजीकरण",
        emergency: "आपातकालीन SOS",
        clear_chat: "चैट साफ़ करें",
        welcome_text: "नमस्ते! **राजकीय सामान्य चिकित्सालय (बड़ा अस्पताल), कुरनूल** में आपका स्वागत है। मैं आपका स्वास्थ्य एवं अस्पताल मार्गदर्शन सहायक हूँ। मैं आपकी क्या मदद कर सकता हूँ?",
        card1_title: "सर्दी, बुखार और फ्लू",
        card1_desc: "सामान्य सर्दी, खांसी या बुखार के लिए परामर्श कक्ष जानें।",
        card2_title: "दवा और फार्मेसी",
        card2_desc: "कमरा 50 फार्मेसी और दवा वितरण नियम जानें।",
        card3_title: "हृदय एवं छाती देखभाल",
        card3_desc: "कार्डियोलॉजी (कमरा 25) और ईसीजी (कमरा 46) की जानकारी।",
        card4_title: "अस्पताल निर्देशिका",
        card4_desc: "सभी 8 सत्यापित कमरों और संपर्कों की सूची देखें।",
        placeholder: "लक्षण, कमरा नंबर या विभाग के बारे में पूछें...",
        speaking: "🔊 पढ़ रहा है...",
        listen_btn: "🔊 सुनें",
        print_btn: "🖨️ पर्ची प्रिंट"
    }
};

function changeLanguage(lang) {
    currentLanguage = lang;
    const t = i18n[lang] || i18n.en;

    document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (t[key]) el.innerHTML = t[key];
    });

    if (userInput) userInput.placeholder = t.placeholder;
}


// ==========================================
// MARKDOWN RENDERING
// ==========================================

function renderMarkdown(text) {
    if (!text) return "";
    if (typeof marked !== "undefined" && marked.parse) {
        try {
            return marked.parse(text);
        } catch (e) {
            console.warn("Markdown parse fallback:", e);
        }
    }
    return `<p>${escapeHTML(text).replace(/\n/g, "<br>")}</p>`;
}


// ==========================================
// SEND MESSAGE
// ==========================================

async function sendMessage() {
    const message = userInput.value.trim();
    if (message === "") return;

    addUserMessage(message);
    userInput.value = "";

    const thinkingMessage = addBotMessage("Thinking...", false, true);

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: message,
                history: chatHistory,
                language: currentLanguage
            })
        });

        const data = await response.json();
        const botReply = data.response || "No response received.";

        const textContainer = thinkingMessage.querySelector(".bot-text");
        if (textContainer) {
            textContainer.innerHTML = renderMarkdown(botReply);
        }

        // Add action buttons (Speaker & Print Slip)
        addActionButtonsToMessage(thinkingMessage, botReply);

        chatHistory.push({ user: message, assistant: botReply });
        if (chatHistory.length > 10) chatHistory.shift();

    } catch (error) {
        console.error("Error sending message:", error);
        const textContainer = thinkingMessage.querySelector(".bot-text");
        if (textContainer) {
            textContainer.innerHTML =
                "<p style='color: #c62828;'>⚠️ Sorry, could not process your question right now.</p>";
        }
    }

    scrollToBottom();
}


// ==========================================
// ADD USER MESSAGE
// ==========================================

function addUserMessage(message) {
    const messageDiv = document.createElement("div");
    messageDiv.className = "user-message";
    messageDiv.innerHTML = `
        <div class="message-content">
            <strong>You</strong>
            <p>${escapeHTML(message)}</p>
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}


// ==========================================
// ADD BOT MESSAGE
// ==========================================

function addBotMessage(message, isRawText = false, isThinking = false) {
    const messageDiv = document.createElement("div");
    messageDiv.className = "bot-message";

    const contentHTML = isThinking
        ? `<p class="thinking-text"><em>Thinking...</em></p>`
        : (isRawText ? `<p>${escapeHTML(message)}</p>` : renderMarkdown(message));

    messageDiv.innerHTML = `
        <div class="bot-avatar">🤖</div>
        <div class="message-content">
            <div class="msg-header">
                <strong>GGH Health Assistant</strong>
                <span class="verified-tag">✓ Hospital Verified</span>
            </div>
            <div class="bot-text">${contentHTML}</div>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    scrollToBottom();

    if (!isThinking) {
        addActionButtonsToMessage(messageDiv, message);
    }

    return messageDiv;
}

function addActionButtonsToMessage(msgElement, text) {
    const content = msgElement.querySelector(".message-content");
    if (!content || content.querySelector(".msg-actions")) return;

    const t = i18n[currentLanguage] || i18n.en;
    const actionsDiv = document.createElement("div");
    actionsDiv.className = "msg-actions";

    actionsDiv.innerHTML = `
        <button class="msg-action-btn" onclick="speakText(this)">${t.listen_btn}</button>
        <button class="msg-action-btn" onclick="extractAndPrintSlip(this)">${t.print_btn}</button>
        <button class="msg-action-btn" onclick="openMapModal()">🗺️ View on Map</button>
    `;

    // Store raw text for text-to-speech
    actionsDiv.dataset.speechText = stripMarkdown(text);
    content.appendChild(actionsDiv);
}


// ==========================================
// TEXT-TO-SPEECH (TTS)
// ==========================================

function speakText(btn) {
    const actionsDiv = btn.closest(".msg-actions");
    const rawText = actionsDiv ? actionsDiv.dataset.speechText : "";
    if (!rawText) return;

    if (!("speechSynthesis" in window)) {
        alert("Text-to-speech is not supported in this browser.");
        return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(rawText);
    if (currentLanguage === "te") {
        utterance.lang = "te-IN";
    } else if (currentLanguage === "hi") {
        utterance.lang = "hi-IN";
    } else {
        utterance.lang = "en-IN";
    }

    utterance.rate = 0.95;
    btn.innerHTML = "🔊 Playing...";
    utterance.onend = () => {
        const t = i18n[currentLanguage] || i18n.en;
        btn.innerHTML = t.listen_btn;
    };
    utterance.onerror = () => {
        const t = i18n[currentLanguage] || i18n.en;
        btn.innerHTML = t.listen_btn;
    };

    window.speechSynthesis.speak(utterance);
}

function stripMarkdown(text) {
    return text
        .replace(/[*#_`~>|]/g, "")
        .replace(/\n+/g, " ")
        .trim();
}


// ==========================================
// SPEECH-TO-TEXT (VOICE INPUT)
// ==========================================

function toggleVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        alert("Speech Recognition is not supported by your browser. Please use Chrome, Edge, or Safari.");
        return;
    }

    if (isRecording) {
        stopVoiceInput();
        return;
    }

    try {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        if (currentLanguage === "te") {
            recognition.lang = "te-IN";
        } else if (currentLanguage === "hi") {
            recognition.lang = "hi-IN";
        } else {
            recognition.lang = "en-IN";
        }

        recognition.onstart = function () {
            isRecording = true;
            if (micBtn) micBtn.classList.add("listening");
            if (voiceIndicator) voiceIndicator.classList.remove("hidden");
        };

        recognition.onresult = function (event) {
            const transcript = event.results[0][0].transcript;
            userInput.value = transcript;
            stopVoiceInput();
            // Automatically send the voice input
            setTimeout(() => sendMessage(), 300);
        };

        recognition.onerror = function (event) {
            console.warn("Speech recognition error:", event.error);
            stopVoiceInput();
        };

        recognition.onend = function () {
            stopVoiceInput();
        };

        recognition.start();

    } catch (e) {
        console.error("Mic initialization error:", e);
        stopVoiceInput();
    }
}

function stopVoiceInput() {
    isRecording = false;
    if (recognition) {
        try { recognition.stop(); } catch (e) { }
    }
    if (micBtn) micBtn.classList.remove("listening");
    if (voiceIndicator) voiceIndicator.classList.add("hidden");
}


// ==========================================
// SYMPTOM CHECKER TRIAGE
// ==========================================

async function runSymptomCheck() {
    const selected = Array.from(document.querySelectorAll('input[name="sym"]:checked')).map(c => c.value);
    const duration = document.getElementById("symDuration").value;
    const severity = document.getElementById("symSeverity").value;

    if (selected.length === 0) {
        alert("Please select at least one symptom.");
        return;
    }

    const resBox = document.getElementById("symptomResult");
    resBox.classList.remove("hidden");

    try {
        const response = await fetch("/api/symptom-check", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                symptoms: selected,
                duration: duration,
                severity: severity,
                language: currentLanguage
            })
        });

        const data = await response.json();

        const badge = document.getElementById("riskBadge");
        badge.textContent = `Risk: ${data.risk_level}`;
        badge.style.backgroundColor = data.color + "22";
        badge.style.color = data.color;

        document.getElementById("destRoom").textContent = data.room;
        document.getElementById("destDept").textContent = data.department;
        document.getElementById("destGuidance").textContent = data.guidance;

        // Cache for printing
        resBox.dataset.dept = data.department;
        resBox.dataset.room = data.room;
        resBox.dataset.symptoms = selected.join(", ");

    } catch (e) {
        console.error("Symptom check error:", e);
        document.getElementById("destGuidance").textContent =
            "General Medicine (Room 12) is recommended for initial consultation.";
    }
}

function printOPDSlipFromSymptom() {
    const resBox = document.getElementById("symptomResult");
    const dept = resBox.dataset.dept || "General Medicine";
    const room = resBox.dataset.room || "Room 12";
    const symptoms = resBox.dataset.symptoms || "General Checkup";
    printOPDSlip(symptoms, dept, room);
}

function askSymptomInChat() {
    const resBox = document.getElementById("symptomResult");
    const dept = resBox.dataset.dept || "General Medicine";
    const room = resBox.dataset.room || "Room 12";
    closeModal("symptomModal");
    useSuggestion(`Tell me more about ${dept} in ${room}`);
}


// ==========================================
// PRINT PATIENT OPD SLIP
// ==========================================

function printOPDSlip(symptoms, department, room) {
    document.getElementById("slipDate").textContent = new Date().toLocaleString();
    document.getElementById("slipSymptoms").textContent = symptoms;
    document.getElementById("slipDept").textContent = department;
    document.getElementById("slipRoom").textContent = room.toUpperCase();

    window.print();
}

function extractAndPrintSlip(btn) {
    const actionsDiv = btn.closest(".msg-actions");
    const text = actionsDiv ? actionsDiv.dataset.speechText : "";

    let room = "Room 12";
    let dept = "General Medicine";

    if (text.includes("Room 25") || text.includes("Cardiology")) {
        room = "Room 25"; dept = "Cardiology";
    } else if (text.includes("Room 18") || text.includes("ENT")) {
        room = "Room 18"; dept = "ENT (Ear, Nose, Throat)";
    } else if (text.includes("Room 30") || text.includes("Orthopaedics")) {
        room = "Room 30"; dept = "Orthopaedics";
    } else if (text.includes("Room 50") || text.includes("Pharmacy")) {
        room = "Room 50"; dept = "Hospital Pharmacy";
    } else if (text.includes("Room 5") || text.includes("Emergency")) {
        room = "Room 5"; dept = "Emergency & Trauma";
    } else if (text.includes("Room 45") || text.includes("Laboratory")) {
        room = "Room 45"; dept = "Diagnostic Laboratory";
    } else if (text.includes("Room 46") || text.includes("ECG")) {
        room = "Room 46"; dept = "ECG Room";
    }

    printOPDSlip("Hospital Outpatient Guidance", dept, room);
}


// ==========================================
// FLOOR MAP VISUALIZER
// ==========================================

function switchFloor(floor) {
    document.querySelectorAll(".floor-tab").forEach(t => t.classList.remove("active"));
    event.target.classList.add("active");

    const fg = document.getElementById("floorGround");
    const ff = document.getElementById("floorFirst");
    const fs = document.getElementById("floorSecond");

    if (floor === "all") {
        fg.style.display = "block";
        ff.style.display = "block";
        fs.style.display = "block";
    } else if (floor === "ground") {
        fg.style.display = "block";
        ff.style.display = "none";
        fs.style.display = "none";
    } else if (floor === "first") {
        fg.style.display = "none";
        ff.style.display = "block";
        fs.style.display = "none";
    } else if (floor === "second") {
        fg.style.display = "none";
        ff.style.display = "none";
        fs.style.display = "block";
    }
}

function selectRoom(roomNum, name, location) {
    document.querySelectorAll(".room-card").forEach(c => c.classList.remove("highlighted"));
    const card = document.getElementById(`roomCard${roomNum}`);
    if (card) card.classList.add("highlighted");

    const info = document.getElementById("mapSelectionInfo");
    info.innerHTML = `
        <strong>📍 Room ${roomNum} — ${name}</strong><br>
        <span><strong>Location:</strong> ${location}</span><br>
        <span><strong>Directions:</strong> Enter from main gate, follow the signage boards for ${name}. Token required at entry.</span>
    `;
}


// ==========================================
// DEPARTMENTS FILTER
// ==========================================

function filterDepartments(query) {
    const q = query.toLowerCase();
    const items = document.querySelectorAll(".dept-item");
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(q) ? "flex" : "none";
    });
}

function askAboutRoom(dept, room) {
    closeModal("deptModal");
    useSuggestion(`Which room is ${dept} and what are the services?`);
}


// ==========================================
// MODAL CONTROLS
// ==========================================

function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.remove("hidden");
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add("hidden");
}

function closeAllModals() {
    document.querySelectorAll(".modal-backdrop").forEach(m => m.classList.add("hidden"));
}

function openSymptomModal() { openModal("symptomModal"); }
function openMapModal() { openModal("mapModal"); }
function openEmergencyModal() { openModal("emergencyModal"); }
function openDeptModal() { openModal("deptModal"); }
function openPharmacyModal() { openModal("pharmacyModal"); }
function openAppointmentsModal() { openModal("appointmentsModal"); }

// Close modals when clicking backdrop
document.addEventListener("click", function (e) {
    if (e.target.classList.contains("modal-backdrop")) {
        e.target.classList.add("hidden");
    }
});


// ==========================================
// CHAT UTILITIES
// ==========================================

function handleEnter(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
}

function useSuggestion(message) {
    userInput.value = message;
    userInput.focus();
    sendMessage();
}

if (clearChatBtn) {
    clearChatBtn.addEventListener("click", async function () {
        try {
            await fetch("/clear-chat", { method: "POST" });
        } catch (e) { }

        chatHistory = [];
        chatMessages.innerHTML = "";
        const t = i18n[currentLanguage] || i18n.en;
        addBotMessage(t.welcome_text);
    });
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHTML(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}