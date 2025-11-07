import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Dict, Any, Annotated
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import os
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# Set environment variables
os.environ["GROQ_API_KEY"] = "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"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGSMITH_PROJECT"] = "ff10"
os.environ["LANGSMITH_API_KEY"] = "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"

# Initialize model
model = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))

# Define state schema properly
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

def create_supervisor(agents, model, prompt):
    """
    Creates a supervisor agent that delegates user messages to sub-agents.
    """
    # Create the graph with proper state
    workflow = StateGraph(AgentState)
    
    # Supervisor node function
    def supervisor_node(state: AgentState):
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        # Route based on keywords
        lower_msg = last_message.lower()
        
        # Crisis detection (highest priority)
        crisis_keywords = ["die", "suicide", "end it", "kill myself", "no point", "can't take this"]
        if any(keyword in lower_msg for keyword in crisis_keywords):
            return {"next": "crisis_agent"}
        
        # Stress/anxiety detection
        stress_keywords = ["stress", "anxious", "anxiety", "exam", "pressure", "overwhelm", "overthinking"]
        if any(keyword in lower_msg for keyword in stress_keywords):
            return {"next": "therapist_agent"}
        
        # Motivation detection
        motivation_keywords = ["fail", "motivation", "lazy", "tired", "can't do", "useless", "give up"]
        if any(keyword in lower_msg for keyword in motivation_keywords):
            return {"next": "motivational_agent"}
        
        # Default to voice companion
        return {"next": "voice_companion_agent"}
    
    # Add supervisor node
    workflow.add_node("supervisor", supervisor_node)
    
    # Add agent nodes
    for agent in agents:
        workflow.add_node(agent.name, agent)
    
    # Add conditional edges from supervisor to agents
    def route_to_agent(state: AgentState) -> str:
        # Get the routing decision from supervisor
        supervisor_result = supervisor_node(state)
        return supervisor_result["next"]
    
    workflow.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "voice_companion_agent": "voice_companion_agent",
            "therapist_agent": "therapist_agent",
            "motivational_agent": "motivational_agent",
            "crisis_agent": "crisis_agent"
        }
    )
    
    # All agents end after responding
    for agent in agents:
        workflow.add_edge(agent.name, END)
    
    # Set entry point
    workflow.set_entry_point("supervisor")
    
    return workflow

# Voice Companion Agent
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

voice_companion_agent = create_react_agent(
    model=model,
    tools=[],
    state_schema=AgentState,
    messages_modifier=voice_companion_prompt
)

# Therapist Agent
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

therapist_agent = create_react_agent(
    model=model,
    tools=[],
    state_schema=AgentState,
    messages_modifier=therapist_system_prompt
)

# Motivational Agent
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

motivational_agent = create_react_agent(
    model=model,
    tools=[],
    state_schema=AgentState,
    messages_modifier=motivational_system_prompt
)

# Crisis Agent
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
    state_schema=AgentState,
    messages_modifier=crisis_system_prompt
)

# Supervisor system message
supervisor_system_message = """
You are the Supervisor Agent that routes messages to the appropriate sub-agent.
"""

# Create and compile supervisor
supervisor = create_supervisor(
    agents=[
        voice_companion_agent,
        therapist_agent,
        motivational_agent,
        crisis_agent
    ],
    model=model,
    prompt=supervisor_system_message
).compile()

# Streamlit UI
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
            try:
                response = supervisor.invoke({"messages": st.session_state.conversation_history})
                st.session_state.conversation_history = response['messages']
                
                # Extract final agent response
                ai_response = None
                for msg in reversed(response['messages']):
                    if hasattr(msg, 'content') and isinstance(msg.content, str) and msg.content.strip():
                        if msg.type == 'ai':
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
                st.error(f"Sorry, I encountered an error: {str(e)}")

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
