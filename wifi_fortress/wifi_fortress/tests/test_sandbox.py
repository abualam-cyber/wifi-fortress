"""Tests for plugin sandbox"""

import os
import sys
import time
import pytest
from pathlib import Path

from wifi_fortress.core.sandbox import PluginSandbox, SecurityError

@pytest.fixture
def sandbox():
    """Create a plugin sandbox for testing"""
    return PluginSandbox(max_memory_mb=10, max_cpu_time=1)

def test_safe_plugin(sandbox, tmp_path):
    """Test loading and executing a safe plugin"""
    # Create test plugin
    plugin_dir = tmp_path / 'plugins'
    plugin_dir.mkdir()
    
    test_plugin = plugin_dir / 'safe_plugin.py'
    test_plugin.write_text('''\
def safe_method():
    # Simple arithmetic
    result = 0
    for i in range(100):
        result += i
    return result
''')
    
    # Load and execute plugin
    module = sandbox.load_plugin(test_plugin)
    result = sandbox.execute_plugin_method(module, 'safe_method')
    assert result == sum(range(100))

def test_dangerous_plugin(sandbox, tmp_path):
    """Test loading a dangerous plugin"""
    plugin_dir = tmp_path / 'plugins'
    plugin_dir.mkdir()
    
    # Plugin that tries to access system resources
    test_plugin = plugin_dir / 'dangerous_plugin.py'
    test_plugin.write_text('''\
import os
import sys

def dangerous_method():
    # Try to delete files
    os.remove('/important_file')
    return True
''')
    
    # Loading should fail due to restricted globals
    with pytest.raises(SecurityError, match='Failed to load plugin in sandbox'):
        sandbox.load_plugin(test_plugin)

def test_resource_limits(sandbox, tmp_path):
    """Test plugin resource limits"""
    plugin_dir = tmp_path / 'plugins'
    plugin_dir.mkdir()
    
    # Plugin that consumes too much memory
    memory_plugin = plugin_dir / 'memory_hog.py'
    memory_plugin.write_text('''\
def consume_memory():
    # Try to allocate a large list
    data = [0] * (1024 * 1024 * 20)  # 20MB (should exceed 10MB limit)
    return len(data)
''')
    
    # Plugin that runs too long
    cpu_plugin = plugin_dir / 'cpu_hog.py'
    cpu_plugin.write_text('''\
def consume_cpu():
    # Infinite loop
    while True:
        pass
''')
    
    # Test memory limit
    module = sandbox.load_plugin(memory_plugin)
    with pytest.raises(SecurityError, match='Memory limit exceeded'):
        sandbox.execute_plugin_method(module, 'consume_memory')
    
    # Test CPU limit
    module = sandbox.load_plugin(cpu_plugin)
    with pytest.raises(SecurityError, match='Plugin method execution timed out'):
        sandbox.execute_plugin_method(module, 'consume_cpu')
