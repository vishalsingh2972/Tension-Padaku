import os
import re
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

from google import genai

# Synchronize API keys for both google-genai and langchain-google-genai
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if api_key:
    os.environ["GEMINI_API_KEY"] = api_key
    os.environ["GOOGLE_API_KEY"] = api_key

# ============================================================
# CONFIGURATION
# ============================================================

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "ggh_kurnool"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# Global vector store cache
_vector_store = None


# ============================================================
# INITIALIZE VECTOR DATABASE & EMBEDDINGS (LAZY)
# ============================================================

def get_gemini_client():
    """Returns an authenticated genai.Client or None if no API key is set."""
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        return None
    try:
        return genai.Client(api_key=key)
    except Exception as e:
        print("Error creating Gemini client:", e)
        return None


def get_vector_store():
    """Lazily initializes and returns the Chroma vector store."""
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        print("Warning: GEMINI_API_KEY is not set. Vector store not initialized.")
        return None

    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=key
        )
        _vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=CHROMA_PATH
        )
        return _vector_store
    except Exception as e:
        print("ChromaDB initialization error:", e)
        return None


# ============================================================
# BUILD DATABASE
# ============================================================

def build_database():
    """Loads text documents from knowledge_base and builds ChromaDB."""
    store = get_vector_store()
    if store is None:
        print("Cannot build database: GEMINI_API_KEY is not set. Please configure .env.")
        return

    existing_documents = store.get()

    if existing_documents and existing_documents.get("ids"):
        print("ChromaDB already contains documents.")
        print("Skipping document insertion.")
        return

    if not os.path.exists("knowledge_base"):
        print("Knowledge base folder 'knowledge_base' not found.")
        return

    loader = DirectoryLoader(
        "knowledge_base",
        glob="*.txt",
        loader_cls=TextLoader
    )

    documents = loader.load()
    print("Documents loaded:", len(documents))

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = text_splitter.split_documents(documents)
    print("Chunks created:", len(chunks))

    store.add_documents(chunks)
    print("Documents added to ChromaDB successfully.")


# ============================================================
# REWRITE FOLLOW-UP QUESTION
# ============================================================

def rewrite_question(question, chat_history):
    """Rewrites follow-up questions using conversation context."""
    if not chat_history:
        return question

    history_text = ""
    for message in chat_history:
        user_text = message.get("user", "")
        bot_text = message.get("assistant", "")
        history_text += f"User: {user_text}\nAssistant: {bot_text}\n\n"

    client = get_gemini_client()
    if client is None:
        return question

    prompt = f"""
You are helping a hospital information chatbot.

The user may ask follow-up questions such as:
- Which room?
- Where is it?
- What about that?
- Is it available?
- What is the number?

Use the conversation history to understand what the user is referring to.

Rewrite the current question into a complete, standalone question.

Do NOT answer the question.
Do NOT add information that is not present in the conversation.

Conversation history:
{history_text}

Current question:
{question}

Return ONLY the rewritten question.
"""

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        rewritten_question = response.text.strip()
        print("\nOriginal question:", question)
        print("Rewritten question:", rewritten_question)
        return rewritten_question
    except Exception as e:
        print("Question rewriting error:", e)
        return question


# ============================================================
# OFFLINE KNOWLEDGE-BASE MATCHER (WORKS WITHOUT API KEY)
# ============================================================

