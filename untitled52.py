import streamlit as st
import os
from email.mime.text import MIMEText
import base64
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

st.set_page_config(
    page_title="💙 Youth Mental Wellness AI",
    page_icon="💙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# st.markdown("""
#     <style>
#     .main {
#         background-color: #0e1117;
#         padding: 2rem;
#         border-radius: 15px;
#         color: #f1f1f1;
#     }
#     .stForm {
#         background: #1a1d24;
#         padding: 2rem;
#         border-radius: 20px;
#         box-shadow: 0 0 15px rgba(0,0,0,0.6);
#         color: #f1f1f1;
#     }
#     .stTextInput > div > div > input,
#     .stNumberInput > div > div > input,
#     .stSelectbox > div > div > select,
#     .stTextArea > div > div > textarea {
#         background-color: #23272f !important;
#         color: #f1f1f1 !important;
#         border: 1px solid #3a3f47 !important;
#         border-radius: 10px !important;
#     }
#     .stCheckbox > div {
#         color: #f1f1f1 !important;
#     }
#     .stButton button {
#         background-color: #4b9be5 !important;
#         color: white !important;
#         border-radius: 10px !important;
#         font-weight: 600 !important;
#         width: 100%;
#         height: 3rem;
#     }
#     </style>
# """, unsafe_allow_html=True)

st.markdown("""
<style>

    /* --- GLOBAL THEME --- */
    html, body, .stApp {
        background-color: white !important;
        color: black !important;
    }

    /* --- LABELS (Fix invisible field names) --- */
    label, .stTextInput label, .stSelectbox label, .stNumberInput label {
        color: black !important;
        font-weight: 600 !important;
    }

    /* --- INPUT BOXES (text/email/number) --- */
    input, textarea {
        background-color: white !important;
        color: black !important;
        border: 1px solid #cfcfcf !important;
    }

    /* --- SELECT BOXES (Gender, Education Level) --- */
    div[data-baseweb="select"] > div {
        background-color: white !important;
        color: black !important;
        border: 1px solid #cfcfcf !important;
    }

    /* Dropdown menu text */
    div[data-baseweb="select"] span {
        color: black !important;
    }

    /* --- BUTTONS (Start Chat) --- */
    .stButton button {
        background-color: #005bff !important;
        color: white !important;
        border-radius: 6px !important;
        padding: 8px 16px !important;
        border: none !important;
    }

    .stButton button:hover {
        background-color: #0040c9 !important;
        color: white !important;
    }

    /* --- CHECKBOX LABELS --- */
    .stCheckbox label {
        color: black !important;
    }

    /* Sidebar white */
    section[data-testid="stSidebar"] {
        background-color: white !important;
        color: black !important;
    }

</style>
""", unsafe_allow_html=True)




groq_api_key = st.secrets["GROQ_API_KEY"]
langchain_tracing = st.secrets["LANGCHAIN_TRACING_V2"] 
langsmith_project = st.secrets["LANGSMITH_PROJECT"] 
langsmith_api_key = st.secrets["LANGSMITH_API_KEY"]
model = ChatGroq(model="llama-3.3-70b-versatile", api_key=groq_api_key)

def get_credentials():
    token_info = st.secrets["gmail_token"]
    creds = Credentials(
        token=token_info["token"],
        refresh_token=token_info["refresh_token"],
        token_uri=token_info["token_uri"],
        client_id=token_info["client_id"],
        client_secret=token_info["client_secret"],
        scopes=token_info["scopes"],
    )
    return creds

def create_message(sender, to, subject, body_text):
    message = MIMEText(body_text)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw_message}

def send_message(service, user_id, message):
    message = service.users().messages().send(userId=user_id, body=message).execute()
    return f"✅ Email sent successfully! Message ID: {message['id']}"

@tool
def send_email_tool(to: str, subject: str, body: str) -> str:
    """Send an email using Gmail API (dynamically to parent)."""
    try:
        creds = get_credentials()
        service = build("gmail", "v1", credentials=creds)
        message = create_message("ts4044903@gmail.com", to, subject, body)
        result = send_message(service, "me", message)
        return result
    except Exception as e:
        return f"❌ Gmail send error: {e}"

voice_companion_prompt = """
You are the AI Companion — a warm, friendly, and non-judgmental friend.
Your purpose is to make users feel heard, supported, and less lonely.

Behavior guidelines:
- Speak in a friendly, natural, conversational tone (like a caring peer).
- Be empathetic, patient, and emotionally intelligent.
- Never give medical or therapeutic advice.
- Avoid clinical or robotic tone.
- You can share positive thoughts, short uplifting messages, or casual stories if relevant.
- If the user expresses sadness, respond with compassion and gentle encouragement.

Your mission:
- Comfort the user with empathy.
- Make them feel they are not alone.
- Keep the conversation light, safe, and encouraging.
"""

