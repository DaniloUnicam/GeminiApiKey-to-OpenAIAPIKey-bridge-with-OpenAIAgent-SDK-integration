"""
Voice Agent Main: Adapted LLM Agent with streaming and tool support.
Wraps the Gemini agent to enable real-time text responses and function calls.
"""
import asyncio
from typing import Optional
from openai import AsyncOpenAI
from agents import Agent, Runner
from agents.run import RunConfig
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from config import AGENT_CONFIG
import logging

logger = logging.getLogger(__name__)


class VoiceAgent:
    """
    Wrapper around openai-agents Agent for voice interaction.
    
    Provides:
    - Async chat interface compatible with voice loop
    - Tool/function call support
    - Streaming response capability
    - Error handling and fallbacks
    """
    
    def __init__(self):
        """Initialize the voice agent with Gemini backend."""
        if not AGENT_CONFIG.GEMINI_API_KEY:
            raise ValueError("❌ GEMINI_API_KEY_env not set in environment")
        
        # Create AsyncOpenAI client pointing to Google's OpenAI-compatible endpoint
        self.client = AsyncOpenAI(
            api_key=AGENT_CONFIG.GEMINI_API_KEY,
            base_url=AGENT_CONFIG.OPENAI_BASE_URL
        )
        
        # Wrap in OpenAI Agents model
        self.model = OpenAIChatCompletionsModel(
            model=AGENT_CONFIG.AGENT_MODEL,
            openai_client=self.client
        )
        
        # Configure agent execution
        self.config = RunConfig(tracing_disabled=True)
        
        # Create the agent
        self.agent = Agent(
            name=AGENT_CONFIG.AGENT_NAME,
            instructions=AGENT_CONFIG.AGENT_INSTRUCTIONS,
            model=self.model
        )
        
        logger.info(
            f"✅ VoiceAgent initialized ({AGENT_CONFIG.AGENT_MODEL}) "
            f"with tools: {AGENT_CONFIG.ENABLE_TOOLS}"
        )
    
    async def chat(self, user_message: str) -> str:
        """
        Process user message and return agent response.
        
        This is the main async interface for the voice loop.
        Runs synchronously (waits for full response before returning).
        
        Args:
            user_message: Transcribed user input text
        
        Returns:
            Agent response text (suitable for TTS)
        """
        if not user_message or not user_message.strip():
            logger.warning("Empty user message")
            return "Scusa, non ho capito. Puoi ripetere?"
        
        try:
            logger.info(f"🤖 Agent processing: {user_message[:100]}")
            
            # Run agent synchronously (blocking call in async context)
            loop = asyncio.get_event_loop()
            
            def _run_agent():
                result = Runner.run_sync(
                    self.agent,
                    user_message,
                    run_config=self.config
                )
                return result.final_output
            
            # Execute in executor to avoid blocking event loop
            response = await asyncio.wait_for(
                loop.run_in_executor(None, _run_agent),
                timeout=15.0
            )
            
            # Truncate response to TTS-friendly length
            if len(response) > AGENT_CONFIG.MAX_RESPONSE_LENGTH:
                response = response[:AGENT_CONFIG.MAX_RESPONSE_LENGTH].rsplit(" ", 1)[0] + "..."
            
            logger.info(f"✅ Agent response: {response[:100]}")
            return response
        
        except asyncio.TimeoutError:
            logger.error("Agent response timeout")
            return "Mi scusa, la risposta ha impiegato troppo tempo. Riprova."
        except Exception as e:
            logger.error(f"Error in agent.chat: {e}")
            return f"Si è verificato un errore: {str(e)[:50]}"
    
    async def chat_with_streaming(self, user_message: str):
        """
        Process user message with streaming output.
        
        Advanced: Yields partial responses as they're generated.
        Useful for more real-time feedback (future enhancement).
        
        Args:
            user_message: Transcribed user input
        
        Yields:
            Partial response text chunks
        """
        if not user_message or not user_message.strip():
            yield "Scusa, non ho capito. Puoi ripetere?"
            return
        
        try:
            logger.info(f"🤖 Agent streaming: {user_message[:100]}")
            
            # Use Runner.run_streamed for event-based streaming
            result = Runner.run_streamed(
                self.agent,
                user_message,
                run_config=self.config
            )
            
            # Collect all stream events and extract text
            full_response = ""
            
            async for event in result.stream_events():
                if event.type == "run_item_stream_event":
                    item = event.item
                    
                    # Extract text from message output items
                    if item.type == "message_output_item":
                        from agents.structure import ItemHelpers
                        text = ItemHelpers.text_message_output(item)
                        if text:
                            yield text
                            full_response += text
                    
                    # Handle tool calls (log only for now)
                    elif item.type == "tool_call_item":
                        logger.debug(f"Tool called: {item.raw_item.name}")
            
            # Truncate if needed
            if len(full_response) > AGENT_CONFIG.MAX_RESPONSE_LENGTH:
                full_response = full_response[:AGENT_CONFIG.MAX_RESPONSE_LENGTH] + "..."
            
            logger.info(f"✅ Streaming response complete: {full_response[:100]}")
        
        except Exception as e:
            logger.error(f"Error in chat_with_streaming: {e}")
            yield f"Si è verificato un errore: {str(e)[:50]}"


class VoiceAgentFactory:
    """Factory to manage single agent instance (singleton)."""
    
    _instance: Optional[VoiceAgent] = None
    
    @classmethod
    async def get_agent(cls) -> VoiceAgent:
        """Get or create the voice agent."""
        if cls._instance is None:
            cls._instance = VoiceAgent()
        return cls._instance


async def test_agent():
    """Test agent response."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    agent = await VoiceAgentFactory.get_agent()
    
    test_messages = [
        "Ciao, come stai?",
        "Qual è la capitale dell'Italia?",
        "Dimmi una barzelletta",
    ]
    
    for msg in test_messages:
        print(f"\n👤 User: {msg}")
        response = await agent.chat(msg)
        print(f"🤖 Agent: {response}\n")


if __name__ == "__main__":
    asyncio.run(test_agent())
