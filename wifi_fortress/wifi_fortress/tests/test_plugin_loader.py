import logging
import pytest
import sys
from pathlib import Path
from wifi_fortress.core.plugin_loader import Plugin, PluginLoader, PluginError

logger = logging.getLogger(__name__)

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class TestPlugin(Plugin):
    name = 'Test Plugin'
    description = 'Test plugin for unit testing'
    version = '1.0.0'
    author = 'Test Author'
    
    def __init__(self):
        super().__init__()
        self.initialized = False
        self.enabled = False
    
    def initialize(self) -> bool:
        self.initialized = True
        self.enabled = True
        return True
        
    def cleanup(self) -> bool:
        self.initialized = False
        self.enabled = False
        return True

    def process_data(self, input_data: dict) -> dict:
        # Safe data processing
        return {k.upper(): v.upper() if isinstance(v, str) else v
                for k, v in input_data.items()}

@pytest.fixture
def temp_plugin_dir(tmp_path):
    """Create a temporary plugin directory"""
    # Create plugins directory
    plugin_dir = tmp_path / 'plugins'
    plugin_dir.mkdir(parents=True, exist_ok=True)
    
    # Add parent directory to Python path
    parent_dir = str(tmp_path)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    return plugin_dir

@pytest.fixture
def plugin_loader(tmp_path):
    """Create a plugin loader for testing"""
    plugin_dir = tmp_path / 'plugins'
    config_dir = tmp_path / 'config'
    plugin_dir.mkdir()
    config_dir.mkdir()
    return PluginLoader(plugin_dir, config_dir)

@pytest.fixture
def test_plugin_file(plugin_loader):
    """Create a test plugin file"""
    plugin_file = plugin_loader.plugin_dir / 'test_plugin.py'
    plugin_content = '''
from wifi_fortress.core.plugin_loader import Plugin

class TestPlugin(Plugin):
    name = "Test Plugin"
    description = "Test plugin for testing"
    version = "1.0.0"
    author = "Test Author"
    
    def initialize(self) -> bool:
        # Safe initialization
        self.data = {}
        return True
        
    def cleanup(self) -> bool:
        # Safe cleanup
        self.data.clear()
        self.initialized = False
        self.enabled = False
        return True
'''
    plugin_file.write_text(plugin_content)
    
    # Wait for file to be written
    assert plugin_file.exists(), "Plugin file not created"
    
    # Clean up module if it exists
    module_name = plugin_file.stem
    if module_name in sys.modules:
        logger.debug(f'Removing existing module: {module_name}')
        del sys.modules[module_name]
    
    # Clean up any previous instances
    for cls in Plugin.__subclasses__():
        if cls.__name__ == 'TestPlugin':
            logger.debug('Found existing TestPlugin class, removing from Plugin subclasses')
            Plugin.__subclasses__().remove(cls)
    
    # Force plugin loader to reload plugins
    plugin_loader._load_plugins()
    
    return plugin_path

@pytest.fixture(autouse=True)
def _cleanup_sys_modules():
    """Clean up test plugin modules from sys.modules after each test"""
    yield
    for name in list(sys.modules.keys()):
        if name.startswith('test_plugin'):
            del sys.modules[name]

def test_plugin_base_class():
    """Test Plugin base class"""
    # Create instance
    plugin = Plugin()
    
    # Check class attributes
    assert plugin.name == 'Base Plugin', "Base plugin name mismatch"
    assert plugin.description == 'Base plugin class', "Base plugin description mismatch"
    assert plugin.version == '1.0.0', "Base plugin version mismatch"
    assert plugin.author == 'Unknown', "Base plugin author mismatch"
    
    # Check instance attributes
    assert isinstance(plugin.logger, logging.Logger), "Logger not properly initialized"
    assert not plugin.enabled, "Plugin should not be enabled by default"
    assert not plugin.initialized, "Plugin should not be initialized by default"
    
    # Test initialization
    success = plugin.initialize()
    assert success, "Plugin initialization failed"
    assert plugin.enabled, "Plugin not enabled after initialization"
    assert plugin.initialized, "Plugin not initialized after initialization"
    
    # Test cleanup
    success = plugin.cleanup()
    assert success, "Plugin cleanup failed"
    assert not plugin.enabled, "Plugin still enabled after cleanup"
    assert not plugin.initialized, "Plugin still initialized after cleanup"

