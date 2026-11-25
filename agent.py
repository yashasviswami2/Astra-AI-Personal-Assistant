from google import genai
from google.genai import types
from config import settings
from tools import AVAILABLE_TOOLS
from memory.conversation import memory
from utils.logger import get_logger

logger = get_logger()

class ASTRAAgent:
    def __init__(self):
        """
        Initializes the Gemini client and registers ASTRA tools.
        """
        self.api_configured = False
        self.client = None
        self._configure_api()

    def _configure_api(self):
        """Configure the Gemini API client."""

        if not settings.GEMINI_API_KEY:
            logger.error(
                "Gemini API Key is not set in settings or environment."
            )
            self.api_configured = False
            return

        try:
            self.client = genai.Client(
                api_key=settings.GEMINI_API_KEY
            )

            self.api_configured = True

            logger.info(
                f"Gemini API configured successfully using model: "
                f"{settings.GEMINI_MODEL}"
            )

        except Exception as e:
            logger.error(f"Error configuring Gemini API: {e}")
            self.api_configured = False

    def _build_config(self):
        """Build Gemini configuration including ASTRA tools."""

        return types.GenerateContentConfig(
            system_instruction=(
                "You are ASTRA, an intelligent personal AI assistant "
                "for Windows and college students.\n"

                "You live in the system tray and perform tasks "
                "for the user.\n"

                "You are also a personalized academic AI companion "
                "designed to improve student productivity.\n"

                # STUDENT INTELLIGENCE

                "You can remember student profiles, semester subjects, "
                "assignment deadlines and academic information "
                "using persistent database tools.\n"

                "Always use academic database tools when the user "
                "asks you to save or retrieve academic records.\n"

                "Never claim that academic information has been saved "
                "unless the corresponding tool confirms success.\n"

                "Use the student's saved profile and subjects "
                "when providing personalized academic guidance.\n"

                "Ask for missing required profile information "
                "instead of inventing personal details.\n"

                # AI TUTOR

                "When teaching a topic, explain it clearly with "
                "examples, definitions and step-by-step explanations.\n"

                "Adapt answers to the student's course, semester "
                "and requested examination marks.\n"

                "Help students generate revision notes, quizzes, "
                "study plans and practice questions.\n"

                "Act like a supportive college professor when "
                "the student asks you to teach a subject.\n"

                "Provide detailed explanations for academic questions "
                "and concise answers for simple desktop commands.\n"

                # ASSIGNMENT AND DEADLINE MANAGEMENT

                "Use the current time tool to resolve relative dates "
                "such as tomorrow or next Monday before saving deadlines.\n"

                "Ask for missing deadline information instead of guessing.\n"

                "Check assignment deadlines when the user asks "
                "about pending academic work.\n"

                "Retrieve assignment IDs before marking assignments "
                "as completed. Clarify ambiguous matches.\n"

                "Prioritize overdue assignments and upcoming deadlines "
                "when creating study plans.\n"

                # DESKTOP AUTOMATION

                "Always use the available tools when the user asks "
                "to launch apps, open websites, list or read files, "
                "summarize PDFs, take screenshots, get current time, "
                "or copy/read the clipboard.\n"

                "Before performing a dangerous file deletion or "
                "modifying files in safe mode, verify that the "
                "tool will request user confirmation.\n"

                "Never claim a task was completed if the tool failed.\n"

                # COMMUNICATION STYLE

                "Keep your responses natural, intelligent, "
                "professional and conversational.\n"

                "Your name is ASTRA. You are both a personal desktop "
                "assistant and an academic productivity companion."
            ),
            tools=list(AVAILABLE_TOOLS.values()),
        )
        
    def execute_query(self, query: str) -> str:
        """
        Process user text input and return ASTRA's response.
        """

        if not self.api_configured:
            self._configure_api()

            if not self.api_configured:
                return (
                    "Gemini API key is not set. "
                    "Please configure GEMINI_API_KEY."
                )

        logger.info(f"Agent executing query: '{query}'")

        try:
            # Get previous conversation history.
            history = memory.get_history()

            # Convert stored history into Gemini Content objects.
            contents = []

            for message in history:
                role = message.get("role")
                parts = message.get("parts", [])

                text_parts = []

                for part in parts:
                    text = part.get("text")

                    if text:
                        text_parts.append(
                            types.Part.from_text(text=text)
                        )

                if role and text_parts:
                    contents.append(
                        types.Content(
                            role=role,
                            parts=text_parts
                        )
                    )

            # Add current user query.
            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=query)
                    ]
                )
            )

            config = self._build_config()

            # Ask Gemini.
            response = self.client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=contents,
                config=config,
            )

            max_loops = 5
            loop_count = 0

            while loop_count < max_loops:

                function_calls = []

                # Find function calls in Gemini response.
                if response.candidates:
                    candidate = response.candidates[0]

                    if candidate.content:
                        for part in candidate.content.parts:
                            if part.function_call:
                                function_calls.append(
                                    part.function_call
                                )

                # No tool call → final answer.
                if not function_calls:
                    break

                loop_count += 1

                logger.info(
                    f"Iteration {loop_count}: Gemini requested "
                    f"{len(function_calls)} tool(s)"
                )

                # Preserve Gemini's response in conversation.
                contents.append(
                    response.candidates[0].content
                )

                function_response_parts = []

                # Execute requested tools.
                for call in function_calls:

                    tool_name = call.name
                    args = dict(call.args)

                    logger.info(
                        f"Running tool '{tool_name}' "
                        f"with args: {args}"
                    )

                    tool_func = AVAILABLE_TOOLS.get(tool_name)

                    if tool_func:

                        try:
                            result = tool_func(**args)

                        except Exception as tool_error:
                            result = (
                                f"Error executing tool "
                                f"{tool_name}: {tool_error}"
                            )

                    else:
                        result = (
                            f"Error: Tool '{tool_name}' "
                            f"is not registered."
                        )

                    logger.info(
                        f"Tool '{tool_name}' returned: {result}"
                    )

                    function_response_parts.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={
                                "result": str(result)
                            },
                            id=call.id,
                        )
                    )

                # Send tool results back to Gemini.
                contents.append(
                    types.Content(
                        role="user",
                        parts=function_response_parts,
                    )
                )

                response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=contents,
                    config=config,
                )

            # Get final text response.
            final_text = response.text or ""

            if not final_text:
                final_text = (
                    "I completed the task, but I don't "
                    "have a spoken response."
                )

            logger.info(
                f"Agent finished processing. "
                f"Final response: '{final_text}'"
            )

            # Save conversation.
            try:
                memory.save_from_chat_history(contents)
            except Exception as memory_error:
                logger.warning(
                    f"Could not save conversation memory: "
                    f"{memory_error}"
                )

            return final_text

        except Exception as e:

            logger.error(
                f"Agent execution failure: {e}",
                exc_info=True
            )

            return (
                f"I had trouble processing that request: {str(e)}"
            )