from google import genai
from google.genai import types

from config import settings
from tools import AVAILABLE_TOOLS
from memory.conversation import memory
from utils.logger import get_logger


logger = get_logger()


class JarvisAgent:

    def __init__(self):
        """
        Initialize the Gemini client and JARVIS tools.
        """

        self.api_configured = False
        self.client = None

        self._configure_api()


    # =========================================================
    # GEMINI CONFIGURATION
    # =========================================================

    def _configure_api(self):
        """
        Configure the Gemini API client.
        """

        if not settings.GEMINI_API_KEY:

            logger.error(
                "Gemini API Key is not set."
            )

            self.api_configured = False

            return


        try:

            self.client = genai.Client(
                api_key=settings.GEMINI_API_KEY
            )

            self.api_configured = True

            logger.info(
                "Gemini API configured successfully "
                f"using model: {settings.GEMINI_MODEL}"
            )


        except Exception as e:

            logger.error(
                f"Error configuring Gemini API: {e}"
            )

            self.api_configured = False


    # =========================================================
    # GEMINI CONFIGURATION
    # =========================================================

    def _build_config(self):

        """
        Build Gemini configuration and register JARVIS tools.
        """

        return types.GenerateContentConfig(

            system_instruction=(

                "You are JARVIS, a helpful and intelligent "
                "Windows desktop AI assistant.\n\n"

                "You live on the user's computer and can "
                "perform tasks using the available tools.\n\n"

                "Keep normal responses natural and reasonably "
                "brief because many responses are spoken aloud.\n\n"


                # =================================================
                # TOOL RULES
                # =================================================

                "IMPORTANT TOOL RULES:\n\n"


                "1. When the user asks for the current time, "
                "use the get_current_time tool.\n\n"


                "2. When the user asks for today's date, "
                "the current date, or what date it is, "
                "use the get_current_date tool.\n\n"


                "3. When the user asks to launch an application, "
                "use the launch_app tool.\n\n"


                "4. When the user asks to open a website, "
                "use the browser tools.\n\n"


                "5. When the user asks to search the web, "
                "use the web_search tool.\n\n"


                "6. When the user asks to list, read, write, "
                "or delete files, use the appropriate "
                "file-management tools.\n\n"


                # =================================================
                # PDF RULES
                # =================================================

                "7. When the user asks to summarize, explain, "
                "or analyze a PDF, first identify the PDF file.\n\n"


                "8. If the user provides an exact PDF path, "
                "use extract_pdf_text directly with that path.\n\n"


                "9. If the user does not provide an exact PDF "
                "path, use find_pdf_files to search for the "
                "relevant PDF using the filename or topic "
                "provided by the user.\n\n"


                "10. After finding the relevant PDF, use "
                "extract_pdf_text to read its contents.\n\n"


                "11. After receiving the extracted PDF text, "
                "generate a clear summary based only on the "
                "PDF content.\n\n"


                "12. For PDF summaries, use useful sections "
                "such as Overview, Key Points, Important "
                "Concepts, and Conclusion when appropriate.\n\n"


                "13. If multiple PDFs match the user's request, "
                "ask the user which PDF they want unless "
                "one result is clearly the intended document.\n\n"


                "14. If PDF extraction fails, clearly explain "
                "the problem instead of pretending to have "
                "read the PDF.\n\n"


                # =================================================
                # SCREENSHOT
                # =================================================

                "15. When the user asks to take a screenshot, "
                "use the take_screenshot tool.\n\n"


                # =================================================
                # GENERAL TOOL SAFETY
                # =================================================

                "16. Always use an available tool when it is "
                "appropriate instead of guessing the result.\n\n"


                "17. Never claim that an application was opened, "
                "a file was created, a screenshot was captured, "
                "or another system action was completed unless "
                "the corresponding tool actually returned "
                "a successful result.\n\n"


                "18. For dangerous file operations, respect "
                "the confirmation requested by the tool.\n"

            ),

            tools=list(
                AVAILABLE_TOOLS.values()
            ),
        )


    # =========================================================
    # EXECUTE USER QUERY
    # =========================================================

    def execute_query(self, query: str) -> str:

        """
        Process a user query using Gemini and JARVIS tools.
        """

        # -----------------------------------------------------
        # Check API
        # -----------------------------------------------------

        if not self.api_configured:

            self._configure_api()

            if not self.api_configured:

                return (
                    "Gemini API key is not configured. "
                    "Please configure GEMINI_API_KEY."
                )


        logger.info(
            f"Agent executing query: '{query}'"
        )


        try:

            # =================================================
            # LOAD MEMORY
            # =================================================

            history = memory.get_history()

            contents = []


            for message in history:

                role = message.get(
                    "role"
                )

                parts = message.get(
                    "parts",
                    []
                )


                text_parts = []


                for part in parts:

                    text = part.get(
                        "text"
                    )


                    if text:

                        text_parts.append(
                            types.Part.from_text(
                                text=text
                            )
                        )


                if role and text_parts:

                    contents.append(
                        types.Content(
                            role=role,
                            parts=text_parts
                        )
                    )


            # =================================================
            # CURRENT USER QUERY
            # =================================================

            contents.append(

                types.Content(

                    role="user",

                    parts=[
                        types.Part.from_text(
                            text=query
                        )
                    ]
                )
            )


            # =================================================
            # BUILD CONFIG
            # =================================================

            config = self._build_config()


            # =================================================
            # GEMINI REQUEST
            # =================================================

            response = (
                self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=contents,
                    config=config,
                )
            )


            # =================================================
            # TOOL EXECUTION LOOP
            # =================================================

            max_loops = 5
            loop_count = 0


            while loop_count < max_loops:

                function_calls = []


                # -------------------------------------------------
                # Find tool calls
                # -------------------------------------------------

                if response.candidates:

                    candidate = (
                        response.candidates[0]
                    )


                    if candidate.content:

                        for part in candidate.content.parts:

                            if part.function_call:

                                function_calls.append(
                                    part.function_call
                                )


                # -------------------------------------------------
                # No tool call = final response
                # -------------------------------------------------

                if not function_calls:

                    break


                loop_count += 1


                logger.info(
                    f"Tool iteration {loop_count}: "
                    f"{len(function_calls)} tool call(s)"
                )


                # -------------------------------------------------
                # Preserve Gemini tool-call response
                # -------------------------------------------------

                contents.append(
                    response.candidates[0].content
                )


                function_response_parts = []


                # =================================================
                # EXECUTE EACH TOOL
                # =================================================

                for call in function_calls:

                    tool_name = call.name

                    args = dict(
                        call.args
                    )


                    logger.info(
                        f"Running tool '{tool_name}' "
                        f"with args: {args}"
                    )


                    tool_func = (
                        AVAILABLE_TOOLS.get(
                            tool_name
                        )
                    )


                    # -------------------------------------------------
                    # Tool exists
                    # -------------------------------------------------

                    if tool_func:

                        try:

                            result = tool_func(
                                **args
                            )


                        except Exception as tool_error:

                            logger.error(
                                f"Tool '{tool_name}' "
                                f"failed: {tool_error}"
                            )


                            result = (
                                f"Error executing tool "
                                f"{tool_name}: "
                                f"{tool_error}"
                            )


                    # -------------------------------------------------
                    # Tool doesn't exist
                    # -------------------------------------------------

                    else:

                        result = (
                            f"Error: Tool '{tool_name}' "
                            f"is not registered."
                        )


                    logger.info(
                        f"Tool '{tool_name}' returned: "
                        f"{result}"
                    )


                    # -------------------------------------------------
                    # Send tool result back to Gemini
                    # -------------------------------------------------

                    function_response_parts.append(

                        types.Part.from_function_response(

                            name=tool_name,

                            response={
                                "result": str(result)
                            },

                            id=call.id,
                        )
                    )


                # =================================================
                # SEND TOOL RESULTS TO GEMINI
                # =================================================

                contents.append(

                    types.Content(

                        role="user",

                        parts=function_response_parts,

                    )
                )


                # =================================================
                # NEXT GEMINI RESPONSE
                # =================================================

                response = (
                    self.client.models.generate_content(

                        model=settings.GEMINI_MODEL,

                        contents=contents,

                        config=config,

                    )
                )


            # =================================================
            # FINAL RESPONSE
            # =================================================

            final_text = (
                response.text or ""
            )


            if not final_text:

                final_text = (
                    "I completed the task, "
                    "but I don't have a spoken response."
                )


            logger.info(
                "Agent finished processing. "
                f"Final response: '{final_text}'"
            )


            # =================================================
            # SAVE MEMORY
            # =================================================

            try:

                memory_contents = list(
                    contents
                )


                # Save current user query

                memory_contents.append(

                    types.Content(

                        role="user",

                        parts=[

                            types.Part.from_text(
                                text=query
                            )

                        ]
                    )
                )


                # Save JARVIS response

                memory_contents.append(

                    types.Content(

                        role="model",

                        parts=[

                            types.Part.from_text(
                                text=final_text
                            )

                        ]
                    )
                )


                memory.save_from_chat_history(
                    memory_contents
                )


                logger.info(
                    "Conversation memory saved successfully."
                )


            except Exception as memory_error:

                logger.warning(
                    "Could not save conversation memory: "
                    f"{memory_error}"
                )


            return final_text


        # =====================================================
        # GLOBAL ERROR HANDLER
        # =====================================================

        except Exception as e:

            logger.error(
                f"Agent execution failure: {e}",
                exc_info=True
            )


            return (
                "I had trouble processing that request: "
                f"{str(e)}"
            )