def test_plugin_loader_init(plugin_loader, temp_plugin_dir):
    """Test PluginLoader initialization"""
    # Check directory path
    assert plugin_loader.plugin_dir == Path(temp_plugin_dir), "Plugin directory path mismatch"
    assert plugin_loader.plugin_dir.exists(), "Plugin directory does not exist"
    assert plugin_loader.plugin_dir.is_dir(), "Plugin directory path is not a directory"
    
    # Check registries
    assert isinstance(plugin_loader.plugins, dict), "Plugins registry not a dictionary"
    assert isinstance(plugin_loader.active_plugins, dict), "Active plugins registry not a dictionary"
    assert isinstance(plugin_loader.loaded_instances, dict), "Loaded instances registry not a dictionary"
    
    # Check initial state
    assert len(plugin_loader.plugins) == 0, "Plugins registry not empty at initialization"
    assert len(plugin_loader.active_plugins) == 0, "Active plugins registry not empty at initialization"
    assert len(plugin_loader.loaded_instances) == 0, "Loaded instances registry not empty at initialization"

def test_plugin_loading(plugin_loader, test_plugin_file):
    """Test plugin loading"""
    # Force reload to ensure clean state
    plugin_loader._load_plugins()
    
    # Plugin should be loaded
    available_plugins = plugin_loader.get_available_plugins()
    assert 'TestPlugin' in available_plugins, "TestPlugin not found in available plugins"
    assert 'TestPlugin' in plugin_loader.plugins, "TestPlugin not found in plugins registry"
    
    # Check plugin class
    plugin_class = plugin_loader.plugins['TestPlugin']
    assert plugin_class.name == 'Test Plugin', "Plugin name mismatch"
    assert plugin_class.version == '1.0.0', "Plugin version mismatch"
    assert plugin_class.description == 'Test plugin for unit testing', "Plugin description mismatch"
    assert plugin_class.author == 'Test Author', "Plugin author mismatch"

def test_plugin_activation(plugin_loader, test_plugin_file):
    """Test plugin activation and deactivation"""
    # Force reload to ensure clean state
    plugin_loader.reload_plugins()
    
    # Initial state
    assert 'TestPlugin' in plugin_loader.plugins, "TestPlugin not found in available plugins"
    assert len(plugin_loader.active_plugins) == 0, "Active plugins not empty at start"
    
    # Activate plugin
    success = plugin_loader.activate_plugin('TestPlugin')
    assert success, "Failed to activate TestPlugin"
    assert 'TestPlugin' in plugin_loader.active_plugins, "TestPlugin not in active plugins after activation"
    
    # Check instance state
    plugin = plugin_loader.active_plugins['TestPlugin']
    assert isinstance(plugin, Plugin), "Plugin instance not of correct type"
    assert plugin.enabled, "Plugin not enabled after activation"
    assert plugin.initialized, "Plugin not initialized after activation"
    
    # Deactivate plugin
    success = plugin_loader.deactivate_plugin('TestPlugin')
    assert success, "Failed to deactivate TestPlugin"
    assert 'TestPlugin' not in plugin_loader.active_plugins, "TestPlugin still in active plugins after deactivation"
    assert not plugin.enabled, "Plugin still enabled after deactivation"
    assert not plugin.initialized, "Plugin still initialized after deactivation"

def test_plugin_errors(plugin_loader):
    """Test plugin error handling"""
    # Force reload to ensure clean state
    plugin_loader.reload_plugins()
    
    # Test non-existent plugin
    with pytest.raises(KeyError):
        plugin_loader.instantiate_plugin('NonExistentPlugin')

    # Test activating non-existent plugin
    with pytest.raises(PluginError, match='Plugin NonExistentPlugin not found'):
        plugin_loader.activate_plugin('NonExistentPlugin')
    
    success = plugin_loader.deactivate_plugin('NonExistentPlugin')
    assert success, "Deactivating non-active plugin should succeed"
    
    # Test activating plugin with invalid initialization
    class InvalidPlugin(Plugin):
        name = 'Invalid Plugin'
        description = 'Invalid plugin for testing'
        version = '1.0.0'
        author = 'Test Author'
        
        def __init__(self):
            super().__init__()
            self.initialized = False
            self.enabled = False
        
        def initialize(self) -> bool:
            raise RuntimeError('Test initialization error')
        
        def cleanup(self) -> bool:
            return True
    
    # Register invalid plugin
    plugin_loader.plugins['InvalidPlugin'] = InvalidPlugin
    
    # Try to activate it
    with pytest.raises(PluginError):
        plugin_loader.activate_plugin('InvalidPlugin')
    
    # Verify it's not active
    assert 'InvalidPlugin' not in plugin_loader.active_plugins, "Invalid plugin should not be active"
    assert 'InvalidPlugin' not in plugin_loader.loaded_instances, "Invalid plugin instance should be cleaned up"

