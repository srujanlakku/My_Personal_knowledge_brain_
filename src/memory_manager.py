
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import List
from loguru import logger
from langchain_community.chat_message_histories import (
    ChatMessageHistory,
)
from langchain_core.messages import HumanMessage, AIMessage
from config import Config


class MemoryManager:

    def __init__(self):
        self._history = ChatMessageHistory()
        self._messages: List[dict] = []
        self._last_user_msg: str = ""
        self._db_path = (
            Path(Config.SESSIONS_PATH) / "chat_history.db"
        )
        self._init_db()

    def _init_db(self) -> None:
        Path(Config.SESSIONS_PATH).mkdir(
            parents=True, exist_ok=True
        )
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                sources TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

    def add_message(
        self,
        role: str,
        content: str,
        sources: List[dict] = None,
    ) -> None:
        ts = datetime.now().strftime("%H:%M")
        self._messages.append({
            "role": role,
            "content": content,
            "sources": sources or [],
            "timestamp": ts,
        })
        if role == "user":
            self._last_user_msg = content
            self._history.add_user_message(content)
        elif role == "assistant":
            self._history.add_ai_message(content)

    def get_history_messages(self) -> list:
        return self._history.messages

    def get_display_messages(self) -> List[dict]:
        return self._messages

    def clear_memory(self) -> None:
        self._history.clear()
        self._messages = []
        self._last_user_msg = ""

    def get_message_count(self) -> int:
        return len(self._messages)

    def save_session(self, name: str) -> str:
        sid = str(uuid.uuid4())
        now = datetime.now().isoformat()
        conn = sqlite3.connect(str(self._db_path))
        conn.execute(
            "INSERT INTO sessions VALUES (?,?,?)",
            (sid, name, now),
        )
        for msg in self._messages:
            conn.execute(
                "INSERT INTO messages "
                "(session_id,role,content,sources,timestamp)"
                " VALUES (?,?,?,?,?)",
                (
                    sid,
                    msg["role"],
                    msg["content"],
                    json.dumps(msg.get("sources", [])),
                    msg.get("timestamp", now),
                ),
            )
        conn.commit()
        conn.close()
        return sid

    def get_all_sessions(self) -> List[dict]:
        try:
            conn = sqlite3.connect(str(self._db_path))
            cur = conn.execute(
                "SELECT id,name,created_at FROM sessions "
                "ORDER BY created_at DESC"
            )
            sessions = [
                {"id": r[0], "name": r[1], "created": r[2]}
                for r in cur.fetchall()
            ]
            conn.close()
            return sessions
        except Exception:
            return []
