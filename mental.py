import streamlit as st
from typing import List, Dict
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from IPython.display import Image, display
from langchain_core.messages import HumanMessage, SystemMessage
import os
from langchain_core.tools import tool
#from googleapiclient.discovery import build
#from google.oauth2.credentials import Credentials

os.environ["GROQ_API_KEY"] = "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"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGSMITH_PROJECT"] = "ff10"
os.environ["LANGSMITH_API_KEY"] = "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"

model = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
# -------------------------------
# Add this before you use create_supervisor
# -------------------------------

from langgraph.graph import StateGraph, END

def create_supervisor(agents, model, prompt, add_handoff_back_messages=False, output_mode="last_message"):
    """
    Creates a supervisor agent that delegates user messages to sub-agents.
    """
    import langchain_core
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    from langgraph.prebuilt import create_react_agent

    # Create the supervisor agent
    supervisor_agent = create_react_agent(
        model=model,
        tools=[],
        prompt=prompt,
        name="supervisor"
    )

    # Define a simple graph
    graph = StateGraph()

    # Add supervisor and sub-agents
    graph.add_node("supervisor", supervisor_agent)
    for agent in agents:
        graph.add_node(agent.name, agent)

    # Route messages (simplified)
    for agent in agents:
        graph.add_edge("supervisor", agent.name)
        graph.add_edge(agent.name, END)

    graph.set_entry_point("supervisor")
    return graph



voice_companion_prompt = """
You are the AI  Companion — a warm, friendly, and non-judgmental friend.
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

voice_companion_agent = create_react_agent(
    model=model,
    tools=[],
    prompt=voice_companion_prompt,
    name="voice_companion_agent"
)

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
- Focus on emotional validation: “It’s okay to feel that way.”
- Encourage reflection and healthy habits (study breaks, journaling, rest).
- Keep the conversation safe, confidential, and kind.
"""

therapist_agent = create_react_agent(
    model=model,
    tools=[],
    prompt=therapist_system_prompt,
    name="therapist_agent"
)
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
- Validate effort before giving advice (“You’re trying, and that matters.”).
- Remind users that failure is feedback.
- Focus on growth mindset: small steps → big progress.
- Avoid judgment or comparison.
- Never mention therapy, medication, or diagnosis.
"""

motivational_agent = create_react_agent(
    model=model,
    tools=[],
    prompt=motivational_system_prompt,
    name="motivational_agent"
)

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

crisis_agent = create_react_agent(
    model=model,
    tools=[],
    prompt=crisis_system_prompt,
    name="crisis_agent"
)

supervisor_system_message = """
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
   - Example: "I’m stressed about my exams." → therapist_agent

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
- If it’s about motivation, failure, or confidence → choose Motivational Coach Agent.
- If it’s anxiety, exam stress, or emotional overwhelm → choose Therapist-like Agent.
- Never respond directly; only route to a sub-agent.
- Do not mix multiple agents at once.
- Keep routing logic safe and emotionally appropriate.
"""

supervisor = create_supervisor(
    agents=[
        voice_companion_agent,
        therapist_agent,
        motivational_agent,
        crisis_agent
    ],
    model=model,
    prompt=supervisor_system_message,
    add_handoff_back_messages=False,
    output_mode="last_message"
).compile()
            
st.set_page_config(
    page_title="Youth Mental Wellness AI",
    page_icon="💙",
    layout="centered"
)

# Custom CSS for better chat UI
st.markdown("""
    <style>
    .stTextInput > div > div > input {
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("💙 Youth Mental Wellness AI")
st.caption("A safe space to talk. You're not alone.")

# Initialize session state for conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

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
            # Add to conversation history
            st.session_state.conversation_history.append(HumanMessage(content=prompt))
            
            # Get response from supervisor
            response = supervisor.invoke({"messages": st.session_state.conversation_history})
            st.session_state.conversation_history = response['messages']
            
            # Extract final agent response
            ai_response = None
            for msg in reversed(response['messages']):
                if (msg.type == 'ai' and 
                    hasattr(msg, 'name') and 
                    msg.name != 'supervisor' and
                    not getattr(msg, 'tool_calls', None)):
                    ai_response = msg.content
                    break
            
            if ai_response:
                st.markdown(ai_response)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
            else:
                st.error("Sorry, I couldn't generate a response. Please try again.")

# Sidebar with info
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
        st.session_state.conversation_history = []
        st.rerun()
