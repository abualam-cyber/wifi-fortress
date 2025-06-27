# WiFi Fortress Installation Guide

## System Requirements

- Python 3.8 or higher
- Windows, Linux, or macOS
- Administrator/root privileges (required for network scanning)
- Git (optional, for development)

## Installation Steps

### 1. Clone the Repository (if using Git)

```bash
git clone https://github.com/your-repo/wifi-fortress.git
cd wifi-fortress
```

### 2. Create a Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configuration

The application will create a default configuration file at:
- Windows: `%USERPROFILE%\.wifi_fortress\config.json`
- Linux/macOS: `~/.wifi_fortress/config.json`

You can modify this file to customize:
- Logging settings
- Network scanning intervals
- Security parameters
- Plugin configurations

### 5. First Run

```bash
# From the project root directory
python -m wifi_fortress
```

## Development Setup

For development, install additional dependencies:

```bash
pip install -r requirements-dev.txt
```

Run tests:

```bash
pytest wifi_fortress/tests/
```

## Troubleshooting

### Common Issues

1. **Permission Errors**
   - Ensure you have administrator/root privileges
   - Check firewall settings
   - Verify network interface permissions

2. **Missing Dependencies**
   - Run `pip install -r requirements.txt` again
   - Check Python version compatibility
   - Install system-level dependencies if needed

3. **Network Scanning Issues**
   - Verify network interface is active
   - Check system firewall settings
   - Ensure proper permissions for packet capture

### Getting Help

- Open an issue on GitHub
- Check the documentation
- Join our community forum

## Security Considerations

1. **Permissions**
   - Run with minimum required privileges
   - Use virtual environment
   - Keep system and dependencies updated

2. **Network Access**
   - Configure firewall rules
   - Use secure protocols
   - Monitor network activity

3. **Data Protection**
   - Enable encryption in configuration
   - Protect configuration files
   - Regular security audits

## Updates and Maintenance

1. **Updating WiFi Fortress**
   ```bash
   git pull origin main
   pip install -r requirements.txt
   ```

2. **Backup Configuration**
   - Regularly backup ~/.wifi_fortress directory
   - Document custom configurations
   - Version control your modifications
