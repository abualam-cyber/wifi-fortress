import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

from wifi_fortress.gui.dashboard import (
    DashboardWidget, StatusWidget, MetricsWidget,
    NetworkDevicesWidget, SecurityAlertsWidget, PluginsWidget
)
from wifi_fortress.core.health_monitor import HealthMonitor
from wifi_fortress.core.network_mapper import NetworkMapper
from wifi_fortress.core.plugin_loader import PluginLoader

@pytest.fixture(scope='session')
def app():
    """QApplication fixture that persists for the whole test session"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

@pytest.fixture
def dashboard(app, monkeypatch):
    """DashboardWidget fixture with mocked monitoring"""
    # Prevent actual monitoring threads from starting
    monkeypatch.setattr('wifi_fortress.core.health_monitor.HealthMonitor.start_monitoring', lambda *args: None)
    monkeypatch.setattr('wifi_fortress.core.health_monitor.HealthMonitor.stop_monitoring', lambda *args: None)
    
    widget = DashboardWidget()
    yield widget
    # Clean up
    widget.close()

def test_dashboard_init(dashboard):
    """Test dashboard initialization"""
    # Check components are initialized
    assert isinstance(dashboard.health_monitor, HealthMonitor)
    assert isinstance(dashboard.network_mapper, NetworkMapper)
    assert isinstance(dashboard.plugin_loader, PluginLoader)
    
    # Check UI elements exist
    assert all(hasattr(dashboard, attr) for attr in [
        'health_status', 'network_status', 'security_status',
        'metrics_widget', 'devices_widget', 'alerts_widget',
        'plugins_widget'
    ])
    
    # Check timer
    assert dashboard.update_timer.interval() == 1000  # 1 second refresh

def test_status_widget(app):
    """Test StatusWidget functionality"""
    widget = StatusWidget("Test Status")
    
    # Test status updates
    widget.update_status("OK", {"metric": 100})
    assert widget.status_label.text() == "OK"
    assert "metric: 100" in widget.details_label.text()
    
    widget.update_status("WARNING", {"alert": "Test warning"})
    assert widget.status_label.text() == "WARNING"
    assert "alert: Test warning" in widget.details_label.text()
    
    widget.update_status("CRITICAL", {"error": "Test error"})
    assert widget.status_label.text() == "CRITICAL"
    assert "error: Test error" in widget.details_label.text()

@pytest.mark.parametrize('cpu,mem,net_io', [
    (50.0, 75.0, {'eth0': {'bytes_sent': 1024*1024, 'bytes_recv': 2*1024*1024}}),
    (0.0, 0.0, {}),
    (100.0, 100.0, {'wlan0': {'bytes_sent': 0, 'bytes_recv': 0}})
])
def test_metrics_widget(app, cpu, mem, net_io):
    """Test MetricsWidget functionality with different metrics"""
    widget = MetricsWidget()
    
    class MockMetrics:
        cpu_percent = cpu
        memory_percent = mem
        network_io = net_io
    
    widget.update_metrics(MockMetrics())
    
    # Verify metrics
    assert widget.cpu_bar.value() == int(cpu)
    assert widget.mem_bar.value() == int(mem)
    assert widget.net_table.rowCount() == len(net_io)
    
    # Verify network table
    for row, (iface, io) in enumerate(net_io.items()):
        assert widget.net_table.item(row, 0).text() == iface
        assert widget.net_table.item(row, 1).text() == f"{io['bytes_sent']/1024/1024:.1f} MB"
        assert widget.net_table.item(row, 2).text() == f"{io['bytes_recv']/1024/1024:.1f} MB"

def test_network_devices_widget(app):
    """Test NetworkDevicesWidget functionality"""
    widget = NetworkDevicesWidget()
    
    # Test device updates
    class MockDevice:
        def __init__(self, ip, mac):
            self.ip_address = ip
            self.mac_address = mac
            self.hostname = f"host-{ip}"
            self.last_seen = "2025-06-22 12:00:00"
    
    devices = [
        MockDevice("192.168.1.1", "00:11:22:33:44:55"),
        MockDevice("192.168.1.2", "AA:BB:CC:DD:EE:FF")
    ]
    
    widget.update_devices(devices)
    
    assert widget.devices_table.rowCount() == 2
    assert widget.devices_table.item(0, 0).text() == "192.168.1.1"
    assert widget.devices_table.item(0, 1).text() == "00:11:22:33:44:55"
    assert widget.devices_table.item(0, 2).text() == "host-192.168.1.1"

@pytest.mark.parametrize('level,source,message', [
    ('HIGH', 'Firewall', 'Unauthorized access attempt'),
    ('MEDIUM', 'Network', 'High latency detected'),
    ('LOW', 'System', 'Resource usage warning')
])
def test_security_alerts_widget(app, level, source, message):
    """Test SecurityAlertsWidget functionality with different alerts"""
    widget = SecurityAlertsWidget()
    
    # Add alert
    widget.add_alert(level, source, message)
    alerts = widget.get_active_alerts()
    
    # Verify alert was added
    assert len(alerts) == 1
    assert alerts[0]['level'] == level
    assert alerts[0]['source'] == source
    assert alerts[0]['message'] == message
    
    # Verify table display
    assert widget.alerts_table.rowCount() == 1
    assert widget.alerts_table.item(0, 1).text() == level
    assert widget.alerts_table.item(0, 2).text() == source
    assert widget.alerts_table.item(0, 3).text() == message

def test_plugins_widget(app):
    """Test PluginsWidget functionality"""
    plugin_loader = PluginLoader()
    widget = PluginsWidget(plugin_loader)
    
    # Test plugin listing
    widget.update_plugins()
    
    # Initially no plugins
    assert widget.plugins_table.rowCount() == 0
    
    # Test reload
    widget.reload_plugins()
    widget.update_plugins()
    
    # Plugins should still be empty since we haven't added any
    assert widget.plugins_table.rowCount() == 0

def test_dashboard_update(dashboard, monkeypatch):
    """Test dashboard update functionality"""
    update_called = False
    
    def mock_update():
        nonlocal update_called
        update_called = True
    
    # Mock the update methods
    monkeypatch.setattr(dashboard.metrics_widget, "update_metrics", mock_update)
    monkeypatch.setattr(dashboard.devices_widget, "update_devices", mock_update)
    monkeypatch.setattr(dashboard.plugins_widget, "update_plugins", mock_update)
    
    # Trigger update
    dashboard.update_dashboard()
    
    assert update_called

def test_dashboard_close(dashboard):
    """Test dashboard cleanup on close"""
    # Trigger close event
    dashboard.close()
    
    # Check cleanup
    assert not dashboard.update_timer.isActive()
    assert not dashboard.health_monitor.is_monitoring
