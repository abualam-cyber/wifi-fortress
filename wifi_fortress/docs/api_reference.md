# WiFi Fortress API Reference

## Core Components

### NetworkMapper

The `NetworkMapper` class provides network discovery and monitoring functionality.

```python
from wifi_fortress.core.network_mapper import NetworkMapper

# Initialize with optional encryption
mapper = NetworkMapper(encryption_key='your-secret-key')
```

#### Methods

##### `scan_network(interface: str, network: str) -> List[NetworkDevice]`
Perform a network scan with security features.

- **Arguments:**
  - `interface`: Network interface name
  - `network`: Network address in CIDR notation (e.g., '192.168.1.0/24')
- **Returns:** List of discovered NetworkDevice objects
- **Raises:**
  - `ValueError`: If inputs are invalid
  - `RuntimeError`: If rate limit exceeded

##### `start_continuous_scanning(interface: str, network: str, interval: int = 300)`
Start continuous network scanning.

- **Arguments:**
  - `interface`: Network interface name
  - `network`: Network address in CIDR notation
  - `interval`: Scan interval in seconds (minimum 60)
- **Raises:**
  - `ValueError`: If inputs are invalid
  - `RuntimeError`: If scanning already active

##### `stop_continuous_scanning(timeout: int = 10) -> bool`
Stop continuous scanning.

- **Arguments:**
  - `timeout`: Maximum wait time in seconds
- **Returns:** True if stopped successfully

### PluginLoader

The `PluginLoader` class manages the plugin system.

```python
from wifi_fortress.core.plugin_loader import PluginLoader

loader = PluginLoader(plugin_dir='plugins')
```

#### Methods

##### `discover_plugins() -> List[str]`
Find available plugins.

- **Returns:** List of plugin file paths

##### `load_plugin(plugin_path: str) -> bool`
Load a specific plugin.

- **Arguments:**
  - `plugin_path`: Path to plugin file
- **Returns:** True if loaded successfully

### ConfigManager

The `ConfigManager` class handles configuration management.

```python
from wifi_fortress.core.config_manager import ConfigManager

config = ConfigManager()
```

#### Methods

##### `get(key: str, default: Any = None) -> Any`
Get configuration value.

- **Arguments:**
  - `key`: Configuration key (dot notation)
  - `default`: Default value if key not found
- **Returns:** Configuration value

##### `set(key: str, value: Any) -> bool`
Set configuration value.

- **Arguments:**
  - `key`: Configuration key (dot notation)
  - `value`: Value to set
- **Returns:** True if saved successfully

## Security Features

### Rate Limiting

The `RateLimiter` class provides thread-safe rate limiting.

```python
from wifi_fortress.core.rate_limiter import RateLimiter

limiter = RateLimiter(max_requests=5, time_window=60)
```

#### Methods

##### `allow_request() -> bool`
Check if request is allowed.

- **Returns:** True if request is within rate limit

##### `reset()`
Reset rate limiter state.

## Plugins

### Creating Custom Plugins

Inherit from the `Plugin` base class:

```python
from wifi_fortress.core.plugin_loader import Plugin

class CustomPlugin(Plugin):
    name = 'Custom Plugin'
    description = 'Custom plugin description'
    version = '1.0.0'
    author = 'Your Name'
    
    def initialize(self) -> bool:
        # Setup code
        return True
        
    def cleanup(self) -> bool:
        # Cleanup code
        return True
```

### Built-in Plugins

#### SecurityMonitor

Monitors network for security threats.

```python
from wifi_fortress.plugins.security_monitor import SecurityMonitor

monitor = SecurityMonitor()
monitor.initialize()
```

## Best Practices

### Security

1. Always use encryption for sensitive data
2. Implement rate limiting for network operations
3. Validate all inputs
4. Handle thread cleanup properly
5. Use proper error handling

### Performance

1. Limit concurrent scans
2. Use appropriate scan intervals
3. Implement timeouts
4. Clean up resources properly

### Plugin Development

1. Implement both initialize() and cleanup()
2. Handle exceptions properly
3. Use logging for important events
4. Document plugin functionality
5. Follow thread safety guidelines
