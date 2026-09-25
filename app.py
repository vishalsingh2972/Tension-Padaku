import os
import sys

# Check if running outside the virtual environment
is_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
if not is_venv and os.path.exists(os.path.join(os.path.dirname(__file__), "venv")):
    try:
        import dotenv
        import google.genai
    except ImportError:
        print("\n" + "=" * 65)
        print("[!] VIRTUAL ENVIRONMENT NOT ACTIVATED!")
        print("=" * 65)
        print("You ran 'python app.py' using global Python, but this project's")
        print("packages are installed in the './venv' virtual environment.\n")
        print("How to run properly:")
        print("   1. Activate the virtual environment:")
        print("      .\\venv\\Scripts\\activate")
        print("      python app.py\n")
        print("   OR run directly with:")
        print("      .\\venv\\Scripts\\python.exe app.py\n")
        print("=" * 65 + "\n")
        sys.exit(1)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import Flask, render_template, request, jsonify
from rag import ask_rag

app = Flask(__name__)


# ==========================================
# Home page
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# Chat API (Stateless, multi-user safe)
# ==========================================

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_message = data.get("message", "").strip()
    history = data.get("history", [])
    language = data.get("language", "en")

    if not user_message:
        return jsonify({
            "response": "Please enter a question."
        })

    try:
        # Pass question, history, and language to RAG engine
        response = ask_rag(user_message, history, language=language)

        return jsonify({
            "response": response
        })

    except Exception as e:
        print("RAG Error:", e)
        return jsonify({
            "response": "Sorry, I could not process your question right now."
        }), 500


# ==========================================
# Symptom Checker Triage API
# ==========================================

@app.route("/api/symptom-check", methods=["POST"])
def symptom_check():
    data = request.get_json() or {}
    symptoms = data.get("symptoms", [])
    duration = data.get("duration", "1-3 days")
    severity = data.get("severity", "moderate")
    language = data.get("language", "en")

    # Assess emergency triage symptoms
    emergency_keywords = ["chest", "breathing", "unconscious", "stroke", "bleeding", "severe injury", "గుండె", "శ్వాస", "छाती", "सांस"]
    has_emergency_sym = any(any(k in s.lower() for k in emergency_keywords) for s in symptoms) or severity == "severe"

    if has_emergency_sym:
        risk_level = "High / Emergency"
        color = "#e53935"
        dept = "Emergency Department"
        room = "Room 5"
        if language == "te":
            guidance = "మీ లక్షణాలు అత్యవసర వైద్య సంరక్షణను సూచిస్తున్నాయి. దయచేసి వెంటనే GGH కర్నూలులోని ఎమర్జెన్సీ (రూమ్ 5) కి వెళ్లండి లేదా 108 అంబులెన్స్ కాల్ చేయండి."
        elif language == "hi":
            guidance = "आपके लक्षण तत्काल आपातकालीन चिकित्सा की आवश्यकता दर्शाते हैं। कृपया तुरंत जीजीएच कुरनूल में इमरजेंसी (कमरा 5) पर जाएं या 108 पर कॉल करें।"
        else:
            guidance = "Your reported symptoms indicate an urgent medical situation. Please proceed directly to Emergency (Room 5) at GGH Kurnool or call 108 for an ambulance."

    elif any("bone" in s.lower() or "joint" in s.lower() or "fracture" in s.lower() or "ఎముక" in s or "हड्डी" in s for s in symptoms):
        risk_level = "Moderate"
        color = "#fb8c00"
        dept = "Orthopaedics"
        room = "Room 30"
        if language == "te":
            guidance = "ఎముక లేదా కీళ్ల నొప్పుల పరీక్ష కోసం ఆర్థోపెడిక్స్ విభాగాన్ని (రూమ్ 30) సంప్రదించండి."
        elif language == "hi":
            guidance = "हड्डी या जोड़ों के दर्द के मूल्यांकन के लिए ऑर्थोपेडिक्स विभाग (कमरा 30) से संपर्क करें।"
        else:
            guidance = "Bone, joint, and musculoskeletal symptoms are evaluated in the Orthopaedics Department."

    elif any("ear" in s.lower() or "throat" in s.lower() or "nose" in s.lower() or "గొంతు" in s or "गला" in s for s in symptoms):
        risk_level = "Moderate" if duration == "> 1 week" else "Mild"
        color = "#fb8c00" if duration == "> 1 week" else "#43a047"
        dept = "ENT Department"
        room = "Room 18"
        if language == "te":
            guidance = "చెవి, ముక్కు లేదా గొంతు సమస్యల కోసం ENT విభాగం (రూమ్ 18) లో సంప్రదించండి."
        elif language == "hi":
            guidance = "कान, नाक या गले की समस्याओं के लिए ईएनटी (ENT) विभाग (कमरा 18) से संपर्क करें।"
        else:
            guidance = "Ear, nose, and throat-related complaints can be examined in the ENT Outpatient Clinic."

    elif any("chest" in s.lower() or "heart" in s.lower() or "bp" in s.lower() or "గుండె" in s or "दिल" in s for s in symptoms):
        risk_level = "High"
        color = "#e53935"
        dept = "Cardiology"
        room = "Room 25"
        if language == "te":
            guidance = "గుండె మరియు ఛాతీ సంబంధిత సమస్యలకు కార్డియాలజీ (రూమ్ 25) లో సంప్రదించండి. తీవ్రమైన నొప్పి ఉంటే ఎమర్జెన్సీ (రూమ్ 5) కి వెళ్లండి."
        elif language == "hi":
            guidance = "हृदय या छाती से संबंधित लक्षणों के लिए कार्डियोलॉजी (कमरा 25) में जांच कराएं।"
        else:
            guidance = "Cardiac and blood pressure evaluations are handled by the Cardiology Department. For sudden acute pain, proceed to Emergency (Room 5)."

    else:
        risk_level = "Mild / General"
        color = "#43a047"
        dept = "General Medicine"
        room = "Room 12"
        if language == "te":
            guidance = "జలుబు, జ్వరం, తలనొప్పి లేదా సాధారణ అనారోగ్యానికి జనరల్ మెడిసిన్ (రూమ్ 12) ప్రాథమిక సంప్రదింపు విభాగం."
        elif language == "hi":
            guidance = "सर्दी, बुखार, सिरदर्द या सामान्य अस्वस्थता के लिए जनरल मेडिसिन (कमरा 12) प्राथमिक परामर्श कक्ष है।"
        else:
            guidance = "For cold, mild fever, headache, or general malaise, General Medicine is the designated initial consultation room."

    return jsonify({
        "risk_level": risk_level,
        "color": color,
        "department": dept,
        "room": room,
        "guidance": guidance,
        "emergency_contact": "108",
        "hospital": "Government General Hospital (GGH), Kurnool"
    })


# ==========================================
# Clear Chat API
# ==========================================

@app.route("/clear-chat", methods=["POST"])
def clear_chat():
    return jsonify({
        "message": "Chat history cleared successfully."
    })


# ==========================================
# Run Flask
# ==========================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    print(f"Starting Health Prediction & Hospital Navigation Chatbot on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)