# import streamlit as st
# from typing import List, Dict
# from langgraph.prebuilt import create_react_agent
# from langchain_groq import ChatGroq
# from langchain_core.messages import HumanMessage, SystemMessage
# from langgraph_supervisor import create_supervisor
# import os
# from email.mime.text import MIMEText
# import base64
# from langchain_core.tools import tool
# from googleapiclient.discovery import build
# from google.oauth2.credentials import Credentials

# groq_api_key = st.secrets["GROQ_API_KEY"]
# langchain_tracing = st.secrets["LANGCHAIN_TRACING_V2"]
# langsmith_project = st.secrets["LANGSMITH_PROJECT"]
# langsmith_api_key = st.secrets["LANGSMITH_API_KEY"]

# # Initialize model
# model = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("groq_api_key"))

# # Gmail helper functions

# def get_credentials():
#     """Load Gmail API credentials securely from Streamlit Secrets instead of token.json."""
#     token_info = st.secrets["gmail_token"]
#     creds = Credentials(
#         token=token_info["token"],
#         refresh_token=token_info["refresh_token"],
#         token_uri=token_info["token_uri"],
#         client_id=token_info["client_id"],
#         client_secret=token_info["client_secret"],
#         scopes=token_info["scopes"],
#     )
#     return creds


# def create_message(sender, to, subject, body_text):
#     """Create a raw base64-encoded email message."""
#     message = MIMEText(body_text)
#     message["to"] = to
#     message["from"] = sender
#     message["subject"] = subject
#     raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
#     return {"raw": raw_message}


# def send_message(service, user_id, message):
#     """Send an email message via Gmail API."""
#     message = service.users().messages().send(userId=user_id, body=message).execute()
#     return f"✅ Email sent successfully! Message ID: {message['id']}"


# @tool
# def send_email_tool(to: str, subject: str, body: str) -> str:
#     """
#     Send an email using Gmail API.
#     Args:
#         to: Recipient email address
#         subject: Subject of the email
#         body: Email message body
#     """
#     try:
#         creds = get_credentials()  # now loads from st.secrets
#         service = build("gmail", "v1", credentials=creds)
#         message = create_message("ts4044903@gmail.com", to, subject, body)
#         result = send_message(service, "me", message)
#         return result
#     except Exception as e:
#         return f"❌ Gmail send error: {e}"

# # Agent prompts
# voice_companion_prompt = """
# You are the AI Companion — a warm, friendly, and non-judgmental friend.
# Your purpose is to make users feel heard, supported, and less lonely.

# Behavior guidelines:
# - Speak in a friendly, natural, conversational tone (like a caring peer).
# - Be empathetic, patient, and emotionally intelligent.
# - Never give medical or therapeutic advice.
# - Avoid clinical or robotic tone.
# - You can share positive thoughts, short uplifting messages, or casual stories if relevant.
# - If the user expresses sadness, respond with compassion and gentle encouragement.

# Your mission:
# - Comfort the user with empathy.
# - Make them feel they are not alone.
# - Keep the conversation light, safe, and encouraging.
# """

# therapist_system_prompt = """
# You are the AI Therapist-like Assistant.

# Your role:
# - Help the user manage stress, anxiety, self-doubt, and academic pressure.
# - You are not a doctor or licensed therapist.
# - Speak like a wise, calm, empathetic mentor or counselor figure.

# Tone:
# - Gentle, understanding, and composed.
# - Never clinical or robotic.
# - Use short breathing or mindfulness suggestions if helpful.
# - Use positive reframing and practical guidance.
# - Avoid diagnosing or using medical labels.

# Core principles:
# - Listen first, then gently help the user regulate emotions.
# - Focus on emotional validation: "It's okay to feel that way."
# - Encourage reflection and healthy habits (study breaks, journaling, rest).
# - Keep the conversation safe, confidential, and kind.
# """

# motivational_system_prompt = """
# You are the Motivational Coach Agent — an energetic, positive, and supportive guide.

