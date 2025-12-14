import os
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import Tool
from typing_extensions import Annotated, TypedDict

from config.logging_config import api_logger

logger = logging.getLogger(__name__)


class ConversationState(TypedDict):
    """State for conversation with memory"""
    messages: Annotated[list, "add_messages"]
    mta_context: Optional[Dict]
    user_query: str


class GeminiServiceLangChain:
    """
    Enhanced Gemini service using LangChain with Tool Calling
    """
    
    def __init__(self, api_key: str, model: str = "models/gemini-2.5-flash"):
        """
        Initialize LangChain-based Gemini service
        
        Args:
            api_key: Google Gemini API key
            model: Model to use (gemini-1.5-flash, gemini-1.5-pro, etc.)
        """
        self.api_key = api_key
        self.model_name = model
        
        # Initialize the LangChain Gemini model
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=0.3,
            top_p=0.95,
            max_output_tokens=2048,
            convert_system_message_to_human=True
        )
        
        # Memory for conversation
        self.conversation_history: Dict[str, List] = {}
        
        # Agent executor (will be created when tools are provided)
        self.agent_executor = None
        self.current_tools = None
        
        logger.info(f"LangChain Gemini service initialized with model: {model}")
    
    def create_agent_with_tools(self, tools: List[Tool]) -> AgentExecutor:
        """
        Create an agent that can use tools to answer questions
        
        Args:
            tools: List of LangChain tools
        
        Returns:
            AgentExecutor that can use the tools
        """
        logger.info(f"Creating agent with {len(tools)} tools")
        
        # Create prompt for agent
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an NYC Transit Assistant with access to real-time MTA data.

                You have access to these tools to help answer user questions:
                - get_train_arrivals: Get real-time train arrival times at a specific station
                - get_service_alerts: Check for delays and service changes on train lines
                - get_elevator_status: Check elevator/escalator availability at stations
                - find_nearby_stations: Find stations by name (useful when user's input is unclear)
                - plan_trip: Plan routes between two stations (USE THIS for "how do I get from X to Y" questions)
                
                Guidelines for using tools:
                1. For "when is the next train" questions → use get_train_arrivals
                2. For "any delays" or "service changes" → use get_service_alerts
                3. For "is elevator working" → use get_elevator_status
                4. For "how do I get from X to Y" → use plan_trip
                5. If station name is unclear → use find_nearby_stations first
                
                When responding:
                - Always call the appropriate tool(s) to get real-time data
                - Present information clearly and conversationally
                - Format times as "in X minutes" or "at HH:MM AM/PM"
                - For trip planning, explain the full route including any transfers
                - If equipment is out of service, suggest alternatives when possible
                - NEVER suggest using other MTA apps - you ARE the app
                
                Current time: {current_time}"""),
                            MessagesPlaceholder(variable_name="chat_history", optional=True),
                            ("human", "{input}"),
                            MessagesPlaceholder(variable_name="agent_scratchpad")
                        ])
        
        # Create agent with tool calling
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )
        
        # Create executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,  # Set to False in production
            max_iterations=5,  # Allow up to 5 tool calls
            max_execution_time=30,  # Timeout after 30 seconds
            handle_parsing_errors=True,
            return_intermediate_steps=True  # Return tool calls for logging
        )
        
        logger.info("Agent executor created successfully")
        return agent_executor
    
    def generate_response_with_tools(
        self,
        user_query: str,
        tools: List[Tool],
        session_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Generate response using tools - AI dynamically decides which APIs to call
        
        This is the main method that:
        1. Takes user's natural language query
        2. Uses LangChain agent to decide which tool(s) to call
        3. Executes the tool calls
        4. Synthesizes the results into a natural response
        5. Maintains conversation memory
        
        Args:
            user_query: User's question in natural language
            tools: List of available LangChain tools
            session_id: Session ID for conversation memory
        
        Returns:
            Dictionary with response and metadata
        """
        start_time = time.time()
        
        try:
            # Create or update agent executor if tools changed
            if (self.agent_executor is None or 
                self.current_tools != tools or
                len(self.current_tools) != len(tools)):
                
                logger.info("Creating new agent executor with updated tools")
                self.agent_executor = self.create_agent_with_tools(tools)
                self.current_tools = tools
            
            # Get chat history for this session
            chat_history = self.conversation_history.get(session_id, [])
            
            logger.info(f"Processing query with tools (session: {session_id}): '{user_query}'")
            logger.debug(f"Available tools: {[tool.name for tool in tools]}")
            logger.debug(f"Chat history length: {len(chat_history)}")
            
            # Invoke the agent - it will decide which tool(s) to call
            result = self.agent_executor.invoke({
                "input": user_query,
                "chat_history": chat_history,
                "current_time": datetime.now().strftime('%I:%M %p, %B %d, %Y')
            })
            
            response_time = time.time() - start_time
            
            # Extract response and intermediate steps
            response_text = result.get('output', '')
            intermediate_steps = result.get('intermediate_steps', [])
            
            # Log which tools were called
            tools_called = []
            for step in intermediate_steps:
                if len(step) >= 2:
                    action, observation = step[0], step[1]
                    tool_name = action.tool if hasattr(action, 'tool') else 'unknown'
                    tool_input = action.tool_input if hasattr(action, 'tool_input') else {}
                    tools_called.append({
                        'tool': tool_name,
                        'input': tool_input,
                        'output_preview': str(observation)[:200]
                    })
            
            logger.info(f"Agent called {len(tools_called)} tool(s): {[t['tool'] for t in tools_called]}")
            
            # Update conversation history
            if session_id not in self.conversation_history:
                self.conversation_history[session_id] = []
            
            self.conversation_history[session_id].append(
                HumanMessage(content=user_query)
            )
            self.conversation_history[session_id].append(
                AIMessage(content=response_text)
            )
            
            # Keep only last 10 messages (5 exchanges)
            if len(self.conversation_history[session_id]) > 10:
                self.conversation_history[session_id] = self.conversation_history[session_id][-10:]
            
            # Log API call with tool details
            api_logger.log_api_call(
                service_name='GEMINI_AGENT_TOOLS',
                endpoint=f'gemini/{self.model_name}',
                method='INVOKE_WITH_TOOLS',
                params={
                    'session_id': session_id,
                    'history_length': len(chat_history),
                    'tools_available': [tool.name for tool in tools],
                    'tools_called': [t['tool'] for t in tools_called]
                },
                response_status=200,
                response_time=response_time,
                response_data={
                    'response_length': len(response_text),
                    'num_tool_calls': len(tools_called)
                }
            )
            
            logger.info(f"Response generated successfully in {response_time:.2f}s")
            
            # Return comprehensive result
            return {
                'response': response_text,
                'tools_called': tools_called,
                'response_time': response_time,
                'session_id': session_id
            }
            
        except TimeoutError:
            response_time = time.time() - start_time
            error_msg = "Request timed out. The MTA APIs might be slow. Please try again."
            logger.error(f"Timeout in generate_response_with_tools: {response_time:.2f}s")
            
            api_logger.log_api_call(
                service_name='GEMINI_AGENT_TOOLS',
                endpoint=f'gemini/{self.model_name}',
                method='INVOKE_WITH_TOOLS',
                response_time=response_time,
                error='TimeoutError'
            )
            
            return {
                'response': error_msg,
                'tools_called': [],
                'response_time': response_time,
                'error': 'timeout'
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"Error processing request: {str(e)}"
            logger.error(f"Error in generate_response_with_tools: {error_msg}", exc_info=True)
            
            api_logger.log_api_call(
                service_name='GEMINI_AGENT_TOOLS',
                endpoint=f'gemini/{self.model_name}',
                method='INVOKE_WITH_TOOLS',
                response_time=response_time,
                error=error_msg
            )
            
            return {
                'response': "I encountered an error while processing your request. Please try rephrasing your question or try again in a moment.",
                'tools_called': [],
                'response_time': response_time,
                'error': str(e)
            }
    
    def generate_response(
        self, 
        user_query: str, 
        mta_data: Dict,
        session_id: str = "default"
    ) -> str:
        """
        Legacy method for backward compatibility (without tools)
        For new implementations, use generate_response_with_tools instead
        """
        logger.warning("Using legacy generate_response without tools. Consider using generate_response_with_tools.")
        
        # Build context from MTA data
        context = self._build_context(mta_data)
        
        # Simple response without tools
        chat_history = self.conversation_history.get(session_id, [])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an NYC Transit Assistant. Current time: {current_time}"),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "MTA Data:\n{mta_context}\n\nUser Question: {user_query}")
        ])
        
        chain = (
            {
                "user_query": RunnablePassthrough(),
                "mta_context": RunnablePassthrough(),
                "current_time": lambda _: datetime.now().strftime('%I:%M %p'),
                "chat_history": lambda x: chat_history
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        response = chain.invoke({
            "user_query": user_query,
            "mta_context": context
        })
        
        # Update history
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        self.conversation_history[session_id].append(HumanMessage(content=user_query))
        self.conversation_history[session_id].append(AIMessage(content=response))
        
        return response
    
    def clear_history(self, session_id: str = "default"):
        """Clear conversation history for a session"""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
            logger.info(f"Cleared history for session: {session_id}")
    
    def get_history(self, session_id: str = "default") -> List:
        """Get conversation history for a session"""
        return self.conversation_history.get(session_id, [])
    
    def _build_context(self, mta_data: Dict) -> str:
        """Build context string from MTA data (for legacy method)"""
        data_type = mta_data.get('type', 'general')
        context_parts = [
            f"Query Type: {data_type}",
            f"Current Time: {datetime.now().strftime('%I:%M %p')}"
        ]
        
        # Add more context based on type
        if data_type == 'train_arrival':
            context_parts.append(f"Train: {mta_data.get('train_line')}")
            context_parts.append(f"Station: {mta_data.get('station')}")
        
        return "\n".join(context_parts)


# Alias for backward compatibility
GeminiService = GeminiServiceLangChain
