import json
from pathlib import Path


class ConversationMemory:

    def __init__(self):
        self.memory_dir = Path(__file__).resolve().parent
        self.memory_file = self.memory_dir / "conversation.json"

    def get_history(self):
        """Load previous conversation history."""

        if not self.memory_file.exists():
            return []

        try:
            with open(
                self.memory_file,
                "r",
                encoding="utf-8"
            ) as f:
                return json.load(f)

        except (json.JSONDecodeError, OSError):
            return []

    def save_from_chat_history(self, chat_history):
        """Save Gemini conversation history locally."""

        try:

            history = []

            for message in chat_history:

                role = getattr(
                    message,
                    "role",
                    None
                )

                parts = getattr(
                    message,
                    "parts",
                    []
                )

                converted_parts = []

                for part in parts:

                    text = getattr(
                        part,
                        "text",
                        None
                    )

                    if text:

                        converted_parts.append({
                            "text": text
                        })

                if role and converted_parts:

                    history.append({
                        "role": role,
                        "parts": converted_parts
                    })

            with open(
                self.memory_file,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    history,
                    f,
                    indent=2,
                    ensure_ascii=False
                )

        except Exception:
            # Memory should never crash JARVIS.
            pass

    def clear_history(self):
        """Clear all saved conversation history."""

        try:

            with open(
                self.memory_file,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    [],
                    f,
                    indent=2
                )

            return True

        except Exception:

            return False


memory = ConversationMemory()