# Growtopia Update Monitor

Growtopia Update Monitor is an **automatic update & data-mining tool** built with Python and Tkinter. It continues the **Bolwl Datamining Project**, providing an easy way to track and analyze Growtopia updates..  
It monitors Growtopia’s official files, app versions, and cache servers, then notifies you via **Discord bot or webhook** when new updates are detected.  

## ✨ Features
- **Update Monitoring**
  - Tracks Growtopia installer file sizes (Windows & macOS).
  - Checks Android version on Google Play Store.
  - Monitors Steam version via Steam API.
  - Sends detailed update notifications to Discord.

- **Auto Data Mining**
  - Downloads the latest macOS client when updates are detected.
  - Extracts the binary using **7zip**.
  - Parses the binary for new items.
  - Compares against the previous version to highlight new content.

- **Cache Checker**
  - Bruteforces Ubistatic CDN URLs to find hidden update files.
  - Supports Windows & macOS installers.
  - Generates multiple cache ID combinations automatically.

- **Discord Integration**
  - Works with both bot tokens and webhooks.
  - Supports channel notifications and direct user messages.
  - Sends alerts with update details, versions, and optional item lists.

## 📋 Requirements
- Python 3.9+
- 7zip installed (`7z.exe` must be accessible in PATH or configured in the app).
- Internet connection for monitoring.
- Discord bot token **or** webhook URL.

## 🚀 Installation
```bash
# 1. Clone the repository
git clone https://github.com/xSkriptx/Auto-Datamining-Growtopia.git
cd Auto-Datamining-Growtopia

# 2. Download packages
pip install -r requirements.txt
or
py -3.12 -m pip install -r requirements.txt

# 3. Run the script
python growtopia_monitor.py

