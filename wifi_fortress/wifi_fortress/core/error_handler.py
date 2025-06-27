import logging
import traceback
import sys
from typing import Any, Callable, Dict, Optional, Type, Union
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)

class WiFiFortressError(Exception):
    """Base exception class for WiFi Fortress"""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code
        self.timestamp = datetime.now()

class NetworkError(WiFiFortressError):
    """Network-related errors"""
    pass

class SecurityError(WiFiFortressError):
    """Security-related errors"""
    pass

class ConfigurationError(WiFiFortressError):
    """Configuration-related errors"""
    pass

class PluginError(WiFiFortressError):
    """Plugin-related errors"""
    pass

class ErrorHandler:
    """Centralized error handling for WiFi Fortress"""
    
    def __init__(self):
        self.error_logger = logging.getLogger('wifi_fortress.error')
        self.error_callbacks: Dict[Type[Exception], list] = {}
        
    def register_callback(self, 
                         exception_type: Type[Exception],
                         callback: Callable[[Exception], None]) -> None:
        """Register error callback for specific exception type
        
        Args:
            exception_type: Type of exception to handle
            callback: Callback function to execute
        """
        if exception_type not in self.error_callbacks:
            self.error_callbacks[exception_type] = []
        self.error_callbacks[exception_type].append(callback)
        
    def handle_error(self, error: Exception,
                    context: Dict[str, Any] = None) -> None:
        """Handle an error with registered callbacks
        
        Args:
            error: Exception to handle
            context: Additional context information
        """
        error_type = type(error)
        
        # Log the error with context
        self._log_error(error, context)
        
        # Execute callbacks for this error type
        callbacks = self._get_callbacks(error_type)
        for callback in callbacks:
            try:
                callback(error)
            except Exception as e:
                self.error_logger.error(
                    f'Error in error callback {callback.__name__}: {str(e)}'
                )
                
    def _log_error(self, error: Exception,
                   context: Optional[Dict[str, Any]] = None) -> None:
        """Log error with full context and stack trace
        
        Args:
            error: Exception to log
            context: Additional context information
        """
        error_type = type(error).__name__
        error_message = str(error)
        stack_trace = ''.join(traceback.format_tb(error.__traceback__))
        
        # Format context information
        context_str = ''
        if context:
            context_str = '\nContext:\n' + '\n'.join(
                f'  {k}: {v}' for k, v in context.items()
            )
            
        # Log the error
        self.error_logger.error(
            f'Error Type: {error_type}\n'
            f'Message: {error_message}\n'
            f'Stack Trace:\n{stack_trace}'
            f'{context_str}'
        )
        
    def _get_callbacks(self, error_type: Type[Exception]) -> list:
        """Get all callbacks for an error type including parent types
        
        Args:
            error_type: Type of exception
            
        Returns:
            list: List of callback functions
        """
        callbacks = []
        for exception_type, type_callbacks in self.error_callbacks.items():
            if issubclass(error_type, exception_type):
                callbacks.extend(type_callbacks)
        return callbacks

# Global error handler instance
error_handler = ErrorHandler()

def handle_errors(error_types: Union[Type[Exception], tuple] = Exception,
                 context_provider: Callable = None,
                 reraise: bool = False):
    """Decorator for automatic error handling
    
    Args:
        error_types: Exception type(s) to catch
        context_provider: Function to provide additional context
        reraise: Whether to reraise the exception after handling
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_types as e:
                # Get context if available
                context = {}
                if context_provider:
                    try:
                        context = context_provider(*args, **kwargs)
                    except Exception as ce:
                        logger.error(f'Error getting context: {str(ce)}')
                
                # Let plugin errors pass through
                if isinstance(e, PluginError):
                    error_handler.handle_error(e, context)
                    raise
                
                # Convert other errors to plugin errors
                msg = f'Error in {func.__name__}: {str(e)}'
                logger.error(msg)
                error_handler.handle_error(e, context)
                raise PluginError(msg)
                
            except Exception as e:
                # Convert unexpected errors to plugin errors
                msg = f'Unexpected error in {func.__name__}: {str(e)}'
                logger.error(msg)
                raise PluginError(msg) from e
        return wrapper
    return decorator

def init_error_handling():
    """Initialize error handling system with default handlers"""
    # Register default error handlers
    error_handler.register_callback(
        WiFiFortressError,
        lambda e: logger.error(f'WiFi Fortress error: {str(e)}')
    )
    
    error_handler.register_callback(
        NetworkError,
        lambda e: logger.error(f'Network error: {str(e)}')
    )
    
    error_handler.register_callback(
        PluginError,
        lambda e: logger.error(f'Plugin error: {str(e)}')
    )
    
    error_handler.register_callback(
        ConfigurationError,
        lambda e: logger.error(f'Configuration error: {str(e)}')
    )
    
    # Register security-specific handlers
    error_handler.register_callback(
        SecurityError,
        lambda e: (
            logger.critical(f'Security violation: {str(e)}'),
            logger.critical('Stack trace:'),
            logger.critical(traceback.format_exc())
        )
    )    
    # Register default callbacks
    def network_error_callback(error: NetworkError):
        """Handle network errors"""
        logger.warning(f'Network error occurred: {str(error)}')
        
    def security_error_callback(error: SecurityError):
        """Handle security errors"""
        logger.critical(f'Security error occurred: {str(error)}')
        
    def plugin_error_callback(error: PluginError):
        """Handle plugin errors"""
        logger.error(f'Plugin error occurred: {str(error)}')
        
    error_handler.register_callback(NetworkError, network_error_callback)
    error_handler.register_callback(SecurityError, security_error_callback)
    error_handler.register_callback(PluginError, plugin_error_callback)
    
    logger.info('Error handling system initialized')