def test_plugin_listing(plugin_loader, test_plugin_file):
    """Test plugin listing methods"""
    # Force reload to ensure clean state
    plugin_loader._load_plugins()
    
    # Get available plugins
    available_plugins = plugin_loader.get_available_plugins()
    assert len(available_plugins) > 0, "No plugins found"
    assert 'TestPlugin' in available_plugins, "TestPlugin not found in available plugins"
    
    # Get active plugins (should be empty)
    active_plugins = plugin_loader.get_active_plugins()
    assert len(active_plugins) == 0, "Active plugins not empty at start"
    
    # Activate plugin
    success = plugin_loader.activate_plugin('TestPlugin')
    assert success, "Failed to activate TestPlugin"
    
    # Check active plugins
    active_plugins = plugin_loader.get_active_plugins()
    assert len(active_plugins) == 1, "Wrong number of active plugins"
    assert 'TestPlugin' in active_plugins, "TestPlugin not in active plugins"
    
    # Deactivate plugin
    success = plugin_loader.deactivate_plugin('TestPlugin')
    assert success, "Failed to deactivate TestPlugin"
    
    # Check active plugins again
    active_plugins = plugin_loader.get_active_plugins()
    assert len(active_plugins) == 0, "Active plugins not empty after deactivation"

def test_plugin_reload(plugin_loader, test_plugin_file):
    """Test plugin reloading"""
    # Initial state check
    assert 'TestPlugin' in plugin_loader.plugins, "TestPlugin not found in available plugins"
    assert len(plugin_loader.active_plugins) == 0, "Active plugins not empty at start"
    
    # Activate plugin
    success = plugin_loader.activate_plugin('TestPlugin')
    assert success, "Failed to activate TestPlugin"
    
    # Check activation state
    assert 'TestPlugin' in plugin_loader.active_plugins, "TestPlugin not in active plugins after activation"
    initial_instance = plugin_loader.active_plugins['TestPlugin']
    assert initial_instance.enabled, "Initial instance not enabled"
    assert initial_instance.initialized, "Initial instance not initialized"
    
    # Reload plugins
    success = plugin_loader.reload_plugins()
    assert success, "Failed to reload plugins"
    
    # Check plugin availability after reload
    assert 'TestPlugin' in plugin_loader.plugins, "TestPlugin not found in available plugins after reload"
    assert 'TestPlugin' in plugin_loader.active_plugins, "TestPlugin not reactivated after reload"
    
    # Check reloaded instance
    new_instance = plugin_loader.active_plugins['TestPlugin']
    assert isinstance(new_instance, Plugin), "Reactivated plugin not an instance of Plugin"
    assert new_instance.enabled, "Reactivated plugin not enabled"
    assert new_instance.initialized, "Reactivated plugin not initialized"
    
    # Verify instance was recreated
    assert id(new_instance) != id(initial_instance), "Plugin instance not recreated on reload"

def test_plugin_listing(plugin_loader, test_plugin_file):
    """Test plugin listing methods"""
    # Force reload plugins to ensure clean state
    plugin_loader.reload_plugins()
    
    # Verify no active plugins initially
    active = plugin_loader.get_active_plugins()
    assert len(active) == 0, f"Expected 0 active plugins, got {len(active)}: {active}"
    
    # Check available plugins
    available = plugin_loader.get_available_plugins()
    assert len(available) == 1, f"Expected 1 available plugin, got {len(available)}: {available}"
    assert 'TestPlugin' in available, f"TestPlugin not found in available plugins: {available}"
    
    # Activate plugin and verify it appears in active list
    success = plugin_loader.activate_plugin('TestPlugin')
    assert success, "Failed to activate TestPlugin"
    
    active = plugin_loader.get_active_plugins()
    assert len(active) == 1, f"Expected 1 active plugin after activation, got {len(active)}: {active}"
    assert 'TestPlugin' in active, f"TestPlugin not found in active plugins after activation: {active}"

