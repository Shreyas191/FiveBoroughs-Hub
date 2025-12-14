import google.generativeai as genai
from datetime import datetime

class GeminiService:
    """Service for interacting with Google Gemini AI"""
    
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('models/gemini-2.5-flash')
    
    def generate_response(self, user_query, mta_data):
        """Generate a response using Gemini based on user query and MTA data"""
        
        # Build context from MTA data
        context = self._build_context(mta_data)
        
        # Create prompt for Gemini
        prompt = f"""You are an NYC Transit Assistant chatbot that provides real-time subway information. You have direct access to MTA real-time data feeds.

User Question: {user_query}

Real-time MTA Data Available:
{context}

Instructions:
- Provide helpful, conversational responses based ONLY on the real-time data provided above
- If train arrival data is available, present it clearly with times and minutes away
- If there are service alerts, explain them clearly and suggest alternatives if possible
- If elevator/escalator data shows no issues, say "No elevator/escalator outages reported at this station"
- Be concise but friendly and helpful
- NEVER suggest using other MTA apps or websites - you ARE the app
- If no real-time data is available, explain what might be happening:
  * The train line might not be running at this time
  * The station might not be served by that train line
  * There might be a temporary issue with the MTA data feed
  * Suggest trying a different station or train line nearby
- If data shows an error, explain it in user-friendly terms
- Always format times in a user-friendly way (e.g., "in 5 minutes" or "at 3:45 PM")
- For elevator queries with no alerts, be reassuring that elevators appear to be operational

Response:"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"I'm having trouble processing your request right now. The error is: {str(e)}. Please try rephrasing your question or ask about a different station or train line."
    
    def _build_context(self, mta_data):
        """Build context string from MTA data for Gemini"""
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
                context_parts.append("Possible reasons: MTA feed temporarily unavailable, or connection issue")
            elif arrivals and len(arrivals) > 0:
                context_parts.append(f"\nFound {len(arrivals)} upcoming trains:")
                for i, arrival in enumerate(arrivals, 1):
                    context_parts.append(
                        f"{i}. {arrival['train_line']} train - {arrival['direction']} - "
                        f"Arriving at {arrival['arrival_time']} ({arrival['minutes_away']} min away)"
                    )
            else:
                context_parts.append("\nNo upcoming arrivals found in the next 30 minutes.")
                context_parts.append(f"This could mean:")
                context_parts.append(f"- The {train_line} train doesn't stop at {station}")
                context_parts.append(f"- No {train_line} trains are currently scheduled")
                context_parts.append(f"- There may be service changes or delays")
                context_parts.append(f"Suggestion: Check if this station serves the {train_line} line, or try asking about a different train line that stops here")
        
        elif data_type == 'alerts':
            alerts = mta_data.get('alerts', [])
            train_line = mta_data.get('train_line')
            
            if train_line:
                context_parts.append(f"\nService Alerts for {train_line} line:")
            else:
                context_parts.append("\nSystem-wide Service Alerts:")
            
            if isinstance(alerts, dict) and 'error' in alerts:
                context_parts.append(f"Alert Data Error: {alerts['error']}")
            elif alerts and len(alerts) > 0:
                for i, alert in enumerate(alerts[:5], 1):  # Limit to 5 alerts
                    context_parts.append(f"\nAlert {i}:")
                    context_parts.append(f"  {alert['header']}")
                    if alert.get('description'):
                        context_parts.append(f"  Details: {alert['description'][:200]}...")
                    if alert['affected_routes']:
                        context_parts.append(f"  Affects routes: {', '.join(alert['affected_routes'])}")
            else:
                context_parts.append("✓ No active service alerts found - trains are running normally!")
        
        elif data_type == 'elevator':
            station = mta_data.get('station', 'Unknown')
            elevator_status = mta_data.get('elevator_status', {})
            
            context_parts.append(f"\nElevator/Escalator Status for: {station}")
            
            if 'error' in elevator_status:
                context_parts.append(f"Error: {elevator_status['error']}")
            elif 'message' in elevator_status:
                context_parts.append(elevator_status['message'])
            elif 'equipment' in elevator_status:
                total = elevator_status.get('total_equipment', 0)
                operational = elevator_status.get('operational', 0)
                out_of_service = elevator_status.get('out_of_service', 0)
                
                context_parts.append(f"Total Equipment: {total}")
                context_parts.append(f"✅ Operational: {operational}")
                context_parts.append(f"❌ Out of Service: {out_of_service}")
                
                if out_of_service == 0:
                    context_parts.append("\n✓ Great news! All elevators and escalators are operational at this station.")
                else:
                    context_parts.append(f"\n⚠️ Warning: {out_of_service} equipment out of service")
                    context_parts.append("\nDetailed Equipment Status:")
                    for equip in elevator_status['equipment']:
                        status_icon = "✅" if not equip['is_out_of_service'] else "❌"
                        equip_type = "Elevator" if equip['equipment_type'] == 'EL' else "Escalator"
                        context_parts.append(
                            f"  {status_icon} {equip_type} - {equip['serving']} - {equip['status']}"
                        )

        
        elif data_type == 'bus':
            context_parts.append("\nBus Query Detected")
            message = mta_data.get('message', '')
            if 'API key' in message:
                context_parts.append("Bus data requires additional configuration.")
                context_parts.append("Currently only subway data is available in this chatbot.")
                context_parts.append("Suggestion: Ask about subway trains instead, or the developer needs to add a Bus API key.")
            else:
                context_parts.append(message)
        
        elif data_type == 'lirr' or data_type == 'metro_north':
            context_parts.append(f"\n{data_type.upper().replace('_', '-')} Query Detected")
            message = mta_data.get('message', '')
            if 'API key' in message:
                context_parts.append("Commuter rail data requires additional configuration.")
                context_parts.append("Currently only subway data is available in this chatbot.")
                context_parts.append("Suggestion: Ask about subway trains instead.")
            else:
                context_parts.append(message)
        
        elif data_type == 'general':
            context_parts.append("\nGeneral transit query - no specific real-time data request")
            context_parts.append("The chatbot can help with:")
            context_parts.append("- Train arrival times (e.g., 'When is the next Q train at Times Square?')")
            context_parts.append("- Service alerts (e.g., 'Any delays on the N line?')")
            context_parts.append("- Elevator status (e.g., 'Are elevators working at Penn Station?')")
            context_parts.append("- General subway information")
        
        else:
            context_parts.append("\nNo specific MTA data retrieved for this query")
        
        return "\n".join(context_parts)
