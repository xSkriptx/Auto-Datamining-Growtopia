import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
import os
import sys
import aiohttp
import asyncio
import ssl
import discord
import subprocess
from google_play_scraper import app
import requests
from tqdm import tqdm
import time
import re
import webbrowser
from PIL import Image, ImageTk

class CacheChecker:
    def __init__(self, log_callback=None, notify_callback=None):
        self.log_callback = log_callback
        self.notify_callback = notify_callback
        self.running = False
        
    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)
            
    def notify(self, message):
        if self.notify_callback:
            self.notify_callback(message)
            
    def generate_cache_ids(self, day, month, year):
        dd = f"{int(day):02d}"  # Day is always two digits
        mm = f"{int(month):02d}"  # Month is always two digits
        yyyy = str(year)  # Full year
        yy = str(year)[-2:]  
        d = f"{int(day)}"
        m = f"{int(month)}"
        cache_ids = []

        # Basic combinations
        cache_ids.append(f"0{dd}{mm}{yyyy}0")
        cache_ids.append(f"{dd}{mm}{yyyy}0")
        cache_ids.append(f"{dd}{mm}{yyyy}")
        cache_ids.append(f"{dd}{mm}{yyyy}00")
        cache_ids.append(f"0{mm}{dd}{yyyy}0")
        cache_ids.append(f"0{mm}{dd}{yyyy}00")
        cache_ids.append(f"0{yyyy}{mm}{dd}0")
        cache_ids.append(f"{yyyy}{dd}{mm}")
        cache_ids.append(f"0{dd}{mm}{yy}00")
        cache_ids.append(f"0{mm}{dd}{yy}00")
        cache_ids.append(f"0{mm}{dd}{yyyy}00")
        cache_ids.append(f"{d}{m}{yyyy}nn")

        # Combinations with and without 'z'
        for z in range(0, 10):
            cache_ids.append(f"0{dd}{mm}{yy}00{z}")
            cache_ids.append(f"0{mm}{dd}{yy}00{z}")
            cache_ids.append(f"0{mm}{dd}{yyyy}0{z}")
            cache_ids.append(f"0{mm}{dd}{yyyy}00{z}")
            cache_ids.append(f"00{mm}{dd}{yy}20{z}")
            cache_ids.append(f"00{mm}{dd}{yy}200{z}")
            cache_ids.append(f"0{dd}{mm}{yyyy}00")
            cache_ids.append(f"{dd}{mm}{yy}00{z}")
            cache_ids.append(f"0{dd}{mm}{yyyy}00{z}")
            cache_ids.append(f"{dd}{mm}{yyyy}00{z}")
            cache_ids.append(f"0{dd}{mm}{yyyy}0{z}")
            cache_ids.append(f"{dd}{mm}{yyyy}0{z}")
            cache_ids.append(f"0{yyyy}{mm}{dd}00{z}")

        # More combinations with YYYY and DDMM
        for z in range(0, 10):
            cache_ids.append(f"{dd}{mm}{yyyy}0{z}")
            cache_ids.append(f"0{yyyy}{mm}{dd}{z}")
            cache_ids.append(f"{mm}{dd}{yyyy}{z}")
            cache_ids.append(f"0{yyyy}{dd}{mm}0{z}")
            cache_ids.append(f"{yyyy}{mm}{dd}0{z}")
            cache_ids.append(f"0{yyyy}{mm}{dd}00{z}")
            cache_ids.append(f"0{z}{dd}{mm}{yyyy}0")
            cache_ids.append(f"0{z}{yyyy}{mm}{dd}00")
            cache_ids.append(f"0{z}{yyyy}{mm}{dd}")
            cache_ids.append(f"0{z}{yyyy}{dd}{mm}0")
            cache_ids.append(f"0{z}{mm}{dd}{yyyy}")
            cache_ids.append(f"0{z}{yyyy}{mm}{dd}")

        # More combinations with YY and YYYY
        for z in range(1, 10):
            cache_ids.append(f"{mm}{dd}{yy}{z}")
            cache_ids.append(f"{mm}{dd}{yyyy}{z}")
            cache_ids.append(f"0{dd}{yyyy}{mm}{z}")
            cache_ids.append(f"{mm}{yyyy}{dd}0{z}")
            cache_ids.append(f"{yyyy}{mm}{dd}{z}")
            cache_ids.append(f"{yyyy}{mm}{dd}0{z}")

        # Double digit suffixes (xx at the end)
        for x in range(0, 10):
            cache_ids.append(f"{dd}{mm}{yyyy}{x}{x}")

        # Different combinations
        for z in range(0, 10):
            cache_ids.append(f"{mm}{yyyy}{dd}{z}")
            cache_ids.append(f"{dd}{yyyy}{mm}0{z}")
            cache_ids.append(f"0{yyyy}{dd}{mm}00{z}")
            cache_ids.append(f"{yyyy}{dd}{mm}{z}")
        
        # Extra zero combinations
        for z in range(0, 10):
            cache_ids.append(f"{dd}{mm}{yy}0{z}")
            cache_ids.append(f"0{mm}{dd}{yyyy}0{z}")
            cache_ids.append(f"0{dd}{mm}{yyyy}{z}")
            cache_ids.append(f"0{dd}{mm}{yy}{z}")
            cache_ids.append(f"0{mm}{dd}{yy}{z}")
            cache_ids.append(f"0{yyyy}{mm}{dd}0{z}")
            cache_ids.append(f"{mm}{dd}{yyyy}{z}")
            cache_ids.append(f"{yyyy}{mm}{dd}{z}")
            cache_ids.append(f"0{mm}{dd}{yy}00{z}")

        # Final zero/z combinations
        for z in range(0, 10):
            cache_ids.append(f"00{dd}{mm}{yyyy}{z}")
            cache_ids.append(f"{mm}{dd}{yyyy}{x}{z}")
            cache_ids.append(f"0{yyyy}{mm}{dd}0{z}")

        return cache_ids
    
    async def check_url(self, session, url):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as response:
                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/' in content_type or 'executable' in content_type:
                        return url
        except:
            pass
        return None

    async def check_ubistatic_urls(self, month, year):
        base_urls = [
            "https://ubistatic-a.akamaihd.net/0098/{cache_id}/GrowtopiaInstaller.exe",
            "https://ubistatic-a.akamaihd.net/0098/{cache_id}/Growtopia.dmg"
        ]
        
        found_urls = set()

        async with aiohttp.ClientSession() as session:
            while self.running:
                for day in range(1, 32): 
                    self.log(f"Checking URLs for day {day}/{month}/{year}")
                    cache_ids = self.generate_cache_ids(day, month, year)
                    
                    tasks = []
                    for base_url in base_urls:
                        for cache_id in cache_ids:
                            url = base_url.format(cache_id=cache_id)
                            tasks.append(self.check_url(session, url))
                    
                    # Process in chunks to avoid memory issues
                    chunk_size = 50
                    for i in range(0, len(tasks), chunk_size):
                        if not self.running:
                            break
                            
                        chunk = tasks[i:i + chunk_size]
                        results = await asyncio.gather(*chunk, return_exceptions=True)
                        
                        for url in results:
                            if url and url not in found_urls:
                                found_urls.add(url)
                                self.log(f"Found valid URL: {url}")
                                self.notify(f"🚀 New Ubistatic URL Found:\n{url}")
                    if not self.running:
                        break
                    await asyncio.sleep(1) 
                
                if not self.running:
                    break
                self.log("Restarting URL scan...")
                await asyncio.sleep(60)  # Wait 1 minute before rescanning DO NOT PLAY WITH IT OR IT WILL SKIP URLs!!!!!

    def start(self, month, year):
        self.running = True
        asyncio.run(self.check_ubistatic_urls(month, year))
        
    def stop(self):
        self.running = False

class GrowtopiaMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Growtopia Update Monitor")
        self.root.geometry("900x800")
        self.root.resizable(True, True)
        
        # Try to set the icon
        try:
            # Try to load from file first
            if os.path.exists("favicon.ico"):
                self.root.iconbitmap("favicon.ico")
            else:
                # Try to load from embedded resource (for PyInstaller)
                base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
                icon_path = os.path.join(base_path, "favicon.ico")
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Could not load icon: {e}")
        
        # Configuration variables
        self.config = {
            "discord_token": "",
            "webhook_url": "",
            "windows_size": 0,
            "macos_size": 0,
            "android_version": "",
            "steam_version": "",
            "channel_ids": [],
            "user_ids": [],
            "use_webhook": False,
            "previous_version": "5.23"
        }
        
        # Initialize monitoring variables
        self.monitoring = False
        self.monitor_thread = None
        self.dm_thread = None
        self.cache_checker = None
        self.cache_checking = False
        
        # Load config if exists
        self.load_config()
        
        # Create tabs
        self.tab_control = ttk.Notebook(root)
        
        # Configuration tab
        self.config_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.config_tab, text='Configuration')
        
        # Log tab
        self.log_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.log_tab, text='Logs')
        
        # Data Mining tab
        self.dm_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.dm_tab, text='Data Mining')
        
        # Cache Checker tab
        self.cache_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.cache_tab, text='Cache Checker')
        
        # Information tab
        self.info_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.info_tab, text='Information')
        
        self.tab_control.pack(expand=1, fill='both')
        
        # Setup configuration tab
        self.setup_config_tab()
        
        # Setup log tab
        self.setup_log_tab()
        
        # Setup data mining tab
        self.setup_dm_tab()
        
        # Setup cache checker tab
        self.setup_cache_tab()
        
        # Setup information tab
        self.setup_info_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Created by Skript")
        self.status_bar = tk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def setup_config_tab(self):
        # Discord configuration
        discord_frame = ttk.LabelFrame(self.config_tab, text="Discord Configuration", padding=10)
        discord_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(discord_frame, text="Bot Token:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.token_entry = ttk.Entry(discord_frame, width=50)
        self.token_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        self.token_entry.insert(0, self.config["discord_token"])
        
        ttk.Label(discord_frame, text="Webhook URL:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.webhook_entry = ttk.Entry(discord_frame, width=50)
        self.webhook_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        self.webhook_entry.insert(0, self.config["webhook_url"])
        
        ttk.Label(discord_frame, text="Channel IDs (comma separated):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.channel_entry = ttk.Entry(discord_frame, width=50)
        self.channel_entry.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)
        self.channel_entry.insert(0, ",".join(map(str, self.config["channel_ids"])))
        
        ttk.Label(discord_frame, text="User IDs (comma separated):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.user_entry = ttk.Entry(discord_frame, width=50)
        self.user_entry.grid(row=3, column=1, padx=5, pady=2, sticky=tk.W)
        self.user_entry.insert(0, ",".join(map(str, self.config["user_ids"])))
        
        self.use_webhook_var = tk.BooleanVar(value=self.config["use_webhook"])
        ttk.Checkbutton(discord_frame, text="Use Webhook Instead of Bot", variable=self.use_webhook_var).grid(row=4, column=1, sticky=tk.W, pady=2)
        
        # Message configuration
        ttk.Label(discord_frame, text="Notification Message:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.message_entry = ttk.Entry(discord_frame, width=50)
        self.message_entry.grid(row=5, column=1, padx=5, pady=2, sticky=tk.W)
        self.message_entry.insert(0, "@everyone 🚀 New update detected!")
        
        # File size configuration
        size_frame = ttk.LabelFrame(self.config_tab, text="File Size Configuration", padding=10)
        size_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(size_frame, text="Windows Size (bytes):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.windows_entry = ttk.Entry(size_frame, width=30)
        self.windows_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        self.windows_entry.insert(0, str(self.config["windows_size"]))
        
        ttk.Label(size_frame, text="macOS Size (bytes):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.macos_entry = ttk.Entry(size_frame, width=30)
        self.macos_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        self.macos_entry.insert(0, str(self.config["macos_size"]))
        
        ttk.Label(size_frame, text="Android Version:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.android_entry = ttk.Entry(size_frame, width=30)
        self.android_entry.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)
        self.android_entry.insert(0, self.config["android_version"])
        
        ttk.Label(size_frame, text="Steam Version:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.steam_entry = ttk.Entry(size_frame, width=30)
        self.steam_entry.grid(row=3, column=1, padx=5, pady=2, sticky=tk.W)
        self.steam_entry.insert(0, self.config.get("steam_version", ""))
        
        ttk.Label(size_frame, text="Previous Version:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.prev_version_entry = ttk.Entry(size_frame, width=30)
        self.prev_version_entry.grid(row=4, column=1, padx=5, pady=2, sticky=tk.W)
        self.prev_version_entry.insert(0, self.config["previous_version"])
        
        # Buttons
        button_frame = ttk.Frame(self.config_tab)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start Monitoring", command=self.start_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop Monitoring", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.save_button = ttk.Button(button_frame, text="Save Configuration", command=self.save_config)
        self.save_button.pack(side=tk.RIGHT, padx=5)
        
    def setup_log_tab(self):
        self.log_text = scrolledtext.ScrolledText(self.log_tab, width=80, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_text.config(state=tk.DISABLED)
        
    def setup_dm_tab(self):
        dm_frame = ttk.LabelFrame(self.dm_tab, text="Data Mining Options", padding=10)
        dm_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(dm_frame, text="7z.exe Path:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.sevenzip_entry = ttk.Entry(dm_frame, width=50)
        self.sevenzip_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        self.sevenzip_entry.insert(0, "7z.exe")
        
        ttk.Label(dm_frame, text="Previous Version File:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.prev_file_entry = ttk.Entry(dm_frame, width=50)
        self.prev_file_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        self.prev_file_entry.insert(0, f"bol_V{self.config['previous_version']}.txt")
        
        # Buttons
        button_frame = ttk.Frame(dm_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.dm_button = ttk.Button(button_frame, text="Run Data Mining", command=self.run_data_mining)
        self.dm_button.pack(side=tk.LEFT, padx=5)
        
    def setup_cache_tab(self):
        cache_frame = ttk.LabelFrame(self.cache_tab, text="Cache Checker Options", padding=10)
        cache_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(cache_frame, text="Current Month:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.month_entry = ttk.Entry(cache_frame, width=10)
        self.month_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        self.month_entry.insert(0, "4")
        
        ttk.Label(cache_frame, text="Current Year:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.year_entry = ttk.Entry(cache_frame, width=10)
        self.year_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        self.year_entry.insert(0, "2025")
        
        # Buttons
        button_frame = ttk.Frame(cache_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.cache_start_button = ttk.Button(button_frame, text="Start Cache Checker", command=self.start_cache_checker)
        self.cache_start_button.pack(side=tk.LEFT, padx=5)
        
        self.cache_stop_button = ttk.Button(button_frame, text="Stop Cache Checker", command=self.stop_cache_checker, state=tk.DISABLED)
        self.cache_stop_button.pack(side=tk.LEFT, padx=5)
        
    def setup_info_tab(self):
        info_frame = ttk.LabelFrame(self.info_tab, text="About Growtopia Update Monitor", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a scrollable text widget for information
        info_text = scrolledtext.ScrolledText(info_frame, width=80, height=20, wrap=tk.WORD)
        info_text.pack(fill=tk.BOTH, expand=True)
        
        # Information content
        info_content = """
Growtopia Update Monitor - Created by Skript

HOW IT WORKS:

1. MONITORING:
   - Continuously checks Growtopia file sizes (Windows & macOS)
   - Monitors Android version on Google Play Store
   - Checks Steam version through Steam API
   - Sends notifications when changes are detected

2. AUTO-DATA MINING:
   - Activated automatically when macOS file size changes
   - Downloads the latest Growtopia .dmg file
   - Extracts the binary using 7zip
   - Parses the binary to find new items
   - Compares with previous version data
   - Sends notification with new items found

3. CACHE CHECKER:
   - Bruteforces Ubistatic URLs to find new cache versions
   - Uses date-based pattern generation
   - Checks both Windows and macOS installer URLs
   - Notifies when valid URLs are found

4. NOTIFICATIONS:
   - Supports both Discord bot and webhook notifications
   - Sends to specified channels and users
   - Includes detailed update information

REQUIREMENTS:
- 7zip installed and accessible for data mining
- Discord bot token or webhook URL for notifications
- Internet connection for monitoring

LINKS:
GitHub: https://github.com/xSkriptx/Growtools
YouTube: https://www.youtube.com/channel/UCvoRNyYeWnmb1TojljTkdbA
Discord: https://discord.com/invite/HSdayEQKwe

For support, join our Discord community!
"""
        
        info_text.insert(tk.INSERT, info_content)
        info_text.config(state=tk.DISABLED)  # Make it read-only
        
        # Add link buttons
        link_frame = ttk.Frame(info_frame)
        link_frame.pack(fill=tk.X, pady=5)
        
        github_btn = ttk.Button(link_frame, text="GitHub", command=lambda: webbrowser.open("https://github.com/xSkriptx/Growtools"))
        github_btn.pack(side=tk.LEFT, padx=5)
        
        youtube_btn = ttk.Button(link_frame, text="YouTube", command=lambda: webbrowser.open("https://www.youtube.com/channel/UCvoRNyYeWnmb1TojljTkdbA"))
        youtube_btn.pack(side=tk.LEFT, padx=5)
        
        discord_btn = ttk.Button(link_frame, text="Discord", command=lambda: webbrowser.open("https://discord.com/invite/HSdayEQKwe"))
        discord_btn.pack(side=tk.LEFT, padx=5)
        
    def log_message(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.status_var.set(f"{message} - Created by Skript")
        
    def load_config(self):
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    self.config = json.load(f)
        except Exception as e:
            self.log_message(f"Failed to load config: {str(e)}")
            
    def save_config(self):
        try:
            # Update config from UI
            self.config["discord_token"] = self.token_entry.get()
            self.config["webhook_url"] = self.webhook_entry.get()
            
            # Parse channel IDs
            channel_text = self.channel_entry.get()
            if channel_text:
                self.config["channel_ids"] = [int(x.strip()) for x in channel_text.split(",") if x.strip()]
            else:
                self.config["channel_ids"] = []
                
            # Parse user IDs
            user_text = self.user_entry.get()
            if user_text:
                self.config["user_ids"] = [int(x.strip()) for x in user_text.split(",") if x.strip()]
            else:
                self.config["user_ids"] = []
                
            self.config["windows_size"] = int(self.windows_entry.get() or 0)
            self.config["macos_size"] = int(self.macos_entry.get() or 0)
            self.config["android_version"] = self.android_entry.get()
            self.config["steam_version"] = self.steam_entry.get()
            self.config["previous_version"] = self.prev_version_entry.get()
            self.config["use_webhook"] = self.use_webhook_var.get()
            
            # Save to file
            with open("config.json", "w") as f:
                json.dump(self.config, f, indent=4)
                
            self.log_message("Configuration saved successfully")
            messagebox.showinfo("Success", "Configuration saved successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {str(e)}")
            
    def start_monitoring(self):
        if self.monitoring:
            return
            
        # Validate configuration
        if not self.use_webhook_var.get() and not self.token_entry.get():
            messagebox.showerror("Error", "Please enter a Discord bot token or enable webhook mode")
            return
            
        if self.use_webhook_var.get() and not self.webhook_entry.get():
            messagebox.showerror("Error", "Please enter a webhook URL")
            return
            
        self.monitoring = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Start monitoring in a separate thread
        self.monitor_thread = threading.Thread(target=self.run_monitor)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.log_message("Monitoring started")
        
    def stop_monitoring(self):
        self.monitoring = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log_message("Monitoring stopped")
        
    def run_monitor(self):
        # This method runs in a separate thread
        asyncio.run(self.monitor_loop())
        
    async def monitor_loop(self):
        urls = {
            "Windows": "https://growtopiagame.com/Growtopia-Installer.exe",
            "macOS": "https://growtopiagame.com/Growtopia-mac.dmg"
        }

        previous_sizes = {
            "Windows": self.config["windows_size"],
            "macOS": self.config["macos_size"]
        }
        
        previous_android_version = self.config["android_version"]
        previous_steam_version = self.config.get("steam_version", "")

        while self.monitoring:
            changes = {}
            tasks = []
            platforms_updated = []
            
            for platform, url in urls.items():
                tasks.append(self.check_file_size(url, previous_sizes[platform]))
                
            sizes = await asyncio.gather(*tasks)

            # Compare sizes
            for i, platform in enumerate(urls.keys()):
                if sizes[i] is not None:
                    changes[urls[platform]] = sizes[i]
                    previous_sizes[platform] = sizes[i]
                    self.log_message(f"{urls[platform]} size changed: {sizes[i]} bytes")
                    platforms_updated.append(platform)
                else:
                    self.log_message(f"{urls[platform]} size is the same: {previous_sizes[platform]} bytes")

            # Android version check
            android_version, playstore_url = await self.get_android_version()
            if android_version:
                self.log_message(f"Android version: {android_version}, Play Store URL: {playstore_url}")
                if android_version != previous_android_version:
                    changes[playstore_url] = android_version
                    previous_android_version = android_version
                    platforms_updated.append("Android")
                    self.log_message(f"Android version updated to: {android_version}")
                else:
                    self.log_message(f"Android version has not changed: {android_version}")

            # Steam version check
            steam_version, steam_url = await self.get_steam_version()
            if steam_version:
                self.log_message(f"Steam version: {steam_version}, Steam URL: {steam_url}")
                if steam_version != previous_steam_version:
                    changes[steam_url] = steam_version
                    previous_steam_version = steam_version
                    platforms_updated.append("Steam")
                    self.log_message(f"Steam version updated to: {steam_version}")
                else:
                    self.log_message(f"Steam version has not changed: {steam_version}")

            # Notify if anything changed
            if changes:
                await self.log_size_change(changes, platforms_updated)

                # Run data mining if macOS file changed
                if "macOS" in platforms_updated:
                    self.log_message("macOS file changed, running data mining...")
                    self.run_data_mining()
                    
            # Update the UI with current values
            self.windows_entry.delete(0, tk.END)
            self.windows_entry.insert(0, str(previous_sizes["Windows"]))
            
            self.macos_entry.delete(0, tk.END)
            self.macos_entry.insert(0, str(previous_sizes["macOS"]))
            
            self.android_entry.delete(0, tk.END)
            self.android_entry.insert(0, previous_android_version)
            
            self.steam_entry.delete(0, tk.END)
            self.steam_entry.insert(0, previous_steam_version)
            
            # Save the updated config
            self.config["windows_size"] = previous_sizes["Windows"]
            self.config["macos_size"] = previous_sizes["macOS"]
            self.config["android_version"] = previous_android_version
            self.config["steam_version"] = previous_steam_version
            with open("config.json", "w") as f:
                json.dump(self.config, f, indent=4)

            # Wait for next check
            for i in range(60):
                if not self.monitoring:
                    break
                await asyncio.sleep(1)
                
    async def check_file_size(self, url, previous_size):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, ssl=ssl_context) as response:
                    if response.status == 200:
                        file_size = response.headers.get('Content-Length', 'Unknown')
                        if file_size != 'Unknown':
                            file_size = int(file_size)
                            return file_size if file_size != previous_size else None
                    else:
                        self.log_message(f"Invalid URL: {url} (Status Code: {response.status})")
            except Exception as e:
                self.log_message(f"Error: {e} (URL: {url})")
            return None
            
    async def get_android_version(self):
        try:
            result = app('com.rtsoft.growtopia')
            return result['version'], result['url']
        except Exception as e:
            self.log_message(f"Error fetching Android version: {e}")
            return None, None
            
    async def get_steam_version(self):
        try:
            app_id = 866020
            steamdb_url = f"https://api.steamcmd.net/v1/info/{app_id}"
            response = requests.get(steamdb_url)
            data = response.json()
            
            if data and 'data' in data and str(app_id) in data['data']:
                buildid = data['data'][str(app_id)]['depots']['branches']['public']['buildid']
                return buildid, f"https://store.steampowered.com/app/{app_id}/Growtopia/"
            
            official_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
            response = requests.get(official_url)
            if response.status_code == 200:
                data = response.json()
                if data and str(app_id) in data and 'data' in data[str(app_id)]:
                    version = data[str(app_id)]['data'].get('depots', {}).get('branches', {}).get('public', {}).get('buildid')
                    if version:
                        return version, f"https://store.steampowered.com/app/{app_id}/Growtopia/"
            
            return None, None
        except Exception as e:
            self.log_message(f"Error fetching Steam version: {e}")
            return None, None
            
    async def log_size_change(self, changes, platforms_updated):
        log_message = "Updates detected:\n"
        for url, change in changes.items():
            if isinstance(change, int):  # Check if change is an integer (file size)
                log_message += f"{url} size changed! (New Size: {change} bytes ({change / (1024 * 1024):.2f} MB))\n"
            else:  # Handle version info
                log_message += f"{url} version updated to {change}.\n"

        # Write to Size.txt file on Desktop (UTF-8)
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "Size.txt")
        with open(desktop_path, "a", encoding='utf-8') as log_file:
            log_file.write(log_message)

        # Send notification
        if self.config["use_webhook"]:
            await self.send_webhook_notification(log_message, platforms_updated)
        else:
            await self.send_discord_notification(log_message, platforms_updated)
            
    async def send_discord_notification(self, message, platforms_updated):
        if not self.config["discord_token"]:
            return
            
        intents = discord.Intents.default()
        client = discord.Client(intents=intents)
        
        @client.event
        async def on_ready():
            try:
                # Send to channels
                for channel_id in self.config["channel_ids"]:
                    channel = client.get_channel(channel_id)
                    if channel:
                        notification_msg = self.message_entry.get() or "@everyone 🚀 New update detected!"
                        if platforms_updated:
                            platform_strings = [f"{platform}" for platform in platforms_updated]
                            notification_msg = f"{notification_msg}\nPlatforms updated: {', '.join(platform_strings)}"
                        await channel.send(notification_msg)
                        await channel.send(message)
                
                # Send to users
                for user_id in self.config["user_ids"]:
                    user = await client.fetch_user(user_id)
                    if user:
                        await user.send(message)
            except Exception as e:
                self.log_message(f"Error sending Discord notification: {e}")
            finally:
                await client.close()
                
        try:
            await client.start(self.config["discord_token"])
        except Exception as e:
            self.log_message(f"Error starting Discord client: {e}")
        
    async def send_webhook_notification(self, message, platforms_updated):
        if not self.config["webhook_url"]:
            return
            
        try:
            # Prepare the message
            content = self.message_entry.get() or "@everyone 🚀 New update detected!"
            if platforms_updated:
                platform_strings = [f"{platform}" for platform in platforms_updated]
                content = f"{content}\nPlatforms updated: {', '.join(platform_strings)}"
            
            data = {
                "content": content,
                "username": "Growtopia Update Monitor",
                "embeds": [{
                    "title": "Update Details",
                    "description": message,
                    "color": 0x00ff00
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.config["webhook_url"], json=data) as response:
                    if response.status != 204:
                        self.log_message(f"Webhook error: {response.status}")
        except Exception as e:
            self.log_message(f"Error sending webhook: {e}")
            
    def start_cache_checker(self):
        if self.cache_checking:
            return
            
        try:
            month = int(self.month_entry.get())
            year = int(self.year_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid month and year numbers")
            return
            
        self.cache_checking = True
        self.cache_start_button.config(state=tk.DISABLED)
        self.cache_stop_button.config(state=tk.NORMAL)
        
        # Initialize cache checker
        self.cache_checker = CacheChecker(
            log_callback=self.log_message,
            notify_callback=lambda msg: asyncio.run(self.send_notification(msg))
        )
        
        # Start cache checker in a separate thread
        cache_thread = threading.Thread(target=lambda: self.cache_checker.start(month, year))
        cache_thread.daemon = True
        cache_thread.start()
        
        self.log_message(f"Cache checker started for month {month}, year {year}")
        
    def stop_cache_checker(self):
        if self.cache_checker:
            self.cache_checker.stop()
            self.cache_checker = None
            
        self.cache_checking = False
        self.cache_start_button.config(state=tk.NORMAL)
        self.cache_stop_button.config(state=tk.DISABLED)
        self.log_message("Cache checker stopped")
        
    async def send_notification(self, message):
        if self.config["use_webhook"]:
            await self.send_webhook_notification(message, [])
        else:
            await self.send_discord_notification(message, [])
        
    def run_data_mining(self):
        if self.dm_thread and self.dm_thread.is_alive():
            self.log_message("Data mining already in progress")
            return
            
        self.dm_thread = threading.Thread(target=self.data_mining_loop)
        self.dm_thread.daemon = True
        self.dm_thread.start()
        
    def data_mining_loop(self):
        asyncio.run(self.run_data_mining_async())
        
    async def run_data_mining_async(self):
        self.log_message("Starting data mining process...")
        
        try:
            # Download the latest Growtopia .dmg file
            await self.download_latest_growtopia()
            
            # Extract Growtopia binary
            await self.extract_growtopia_binary()
            
            # Load previous version data
            vold = self.config["previous_version"]
            old_items = self.load_previous_version_data(vold)
            
            if old_items is None:
                self.log_message("Previous version data not found!")
                await self.send_notification("Previous version data not found! Exiting...")
                return
            
            # Read and process the binary file
            with open("Growtopia", "rb") as file:
                binary_data = file.read().decode("latin-1")

            items = self.extract_items(binary_data)
            version = self.extract_version(binary_data)

            # Save new version data
            self.save_new_version_data(version, items)
            
            # Save and send new items
            new_items = await self.save_new_items_to_file(items, old_items, version)
            
            if new_items:
                self.log_message(f"Data mining completed successfully. Found {len(new_items)} new items:")
                for item in new_items:
                    self.log_message(f"  - {item}")
            else:
                self.log_message("Data mining completed successfully. No new items found.")
            
        except Exception as e:
            error_msg = f"Error in data mining: {str(e)}"
            self.log_message(error_msg)
            await self.send_notification(error_msg)
                
    async def download_latest_growtopia(self):
        """Download the latest Growtopia .dmg file for data mining."""
        url = "https://growtopiagame.com/Growtopia-mac.dmg"

        self.log_message("Attempting to download the latest Growtopia file...")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Failed to download the Growtopia file: {e}")

        total_size = int(response.headers.get('content-length', 0))
        self.log_message("Downloading Latest Growtopia for data mining...")

        with open("Growtopia.dmg", 'wb') as file, tqdm(
            total=total_size, unit='B', unit_scale=True, desc="Growtopia", ncols=80
        ) as progress_bar:
            for data in response.iter_content(1024):
                file.write(data)
                progress_bar.update(len(data))

        self.log_message("Download Completed! The file is saved as Growtopia.dmg.")
        return total_size
        
    async def extract_growtopia_binary(self):
        """Extract Growtopia binary using 7zip."""
        self.log_message("Extracting Growtopia binary...")
        sevenzip_path = self.sevenzip_entry.get()
        result = os.system(f'"{sevenzip_path}" e Growtopia.dmg Growtopia.app/Contents/MacOS/Growtopia -aoa')
        if result != 0:
            raise Exception("Failed to extract the Growtopia binary.")
        self.log_message("Extraction completed successfully.")
            
    def load_previous_version_data(self, version):
        """Load item data from the previous version file."""
        file_path = self.prev_file_entry.get() or f"bol_V{version}.txt"
        self.log_message(f"Looking for file: {file_path}")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read().splitlines()
        self.log_message("File not found!")
        return None
        
    def remove_non_ascii(self, text):
        """Remove non-ASCII characters from the text."""
        return ''.join([s for s in text if 31 < ord(s) < 127])
        
    def extract_items(self, data):
        """Extract and clean item data from the binary."""
        items = []
        for line in data.split("\n"):
            line = line.replace("ITEM_ID_", "splitherelolITEM_ID_")
            for part in line.split("splitherelol"):
                if "ITEM_ID_" in part:
                    if len(part) > 500:
                        part = part.split("solid")[0]
                    items.append(self.remove_non_ascii(part[:-1]))  # Remove last character
        if items:
            items[-1] = items[-1][:items[-1].find("ALIGNMENT")]
        return items
        
    def extract_version(self, data):
        """Extract version information from the binary."""
        version_start = data.find("www.growtopia1.com") + 18
        version_info = data[version_start:data.find("Growtopia", version_start)]
        return self.remove_non_ascii(version_info)
        
    def save_new_version_data(self, version, items):
        """Save new version item data to a file."""
        with open(f"bol_{version}.txt", "w", encoding="utf-8") as file:
            file.write("\n".join(items))
        self.log_message(f"Saved new version data to bol_{version}.txt")
        
    async def save_new_items_to_file(self, items, old_items, version):
        """Save newly added item names to a text file and send it to the channels."""
        new_items = [item.replace("ITEM_ID_", "").replace("_", " ").title() for item in items if item not in old_items]
        if new_items:
            file_path = f"new_items_v{version}.txt"
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("\n".join(new_items))
            
            message = "New items found in the latest version:"
            
            if not self.config["use_webhook"]:
                # Send via Discord bot
                intents = discord.Intents.default()
                client = discord.Client(intents=intents)
                
                @client.event
                async def on_ready():
                    try:
                        for channel_id in self.config["channel_ids"]:
                            channel = client.get_channel(channel_id)
                            if channel:
                                with open(file_path, "rb") as f:
                                    await channel.send(message, file=discord.File(f, os.path.basename(file_path)))
                    except Exception as e:
                        self.log_message(f"Error sending file via Discord: {e}")
                    finally:
                        await client.close()
                        
                await client.start(self.config["discord_token"])
            else:
                # Send via webhook (files can't be sent via webhook, so send list instead)
                items_list = "\n".join(new_items)
                await self.send_webhook_notification(f"{message}\n{items_list}", [])
                
            self.log_message("Sent new items notification.")
            return new_items
        else:
            message = "No new items found."
            await self.send_notification(message)
            self.log_message(message)
            return []

def main():
    root = tk.Tk()
    app = GrowtopiaMonitor(root)
    root.mainloop()

if __name__ == "__main__":
    main()