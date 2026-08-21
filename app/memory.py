from typing import List, Dict, Any, Optional
from app.tools import OrderLookupService

class ConversationTurn:
    def __init__(
        self,
        role: str,
        content: str,
        sources: Optional[List[str]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        needs_handoff: bool = False,
    ):
        self.role = role
        self.content = content
        self.sources = sources or []
        self.tool_calls = tool_calls or []
        self.needs_handoff = needs_handoff

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "sources": self.sources,
            "tool_calls": self.tool_calls,
            "needs_handoff": self.needs_handoff,
        }

class ConversationSession:
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.turns: List[ConversationTurn] = []
        self.last_order_id: Optional[str] = None
        self.last_topic: Optional[str] = None

    def add_turn(
        self,
        role: str,
        content: str,
        sources: Optional[List[str]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        needs_handoff: bool = False,
    ):
        turn = ConversationTurn(
            role=role,
            content=content,
            sources=sources,
            tool_calls=tool_calls,
            needs_handoff=needs_handoff,
        )
        self.turns.append(turn)

        # Track contextual entity if found
        extracted_oid = OrderLookupService.extract_order_id(content)
        if extracted_oid:
            self.last_order_id = extracted_oid

    def resolve_contextual_query(self, current_user_query: str) -> str:
        """
        Enriches a follow-up query with context from previous turns if it contains pronouns
        or implicit references (e.g. 'When will it arrive?', 'What about Canada?').
        """
        query_lower = current_user_query.lower().strip()
        
        # Check if the query is a follow-up for a previous order
        has_pronoun_or_short = any(p in query_lower for p in ["it", "arrive", "status", "tracking", "carrier", "where is", "when will"])
        has_explicit_order = bool(OrderLookupService.extract_order_id(current_user_query))

        if self.last_order_id and not has_explicit_order and has_pronoun_or_short:
            return f"{current_user_query} (referring to order {self.last_order_id})"

        # Check for shipping follow-ups (e.g. "What about Canada?")
        if "canada" in query_lower and len(self.turns) > 0:
            last_user_turn = next((t.content for t in reversed(self.turns) if t.role == "user"), "")
            if "international" in last_user_turn.lower() or "shipping" in last_user_turn.lower():
                return f"International shipping: {current_user_query}"

        return current_user_query

    def get_history_summary(self, max_turns: int = 6) -> List[Dict[str, str]]:
        """Returns the recent history formatted for LLM prompts."""
        recent = self.turns[-max_turns:]
        return [{"role": t.role, "content": t.content} for t in recent]

    def clear(self):
        self.turns.clear()
        self.last_order_id = None
        self.last_topic = None

class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, ConversationSession] = {}

    def get_session(self, session_id: str = "default") -> ConversationSession:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationSession(session_id=session_id)
        return self._sessions[session_id]

    def clear_session(self, session_id: str = "default"):
        if session_id in self._sessions:
            self._sessions[session_id].clear()

session_manager = SessionManager()
