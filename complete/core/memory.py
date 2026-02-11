"""
Session Memory - Persistent session storage
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict, field


@dataclass
class Session:
    """Represents a conversation session."""

    id: str
    created_at: str
    updated_at: str
    title: str
    messages: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class SessionManager:
    """Manages session persistence."""

    def __init__(self, sessions_dir: str = "./sessions"):
        """
        Initialize session manager.

        Args:
            sessions_dir: Directory for storing session files
        """
        self.sessions_dir = sessions_dir
        os.makedirs(sessions_dir, exist_ok=True)

    def create(self, title: str = "New Session") -> Session:
        """
        Create a new session.

        Args:
            title: Session title

        Returns:
            New Session object
        """
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        now = datetime.now().isoformat()

        session = Session(
            id=session_id,
            created_at=now,
            updated_at=now,
            title=title,
            messages=[],
            metadata={},
        )
        self.save(session)
        return session

    def save(self, session: Session):
        """
        Save session to disk.

        Args:
            session: Session object to save
        """
        session.updated_at = datetime.now().isoformat()
        path = os.path.join(self.sessions_dir, f"{session.id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(session), f, indent=2)

    def load(self, session_id: str) -> Optional[Session]:
        """
        Load session from disk.

        Args:
            session_id: Session identifier

        Returns:
            Session object or None if not found
        """
        path = os.path.join(self.sessions_dir, f"{session_id}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Session(**data)

    def list_sessions(self) -> List[Dict]:
        """
        List all sessions.

        Returns:
            List of session summaries sorted by update time
        """
        sessions = []
        for filename in os.listdir(self.sessions_dir):
            if filename.endswith(".json"):
                path = os.path.join(self.sessions_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    sessions.append(
                        {
                            "id": data.get("id"),
                            "title": data.get("title"),
                            "created_at": data.get("created_at"),
                            "updated_at": data.get("updated_at"),
                            "message_count": len(data.get("messages", [])),
                        }
                    )
                except (json.JSONDecodeError, KeyError):
                    continue

        return sorted(sessions, key=lambda x: x.get("updated_at", ""), reverse=True)

    def delete(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        path = os.path.join(self.sessions_dir, f"{session_id}.json")
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def add_message(self, session: Session, role: str, content: Any):
        """
        Add a message to session.

        Args:
            session: Session object
            role: Message role ("user" or "assistant")
            content: Message content
        """
        session.messages.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self.save(session)

    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """
        Get most recent sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of recent session summaries
        """
        sessions = self.list_sessions()
        return sessions[:limit]

    def search_sessions(self, query: str) -> List[Dict]:
        """
        Search sessions by title or content.

        Args:
            query: Search query

        Returns:
            List of matching session summaries
        """
        query_lower = query.lower()
        results = []

        for filename in os.listdir(self.sessions_dir):
            if filename.endswith(".json"):
                path = os.path.join(self.sessions_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    # Search in title
                    if query_lower in data.get("title", "").lower():
                        results.append(
                            {
                                "id": data.get("id"),
                                "title": data.get("title"),
                                "updated_at": data.get("updated_at"),
                                "match": "title",
                            }
                        )
                        continue

                    # Search in messages
                    for msg in data.get("messages", []):
                        content = str(msg.get("content", ""))
                        if query_lower in content.lower():
                            results.append(
                                {
                                    "id": data.get("id"),
                                    "title": data.get("title"),
                                    "updated_at": data.get("updated_at"),
                                    "match": "content",
                                }
                            )
                            break
                except (json.JSONDecodeError, KeyError):
                    continue

        return sorted(results, key=lambda x: x.get("updated_at", ""), reverse=True)

    def export_session(self, session_id: str, output_path: str) -> bool:
        """
        Export session to a file.

        Args:
            session_id: Session identifier
            output_path: Output file path

        Returns:
            True if exported successfully
        """
        session = self.load(session_id)
        if not session:
            return False

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(asdict(session), f, indent=2)
        return True


# Fix missing import
from typing import Any