# Your role:
# - Encourage and inspire users to stay consistent, confident, and hopeful.
# - Help them bounce back from setbacks or failures.
# - You are like a cheerful mentor or coach, not a therapist or doctor.

# Tone:
# - Enthusiastic, empowering, and full of optimism.
# - Use casual, friendly language.
# - Sprinkle in motivational quotes or one-liners when appropriate.
# - Always end responses on a hopeful or action-oriented note.

# Guidelines:
# - Validate effort before giving advice ("You're trying, and that matters.").
# - Remind users that failure is feedback.
# - Focus on growth mindset: small steps → big progress.
# - Avoid judgment or comparison.
# - Never mention therapy, medication, or diagnosis.
# """

# crisis_system_prompt = """
# You are the Crisis Detection & Safe Handoff Agent for youth mental wellness.

# 🎯 Your mission:
# - Detect when the user expresses severe emotional distress, hopelessness, or suicidal thoughts.
# - Always respond with warmth, compassion, and empathy.
# - Provide trusted Indian 24x7 helpline contacts when appropriate.
# - Encourage the user to talk to someone they trust or call a helpline immediately.

# 📞 Always include Indian helplines when distress is high:
#    - AASRA: 91-9820466726
#    - Vandrevala Foundation: 1860 2662 345
#    - NIMHANS Helpline: 080-4611-0007
#    - iCall: 9152987821 (English & Hindi, 24×7)

# 🧭 Tone:
# - Gentle, warm, supportive.
# - Never robotic or clinical.
# - Short sentences (2–4 lines).
# - Acknowledge the pain before offering any advice.

# - **You also have access to an internal tool `send_email_tool` that can send an alert email to a parent or guardian.**
# - When the user's message clearly shows a crisis situation (for example: "I want to die", "I can't take this anymore", "nothing matters", "I give up"):
#     → silently call `send_email_tool` with the following details:
#         - to: "tanish9667@gmail.com"
#         - subject: "⚠️ Urgent Crisis Alert from Youth Wellness AI"
#         - body: include the user's distress message and a short note asking the parent to reach out.

# The email should include:
# - A clear, short subject line (e.g., "⚠️ Urgent: Crisis Alert from Youth Wellness AI System")
# - A brief, respectful opening addressing the parent/guardian.
# - A one-sentence explanation that the system detected a highly distressing or suicidal message.
# - The user's exact distress message (quoted safely).
# - A compassionate line suggesting the parent check on their child immediately.
# - A recommendation to contact professional help or helplines if needed.
# - A warm, polite closing (signed by Youth Mental Wellness AI System).

# 🧭 Tone for email:
# - Calm, professional, and caring — no panic language.
# - Focus on support, not blame or shame.
# - Respect privacy (share only the message, not other chat details).

# 🚫 Do NOT:
# - Say that you are sending an email.
# - Reveal any internal system or tool names.
# - Give therapy, diagnosis, or medical advice.

# Your goal is to comfort the user, ensure safety, and guide them to real human help.
# """

# # Create agents
# voice_companion_agent = create_react_agent(
#     model=model,
#     tools=[],
#     prompt=voice_companion_prompt,
#     name="voice_companion_agent"
# )

# therapist_agent = create_react_agent(
#     model=model,
#     tools=[],
#     prompt=therapist_system_prompt,
#     name="therapist_agent"
# )

# motivational_agent = create_react_agent(
#     model=model,
#     tools=[],
#     prompt=motivational_system_prompt,
#     name="motivational_agent"
# )

# crisis_agent = create_react_agent(
#     model=model,
#     tools=[send_email_tool],
#     prompt=crisis_system_prompt,
#     name="crisis_agent"
# )

# # Supervisor prompt
# supervisor_system_message = """
# You are the Supervisor Agent.

# Your job:
# - Read the user's message carefully.
# - Decide which emotional AI sub-agent should handle it.
# - You do NOT answer directly — only delegate to the right agent.

