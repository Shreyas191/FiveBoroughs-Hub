from flask import Flask, render_template, request, jsonify, session, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os
import time
import logging
import secrets
from config.logging_config import setup_logging, user_query_logger
from services.mta_service import MTAService
from services.elevator_service import ElevatorEscalatorService
from services.gemini_service_langchain import GeminiServiceLangChain
from services.mta_tools import mta_tools

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


# Determine environment
IS_PRODUCTION = os.getenv('FLASK_ENV') == 'production'

if IS_PRODUCTION:
    # In production, we serve the Vite build
    # expected to be in 'frontend_dist'
    app = Flask(__name__, 
                static_folder='frontend_dist/assets', 
                template_folder='frontend_dist',
                static_url_path='/assets')
else:
    # In development, use default folders
    app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))
CORS(app)

# Catch-all route for React Router (only in production)
if IS_PRODUCTION:
    @app.route('/<path:path>')
    def catch_all(path):
        # Allow API calls to pass through
        if path.startswith('api/'):
            return jsonify({'error': 'Not found'}), 404
        # Serve static files if they exist (e.g. images in public folder)
        # Check root of frontend_dist
        if os.path.exists(os.path.join(app.root_path, 'frontend_dist', path)):
            return send_from_directory('frontend_dist', path)
            
        # Otherwise serve index.html
        return render_template('index.html')

logger.info("="*60)
logger.info("NYC Transit Chatbot (LangChain Edition) starting up...")
logger.info("="*60)

# Initialize services with LangChain
try:
    mta_service = MTAService()
    elevator_service = ElevatorEscalatorService()
    
    # Use LangChain-based Gemini service
    gemini_service = GeminiServiceLangChain(
        api_key=os.getenv('GEMINI_API_KEY'),
        model='models/gemini-2.5-flash'  # or 'gemini-1.5-pro' for more advanced
    )
    
    logger.info("All services initialized successfully (using LangChain)")
except Exception as e:
    logger.error(f"Failed to initialize services: {str(e)}", exc_info=True)
    raise

@app.route('/')
def index():
    """Render the chat interface"""
    # Generate session ID if not exists
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(8)
        logger.info(f"New session created: {session['session_id']}")
    
    return render_template('index.html')

from services.mta_tools import mta_tools  # Add this import

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests with LangChain tools"""
    start_time = time.time()
    
    try:
        user_query = request.json.get('message', '')
        session_id = session.get('session_id', 'default')
        
        logger.info(f"Chat request (session: {session_id}): '{user_query}'")
        
        if not user_query:
            return jsonify({'error': 'No message provided'}), 400
        
        # NEW: Use tools approach - AI decides which APIs to call
        response = gemini_service.generate_response_with_tools(
            user_query=user_query,
            tools=mta_tools,
            session_id=session_id
        )
        
        response_time = time.time() - start_time
        logger.info(f"Chat completed in {response_time:.2f}s")
        
        return jsonify({
            'response': response['response'],
            'session_id': session_id
        })
    
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    """Clear conversation history for current session"""
    session_id = session.get('session_id', 'default')
    gemini_service.clear_history(session_id)
    logger.info(f"History cleared for session: {session_id}")
    return jsonify({'message': 'Conversation history cleared'})

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get conversation history for current session"""
    session_id = session.get('session_id', 'default')
    history = gemini_service.get_history(session_id)
    
    # Convert to serializable format
    history_list = [
        {
            'role': 'human' if isinstance(msg, type(history[0])) and 'Human' in str(type(msg)) else 'ai',
            'content': msg.content
        }
        for msg in history
    ]
    
    return jsonify({'history': history_list, 'session_id': session_id})

@app.route('/api/stations', methods=['GET'])
def get_stations():
    """Get stations, optionally filtered by line"""
    try:
        line = request.args.get('line')
        stations = mta_service.stations
        
        if line:
            line = line.upper()
            stations = [s for s in stations if line in s.get('routes', [])]
            
        return jsonify({'stations': stations, 'count': len(stations)})
    except Exception as e:
        logger.error(f"Error fetching stations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get service alerts"""
    try:
        line = request.args.get('line')
        alerts = mta_service.get_service_alerts(line)
        return jsonify({'alerts': alerts})
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/elevator-status', methods=['GET'])
def get_elevator_status():
    """Get elevator status"""
    try:
        station_name = request.args.get('station')
        if not station_name:
             # If no station, maybe return all? ElevatorService might not support "all" easily without iteration
             # For now, let's just return a helpful message or strict requirement
             return jsonify({'error': 'Station name required'}), 400
        
        # We need a station dict for get_elevator_status
        # Use find_station to get the object
        station_obj = mta_service.find_station(station_name)
        if not station_obj:
             return jsonify({'error': 'Station not found'}), 404
             
        status = mta_service.get_elevator_status(station_obj)
        return jsonify({'station': station_obj['stop_name'], 'status': status})
    except Exception as e:
        logger.error(f"Error fetching elevator status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/arrivals', methods=['GET'])
def get_arrivals():
    """Get arrivals for a station"""
    try:
        station_query = request.args.get('station')
        train_line = request.args.get('line')
        
        if not station_query or not train_line:
             return jsonify({'error': 'Station and Line required'}), 400
             
        station_obj = mta_service.find_station(station_query)
        if not station_obj:
             return jsonify({'error': 'Station not found'}), 404
             
        arrivals = mta_service.get_train_arrivals(train_line, station_obj)
        return jsonify({'station': station_obj['stop_name'], 'arrivals': arrivals})
    except Exception as e:
        logger.error(f"Error fetching arrivals: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/live-trains', methods=['GET'])
def get_live_trains():
    """Get live train positions"""
    try:
        line = request.args.get('line')
        positions = mta_service.get_vehicle_positions(line)
        return jsonify({'positions': positions})
    except Exception as e:
        logger.error(f"Error fetching live trains: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'langchain',
        'model': gemini_service.model_name
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Starting Flask app (LangChain) on port {port}")
    app.run(debug=True, host='0.0.0.0', port=port)
