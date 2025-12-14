import os
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from typing_extensions import Annotated, TypedDict
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

from config.logging_config import api_logger

logger = logging.getLogger(__name__)


class ConversationState(TypedDict):
    """State for conversation with memory"""
    # messages: Annotated[list, add_messages]
    mta_context: Optional[Dict]
    user_query: str


class GeminiServiceLangChain:
    """
    Enhanced Gemini service using LangChain
    Features:
    - Conversational memory
    - Structured prompts
    - Better error handling
    - Tool integration ready
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
            temperature=0.3,  # Lower for more consistent responses
            top_p=0.95,
            max_output_tokens=1024,
            convert_system_message_to_human=True  # Gemini doesn't support system messages directly
        )
        
        # Create prompt template
        self.prompt = self._create_prompt_template()
        
        # Create the chain
        self.chain = self._create_chain()
        
        # Memory for conversation
        # self.memory = MemorySaver()
        self.conversation_history: Dict[str, List] = {}
        
        logger.info(f"LangChain Gemini service initialized with model: {model}")
    
    def _create_prompt_template(self):
        """Create structured prompt template"""
        system_prompt = """You are an NYC Transit Assistant chatbot that provides real-time subway information. You have direct access to MTA real-time data feeds.

Your capabilities:
- Provide real-time train arrival times
- Report service alerts and delays
- Check elevator and escalator status
- Answer general NYC transit questions

Guidelines:
- Provide helpful, conversational responses based ONLY on the real-time data provided
- If train arrival data is available, present it clearly with times and minutes away
- If there are service alerts, explain them clearly and suggest alternatives if possible
- If elevator/escalator data shows no issues, say "No elevator/escalator outages reported at this station"
- Be concise but friendly and helpful
- NEVER suggest using other MTA apps or websites - you ARE the app
- If no real-time data is available, explain what might be happening and suggest alternatives within the app
- Always format times in a user-friendly way (e.g., "in 5 minutes" or "at 3:45 PM")
- For elevator queries with no alerts, be reassuring that elevators appear to be operational