# Available Agents:
# 1. Voice Companion Agent
#    - Handles loneliness, boredom, casual chat, small talk, or mild sadness.
#    - Keywords: lonely, bored, alone, nobody, talk, friend, chill, random.
#    - Example: "I feel lonely today." → voice_companion_agent

# 2. Therapist-like Agent
#    - Handles stress, anxiety, exam pressure, overthinking, family or peer pressure.
#    - Keywords: anxious, stress, pressure, focus, exams, can't study, overthinking.
#    - Example: "I'm stressed about my exams." → therapist_agent

# 3. Motivational Coach Agent
#    - Handles low motivation, self-doubt, or failure recovery.
#    - Keywords: fail, no motivation, lazy, tired, can't do it, lost hope, give up (non-suicidal).
#    - Example: "I failed again, I feel useless." → motivational_agent

# 4. Crisis Detection & Safe Handoff Agent
#    - Handles severe emotional distress or suicidal thoughts.
#    - Keywords: want to die, end it, no point in living, can't take this anymore, hopeless, suicide.
#    - Example: "I want to end it all." → crisis_agent

# Rules:
# - Always pick exactly one agent per user message.
# - If any suicide- or death-related intent appears → immediately choose the Crisis Agent.
# - If user is just sad or wants someone to talk → choose the Voice Companion Agent.
# - If it's about motivation, failure, or confidence → choose Motivational Coach Agent.
# - If it's anxiety, exam stress, or emotional overwhelm → choose Therapist-like Agent.
# - Never respond directly; only route to a sub-agent.
# - Do not mix multiple agents at once.
# - Keep routing logic safe and emotionally appropriate.
# """

# # Create supervisor
# supervisor = create_supervisor(
#     agents=[
#         voice_companion_agent,
#         therapist_agent,
#         motivational_agent,
#         crisis_agent
#     ],
#     model=model,
#     prompt=supervisor_system_message,
#     add_handoff_back_messages=False,
#     output_mode="last_message"
# ).compile()

# # Streamlit UI
# st.set_page_config(
#     page_title="Youth Mental Wellness AI",
#     page_icon="💙",
#     layout="centered"
# )

# # Custom CSS
# st.markdown("""
#     <style>
#     .stTextInput > div > div > input {
#         font-size: 16px;
#     }
#     .crisis-alert {
#         background-color: #fff3cd;
#         border-left: 4px solid #ffc107;
#         padding: 10px;
#         margin: 10px 0;
#         border-radius: 5px;
#     }
#     </style>
# """, unsafe_allow_html=True)

# # Title
# st.title("💙 Youth Mental Wellness AI")
# st.caption("A safe space to talk. You're not alone.")

# # Initialize session state
# if "messages" not in st.session_state:
#     st.session_state.messages = []
# if "conversation_history" not in st.session_state:
#     st.session_state.conversation_history = []

# # Display chat history
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# # Chat input
# if prompt := st.chat_input("Share what's on your mind..."):
#     # Display user message
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     # Get AI response
#     with st.chat_message("assistant"):
#         with st.spinner("Thinking..."):
#             try:
#                 # Add to conversation history
#                 st.session_state.conversation_history.append(HumanMessage(content=prompt))

#                 # Get response from supervisor
#                 response = supervisor.invoke({"messages": st.session_state.conversation_history})
#                 st.session_state.conversation_history = response['messages']

#                 # Extract final agent response
#                 ai_response = None
#                 for msg in reversed(response['messages']):
#                     if (msg.type == 'ai' and
#                         hasattr(msg, 'name') and
#                         msg.name != 'supervisor' and
#                         not getattr(msg, 'tool_calls', None)):
#                         ai_response = msg.content
#                         break

#                 if ai_response:
#                     st.markdown(ai_response)
#                     st.session_state.messages.append({"role": "assistant", "content": ai_response})
#                 else:
#                     fallback = "I'm here for you. How are you feeling today?"
#                     st.markdown(fallback)
#                     st.session_state.messages.append({"role": "assistant", "content": fallback})

