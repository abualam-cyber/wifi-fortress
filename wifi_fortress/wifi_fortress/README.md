# WiFi Fortress

A powerful and extensible WiFi security suite with plugin support.

## Features

- Plugin-based architecture for easy extensibility
- Modern PyQt5-based GUI
- Real-time WiFi network scanning
- Network security analysis tools
- Cross-platform support

## Requirements

- Python 3.8 or higher
- Dependencies listed in requirements.txt

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/wifi_fortress.git
   cd wifi_fortress
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. The main window will show available plugins
3. Select a plugin and click 'Start Selected' to begin

## Creating Plugins

1. Create a new Python file in the `plugins` directory
2. Inherit from the `Plugin` base class
3. Implement required methods:
   - `initialize()`
   - `cleanup()`

Example plugin:

```python
from core.plugin_loader import Plugin

class MyPlugin(Plugin):
    name = 'My Plugin'
    description = 'Does something cool'
    version = '1.0.0'
    author = 'Your Name'
    
    def initialize(self) -> bool:
        # Setup code here
        return True
        
    def cleanup(self) -> bool:
        # Cleanup code here
        return True
```

## License

MIT License - see LICENSE file for details