"""Plugin sandbox module for WiFi Fortress"""

import os
import sys
import psutil
import importlib.util
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Union

from wifi_fortress.core.error_handler import handle_errors, SecurityError
import logging

logger = logging.getLogger(__name__)

class PluginSandbox:
    """Provides a restricted execution environment for plugins"""
    
    def __init__(self, max_memory_mb: int = 100, max_cpu_time: int = 30):
        """Initialize plugin sandbox
        
        Args:
            max_memory_mb: Maximum memory usage in MB
            max_cpu_time: Maximum CPU time in seconds
        """
        self.max_memory = max_memory_mb * 1024 * 1024  # Convert to bytes
        self.max_cpu_time = max_cpu_time
        
    def _check_resource_limits(self):
        """Check resource usage against limits"""
        process = psutil.Process()
        
        # Check memory usage
        memory_used = process.memory_info().rss
        if memory_used > self.max_memory:
            raise SecurityError(f'Memory limit exceeded: {memory_used} bytes')
        
        # CPU time is checked via thread timeout
        
    def _create_restricted_globals(self) -> Dict[str, Any]:
        """Create restricted globals for plugin execution"""
        safe_builtins = {
            'abs': abs,
            'bool': bool,
            'dict': dict,
            'float': float,
            'int': int,
            'len': len,
            'list': list,
            'max': max,
            'min': min,
            'range': range,
            'set': set,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'type': type
        }
        
        return {
            '__builtins__': safe_builtins,
            '__name__': '__plugin__',
            '__file__': None,
            '__loader__': None,
            '__package__': None,
            '__spec__': None,
            '__cached__': None,
            '__doc__': None
        }
        
    def load_plugin(self, plugin_path: Union[str, Path]) -> Any:
        """Load a plugin in the sandbox
        
        Args:
            plugin_path: Path to plugin file
            
        Returns:
            Any: Plugin module
            
        Raises:
            SecurityError: If loading fails or sandbox is violated
        """
        try:
            plugin_path = Path(plugin_path)
            if not plugin_path.exists():
                raise SecurityError(f'Plugin file not found: {plugin_path}')
            
            # Create module spec
            spec = importlib.util.spec_from_file_location(
                '__plugin__',
                str(plugin_path)
            )
            if spec is None or spec.loader is None:
                raise SecurityError(f'Failed to create module spec for {plugin_path}')
            
            # Create module
            module = importlib.util.module_from_spec(spec)
            
            # Set up restricted environment
            module.__dict__.update(self._create_restricted_globals())
            
            # Load in thread with resource monitoring
            def load_with_monitoring():
                try:
                    spec.loader.exec_module(module)
                    self._check_resource_limits()
                except Exception as e:
                    raise SecurityError(f'Plugin loading failed: {str(e)}')
                
            thread = threading.Thread(target=load_with_monitoring, daemon=True)
            thread.start()
            thread.join(timeout=self.max_cpu_time)
            
            if thread.is_alive():
                # Thread is still running after timeout
                raise SecurityError('Plugin execution timed out')
                
            return module
            
        except SecurityError:
            raise
        except Exception as e:
            msg = f'Failed to load plugin in sandbox: {str(e)}'
            logger.error(msg)
            raise SecurityError(msg)
            
    def execute_plugin_method(self, module: Any, method_name: str, *args, **kwargs) -> Any:
        """Execute a plugin method in the sandbox
        
        Args:
            module: Plugin module
            method_name: Name of method to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Any: Method result
            
        Raises:
            SecurityError: If execution fails or sandbox is violated
        """
        try:
            if not hasattr(module, method_name):
                raise SecurityError(f'Method {method_name} not found in plugin')
                
            method = getattr(module, method_name)
            
            # Execute in thread with resource limits
            result = None
            error = None
            
            def execute_with_monitoring():
                nonlocal result, error
                try:
                    result = method(*args, **kwargs)
                    self._check_resource_limits()
                except Exception as e:
                    error = e
                    
            thread = threading.Thread(target=execute_with_monitoring, daemon=True)
            thread.start()
            thread.join(timeout=self.max_cpu_time)
            
            if thread.is_alive():
                raise SecurityError('Plugin method execution timed out')
                
            if error:
                if isinstance(error, SecurityError):
                    raise error
                raise SecurityError(f'Plugin method execution failed: {str(error)}')
                
            return result
            
        except SecurityError:
            raise
        except Exception as e:
            msg = f'Failed to execute plugin method: {str(e)}'
            logger.error(msg)
            raise SecurityError(msg)