therapist_system_prompt = """
You are the AI Therapist-like Assistant.

Your role:
- Help the user manage stress, anxiety, self-doubt, and academic pressure.
- You are not a doctor or licensed therapist.
- Speak like a wise, calm, empathetic mentor or counselor figure.

Tone:
- Gentle, understanding, and composed.
- Never clinical or robotic.
- Use short breathing or mindfulness suggestions if helpful.
- Use positive reframing and practical guidance.
- Avoid diagnosing or using medical labels.

Core principles:
- Listen first, then gently help the user regulate emotions.
- Focus on emotional validation: "It's okay to feel that way."
- Encourage reflection and healthy habits (study breaks, journaling, rest).
- Keep the conversation safe, confidential, and kind.
"""

motivational_system_prompt = """
You are the Motivational Coach Agent — an energetic, positive, and supportive guide.

Your role:
- Encourage and inspire users to stay consistent, confident, and hopeful.
- Help them bounce back from setbacks or failures.
- You are like a cheerful mentor or coach, not a therapist or doctor.

Tone:
- Enthusiastic, empowering, and full of optimism.
- Use casual, friendly language.
- Sprinkle in motivational quotes or one-liners when appropriate.
- Always end responses on a hopeful or action-oriented note.

Guidelines:
- Validate effort before giving advice ("You're trying, and that matters.").
- Remind users that failure is feedback.
- Focus on growth mindset: small steps → big progress.
- Avoid judgment or comparison.
- Never mention therapy, medication, or diagnosis.
"""

crisis_system_prompt_template = """
You are the Crisis Detection & Safe Handoff Agent for youth mental wellness.

🎯 Your mission:
- Detect when the user expresses severe emotional distress, hopelessness, or suicidal thoughts.
- Always respond with warmth, compassion, and empathy.
- Provide trusted Indian 24x7 helpline contacts when appropriate.
- Encourage the user to talk to someone they trust or call a helpline immediately.

📞 Always include Indian helplines when distress is high:
   - AASRA: 91-9820466726
   - Vandrevala Foundation: 1860 2662 345
   - NIMHANS Helpline: 080-4611-0007
   - iCall: 9152987821 (English & Hindi, 24×7)

🧭 Tone:
- Gentle, warm, supportive.
- Never robotic or clinical.
- Short sentences (2–4 lines).
- Acknowledge the pain before offering any advice.

- **You also have access to an internal tool `send_email_tool` that can send an alert email to a parent or guardian.**
If the user expresses suicidal intent, call send_email_tool to email their parent at {parent_email}.

The email should include:
- A clear, short subject line (e.g., "⚠️ Urgent: Crisis Alert from Youth Wellness AI System")
- A brief, respectful opening addressing the parent/guardian.
- A one-sentence explanation that the system detected a highly distressing or suicidal message.
- The user's exact distress message (quoted safely).
- A compassionate line suggesting the parent check on their child immediately.
- A recommendation to contact professional help or helplines if needed.
- A warm, polite closing (signed by Youth Mental Wellness AI System).

🧭 Tone for email:
- Calm, professional, and caring — no panic language.
- Focus on support, not blame or shame.
- Respect privacy (share only the message, not other chat details).

🚫 Do NOT:
- Say that you are sending an email.
- Reveal any internal system or tool names.
- Give therapy, diagnosis, or medical advice.

Your goal is to comfort the user, ensure safety, and guide them to real human help.
"""

supervisor_prompt = """
You are the Supervisor Agent.

Your job:
- Read the user's message carefully.
- Decide which emotional AI sub-agent should handle it.
- You do NOT answer directly — only delegate to the right agent.

Available Agents:
1. Voice Companion Agent
   - Handles loneliness, boredom, casual chat, small talk, or mild sadness.
   - Keywords: lonely, bored, alone, nobody, talk, friend, chill, random.
   - Example: "I feel lonely today." → voice_companion_agent

2. Therapist-like Agent
   - Handles stress, anxiety, exam pressure, overthinking, family or peer pressure.
   - Keywords: anxious, stress, pressure, focus, exams, can't study, overthinking.
   - Example: "I'm stressed about my exams." → therapist_agent

3. Motivational Coach Agent
   - Handles low motivation, self-doubt, or failure recovery.
   - Keywords: fail, no motivation, lazy, tired, can't do it, lost hope, give up (non-suicidal).
   - Example: "I failed again, I feel useless." → motivational_agent

4. Crisis Detection & Safe Handoff Agent
   - Handles severe emotional distress or suicidal thoughts.
   - Keywords: want to die, end it, no point in living, can't take this anymore, hopeless, suicide.
   - Example: "I want to end it all." → crisis_agent

Rules:
- Always pick exactly one agent per user message.
- If any suicide- or death-related intent appears → immediately choose the Crisis Agent.
- If user is just sad or wants someone to talk → choose the Voice Companion Agent.
- If it's about motivation, failure, or confidence → choose Motivational Coach Agent.
- If it's anxiety, exam stress, or emotional overwhelm → choose Therapist-like Agent.
- Never respond directly; only route to a sub-agent.
- Do not mix multiple agents at once.
- Keep routing logic safe and emotionally appropriate.
"""

