# 🛡️ WiFi Fortress — Automated Wi-Fi Security Audit Framework

**WiFi Fortress** is an advanced, modular, and automated Wi-Fi penetration testing toolkit designed for red team operations, 
wireless vulnerability assessments, and rogue access point simulations. 
It empowers cybersecurity professionals and researchers with a one-click solution for performing stealth Wi-Fi attacks, 
logging credentials, emulating Evil Twin APs, and generating detailed HTML/PDF security reports.

---

## ✨ Features

- ✅ **Automated Wi-Fi Reconnaissance**
- ✅ **WPA2/WPA3 Handshake Capture & Cracking (PMKID + 4-Way)**
- ✅ **Evil Twin AP Emulation**
- ✅ **Captive Portal Hijacking with Credential Logging**
- ✅ **KRACK Vulnerability Simulation**
- ✅ **Deauthentication & Rogue AP Detection**
- ✅ **DNS Spoofing with Phishing Pages**
- ✅ **JavaScript Injection Attacks (e.g., Browser Update, Keylogger)**
- ✅ **Network Segmentation Mapping**
- ✅ **Encrypted and Timestamped HTML Reporting**
- ✅ **Headless Mode Support (Raspberry Pi Ready)**
- ✅ **Auto-Connect to Cracked Wi-Fi**
- ✅ **Modular Plugin System**
- ✅ **One-Click `.deb` Installer (Linux)**

---

## 📦 Project Structure

wifi-fortress/
├── plugins/ # Plugin-based attack modules
├── core/ # Core logic and attack orchestration
├── logger/ # Encrypted and timestamped logging system
├── ui/ # GUI components (if applicable)
├── reports/ # HTML/PDF reports generated after attacks
├── config/ # Hostapd, dnsmasq, Bettercap, caplets, etc.
├── utils/ # Helper scripts (wifi scan, interface mgmt)
├── docs/ # User and Admin manuals
├── install/ # Installers (.deb, .zip), setup scripts
├── main.py # Entry point for full automation
└── README.md # You're reading it now


---

## 🚀 Usage

### Option 1: Full Auto Mode (Raspberry Pi / Headless)

```bash
sudo ./main.py --auto
Runs the full attack chain:

Wi-Fi scanning

Handshake capture

Cracking

MITM phishing

Report generation

Option 2: Selective Manual Modules

sudo ./main.py --module evil_twin
sudo ./main.py --module krack
Run specific plugins for targeted assessments.

📄 Reports
Generated in reports/ as .html and optionally .pdf

Includes:

Captured handshakes

Cracked credentials

Device list

Phishing logs

Injected payload captures

Toolchain logs (Bettercap, Nmap, Wifite, etc.)

⚙️ Requirements
Python 3.7+

aircrack-ng, wifite, bettercap, dnsmasq, hostapd

metasploit-framework (optional)

pdfkit, jinja2, cryptography, netifaces, scapy, pywifi

Install dependencies (Linux):

sudo apt install aircrack-ng wifite bettercap dnsmasq hostapd metasploit-framework
pip3 install -r requirements.txt
📝 Notes for Users
🧠 Educational Use Only: This tool is for authorized security testing, red teaming, and research purposes.

🧪 Run as Root: Due to low-level network access, WiFi Fortress must be executed with root privileges.

🛰️ Wireless Interface Support: Ensure your Wi-Fi card supports monitor mode and packet injection.

🔐 Logs Are Encrypted: All credentials, traffic, and scan logs are stored encrypted in /logs/.

💾 Auto-Save Reports: Even on failure, a partial report is auto-generated and time-stamped.

🧱 Firewall Considerations: Local firewalls may block MITM or DNS spoofing modules.

🐍 Modular Design: You can create your own plugin by adding it to plugins/ and registering in main.py.

📥 Installation
Install via .deb Package (Recommended for Debian/Ubuntu/Kali)

sudo dpkg -i wifi-fortress_x.x_all.deb
Then enable auto-pentest service:

sudo systemctl enable wifi-fortress.service
sudo systemctl start wifi-fortress.service
📤 Output Example
Report Path: reports/report_<timestamp>.html


👤 Author
Abu Sharrukh Alam 


🛑 Disclaimer
This software is intended ONLY for authorized penetration testing and educational research.
Misuse of this tool in unauthorized networks is illegal and unethical.
The author is not responsible for any misuse or damage.