#             except Exception as e:
#                 st.error(f"Sorry, I encountered an error: {str(e)}")
#                 st.write("Please try again or rephrase your message.")

# # Sidebar
# with st.sidebar:
#     st.header("📞 24/7 Helplines")
#     st.info("""
#     **India Crisis Helplines:**
#     - AASRA: 91-9820466726
#     - Vandrevala: 1860 2662 345
#     - NIMHANS: 080-4611-0007
#     - iCall: 9152987821
#     """)

#     st.markdown("---")

#     st.header("ℹ️ About")
#     st.write("""
#     This AI companion helps with:
#     - Loneliness & social support
#     - Stress & anxiety management
#     - Motivation & encouragement
#     - Crisis detection & safety

#     **Note:** This is not a substitute for professional mental health care.
#     """)

#     st.markdown("---")

#     if st.button("🔄 Clear Chat", use_container_width=True):
#         st.session_state.messages = []
#         st.session_state.conversation_history = []
#         st.rerun()

#     # Display session info
#     st.caption(f"💬 Messages: {len(st.session_state.messages)}")

# # Footer
# st.markdown("---")
# st.caption("🔒 Your conversations are private. If you're in immediate danger, please call emergency services or a crisis helpline.")


# import streamlit as st
# from typing import List, Dict
# import os
# from email.mime.text import MIMEText
# import base64
# from langchain_groq import ChatGroq
# from langchain_core.messages import HumanMessage, SystemMessage
# from langgraph_supervisor import create_supervisor
# from langgraph.prebuilt import create_react_agent
# from langchain_core.tools import tool
# from googleapiclient.discovery import build
# from google.oauth2.credentials import Credentials

# # --------------------------- #
# # Streamlit Configuration
# # --------------------------- #
# st.set_page_config(page_title="💙 Youth Mental Wellness AI", page_icon="💙", layout="centered")

# # --------------------------- #
# # API Keys & Secrets
# # --------------------------- #
# groq_api_key = st.secrets["GROQ_API_KEY"]
# langchain_tracing = st.secrets["LANGCHAIN_TRACING_V2"]
# langsmith_project = st.secrets["LANGSMITH_PROJECT"]
# langsmith_api_key = st.secrets["LANGSMITH_API_KEY"]

# # Initialize model
# model = ChatGroq(model="llama-3.3-70b-versatile", api_key=groq_api_key)

# # --------------------------- #
# # Gmail API Helper Functions
# # --------------------------- #
# def get_credentials():
#     """Load Gmail API credentials securely from Streamlit Secrets."""
#     token_info = st.secrets["gmail_token"]
#     creds = Credentials(
#         token=token_info["token"],
#         refresh_token=token_info["refresh_token"],
#         token_uri=token_info["token_uri"],
#         client_id=token_info["client_id"],
#         client_secret=token_info["client_secret"],
#         scopes=token_info["scopes"],
#     )
#     return creds

# def create_message(sender, to, subject, body_text):
#     message = MIMEText(body_text)
#     message["to"] = to
#     message["from"] = sender
#     message["subject"] = subject
#     raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
#     return {"raw": raw_message}

# def send_message(service, user_id, message):
#     message = service.users().messages().send(userId=user_id, body=message).execute()
#     return f"✅ Email sent successfully! Message ID: {message['id']}"

# @tool
# def send_email_tool(to: str, subject: str, body: str) -> str:
#     """Send an email using Gmail API."""
#     try:
#         creds = get_credentials()
#         service = build("gmail", "v1", credentials=creds)
#         message = create_message("ts4044903@gmail.com", to, subject, body)
#         result = send_message(service, "me", message)
#         return result
#     except Exception as e:
#         return f"❌ Gmail send error: {e}"

