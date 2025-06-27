# WiFi Fortress - User Guide

## Introduction
WiFi Fortress is a Wi-Fi auditing platform designed for ethical hacking, red teaming, and security analysis.

## Requirements
- A Linux or Windows machine
- Monitor-mode capable wireless adapter
- Installed: aircrack-ng, Python 3.10+, PyQt5

## Running the Application
1. Launch the GUI from your system menu or terminal:
   ```bash
   sudo python3 main.py
   ```
2. Choose your wireless adapter (must support monitor mode)
3. Scan, select targets, and choose attacks (Evil Twin, WPA Crack, PMKID)
4. Use the "Generate Report" button to create compliance audit documents

## Reports
Reports are saved in `/reports/` as both PDF and HTML.