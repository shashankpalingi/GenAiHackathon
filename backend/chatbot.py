"""
Drishyamitra - Conversational AI Chatbot
Powered by Groq API (Llama 3.3 70B / Mixtral 8x7B)
Adapted from FileMind's /ask RAG endpoint pattern.
"""

import os
import json
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL


# Initialize Groq client
client = None
if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)


# Conversation history per session (in-memory)
_conversations = {}


def process_query(user_query, context=None, session_id="default"):
    """
    Process a natural language query from the user.
    Parses intent and generates an appropriate response.
    
    Adapted from FileMind's RAG /ask endpoint — same context injection pattern,
    but uses Groq instead of Gemini, and photo/person context instead of documents.
    
    Args:
        user_query: The user's natural language input
        context: Dict with system state (persons, photos, etc.)
        session_id: Session identifier for conversation history
    
    Returns:
        dict: {"response": str, "intent": str, "action": dict or None}
    """
    if not client:
        return {
            "response": "Chatbot is not configured. Please set GROQ_API_KEY.",
            "intent": "error",
            "action": None
        }

    try:
        # Build context string from system state
        context_str = _build_context(context)

        # Get conversation history
        history = _conversations.get(session_id, [])

        # System prompt
        system_prompt = f"""You are Drishyamitra, an AI-powered photo management assistant.
You help users organize, search, and share their photos using face recognition.

Your capabilities:
- Search photos by person name (e.g., "Show me photos of Mom")
- Organize photos into person-specific folders
- Send photos via email or WhatsApp
- Answer questions about their photo collection
- Name or rename detected persons

Current System State:
{context_str}

Rules:
- Be concise and helpful
- If the user wants to search for a person, extract the person's name and return it as an action
- If the user wants to send/share photos, extract recipient and method as an action
- Always respond in a friendly, conversational tone

For actions, respond with a JSON block at the end of your message:
ACTION: {{"type": "search_person", "person_name": "..."}}
ACTION: {{"type": "send_photos", "method": "email|whatsapp", "recipient": "...", "person_name": "..."}}
ACTION: {{"type": "rename_person", "person_id": "...", "new_name": "..."}}
ACTION: {{"type": "list_persons"}}
ACTION: {{"type": "none"}}
"""

        # Build messages for Groq
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history[-10:])  # Last 10 messages for context
        messages.append({"role": "user", "content": user_query})

        # Call Groq API
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )

        reply = response.choices[0].message.content.strip()

        # Store conversation history
        if session_id not in _conversations:
            _conversations[session_id] = []
        _conversations[session_id].append({"role": "user", "content": user_query})
        _conversations[session_id].append({"role": "assistant", "content": reply})

        # Keep history manageable
        if len(_conversations[session_id]) > 20:
            _conversations[session_id] = _conversations[session_id][-20:]

        # Parse action from response
        action = _parse_action(reply)

        # Clean reply (remove ACTION line)
        clean_reply = reply
        if "ACTION:" in reply:
            clean_reply = reply[:reply.rfind("ACTION:")].strip()

        return {
            "response": clean_reply,
            "intent": action.get("type", "none") if action else "none",
            "action": action
        }

    except Exception as e:
        print(f"Chatbot Error: {e}")
        error_msg = "I encountered an error. Please try again."
        if "429" in str(e):
            error_msg = "I'm being rate-limited. Please wait a moment and try again."
        return {
            "response": error_msg,
            "intent": "error",
            "action": None,
            "error": str(e)
        }


def _build_context(context):
    """Build a context string from system state."""
    if not context:
        return "No system state available."

    parts = []

    persons = context.get("persons", {})
    if persons:
        parts.append(f"Known Persons ({len(persons)}):")
        for pid, info in persons.items():
            parts.append(f"  - {info.get('name', pid)}: {info.get('photo_count', 0)} photos")

    total_photos = context.get("total_photos", 0)
    if total_photos:
        parts.append(f"\nTotal Photos: {total_photos}")

    return "\n".join(parts) if parts else "Photo collection is empty."


def _parse_action(response_text):
    """Extract ACTION JSON from the response."""
    try:
        if "ACTION:" in response_text:
            action_str = response_text[response_text.rfind("ACTION:") + 7:].strip()
            # Find JSON object
            start = action_str.find("{")
            end = action_str.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(action_str[start:end])
    except (json.JSONDecodeError, ValueError):
        pass
    return {"type": "none"}


def clear_session(session_id="default"):
    """Clear conversation history for a session."""
    _conversations.pop(session_id, None)