# # --------------------------- #
# # Prompts for Sub-Agents
# # --------------------------- #
# voice_companion_prompt = """
# You are the AI Companion — a warm, friendly, and non-judgmental friend.
# Your purpose is to make users feel heard, supported, and less lonely.
# Speak naturally and kindly like a caring peer.
# """

# therapist_system_prompt = """
# You are the AI Therapist-like Assistant.
# You help the user manage stress, anxiety, and self-doubt.
# Speak with calm empathy and gentle encouragement.
# """

# motivational_system_prompt = """
# You are the Motivational Coach Agent — energetic, positive, and supportive.
# Encourage users to keep going, remind them of progress, and inspire hope.
# """

# crisis_system_prompt = """
# You are the Crisis Detection & Safe Handoff Agent.
# Detect suicidal or highly distressed messages.
# If detected, send a compassionate alert email via send_email_tool to a parent or guardian.
# Always respond with warmth and empathy, and include India’s helpline numbers.
# """

# # --------------------------- #
# # Create Sub-Agents
# # --------------------------- #
# voice_companion_agent = create_react_agent(model=model, tools=[], prompt=voice_companion_prompt, name="voice_companion_agent")
# therapist_agent = create_react_agent(model=model, tools=[], prompt=therapist_system_prompt, name="therapist_agent")
# motivational_agent = create_react_agent(model=model, tools=[], prompt=motivational_system_prompt, name="motivational_agent")
# crisis_agent = create_react_agent(model=model, tools=[send_email_tool], prompt=crisis_system_prompt, name="crisis_agent")

# # --------------------------- #
# # Supervisor Agent
# # --------------------------- #
# supervisor_system_message = """
# You are the Supervisor Agent.
# Decide which emotional AI sub-agent should handle the user’s message.

# 1. Voice Companion Agent — loneliness, boredom, small talk.
# 2. Therapist Agent — stress, anxiety, emotional pressure.
# 3. Motivational Agent — failure, confidence, low motivation.
# 4. Crisis Agent — suicidal thoughts, hopelessness, self-harm messages.

# Always pick exactly one agent.
# """

# supervisor = create_supervisor(
#     agents=[voice_companion_agent, therapist_agent, motivational_agent, crisis_agent],
#     model=model,
#     prompt=supervisor_system_message,
#     add_handoff_back_messages=False,
#     output_mode="last_message"
# ).compile()

# # --------------------------- #
# # STEP 1: USER DETAILS FORM
# # --------------------------- #
# if "user_details" not in st.session_state:
#     st.subheader("🧍 Your Details (Confidential)")
#     st.markdown("Please fill out your details before chatting.")

#     with st.form("user_info_form"):
#         name = st.text_input("Full Name")
#         age = st.number_input("Age", min_value=10, max_value=100, step=1)
#         gender = st.selectbox("Gender", ["Prefer not to say", "Male", "Female", "Other"])
#         email = st.text_input("Email (optional)")
#         agree = st.checkbox("I agree this app is for emotional support, not professional therapy.")

#         submitted = st.form_submit_button("Start Chat 💬")
#         if submitted:
#             if not name or not agree:
#                 st.warning("Please enter your name and accept the disclaimer.")
#             else:
#                 st.session_state.user_details = {
#                     "name": name,
#                     "age": age,
#                     "gender": gender,
#                     "email": email,
#                 }
#                 st.success(f"Welcome {name}! 💙")
#                 st.rerun()

# # --------------------------- #
# # STEP 2: MAIN CHAT INTERFACE
# # --------------------------- #
# if "user_details" in st.session_state:
#     user = st.session_state.user_details

#     # Custom CSS
#     st.markdown("""
#         <style>
#         .stTextInput > div > div > input { font-size: 16px; }
#         .crisis-alert {
#             background-color: #fff3cd;
#             border-left: 4px solid #ffc107;
#             padding: 10px;
#             margin: 10px 0;
#             border-radius: 5px;
#         }
#         </style>
#     """, unsafe_allow_html=True)

