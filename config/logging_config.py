import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import json

def setup_logging():
    """
    Configure comprehensive logging for the application
    Creates separate logs for:
    - General app logs
    - API calls and responses
    - Errors
    - User queries
    """
    
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Format for logs
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler (for development)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File Handler - General App Logs (Rotating by size)
    app_file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    app_file_handler.setLevel(logging.INFO)
    app_file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(app_file_handler)
    
    # File Handler - Error Logs
    error_file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_file_handler)
    
    # File Handler - Debug Logs (Daily rotation)
    debug_file_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'debug.log'),
        when='midnight',
        interval=1,
        backupCount=7
    )
    debug_file_handler.setLevel(logging.DEBUG)
    debug_file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(debug_file_handler)
    
    return root_logger


class APILogger:
    """
    Specialized logger for API calls and responses
    Logs in JSON format for easy parsing and analysis
    """
    
    def __init__(self):
        self.logger = logging.getLogger('APILogger')
        self.logger.setLevel(logging.INFO)
        
        # Create separate file for API logs
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        
        # JSON format handler for API logs
        api_handler = RotatingFileHandler(
            os.path.join(log_dir, 'api_calls.log'),
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10
        )
        api_handler.setLevel(logging.INFO)
        
        # Simple formatter for JSON logs
        formatter = logging.Formatter('%(message)s')
        api_handler.setFormatter(formatter)
        
        self.logger.addHandler(api_handler)
        self.logger.propagate = False  # Don't propagate to root logger
    
    def log_api_call(self, service_name, endpoint, method='GET', params=None, 
                     headers=None, response_status=None, response_data=None, 
                     response_time=None, error=None):
        """
        Log API call with all details in JSON format
        
        Args:
            service_name: Name of the service (e.g., 'MTA_GTFS', 'Gemini', 'Elevator')
            endpoint: API endpoint URL
            method: HTTP method
            params: Request parameters
            headers: Request headers (sensitive data should be masked)
            response_status: HTTP status code
            response_data: Response data (can be truncated if too large)
            response_time: Time taken for the request in seconds
            error: Error message if request failed
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'service': service_name,
            'endpoint': endpoint,
            'method': method,
            'params': params,
            'headers': self._mask_sensitive_data(headers) if headers else None,
            'response_status': response_status,
            'response_time_seconds': round(response_time, 3) if response_time else None,
            'success': error is None,
            'error': error
        }
        
        # Add truncated response data if available
        if response_data:
            log_entry['response_summary'] = self._summarize_response(response_data)
        
        self.logger.info(json.dumps(log_entry))
    
    def _mask_sensitive_data(self, headers):
        """Mask API keys and sensitive information"""
        if not headers:
            return None
        
        masked = dict(headers)
        sensitive_keys = ['x-api-key', 'authorization', 'api-key', 'api_key']
        
        for key in masked:
            if key.lower() in sensitive_keys:
                if masked[key]:
                    masked[key] = masked[key][:8] + '...' + masked[key][-4:]
        
        return masked
    
    def _summarize_response(self, response_data):
        """Create summary of response data"""
        if isinstance(response_data, dict):
            return {
                'type': 'dict',
                'keys': list(response_data.keys())[:10],  # First 10 keys
                'size': len(str(response_data))
            }
        elif isinstance(response_data, list):
            return {
                'type': 'list',
                'length': len(response_data),
                'sample': response_data[:2] if len(response_data) > 0 else []
            }
        else:
            return {
                'type': type(response_data).__name__,
                'preview': str(response_data)[:200]
            }


class UserQueryLogger:
    """
    Logger for user queries and chatbot responses
    Useful for analytics and improving the chatbot
    """
    
    def __init__(self):
        self.logger = logging.getLogger('UserQueryLogger')
        self.logger.setLevel(logging.INFO)
        
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        
        query_handler = TimedRotatingFileHandler(
            os.path.join(log_dir, 'user_queries.log'),
            when='midnight',
            interval=1,
            backupCount=30  # Keep 30 days
        )
        query_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(message)s')
        query_handler.setFormatter(formatter)
        
        self.logger.addHandler(query_handler)
        self.logger.propagate = False
    
    def log_query(self, user_query, query_type, detected_station=None, 
                  detected_train_line=None, response_time=None, 
                  response_length=None, error=None):
        """Log user query with metadata"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'query': user_query,
            'query_type': query_type,
            'detected_station': detected_station,
            'detected_train_line': detected_train_line,
            'response_time_seconds': round(response_time, 3) if response_time else None,
            'response_length_chars': response_length,
            'success': error is None,
            'error': error
        }
        
        self.logger.info(json.dumps(log_entry))


# Initialize loggers
api_logger = APILogger()
user_query_logger = UserQueryLogger()
