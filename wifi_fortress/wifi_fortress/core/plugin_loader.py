import logging
import importlib
import inspect
import os
import sys
from typing import Dict, List, Optional, Type
from pathlib import Path
from wifi_fortress.core.error_handler import handle_errors, PluginError
from wifi_fortress.core.security import SecurityManager
from wifi_fortress.core.sandbox import PluginSandbox

logger = logging.getLogger(__name__)

class Plugin:
    """Base class for all plugins"""
    name: str = 'Base Plugin'
    description: str = 'Base plugin class'
    version: str = '1.0.0'
    author: str = 'Unknown'
    
    def __init__(self):
        self.enabled = False
        self.initialized = False
        self.logger = logging.getLogger(f'wifi_fortress.plugins.{self.name}')
    
    def initialize(self) -> bool:
        """Initialize the plugin"""
        self.logger.info(f'Initializing plugin {self.name}')
        self.initialized = True
        self.enabled = True
        return True
    
    def cleanup(self) -> bool:
        """Cleanup resources"""
        self.logger.info(f'Cleaning up plugin {self.name}')
        self.initialized = False
        self.enabled = False
        return True

class PluginLoader:
    """Dynamic plugin loader for WiFi Fortress"""
    
    def __init__(self, plugin_dir: Union[str, Path], config_dir: Union[str, Path]):
        """Initialize plugin loader
        
        Args:
            plugin_dir: Directory containing plugins
            config_dir: Directory for configuration files
        """
        self.plugin_dir = Path(plugin_dir).resolve()
        self.config_dir = Path(config_dir).resolve()
        self.plugins = {}
        self.security = SecurityManager(config_dir)
        self.sandbox = PluginSandbox(max_memory_mb=100, max_cpu_time=30)
        
        # Create plugin directory if it doesn't exist
        if not self.plugin_dir.exists():
            logger.info(f'Creating plugin directory: {self.plugin_dir}')
            self.plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize security manager
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / 'config'
        self.security = SecurityManager(config_dir)
        
        # Initialize registries
        self.active_plugins: Dict[str, Plugin] = {}
        self.loaded_instances: Dict[str, Plugin] = {}
        logger.debug('Initialized empty plugin registries')
        
        # Load plugins
        logger.info('Loading plugins...')
        self._load_plugins()
        
    @handle_errors(error_types=PluginError)
    def _load_plugins(self) -> None:
        """Load plugins from plugin directory"""
        if not self.plugin_dir.exists():
            logger.warning(f'Plugin directory {self.plugin_dir} does not exist')
            self.plugin_dir.mkdir(parents=True, exist_ok=True)
            return
        
        plugin_dir = Path(self.plugin_dir).resolve()
        plugin_dir_str = str(plugin_dir)
        logger.info(f'Plugin directory: {plugin_dir_str}')
        
        if plugin_dir_str not in sys.path:
            sys.path.insert(0, plugin_dir_str)
            
        # Clear existing plugins
        self.plugins.clear()
        
        # Find Python files in plugin directory
        for plugin_file in plugin_dir.glob('*.py'):
            if plugin_file.stem.startswith('_'):
                continue
                
            try:
                # Validate plugin security
                if not self.security.validate_plugin(plugin_file):
                    continue
                
                # Load module in sandbox
                module = self.sandbox.load_plugin(plugin_file)
                
                # Find plugin class
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if (isinstance(item, type) and 
                        issubclass(item, Plugin) and 
                        item != Plugin):
                        self.plugins[item.name] = item
                        logger.info(f'Loaded plugin: {item.name}')
                        
            except Exception as e:
                logger.error(
                    f'Failed to load plugin {plugin_file}: {str(e)}'
                )
                
    @handle_errors(error_types=PluginError)
    def get_available_plugins(self) -> List[str]:
        """Get list of available plugin names
        
        Returns:
            List[str]: List of plugin names
        """
        # Force reload to ensure we have latest plugins
        self._load_plugins()
        
        # Get plugin names
        plugin_names = list(self.plugins.keys())
        logger.debug(f'Available plugins: {plugin_names}')
        return plugin_names
        
    @handle_errors(error_types=PluginError)
    def get_active_plugins(self) -> List[str]:
        """Get list of active plugins
        
        Returns:
            List[str]: Names of active plugins
        """
        return list(self.active_plugins.keys())
        
    @handle_errors(error_types=PluginError)
    def activate_plugin(self, name: str, **kwargs) -> bool:
        """Activate a plugin
        
        Args:
            name (str): Plugin name
            **kwargs: Additional arguments to pass to plugin
            
        Returns:
            bool: True if activation was successful
            
        Raises:
            PluginError: If plugin activation fails
        """
        logger.info(f'Activating plugin: {name}')
        
        # Check if plugin exists
        if name not in self.plugins:
            msg = f'Plugin {name} not found'
            logger.error(msg)
            raise PluginError(msg)
        
        # Check if already active
        if name in self.active_plugins:
            logger.warning(f'Plugin {name} already active')
            return True
        
        # Get or create plugin instance
        if name in self.loaded_instances:
            logger.debug(f'Using existing instance for plugin: {name}')
            instance = self.loaded_instances[name]
        else:
            logger.debug(f'Creating new instance for plugin: {name}')
            instance = self.instantiate_plugin(name)
            self.loaded_instances[name] = instance
        
        # Initialize plugin
        logger.debug(f'Initializing plugin: {name}')
        try:
            success = instance.initialize(**kwargs)
            if not success:
                msg = f'Failed to initialize plugin {name}'
                logger.error(msg)
                # Remove instance on error
                if name in self.loaded_instances:
                    del self.loaded_instances[name]
                raise PluginError(msg)
                
            # Add to active plugins
            self.active_plugins[name] = instance
            logger.info(f'Successfully activated plugin: {name}')
            return True
            
        except PluginError:
            # Let plugin errors pass through
            raise
            
        except Exception as e:
            msg = f'Error initializing plugin {name}: {str(e)}'
            logger.error(msg)
            # Remove instance on error
            if name in self.loaded_instances:
                del self.loaded_instances[name]
            # Re-raise as PluginError
            raise PluginError(msg) from e
            
    @handle_errors(error_types=PluginError)
    def deactivate_plugin(self, name: str) -> bool:
        """Deactivate a plugin
        
        Args:
            name: Plugin name
            
        Returns:
            bool: True if plugin was deactivated
            
        Raises:
            PluginError: If plugin deactivation fails
        """
        logger.debug(f'Attempting to deactivate plugin: {name}')
        if name not in self.active_plugins:
            logger.warning(f'Plugin {name} not active')
            return True
            
        try:
            # Get plugin instance
            plugin = self.active_plugins[name]
            logger.debug(f'Running cleanup for plugin: {name}')
            
            # Run cleanup
            if not plugin.cleanup():
                msg = f'Plugin {name} cleanup failed'
                logger.error(msg)
                raise PluginError(msg)
            
            # Remove from active plugins but keep instance
            del self.active_plugins[name]
            logger.info(f'Successfully deactivated plugin: {name}')
            return True
            
        except Exception as e:
            msg = f'Error deactivating plugin {name}: {str(e)}'
            logger.error(msg)
            # Remove instance on error
            if name in self.loaded_instances:
                del self.loaded_instances[name]
            raise PluginError(msg)
            
    @handle_errors(error_types=PluginError)
    def reload_plugins(self) -> bool:
        """Reload all plugins
        
        Returns:
            bool: True if reload was successful
        """
        logger.info('Reloading all plugins...')
        
        try:
            # Store active plugins
            active_plugins = list(self.active_plugins.keys())
            logger.debug(f'Currently active plugins: {active_plugins}')
            
            # Deactivate all plugins
            for name in active_plugins:
                logger.debug(f'Deactivating plugin: {name}')
                if not self.deactivate_plugin(name):
                    logger.error(f'Failed to deactivate plugin: {name}')
                    return False
            
            # Clear all registries
            logger.debug('Clearing plugin registries')
            self.plugins.clear()
            self.active_plugins.clear()
            self.loaded_instances.clear()
            
            # Reload plugins
            logger.debug('Loading plugins from disk')
            self._load_plugins()
            
            # Reactivate plugins that were previously active
            success = True
            for name in active_plugins:
                if name in self.plugins:
                    logger.debug(f'Reactivating plugin: {name}')
                    if not self.activate_plugin(name):
                        logger.error(f'Failed to reactivate plugin: {name}')
                        success = False
                else:
                    logger.warning(f'Previously active plugin not found after reload: {name}')
                    success = False
            
            logger.info(f'Plugin reload completed with status: {success}')
            return success
            
        except Exception as e:
            logger.error(f'Error reloading plugins: {str(e)}')
            import traceback
            logger.error(traceback.format_exc())
            return False
            
    def instantiate_plugin(self, plugin_name: str) -> Plugin:
        """Create an instance of a plugin in a sandbox
        
        Args:
            plugin_name: Name of plugin to instantiate
            
        Returns:
            Plugin: Plugin instance
            
        Raises:
            PluginError: If plugin instantiation fails
        """
        try:
            plugin_class = self.plugins[plugin_name]
            
            # Create plugin instance in sandbox
            def create_instance():
                return plugin_class()
                
            plugin_instance = self.sandbox.execute_plugin_method(
                plugin_class, '__call__'
            )
            
            return plugin_instance
            
        except Exception as e:
            msg = f'Failed to instantiate plugin {plugin_name}: {str(e)}'
            logger.error(msg)
            raise PluginError(msg) from e
    
    def get_plugin_info(self) -> List[Dict]:
        """Get information about all loaded plugins"""
        info = []
        for name, plugin_class in self.plugins.items():
            info.append({
                'name': plugin_class.name,
                'description': plugin_class.description,
                'version': plugin_class.version,
                'author': plugin_class.author,
                'module_name': name
            })
        return info
    
    def cleanup_plugins(self) -> None:
        """Cleanup all loaded plugin instances"""
        for name, instance in self.loaded_instances.items():
            try:
                instance.cleanup()
            except Exception as e:
                print(f'Error cleaning up plugin {name}: {str(e)}')
        self.loaded_instances.clear()