def _search_text_files_fallback(question):
    """Scans text files in knowledge_base folder and extracts matching paragraphs."""
    kb_dir = "knowledge_base"
    if not os.path.exists(kb_dir):
        return (
            "I could not find verified hospital records in the project.\n\n"
            "*(ℹ️ Running in Offline Knowledge-Base mode. Add `GEMINI_API_KEY` in `.env` for generative AI.)*"
        )

    words = set(re.findall(r"\w+", question.lower()))
    stop = {"i", "have", "a", "an", "the", "and", "or", "which", "where", "what", "is", "should", "go", "to", "my", "in", "for", "at", "please", "tell", "me", "about"}
    keywords = words - stop

    best_score = 0
    best_passage = ""
    best_title = ""

    for filename in os.listdir(kb_dir):
        if not filename.endswith(".txt"):
            continue
        filepath = os.path.join(kb_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        blocks = content.split("\n\n")
        for block in blocks:
            b_clean = block.strip()
            if not b_clean or len(b_clean) < 15:
                continue
            b_words = set(re.findall(r"\w+", b_clean.lower()))
            overlap = len(keywords & b_words)
            if overlap > best_score:
                best_score = overlap
                best_passage = b_clean
                best_title = filename.replace("_", " ").replace(".txt", "").title()

    if best_score > 0 and best_passage:
        return (
            f"### 🏥 Information from Hospital Records ({best_title})\n\n"
            f"{best_passage}\n\n"
            f"> **Note:** For medical emergencies, please visit **Emergency (Room 5)** or call **108**.\n\n"
            f"*(ℹ️ Running in Offline Knowledge-Base mode. Add `GEMINI_API_KEY` in `.env` for full conversational AI.)*"
        )

    return (
        "### 🏥 Government General Hospital (GGH), Kurnool\n\n"
        "I could not find verified information for that specific query in current hospital records.\n\n"
        "**Available Departments & Rooms:**\n"
        "* **General Medicine:** Room 12 (Cold, fever, headaches, initial checkup)\n"
        "* **Cardiology:** Room 25 (Heart & chest conditions)\n"
        "* **ENT:** Room 18 (Ear, nose, throat)\n"
        "* **Orthopaedics:** Room 30 (Bone & joint problems)\n"
        "* **Emergency:** Room 5 (24/7 Urgent care, Ambulance: 108)\n"
        "* **Pharmacy:** Room 50 | **Laboratory:** Room 45 | **ECG:** Room 46\n\n"
        "*(ℹ️ Running in Offline Knowledge-Base mode. Add `GEMINI_API_KEY` in `.env` for full conversational AI.)*"
    )


def offline_knowledge_base_search(question, language="en"):
    """Answers hospital navigation and health queries using local verified documents."""
    q_lower = question.lower()

    is_cold = any(w in q_lower for w in ["cold", "cough", "fever", "flu", "sneeze", "headache", "body pain", "vomit", "nausea", "temperature", "జలుబు", "దగ్గు", "జ్వరం", "తలనొప్పి", "सर्दी", "खांसी", "बुखार", "सिरदर्द"])
    is_ent = any(w in q_lower for w in ["ent", "ear", "nose", "throat", "tonsil", "sinus", "hearing", "nasal", "గొంతు", "చెవి", "ముక్కు", "गला", "कान", "नाक"])
    is_chest = any(w in q_lower for w in ["chest", "heart", "cardio", "cardiology", "bp", "blood pressure", "hypertension", "palpitation", "గుండె", "ఛాతీ", "दिल", "छाती", "हृदय"])
    is_ortho = any(w in q_lower for w in ["ortho", "bone", "joint", "fracture", "leg", "knee", "back pain", "musculoskeletal", "spine", "ఎముక", "కీళ్ళు", "నడుము నొప్పి", "हड्डी", "जोड़"])
    is_lab = any(w in q_lower for w in ["lab", "laboratory", "blood test", "urine", "test", "scan", "report", "రక్త పరీక్ష", "ల్యాబ్", "खून जांच", "लैब"])
    is_ecg = any(w in q_lower for w in ["ecg", "electrocardiogram", "ఈసీజీ"])
    is_pharmacy = any(w in q_lower for w in ["pharmacy", "medicine", "tablet", "syrup", "prescription", "drug", "మందులు", "ఫార్మసీ", "दवा", "दवाएं", "फार्मेसी"])
    is_emergency = any(w in q_lower for w in ["emergency", "urgent", "accident", "bleeding", "unconscious", "stroke", "severe", "అత్యవసర", "ప్రమాదం", "ఆపద", "आपातकालीन", "दुर्घटना"])
    is_all_rooms = any(w in q_lower for w in ["all rooms", "list rooms", "which rooms", "room numbers", "departments", "రూములు", "గదులు", "कमरे"])
    is_hospital_info = any(w in q_lower for w in ["location", "address", "where is", "pedda hospital", "hospital name", "contact", "phone", "number", "ఎక్కడ", "చిరునామా", "पता", "कहाँ"])
    is_doctor = any(w in q_lower for w in ["doctor", "timings", "opd", "appointment", "schedule", "fee", "cost", "డాక్టర్", "సమయం", "डॉक्टर", "समय"])

    # 1. Cold / Flu / Fever
    if is_cold:
        if language == "te":
            return (
                "### 🏥 జలుబు, జ్వరం మరియు సాధారణ అనారోగ్యం మార్గదర్శకం\n\n"
                "**ప్రభుత్వ జనరల్ ఆసుపత్రి (GGH), కర్నూలు** లో సంప్రదించవలసిన విభాగాలు:\n\n"
                "* **జనరల్ మెడిసిన్ — రూమ్ 12** (ప్రాథమిక వైద్య పరీక్ష కోసం)\n"
                "* **ENT (చెవి, ముక్కు, గొంతు) — రూమ్ 18** (గొంతు నొప్పి, చెవి నొప్పి లేదా ముక్కు సమస్యలకు)\n\n"
                "> **గమనిక:** ఇది ఆసుపత్రి మార్గదర్శకం మాత్రమే, వైద్య నిర్ధారణ కాదు. శ్వాస ఆడకపోవడం లేదా తీవ్రమైన సమస్య ఉంటే **ఎమర్జెన్సీ (రూమ్ 5)** కి వెళ్లండి లేదా **108** కి కాల్ చేయండి."
            )
        elif language == "hi":
            return (
                "### 🏥 सर्दी, बुखार एवं सामान्य बीमारी मार्गदर्शन\n\n"
                "**राजकीय सामान्य चिकित्सालय (GGH), कुरनूल** में परामर्श कक्ष:\n\n"
                "* **जनरल मेडिसिन — कमरा 12** (प्राथमिक चिकित्सकीय जांच हेतु)\n"
                "* **ईएनटी (कान, नाक, गला) — कमरा 18** (गले या नाक के लक्षणों हेतु)\n\n"
                "> **नोट:** यह अस्पताल मार्गदर्शन मात्र है। गंभीर लक्षणों या सांस लेने में तकलीफ पर तुरंत **इमरजेंसी (कमरा 5)** जाएं या **108** पर कॉल करें।"
            )

        ans = (
            "### 🏥 Department & Room Guidance for Cold / General Illness\n\n"
            "For a cold, fever, cough, or general illness at **Government General Hospital (GGH), Kurnool**, please proceed to:\n\n"
            "* **General Medicine — Room 12** (Recommended for initial medical evaluation)\n"
        )
        if is_ent or "cough" in q_lower or "throat" in q_lower:
            ans += "* **ENT (Ear, Nose & Throat) — Room 18** (Recommended if you have throat soreness, ear pain, or nasal congestion)\n\n"
        else:
            ans += "* **ENT (Ear, Nose & Throat) — Room 18** (Consult if symptoms involve ear, nose, or throat irritation)\n\n"
        ans += (
            "> **Note:** This information is general hospital navigation guidance and not a medical diagnosis. "
            "If symptoms worsen or you experience severe difficulty breathing, please seek immediate care at **Emergency (Room 5)** or call **108**.\n\n"
            "*(ℹ️ Running in Offline Knowledge-Base mode. Add `GEMINI_API_KEY` in `.env` for generative AI responses.)*"
        )
        return ans

    # 2. Ear, Nose, Throat (ENT)
    if is_ent:
        return (
            "### 🏥 ENT Department Information\n\n"
            "For ear, nose, or throat-related problems at GGH Kurnool:\n\n"
            "* **ENT (Ear, Nose, Throat): Room 18**\n"
            "* **General Medicine: Room 12** (for viral flu or systemic symptoms)\n\n"
            "> **Note:** Navigation guidance only. For medical emergencies, visit **Emergency — Room 5**.\n\n"
            "*(ℹ️ Running in Offline Knowledge-Base mode. Add `GEMINI_API_KEY` in `.env` for generative AI responses.)*"
        )

    # 3. Chest / Cardiology
    if is_chest:
        return (
            "### 🏥 Cardiology & Heart Care Information\n\n"
            "For chest-related symptoms, cardiac evaluation, or heart conditions at GGH Kurnool:\n\n"
            "* **Cardiology: Room 25**\n"
            "* **ECG: Room 46**\n"
            "* **Emergency: Room 5** (Urgent care)\n\n"
            "> **⚠️ Urgent Warning:** If you are experiencing severe chest pain, breathlessness, sudden sweating, or radiating pain, **seek immediate emergency care** at **Room 5** or call **108**.\n\n"
            "*(ℹ️ Running in Offline Knowledge-Base mode. Add `GEMINI_API_KEY` in `.env` for generative AI responses.)*"
        )

    # 4. Orthopaedics / Bones / Joints
    if is_ortho:
        return (
            "### 🏥 Orthopaedics Department Information\n\n"
            "For bone, joint, musculoskeletal problems, or fractures:\n\n"
            "* **Orthopaedics: Room 30**\n\n"
            "> **Note:** For severe fractures, trauma, or accidents, proceed directly to **Emergency (Room 5)**.\n\n"
            "*(ℹ️ Running in Offline Knowledge-Base mode. Add `GEMINI_API_KEY` in `.env` for generative AI responses.)*"
        )

    # 5. Laboratory
    if is_lab:
        return (
            "### 🏥 Laboratory Information\n\n"
            "For blood tests, urine analysis, or clinical lab investigations:\n\n"
            "* **Laboratory: Room 45**\n\n"
            "> **Note:** Laboratory services are available on hospital grounds.\n\n"
            "*(ℹ️ Running in Offline Knowledge-Base mode. Add `GEMINI_API_KEY` in `.env` for generative AI responses.)*"
        )

    # 6. ECG
    if is_ecg:
        return (
            "### 🏥 ECG Services\n\n"
            "For Electrocardiogram (ECG) testing:\n\n"
            "* **ECG: Room 46**\n"
            "* **Cardiology: Room 25**\n\n"
            "*(ℹ️ Running in Offline Knowledge-Base mode. Add `GEMINI_API_KEY` in `.env` for generative AI responses.)*"
        )

    # 7. Pharmacy / Medicines
    if is_pharmacy:
        return (
            "### 🏥 Hospital Pharmacy\n\n"
            "For medication dispensing and prescription services:\n\n"
            "* **Pharmacy: Room 50**\n\n"
            "> **Note:** Please present your doctor's hospital prescription slip for medicine dispensing.\n\n"
            "*(ℹ️ Running in Offline Knowledge-Base mode. Add `GEMINI_API_KEY` in `.env` for generative AI responses.)*"
        )

    # 8. Emergency
    if is_emergency:
        return (
            "### 🚨 Emergency Medical Services\n\n"
            "For life-threatening emergencies, trauma, or urgent medical care:\n\n"
            "* **Emergency Department: Room 5**\n"
            "* **Emergency Ambulance: 108**\n\n"
            "> **Important:** Seek immediate emergency medical care for severe breathing difficulty, loss of consciousness, severe bleeding, or sudden paralysis/weakness.\n\n"
            "*(ℹ️ Running in Offline Knowledge-Base mode. Add `GEMINI_API_KEY` in `.env` for generative AI responses.)*"
        )

    # 9. All Rooms / General Navigation
    if is_all_rooms or "room" in q_lower:
        return (
            "### 🏥 GGH Kurnool Room Directory\n\n"
            "Here are the verified room numbers at Government General Hospital, Kurnool:\n\n"
            "| Department / Service | Room Number |\n"
            "| :--- | :--- |\n"
            "| **General Medicine** | **Room 12** |\n"
            "| **Cardiology** | **Room 25** |\n"
            "| **ENT (Ear, Nose, Throat)** | **Room 18** |\n"
            "| **Orthopaedics** | **Room 30** |\n"
            "| **Laboratory** | **Room 45** |\n"
            "| **ECG** | **Room 46** |\n"
            "| **Pharmacy** | **Room 50** |\n"
            "| **Emergency** | **Room 5** |\n\n"
            "> **Note:** If a department or room is not listed above, please check with the main hospital reception counter.\n\n"
            "*(ℹ️ Running in Offline Knowledge-Base mode. Add `GEMINI_API_KEY` in `.env` for generative AI responses.)*"
        )

    # 10. Hospital Info / Location / Contact
    if is_hospital_info:
        return (
            "### 🏥 Government General Hospital (GGH), Kurnool\n\n"
            "* **Common Name:** Pedda Hospital, Kurnool\n"
            "* **Location:** Budhwarpet Road, Kurnool, Andhra Pradesh — 518002, India\n"
            "* **Superintendent Contact:** 08518-279030\n"
            "* **Emergency Ambulance:** 108\n\n"
            "> **Services Available:** General Medicine, Cardiology, ENT, Orthopaedics, Emergency, Laboratory, ECG, Pharmacy.\n\n"
            "*(ℹ️ Running in Offline Knowledge-Base mode. Add `GEMINI_API_KEY` in `.env` for generative AI responses.)*"
        )

    # 11. Doctors / Timings / Appointments
    if is_doctor:
        return (
            "### ℹ️ Hospital Timings & Doctor Consultations\n\n"
            "* **Doctor Schedules & OPD Timings:** Specific doctor rosters and verified OPD timings are not published in the current offline records.\n"
            "* **Appointments:** Handled on-site at the hospital registration counter.\n"
            "* **Hospital Contact:** Superintendent Office at **08518-279030** for inquiry.\n\n"
            "> For immediate consultations, visit the Outpatient Department or **Emergency (Room 5)**.\n\n"
            "*(ℹ️ Running in Offline Knowledge-Base mode. Add `GEMINI_API_KEY` in `.env` for generative AI responses.)*"
        )

    # Fallback to scanning knowledge base text files
    return _search_text_files_fallback(question)


# ============================================================
# MAIN RAG FUNCTION
# ============================================================

def ask_rag(question, chat_history=None, language="en"):
    """Retrieves relevant hospital context and generates a response."""
    if chat_history is None:
        chat_history = []

    client = get_gemini_client()
    store = get_vector_store()

    # If Gemini API key is not configured, seamlessly use local offline knowledge-base matcher!
    if client is None or store is None:
        return offline_knowledge_base_search(question, language=language)

    # --------------------------------------------------------
    # STEP 1: REWRITE FOLLOW-UP QUESTION
    # --------------------------------------------------------
    search_question = rewrite_question(question, chat_history)

    # --------------------------------------------------------
    # STEP 2: SEARCH VECTOR DATABASE
    # --------------------------------------------------------
    try:
        results = store.similarity_search(search_question, k=4)
        print("\nRelevant information retrieved:", len(results), "chunks.")
        context = "\n\n".join(document.page_content for document in results)
    except Exception as e:
        print("Similarity search error:", e)
        context = ""

    # --------------------------------------------------------
    # STEP 3: CREATE CHAT HISTORY TEXT
    # --------------------------------------------------------
    history_text = ""
    for message in chat_history:
        user_text = message.get("user", "")
        bot_text = message.get("assistant", "")
        history_text += f"User: {user_text}\nAssistant: {bot_text}\n\n"

    # Multilingual instruction directive
    lang_directive = "Give a clear and simple answer in English."
    if language == "te":
        lang_directive = "IMPORTANT: Answer in polite, natural Telugu (తెలుగు). Make sure all hospital room numbers and department names are clearly stated (e.g. జనరల్ మెడిసిన్ - రూమ్ 12)."
    elif language == "hi":
        lang_directive = "IMPORTANT: Answer in polite, natural Hindi (हिंदी). Make sure all hospital room numbers and department names are clearly stated (e.g. जनरल मेडिसिन - कमरा 12)."

    # --------------------------------------------------------
    # STEP 4: FINAL PROMPT
    # --------------------------------------------------------
    prompt = f"""
You are a healthcare information assistant for Government General Hospital, Kurnool.

Your job is to provide:
- Hospital information
- Department information
- Room information
- Service information
- General health information
- Hospital navigation guidance

Use ONLY the information provided in the retrieved context.
You may use conversation history to understand follow-up questions.

IMPORTANT RULES:
1. {lang_directive}
2. Give a clear and structured answer with bullet points and bold room numbers where appropriate.
3. Do not invent information.
4. Do not invent doctor names, department names, room numbers, timings, prices, appointments, or services.
5. If the requested information is not available in the context, say:
   "I don't have verified information about that." (translated to the requested language if applicable)
6. If a room number is present in the retrieved information, you may provide that room number.
7. Do not create a room number that is not present in the retrieved context.
8. For medical questions, provide general educational information only.
9. Do not diagnose diseases.
10. Do not claim that the user has a particular disease.
11. If the user describes potentially serious symptoms, advise them to seek immediate professional medical care.
12. Use the conversation history to understand follow-up questions.
13. Answer the user's actual question directly.
14. Keep answers concise and easy to understand.
15. This chatbot provides healthcare information and hospital navigation support. It is not a medical diagnosis system.

==================================================
CONVERSATION HISTORY
==================================================
{history_text}

==================================================
REWRITTEN SEARCH QUESTION
==================================================
{search_question}

==================================================
RETRIEVED HOSPITAL INFORMATION
==================================================
{context}

==================================================
CURRENT USER QUESTION
==================================================
{question}

==================================================
FINAL ANSWER
==================================================
"""

    # --------------------------------------------------------
    # STEP 5: GENERATE FINAL ANSWER
    # --------------------------------------------------------
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print("Gemini Generation Error:", e)
        print("Seamlessly falling back to verified offline knowledge base...")
        return offline_knowledge_base_search(question, language=language)


# ============================================================
# TEST RAG
# ============================================================

if __name__ == "__main__":
    print("Testing RAG database setup...")
    build_database()

    test_query = "What services are available at Government General Hospital, Kurnool?"
    print(f"\nQuerying: {test_query}\n")
    answer = ask_rag(test_query)

    print("\n================================")
    print("FINAL ANSWER")
    print("================================")
    print(answer)