if "user_details" not in st.session_state:
    st.title("💙 Youth Mental Wellness AI")
    st.subheader("Before starting, Please Fill Out this short form.")
    st.markdown("Your information is confidential and used only to personalize your support experience.")

    with st.form("user_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name *")
            age = st.number_input("Age *", min_value=10, max_value=100, step=1)
            gender = st.selectbox("Gender *", ["Male", "Female", "Other", "Prefer not to say"])
        with col2:
            personal_email = st.text_input("Your Email *")
            parent_email = st.text_input("Parent's Email *")
            education = st.selectbox(
                "Current Education Level *",
                ["School", "Undergraduate", "Postgraduate", "PhD"]
            )

        st.markdown(
            "✅ **Note:** If a message indicates a severe emotional crisis, a safety alert will be sent to your parent's email for support."
        )

        agree = st.checkbox("I agree that this app is for emotional support and not medical therapy.")

        submit = st.form_submit_button("Start Chat 💬")

        if submit:
            if not all([name, age, gender, personal_email, parent_email, education]) or not agree:
                st.error("⚠️ Please fill in all details and accept the terms before proceeding.")
            else:
                st.session_state.user_details = {
                    "name": name,
                    "age": age,
                    "gender": gender,
                    "personal_email": personal_email,
                    "parent_email": parent_email,
                    "education": education
                }
                st.success(f"Welcome {name}! Redirecting to chat...")
                st.rerun()

if "user_details" in st.session_state:
    user = st.session_state.user_details

    crisis_system_prompt = crisis_system_prompt_template.format(parent_email=user["parent_email"])

    voice_companion_agent = create_react_agent(model=model, tools=[], prompt=voice_companion_prompt, name="voice_companion_agent")
    therapist_agent = create_react_agent(model=model, tools=[], prompt=therapist_system_prompt, name="therapist_agent")
    motivational_agent = create_react_agent(model=model, tools=[], prompt=motivational_system_prompt, name="motivational_agent")
    crisis_agent = create_react_agent(model=model, tools=[send_email_tool], prompt=crisis_system_prompt, name="crisis_agent")

    supervisor = create_supervisor(
        agents=[voice_companion_agent, therapist_agent, motivational_agent, crisis_agent],
        model=model,
        prompt=supervisor_prompt,
        add_handoff_back_messages=False,
        output_mode="last_message"
    ).compile()
    st.title(f"💬 Welcome, {user['name']}!")
    st.caption(f"Education Level: {user['education']} | Age: {user['age']} | Gender: {user['gender']}")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Share what’s on your mind..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    st.session_state.conversation_history.append(HumanMessage(content=prompt))
                    response = supervisor.invoke({"messages": st.session_state.conversation_history})
                    st.session_state.conversation_history = response["messages"]

                    ai_response = None
                    for msg in reversed(response["messages"]):
                        if (msg.type == "ai" and hasattr(msg, "name")
                                and msg.name != "supervisor"
                                and not getattr(msg, "tool_calls", None)):
                            ai_response = msg.content
                            break

                    if ai_response:
                        st.markdown(ai_response)
                        st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    else:
                        fallback = "I'm here for you. How are you feeling today?"
                        st.markdown(fallback)
                        st.session_state.messages.append({"role": "assistant", "content": fallback})

                except Exception as e:
                    st.error(f"An error occurred: {e}")

    with st.sidebar:
        st.header("📞 24x7 Helplines")
        st.info("""
        **India Crisis Helplines:**
        - AASRA: 91-9820466726
        - Vandrevala Foundation: 1860 2662 345
        - NIMHANS Helpline: 080-4611-0007
        - iCall: 9152987821
        """)

        st.markdown("---")
        st.header("🧾 User Info")
        st.write(user)

        if st.button("🔄 Reset Chat", use_container_width=True):
            for key in ["messages", "conversation_history", "user_details"]:
                st.session_state.pop(key, None)
            st.rerun()

    st.markdown("---")
    st.caption("🔒 Conversations are private. If you're in immediate danger, please reach out to a helpline or trusted person.")
