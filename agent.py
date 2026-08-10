import google.generativeai as genai
from google.generativeai.types import content_types
from config import settings
from tools import AVAILABLE_TOOLS
from memory.conversation import memory
from utils.logger import get_logger

logger = get_logger()

class JarvisAgent:
    def __init__(self):
        """
        Initializes the Gemini agent client and registers tools.
        """
        self.api_configured = False
        self._configure_api()

    def _configure_api(self):
        if not settings.GEMINI_API_KEY:
            logger.error("Gemini API Key is not set in settings or environment.")
            self.api_configured = False
            return
            
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Register functions directly as tools.
            # google-generativeai automatically reads docstrings and type annotations to build the JSON schema!
            self.model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                tools=list(AVAILABLE_TOOLS.values()),
                system_instruction=(
                    "You are Jarvis, a lightweight and helpful voice-controlled Windows desktop assistant.\n"
                    "You live in the system tray and perform tasks for the user.\n"
                    "Keep your responses natural, conversational, and brief (since they are spoken aloud).\n"
                    "Always execute tools automatically when the user asks to launch apps, open sites, list or "
                    "read files, summarize PDFs, take screenshots, or copy/read the clipboard.\n"
                    "Before performing a dangerous file deletion or modifying files in safe mode, verify that "
                    "the tool will request user confirmation."
                )
            )
            self.api_configured = True
            logger.info(f"Gemini API configured successfully using model: {settings.GEMINI_MODEL}")
        except Exception as e:
            logger.error(f"Error configuring Gemini API: {e}")
            self.api_configured = False

    def execute_query(self, query: str) -> str:
        """
        Process user text input, handle multi-step tool executions, and return a final spoken response.
        
        Args:
            query (str): User command text.
            
        Returns:
            str: Assistant text answer.
        """
        if not self.api_configured:
            # Try to reconfigure on the fly if key was loaded late
            self._configure_api()
            if not self.api_configured:
                return "Gemini API key is not set. Please set the GEMINI_API_KEY environment variable."

        logger.info(f"Agent executing query: '{query}'")
        
        try:
            # Start chat session with historical messages
            chat = self.model.start_chat(history=memory.get_history())
            
            # Send the initial query
            response = chat.send_message(query)
            
            loop_count = 0
            max_loops = 5  # Prevent infinite loops in case of tool execution cycles
            
            while response.function_calls and loop_count < max_loops:
                loop_count += 1
                logger.info(f"Iteration {loop_count}: Model requested {len(response.function_calls)} tool execution(s)")
                
                tool_response_parts = []
                for call in response.function_calls:
                    tool_name = call.name
                    args = dict(call.args)
                    logger.info(f"Running tool '{tool_name}' with args: {args}")
                    
                    tool_func = AVAILABLE_TOOLS.get(tool_name)
                    if tool_func:
                        try:
                            # Run tool synchronously
                            result = tool_func(**args)
                        except Exception as tool_err:
                            result = f"Error executing tool {tool_name}: {str(tool_err)}"
                    else:
                        result = f"Error: Tool '{tool_name}' is not registered."
                        
                    logger.info(f"Tool '{tool_name}' returned: {result}")
                    
                    # Package tool response back into Gemini structure
                    part = content_types.Part.from_function_response(
                        name=tool_name,
                        response={"result": str(result)}
                    )
                    tool_response_parts.append(part)
                
                # Send tool responses back to Gemini
                response = chat.send_message(tool_response_parts)
            
            # Sync and save history to local file
            memory.save_from_chat_history(chat.history)
            
            final_text = response.text
            logger.info(f"Agent finished processing. Final response: '{final_text}'")
            return final_text
            
        except Exception as e:
            logger.error(f"Agent execution failure: {e}")
            return f"I had trouble processing that request: {str(e)}"