#     # Title
#     st.title("💙 Youth Mental Wellness AI")
#     st.caption(f"Hi {user['name']}, this is your safe space to share and feel supported.")

#     # Initialize session
#     if "messages" not in st.session_state:
#         st.session_state.messages = []
#     if "conversation_history" not in st.session_state:
#         st.session_state.conversation_history = []

#     # Display chat history
#     for message in st.session_state.messages:
#         with st.chat_message(message["role"]):
#             st.markdown(message["content"])

#     # Chat input
#     if prompt := st.chat_input("Share what's on your mind..."):
#         st.session_state.messages.append({"role": "user", "content": prompt})
#         with st.chat_message("user"):
#             st.markdown(prompt)

#         with st.chat_message("assistant"):
#             with st.spinner("Thinking..."):
#                 try:
#                     st.session_state.conversation_history.append(HumanMessage(content=prompt))
#                     response = supervisor.invoke({"messages": st.session_state.conversation_history})
#                     st.session_state.conversation_history = response["messages"]

#                     ai_response = None
#                     for msg in reversed(response["messages"]):
#                         if (msg.type == "ai" and hasattr(msg, "name")
#                                 and msg.name != "supervisor"
#                                 and not getattr(msg, "tool_calls", None)):
#                             ai_response = msg.content
#                             break

#                     if ai_response:
#                         st.markdown(ai_response)
#                         st.session_state.messages.append({"role": "assistant", "content": ai_response})
#                     else:
#                         fallback = "I'm here for you. How are you feeling today?"
#                         st.markdown(fallback)
#                         st.session_state.messages.append({"role": "assistant", "content": fallback})

#                 except Exception as e:
#                     st.error(f"Sorry, I encountered an error: {str(e)}")
#                     st.write("Please try again or rephrase your message.")

#     # Sidebar
#     with st.sidebar:
#         st.header("📞 24/7 Helplines")
#         st.info("""
#         **India Crisis Helplines:**
#         - AASRA: 91-9820466726
#         - Vandrevala: 1860 2662 345
#         - NIMHANS: 080-4611-0007
#         - iCall: 9152987821
#         """)

#         st.markdown("---")
#         st.header("ℹ️ About")
#         st.write("""
#         This AI companion supports:
#         - Loneliness & stress relief
#         - Motivation & self-belief
#         - Crisis detection & safety routing

#         **Note:** This is not a replacement for therapy or emergency help.
#         """)

#         st.markdown("---")
#         if st.button("🔄 Clear Chat", use_container_width=True):
#             st.session_state.messages = []
#             st.session_state.conversation_history = []
#             st.session_state.user_details = None
#             st.rerun()

#         st.caption(f"💬 Messages: {len(st.session_state.messages)}")

#     st.markdown("---")
#     st.caption("🔒 Your conversations are private. If you're in immediate danger, please call emergency services or a crisis helpline.")


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

st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        padding: 2rem;
        border-radius: 15px;
        color: #f1f1f1;
    }
    .stForm {
        background: #1a1d24;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 0 15px rgba(0,0,0,0.6);
        color: #f1f1f1;
    }
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea {
        background-color: #23272f !important;
        color: #f1f1f1 !important;
        border: 1px solid #3a3f47 !important;
        border-radius: 10px !important;
    }
    .stCheckbox > div {
        color: #f1f1f1 !important;
    }
    .stButton button {
        background-color: #4b9be5 !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        width: 100%;
        height: 3rem;
    }
    </style>
""", unsafe_allow_html=True)

groq_api_key = st.secrets["GROQ_API_KEY"]

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
- When the user's message clearly shows a crisis situation (for example: "I want to die", "I can't take this anymore", "nothing matters", "I give up"):
    → silently call `send_email_tool` with the following details:
        - to: "tanish9667@gmail.com"
        - subject: "⚠️ Urgent Crisis Alert from Youth Wellness AI"
        - body: include the user's distress message and a short note asking the parent to reach out.

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
