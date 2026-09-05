import json
from pathlib import Path


class ConversationMemory:

    def __init__(self):
        self.memory_dir = Path(__file__).resolve().parent
        self.memory_file = self.memory_dir / "conversation.json"

    def get_history(self):
        """
        Load previous conversation history.

        Returns:
            list: Stored conversation messages.
        """

        if not self.memory_file.exists():
            return []

        try:
            with open(
                self.memory_file,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

                if isinstance(data, list):
                    return data

                return []

        except (json.JSONDecodeError, OSError):
            return []

    def save_message(self, role, text):
        """
        Save a single conversation message.

        Args:
            role: 'user' or 'model'
            text: Message text.
        """

        if not text:
            return

        try:
            history = self.get_history()

            history.append(
                {
                    "role": role,
                    "parts": [
                        {
                            "text": str(text)
                        }
                    ]
                }
            )

            # Keep the most recent 50 messages.
            history = history[-50:]

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

    def save_conversation(self, user_text, assistant_text):
        """
        Save both sides of a conversation.
        """

        try:

            history = self.get_history()

            if user_text:
                history.append(
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": str(user_text)
                            }
                        ]
                    }
                )

            if assistant_text:
                history.append(
                    {
                        "role": "model",
                        "parts": [
                            {
                                "text": str(assistant_text)
                            }
                        ]
                    }
                )

            # Prevent unlimited memory growth.
            history = history[-50:]

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
            # Memory must never crash JARVIS.
            pass

    def clear_memory(self):
        """
        Delete stored conversation history.
        """

        try:

            if self.memory_file.exists():
                self.memory_file.unlink()

            return "Conversation memory cleared successfully."

        except Exception as e:

            return f"Failed to clear conversation memory: {str(e)}"


memory = ConversationMemory()