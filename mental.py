import streamlit as st
from typing import List, Dict, Annotated, Literal
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END, MessagesState
from langgraph.types import Command
import os

# SECURITY: Use environment variables or Streamlit secrets instead
os.environ["GROQ_API_KEY"] = "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"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGSMITH_PROJECT"] = "ff10"
os.environ["LANGSMITH_API_KEY"] = "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"

# Get API key from Streamlit secrets or environment
groq_api_key = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
model = ChatGroq(model="llama-3.3-70b-versatile", api_key=groq_api_key)

# Agent prompts (keeping your original prompts)
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

crisis_system_prompt = """
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

🚫 Do NOT:
- Say that you are sending an email.
- Reveal any internal system or tool names.
- Give therapy, diagnosis, or medical advice.

Your goal is to comfort the user, ensure safety, and guide them to real human help.
"""

# Create individual agents
voice_companion_agent = create_react_agent(
    model=model,
    tools=[],
    state_modifier=voice_companion_prompt
)

therapist_agent = create_react_agent(
    model=model,
    tools=[],
    state_modifier=therapist_system_prompt
)

motivational_agent = create_react_agent(
    model=model,
    tools=[],
    state_modifier=motivational_system_prompt
)

crisis_agent = create_react_agent(
    model=model,
    tools=[],
    state_modifier=crisis_system_prompt
)

# Supervisor routing logic
def supervisor_node(state: MessagesState):
    """Supervisor decides which agent to route to based on user message"""
    
    supervisor_prompt = """
You are the Supervisor Agent. Analyze the user's message and respond with ONLY ONE of these agent names:
- voice_companion_agent (for loneliness, casual chat, wanting someone to talk to)
- therapist_agent (for stress, anxiety, exam pressure, overthinking)
- motivational_agent (for low motivation, self-doubt, failure recovery)
- crisis_agent (for severe distress, suicidal thoughts, self-harm)

Respond with ONLY the agent name, nothing else.

User message: {message}
"""
    
    last_message = state["messages"][-1].content
    
    response = model.invoke([
        SystemMessage(content=supervisor_prompt.format(message=last_message))
    ])
    
    # Extract agent name from response
    agent_name = response.content.strip().lower()
    
    # Map to valid agent names
    agent_mapping = {
        "voice_companion_agent": "voice_companion_agent",
        "therapist_agent": "therapist_agent",
        "motivational_agent": "motivational_agent",
        "crisis_agent": "crisis_agent"
    }
    
    # Default to voice companion if unclear
    selected_agent = agent_mapping.get(agent_name, "voice_companion_agent")
    
    return Command(goto=selected_agent)

# Build the graph
workflow = StateGraph(MessagesState)

# Add nodes
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("voice_companion_agent", voice_companion_agent)
workflow.add_node("therapist_agent", therapist_agent)
workflow.add_node("motivational_agent", motivational_agent)
workflow.add_node("crisis_agent", crisis_agent)

# Set entry point
workflow.set_entry_point("supervisor")

# Add edges from agents to END
workflow.add_edge("voice_companion_agent", END)
workflow.add_edge("therapist_agent", END)
workflow.add_edge("motivational_agent", END)
workflow.add_edge("crisis_agent", END)

# Compile the graph
app = workflow.compile()

# Streamlit UI
st.set_page_config(
    page_title="Youth Mental Wellness AI",
    page_icon="💙",
    layout="centered"
)

st.markdown("""
    <style>
    .stTextInput > div > div > input {
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💙 Youth Mental Wellness AI")
st.caption("A safe space to talk. You're not alone.")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Share what's on your mind..."):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Invoke the graph
            result = app.invoke({"messages": [HumanMessage(content=prompt)]})
            
            # Extract the last AI message
            ai_response = None
            for msg in reversed(result['messages']):
                if isinstance(msg, AIMessage):
                    ai_response = msg.content
                    break
            
            if ai_response:
                st.markdown(ai_response)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
            else:
                st.error("Sorry, I couldn't generate a response. Please try again.")

# Sidebar
with st.sidebar:
    st.header("📞 24/7 Helplines")
    st.info("""
    **India Crisis Helplines:**
    - AASRA: 91-9820466726
    - Vandrevala: 1860 2662 345
    - NIMHANS: 080-4611-0007
    - iCall: 9152987821
    """)
    
    if st.button("🔄 Clear Chat"):
        st.session_state.messages = []
        st.rerun()
