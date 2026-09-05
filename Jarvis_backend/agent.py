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

                "You are JARVIS, a helpful, intelligent, "
                "and action-oriented Windows desktop AI assistant.\n\n"

                "You live on the user's computer and can "
                "perform real tasks using the available tools.\n\n"

                "Keep normal responses natural and reasonably "
                "brief because many responses are spoken aloud.\n\n"


                # =================================================
                # AGENTIC BEHAVIOR
                # =================================================

                "=================================================\n"
                "AGENTIC TASK EXECUTION RULES\n"
                "=================================================\n\n"

                "1. Understand the user's COMPLETE request before "
                "deciding that the task is finished.\n\n"

                "2. If the request requires multiple actions, "
                "perform those actions step by step using the "
                "available tools.\n\n"

                "3. Do NOT stop after completing only the first "
                "part of a multi-step request.\n\n"

                "4. When one tool produces information required "
                "by another tool, use the result of the first "
                "tool as the input for the next tool.\n\n"

                "5. Continue executing tools until the user's "
                "overall request has been completed or a genuine "
                "problem prevents completion.\n\n"

                "6. Never pretend that a multi-step task is "
                "complete when only one step has been performed.\n\n"

                "7. For example, if the user says "
                "'Find my DAA PDF and summarize it', the correct "
                "workflow is:\n"
                "   a. Search for the relevant PDF.\n"
                "   b. Identify the appropriate PDF.\n"
                "   c. Extract its contents.\n"
                "   d. Analyze the extracted contents.\n"
                "   e. Provide the requested summary.\n\n"

                "8. For example, if the user says "
                "'Open Chrome and search for Generative AI', "
                "complete both actions rather than only opening "
                "Chrome.\n\n"

                "9. When a task can be completed using available "
                "tools, prefer performing the task instead of "
                "simply explaining how the user could do it.\n\n"

                "10. If a required tool fails, use the available "
                "information to determine whether the task can "
                "continue. If it cannot, clearly explain what "
                "failed.\n\n"


                # =================================================
                # TOOL RULES
                # =================================================

                "=================================================\n"
                "TOOL RULES\n"
                "=================================================\n\n"

                "11. When the user asks for the current time, "
                "use the get_current_time tool.\n\n"

                "12. When the user asks for today's date, "
                "the current date, or what date it is, "
                "use the get_current_date tool.\n\n"

                "13. When the user asks to launch an application, "
                "use the launch_app tool.\n\n"

                "14. When the user asks to open a website, "
                "use the browser tools.\n\n"

                "15. When the user asks to search the web, "
                "use the web_search tool.\n\n"

                "16. When the user asks to list, read, write, "
                "or delete files, use the appropriate "
                "file-management tools.\n\n"


                # =================================================
                # PDF RULES
                # =================================================

                "=================================================\n"
                "PDF RULES\n"
                "=================================================\n\n"

                "17. When the user asks to summarize, explain, "
                "or analyze a PDF, first identify the PDF file.\n\n"

                "18. If the user provides an exact PDF path, "
                "use extract_pdf_text directly with that path.\n\n"

                "19. If the user does not provide an exact PDF "
                "path, use find_pdf_files to search for the "
                "relevant PDF using the filename or topic "
                "provided by the user.\n\n"

                "20. After finding the relevant PDF, use "
                "extract_pdf_text to read its contents.\n\n"

                "21. After receiving the extracted PDF text, "
                "generate the requested answer using the "
                "extracted PDF content.\n\n"

                "22. For PDF summaries, use useful sections "
                "such as Overview, Key Points, Important "
                "Concepts, and Conclusion when appropriate.\n\n"

                "23. Base PDF-specific answers on the extracted "
                "PDF content. Do not pretend to have read "
                "content that was not successfully extracted.\n\n"

                "24. If multiple PDFs match the user's request, "
                "ask the user which PDF they want unless "
                "one result is clearly the intended document.\n\n"

                "25. If PDF extraction fails, clearly explain "
                "the problem instead of pretending to have "
                "read the PDF.\n\n"

                "26. If the extracted PDF content is large, "
                "work with the available extracted content and "
                "give the most useful answer possible.\n\n"


                # =================================================
                # SCREENSHOT
                # =================================================

                "=================================================\n"
                "SCREENSHOT RULES\n"
                "=================================================\n\n"

                "27. When the user asks to take a screenshot, "
                "use the take_screenshot tool.\n\n"

                "28. Only report that a screenshot was captured "
                "if the screenshot tool returns a successful "
                "result.\n\n"


                # =================================================
                # WEB / BROWSER
                # =================================================

                "=================================================\n"
                "WEB AND BROWSER RULES\n"
                "=================================================\n\n"

                "29. When the user asks to search for current "
                "information on the web, use web_search.\n\n"

                "30. When a web search returns information "
                "needed for another action, use that information "
                "for the next appropriate tool call.\n\n"

                "31. Do not claim to have opened a website or "
                "completed a browser action unless the relevant "
                "tool successfully performed it.\n\n"


                # =================================================
                # FILE MANAGEMENT
                # =================================================

                "=================================================\n"
                "FILE MANAGEMENT RULES\n"
                "=================================================\n\n"

                "32. Use the available file-management tools "
                "for file operations rather than guessing "
                "file contents or locations.\n\n"

                "33. For potentially destructive operations, "
                "respect any confirmation or safety mechanism "
                "implemented by the tool.\n\n"


                # =================================================
                # GENERAL TOOL SAFETY
                # =================================================

                "=================================================\n"
                "GENERAL TOOL SAFETY\n"
                "=================================================\n\n"

                "34. Always use an available tool when it is "
                "appropriate instead of guessing the result.\n\n"

                "35. Never claim that an application was opened, "
                "a file was created, a screenshot was captured, "
                "or another system action was completed unless "
                "the corresponding tool actually returned "
                "a successful result.\n\n"

                "36. Do not invent tool results.\n\n"

                "37. If a tool returns an error, treat that "
                "error as real information and respond accordingly.\n\n"

                "38. After all required tool actions are complete, "
                "give the user a concise and useful final response.\n"

            ),

            tools=list(
                AVAILABLE_TOOLS.values()
            ),
        )

    # =========================================================
    # CONVERT MEMORY TO GEMINI CONTENT
    # =========================================================

    def _load_memory_contents(self):
        """
        Load previous conversation memory and convert it
        into Gemini-compatible Content objects.
        """

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

        return contents

    # =========================================================
    # EXTRACT FUNCTION CALLS
    # =========================================================

    def _get_function_calls(self, response):
        """
        Extract all function calls from a Gemini response.
        """

        function_calls = []

        if not response:

            return function_calls

        if not response.candidates:

            return function_calls

        candidate = response.candidates[0]

        if not candidate.content:

            return function_calls

        for part in candidate.content.parts:

            if part.function_call:

                function_calls.append(
                    part.function_call
                )

        return function_calls

    # =========================================================
    # EXECUTE TOOL
    # =========================================================

    def _execute_tool(self, tool_name, args):
        """
        Execute one registered JARVIS tool safely.
        """

        logger.info(
            f"Running tool '{tool_name}' "
            f"with args: {args}"
        )

        tool_func = AVAILABLE_TOOLS.get(
            tool_name
        )

        if not tool_func:

            result = (
                f"Error: Tool '{tool_name}' "
                f"is not registered."
            )

            logger.error(result)

            return result

        try:

            result = tool_func(
                **args
            )

            logger.info(
                f"Tool '{tool_name}' returned: "
                f"{result}"
            )

            return result

        except Exception as tool_error:

            logger.error(
                f"Tool '{tool_name}' failed: "
                f"{tool_error}",
                exc_info=True
            )

            return (
                f"Error executing tool "
                f"{tool_name}: "
                f"{tool_error}"
            )

    # =========================================================
    # EXECUTE USER QUERY
    # =========================================================

    def execute_query(self, query: str) -> str:
        """
        Process a user query using Gemini and JARVIS tools.

        Supports multi-step tool execution where the result
        of one tool can be used to determine the next action.
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

            contents = self._load_memory_contents()

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
            # INITIAL GEMINI REQUEST
            # =================================================

            logger.info(
                "Sending request to Gemini..."
            )

            response = (
                self.client.models.generate_content(

                    model=settings.GEMINI_MODEL,

                    contents=contents,

                    config=config,

                )
            )

            # =================================================
            # MULTI-STEP TOOL EXECUTION LOOP
            # =================================================

            max_loops = 8
            loop_count = 0

            while loop_count < max_loops:

                function_calls = (
                    self._get_function_calls(
                        response
                    )
                )

                # -------------------------------------------------
                # No tool call = final response
                # -------------------------------------------------

                if not function_calls:

                    break

                loop_count += 1

                logger.info(
                    f"Agent tool iteration "
                    f"{loop_count}/{max_loops}: "
                    f"{len(function_calls)} tool call(s)"
                )

                # -------------------------------------------------
                # Preserve Gemini tool-call response
                # -------------------------------------------------

                if (
                    response.candidates
                    and response.candidates[0].content
                ):

                    contents.append(
                        response.candidates[0].content
                    )

                # -------------------------------------------------
                # Execute requested tools
                # -------------------------------------------------

                function_response_parts = []

                for call in function_calls:

                    tool_name = call.name

                    args = dict(
                        call.args
                    )

                    result = self._execute_tool(
                        tool_name,
                        args
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
                # SEND TOOL RESULTS BACK TO GEMINI
                # =================================================

                contents.append(

                    types.Content(

                        role="user",

                        parts=function_response_parts,

                    )

                )

                # =================================================
                # ASK GEMINI FOR NEXT STEP / FINAL RESPONSE
                # =================================================

                logger.info(
                    "Sending tool results back to Gemini..."
                )

                response = (
                    self.client.models.generate_content(

                        model=settings.GEMINI_MODEL,

                        contents=contents,

                        config=config,

                    )
                )

            # =================================================
            # MAX LOOP PROTECTION
            # =================================================

            if loop_count >= max_loops:

                remaining_calls = (
                    self._get_function_calls(
                        response
                    )
                )

                if remaining_calls:

                    logger.warning(
                        "Maximum tool execution loops reached."
                    )

            # =================================================
            # FINAL RESPONSE
            # =================================================

            final_text = (
                response.text or ""
            )

            if not final_text:

                final_text = (
                    "I completed the available steps, "
                    "but I don't have a final spoken response."
                )

            logger.info(
                "Agent finished processing. "
                f"Final response: '{final_text}'"
            )

            # =================================================
            # SAVE MEMORY
            # =================================================

            try:

                memory.save_conversation(
                    query,
                    final_text
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