Current time: {current_time}"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "Real-time MTA Data:\n{mta_context}\n\nUser Question: {user_query}")
        ])
        
        return prompt
    
    def _create_chain(self):
        """Create LangChain processing chain"""
        chain = (
            {
                "user_query": RunnablePassthrough(),
                "mta_context": RunnablePassthrough(),
                "current_time": lambda _: datetime.now().strftime('%I:%M %p'),
                "chat_history": lambda x: x.get("chat_history", [])
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        return chain
    
    def generate_response(
        self, 
        user_query: str, 
        mta_data: Dict,
        session_id: str = "default"
    ) -> str:
        """
        Generate response using LangChain with memory
        
        Args:
            user_query: User's question
            mta_data: Context from MTA APIs
            session_id: Session identifier for conversation memory
        
        Returns:
            Generated response string
        """
        start_time = time.time()
        
        try:
            # Build context from MTA data
            context = self._build_context(mta_data)
            
            # Get conversation history for this session
            chat_history = self.conversation_history.get(session_id, [])
            
            logger.info(f"Generating response for query type: {mta_data.get('type')}")
            logger.debug(f"Session: {session_id}, History length: {len(chat_history)}")
            
            # Invoke the chain
            response = self.chain.invoke({
                "user_query": user_query,
                "mta_context": context,
                "chat_history": chat_history
            })
            
            response_time = time.time() - start_time
            
            # Update conversation history
            if session_id not in self.conversation_history:
                self.conversation_history[session_id] = []
            
            self.conversation_history[session_id].append(
                HumanMessage(content=user_query)
            )
            self.conversation_history[session_id].append(
                AIMessage(content=response)
            )
            
            # Keep only last 10 messages (5 exchanges) to avoid context length issues
            if len(self.conversation_history[session_id]) > 10:
                self.conversation_history[session_id] = self.conversation_history[session_id][-10:]
            
            # Log API call
            api_logger.log_api_call(
                service_name='GEMINI_LANGCHAIN',
                endpoint=f'gemini/{self.model_name}',
                method='INVOKE',
                params={
                    'query_type': mta_data.get('type'),
                    'prompt_length': len(context),
                    'session_id': session_id,
                    'history_length': len(chat_history)
                },
                response_status=200,
                response_time=response_time,
                response_data={
                    'response_length': len(response)
                }
            )
            
            logger.info(f"Response generated successfully in {response_time:.2f}s")
            return response
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"LangChain Gemini error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            api_logger.log_api_call(
                service_name='GEMINI_LANGCHAIN',
                endpoint=f'gemini/{self.model_name}',
                method='INVOKE',
                response_time=response_time,
                error=error_msg
            )
            
            return f"I'm having trouble processing your request right now. Error: {str(e)}"
    
    def generate_response_with_tools(
        self,
        user_query: str,
        available_tools: List = None
    ) -> str:
        """
        Generate response with tool calling (for future enhancement)
        This allows the AI to decide which MTA API to call
        """
        # TODO: Implement tool calling for dynamic API selection
        pass
    
    def clear_history(self, session_id: str = "default"):
        """Clear conversation history for a session"""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
            logger.info(f"Cleared history for session: {session_id}")
    
    def get_history(self, session_id: str = "default") -> List:
        """Get conversation history for a session"""
        return self.conversation_history.get(session_id, [])
    
    def _build_context(self, mta_data: Dict) -> str:
        """Build context string from MTA data"""
        data_type = mta_data.get('type', 'general')
        context_parts = []
        
        context_parts.append(f"Query Type: {data_type}")
        context_parts.append(f"Current Time: {datetime.now().strftime('%I:%M %p')}")
        
        if data_type == 'train_arrival':
            train_line = mta_data.get('train_line', 'Unknown')
            station = mta_data.get('station', 'Unknown')
            arrivals = mta_data.get('arrivals', [])
            
            context_parts.append(f"\nTrain Line Requested: {train_line}")
            context_parts.append(f"Station: {station}")
            
            if isinstance(arrivals, dict) and 'error' in arrivals:
                context_parts.append(f"Data Error: {arrivals['error']}")
            elif arrivals and len(arrivals) > 0:
                context_parts.append(f"\nFound {len(arrivals)} upcoming trains:")
                for i, arrival in enumerate(arrivals, 1):
                    context_parts.append(
                        f"{i}. {arrival['train_line']} train - {arrival['direction']} - "
                        f"Arriving at {arrival['arrival_time']} ({arrival['minutes_away']} min away)"
                    )
            else:
                context_parts.append("\nNo upcoming arrivals found in the next 30 minutes.")
        
        elif data_type == 'alerts':
            alerts = mta_data.get('alerts', [])
            train_line = mta_data.get('train_line')
            
            if train_line:
                context_parts.append(f"\nService Alerts for {train_line} line:")
            else:
                context_parts.append("\nSystem-wide Service Alerts:")
            
            if alerts and len(alerts) > 0:
                for i, alert in enumerate(alerts[:5], 1):
                    context_parts.append(f"\nAlert {i}: {alert['header']}")
            else:
                context_parts.append("✓ No active service alerts - trains running normally!")
        
        elif data_type == 'elevator':
            station = mta_data.get('station', 'Unknown')
            elevator_status = mta_data.get('elevator_status', {})
            
            context_parts.append(f"\nElevator/Escalator Status for: {station}")
            
            if 'equipment' in elevator_status:
                total = elevator_status.get('total_equipment', 0)
                operational = elevator_status.get('operational', 0)
                out_of_service = elevator_status.get('out_of_service', 0)
                
                context_parts.append(f"Total Equipment: {total}")
                context_parts.append(f"✅ Operational: {operational}")
                context_parts.append(f"❌ Out of Service: {out_of_service}")
        
        return "\n".join(context_parts)
    
    def create_agent_with_tools(self, tools: List):
        """Create an agent that can use tools to answer questions"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an NYC Transit Assistant with access to real-time MTA data.

You have access to these tools:
- get_train_arrivals: Get real-time train times at a specific station
- get_service_alerts: Check for delays and service changes
- get_elevator_status: Check elevator/escalator availability
- find_nearby_stations: Find stations by name (when user's input is unclear)
- plan_trip: Plan routes between two stations (USE THIS for "how do I get from X to Y" questions)

When users ask about traveling between stations:
1. Use the plan_trip tool to find routes
2. If there's a direct route, mention which train(s) to take
3. If transfer is needed, explain the transfer point and both trains
4. Use get_train_arrivals to show when the next trains are arriving

Always:
- Present information clearly and conversationally
- Format times as "in X minutes" or "at HH:MM AM/PM"
- For trip planning, explain the full route including transfers
- If equipment is out of service, suggest alternatives

Current time: {current_time}"""),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])


        # Create agent
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
            max_iterations=3,
            handle_parsing_errors=True
        )

        return agent_executor

    def generate_response_with_tools(
        self,
        user_query: str,
        tools: List,
        session_id: str = "default"
    ) -> str:
        """
        Generate response using tools (AI decides which APIs to call)

        Args:
            user_query: User's question
            tools: List of available tools
            session_id: Session ID for memory

        Returns:
            Generated response
        """
        start_time = time.time()

        try:
            # Create or get agent executor
            if not hasattr(self, 'agent_executor') or self.agent_executor is None:
                self.agent_executor = self.create_agent_with_tools(tools)

            # Get chat history
            chat_history = self.conversation_history.get(session_id, [])

            logger.info(f"Generating response with tools for: {user_query}")

            # Invoke agent
            result = self.agent_executor.invoke({
                "input": user_query,
                "chat_history": chat_history,
                "current_time": datetime.now().strftime('%I:%M %p')
            })

            response = result['output']
            response_time = time.time() - start_time

            # Update history
            if session_id not in self.conversation_history:
                self.conversation_history[session_id] = []

            self.conversation_history[session_id].append(HumanMessage(content=user_query))
            self.conversation_history[session_id].append(AIMessage(content=response))

            # Keep last 10 messages
            if len(self.conversation_history[session_id]) > 10:
                self.conversation_history[session_id] = self.conversation_history[session_id][-10:]

            logger.info(f"Response with tools generated in {response_time:.2f}s")

            return response
        
        except Exception as e:
            logger.error(f"Error in generate_response_with_tools: {str(e)}", exc_info=True)
            return f"I encountered an error: {str(e)}"


# For backward compatibility, create an alias
GeminiService = GeminiServiceLangChain
