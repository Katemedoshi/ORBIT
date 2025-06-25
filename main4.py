import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, simpledialog, filedialog
from gpt4all import GPT4All
import pyttsx3
import datetime
import math
import threading
import webbrowser
import os
import json
import random
import subprocess
from plyer import notification
import requests
from PIL import Image, ImageTk

class ORBITAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("ORBIT Desktop Assistant v3.0")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)
        
        # Initialize components
        self.setup_ai()
        self.setup_voice()
        self.load_settings()
        
        # Task manager data
        self.tasks = self.load_tasks()
        
        # Setup GUI
        self.setup_gui()
        
        # Initial greeting
        self.greet_user()
        
        # Start background tasks
        self.start_background_tasks()
    
    def setup_ai(self):
        """Initialize the AI model with error handling"""
        try:
            self.ai_model = GPT4All("orca-mini-3b-gguf2-q4_0.gguf", device="cpu")
            self.ai_ready = True
        except Exception as e:
            messagebox.showerror("AI Error", f"Failed to load AI model: {str(e)}")
            self.ai_ready = False
    
    def setup_voice(self):
        """Initialize text-to-speech engine"""
        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty('voices')
            self.engine.setProperty('voice', voices[0].id)
            self.engine.setProperty('rate', 180)
            self.voice_enabled = True
        except:
            self.voice_enabled = False
    
    def load_settings(self):
        """Load user settings from file"""
        self.settings = {
            'theme': 'light',
            'voice': True,
            'notifications': True,
            'ai_enabled': True,
            'music_path': os.path.expanduser('~/Music')
        }
        try:
            with open('orbit_settings.json', 'r') as f:
                self.settings.update(json.load(f))
        except:
            pass
    
    def save_settings(self):
        """Save user settings to file"""
        with open('orbit_settings.json', 'w') as f:
            json.dump(self.settings, f)
    
    def load_tasks(self):
        """Load tasks from file"""
        try:
            with open('orbit_tasks.json', 'r') as f:
                return json.load(f)
        except:
            return []
    
    def save_tasks(self):
        """Save tasks to file"""
        with open('orbit_tasks.json', 'w') as f:
            json.dump(self.tasks, f)
    
    def setup_gui(self):
        """Setup the main GUI components"""
        self.setup_theme()
        self.setup_menu()
        self.setup_header()
        self.setup_content()
        self.setup_footer()
    
    def setup_theme(self):
        """Configure theme colors"""
        if self.settings['theme'] == 'dark':
            self.bg_color = '#2c3e50'
            self.fg_color = '#ecf0f1'
            self.accent_color = '#3498db'
            self.text_bg = '#34495e'
        else:
            self.bg_color = '#ecf0f1'
            self.fg_color = '#2c3e50'
            self.accent_color = '#2980b9'
            self.text_bg = '#ffffff'
        
        self.root.config(bg=self.bg_color)
    
    def setup_menu(self):
        """Create the menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="System Info", command=self.show_system_info)
        tools_menu.add_command(label="Word of the Day", command=self.word_of_the_day)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Change Theme", command=self.toggle_theme)
        settings_menu.add_command(label="Preferences", command=self.show_settings)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        
        self.root.config(menu=menubar)
    
    def setup_header(self):
        """Setup the header area"""
        self.header_frame = tk.Frame(self.root, bg=self.bg_color)
        self.header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Logo
        try:
            logo_img = Image.open("orbit_logo.png").resize((50, 50))
            self.logo = ImageTk.PhotoImage(logo_img)
            tk.Label(self.header_frame, image=self.logo, bg=self.bg_color).pack(side=tk.LEFT)
        except:
            pass
        
        # Title
        tk.Label(self.header_frame, 
                text="ORBIT Desktop Assistant", 
                font=('Helvetica', 18, 'bold'), 
                fg=self.accent_color, 
                bg=self.bg_color).pack(side=tk.LEFT, padx=10)
        
        # Status indicators
        self.status_frame = tk.Frame(self.header_frame, bg=self.bg_color)
        self.status_frame.pack(side=tk.RIGHT, padx=10)
        
        self.status_label = tk.Label(
            self.status_frame, 
            text="✓ Ready", 
            fg='#2ecc71', 
            bg=self.bg_color
        )
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.ai_status = tk.Label(
            self.status_frame, 
            text="AI: Online" if self.ai_ready else "AI: Offline", 
            fg='#2ecc71' if self.ai_ready else '#e74c3c', 
            bg=self.bg_color
        )
        self.ai_status.pack(side=tk.LEFT, padx=5)
    
    def setup_content(self):
        """Setup the main content area"""
        self.content_frame = tk.Frame(self.root, bg=self.bg_color)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Conversation area
        self.conversation = scrolledtext.ScrolledText(
            self.content_frame,
            wrap=tk.WORD,
            width=80,
            height=20,
            font=('Consolas', 11),
            bg=self.text_bg,
            fg=self.fg_color,
            insertbackground=self.fg_color
        )
        self.conversation.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.conversation.tag_config('user', foreground='#3498db')
        self.conversation.tag_config('orbit', foreground='#2c3e50')
        self.conversation.tag_config('system', foreground='#7f8c8d')
        
        # Input area
        self.input_frame = tk.Frame(self.content_frame, bg=self.bg_color)
        self.input_frame.pack(fill=tk.X, pady=5)
        
        self.user_input = tk.Entry(
            self.input_frame,
            font=('Helvetica', 12),
            width=70,
            bg=self.text_bg,
            fg=self.fg_color,
            insertbackground=self.fg_color
        )
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.user_input.bind('<Return>', self.process_input)
        self.user_input.focus_set()
        
        # Voice button
        self.voice_btn = tk.Button(
            self.input_frame,
            text="🎤",
            font=('Helvetica', 14),
            command=self.start_voice_input,
            bg=self.accent_color,
            fg=self.bg_color,
            relief=tk.FLAT
        )
        self.voice_btn.pack(side=tk.LEFT, padx=5)
    
    def setup_footer(self):
        """Setup the footer with quick actions"""
        self.footer_frame = tk.Frame(self.root, bg=self.bg_color)
        self.footer_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Quick actions
        actions = [
            ("🌐 Browser", self.open_browser),
            ("🎵 Music", self.play_music),
            ("📝 Tasks", self.show_task_manager),
            ("🧮 Calculator", self.show_calculator),
            ("📅 Calendar", self.show_calendar),
            ("🤖 Ask AI", self.ask_ai),
            ("⚙ Settings", self.show_settings)
        ]
        
        for text, cmd in actions:
            btn = tk.Button(
                self.footer_frame,
                text=text,
                command=cmd,
                bg=self.accent_color,
                fg=self.bg_color,
                relief=tk.FLAT,
                font=('Helvetica', 10)
            )
            btn.pack(side=tk.LEFT, padx=5, pady=5)
    
    def greet_user(self):
        """Display initial greeting"""
        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            greeting = "Good morning"
        elif 12 <= hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        
        self.add_message(f"ORBIT: {greeting}! I'm your desktop assistant ORBIT. How can I help you today?", 'orbit')
        
        if self.settings.get('word_of_day', True):
            self.word_of_the_day()
    
    def add_message(self, text, sender='system'):
        """Add a message to the conversation"""
        self.conversation.config(state=tk.NORMAL)
        self.conversation.insert(tk.END, f"{text}\n", sender)
        self.conversation.config(state=tk.DISABLED)
        self.conversation.see(tk.END)
        
        if sender == 'orbit' and self.voice_enabled and self.settings['voice']:
            self.speak(text.replace("ORBIT: ", ""))
    
    def speak(self, text):
        """Speak text using TTS"""
        def _speak():
            self.engine.say(text)
            self.engine.runAndWait()
        
        threading.Thread(target=_speak, daemon=True).start()
    
    def start_voice_input(self):
        """Start voice input in a separate thread"""
        threading.Thread(target=self.take_voice_command, daemon=True).start()
    
    def take_voice_command(self):
        """Capture voice command using microphone"""
        self.status_label.config(text="🎤 Listening...", fg='#f39c12')
        self.voice_btn.config(state=tk.DISABLED)
        
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.Microphone() as source:
                audio = r.listen(source, timeout=5)
            
            try:
                query = r.recognize_google(audio)
                self.user_input.delete(0, tk.END)
                self.user_input.insert(0, query)
                self.process_input()
            except sr.UnknownValueError:
                self.add_message("ORBIT: Sorry, I didn't catch that", 'orbit')
            except sr.RequestError:
                self.add_message("ORBIT: Speech service unavailable", 'orbit')
        
        except ImportError:
            self.add_message("ORBIT: Speech recognition not available", 'orbit')
        except Exception as e:
            self.add_message(f"ORBIT: Voice error: {str(e)}", 'orbit')
        
        self.status_label.config(text="✓ Ready", fg='#2ecc71')
        self.voice_btn.config(state=tk.NORMAL)
    
    def process_input(self, event=None):
        """Process user input"""
        query = self.user_input.get().strip()
        if not query:
            return
        
        self.add_message(f"You: {query}", 'user')
        self.user_input.delete(0, tk.END)
        
        # Process commands
        if query.lower().startswith(('calculate', 'what is', 'math', 'solve')):
            self.calculate(query)
        elif query.lower().startswith(('add task', 'new task')):
            self.add_task(query)
        elif query.lower().startswith(('open ', 'launch ')):
            self.open_application(query)
        elif query.lower().startswith(('search ', 'look up ')):
            self.search_web(query)
        elif 'time' in query.lower():
            self.get_time()
        elif 'date' in query.lower():
            self.get_date()
        elif any(cmd in query.lower() for cmd in ['remind me', 'set reminder']):
            self.set_reminder(query)
        elif self.ai_ready:
            self.ask_ai(query)
        else:
            self.add_message("ORBIT: I'm not sure how to help with that", 'orbit')
    
    def calculate(self, query):
        """Perform calculations"""
        try:
            # Extract math expression
            expr = query.lower().replace('calculate', '').replace('what is', '').replace('math', '').strip()
            if not expr:
                self.add_message("ORBIT: Please provide a calculation", 'orbit')
                return
            
            # Safety check - only allow certain characters
            allowed_chars = set('0123456789+-*/.() ')
            if not all(c in allowed_chars for c in expr):
                raise ValueError("Invalid characters in expression")
            
            result = eval(expr)
            self.add_message(f"ORBIT: {expr} = {result}", 'orbit')
        except Exception as e:
            self.add_message(f"ORBIT: Calculation error: {str(e)}", 'orbit')
    
    def ask_ai(self, prompt=None):
        """Get response from AI model"""
        if not self.ai_ready:
            self.add_message("ORBIT: AI is currently unavailable", 'orbit')
            return
        
        if not prompt:
            prompt = simpledialog.askstring("Ask AI", "Enter your question:")
            if not prompt:
                return
        
        def generate_response():
            self.status_label.config(text="AI: Thinking...", fg='#f39c12')
            try:
                response = self.ai_model.generate(prompt, max_tokens=300)
                self.add_message(f"ORBIT: {response}", 'orbit')
            except Exception as e:
                self.add_message(f"ORBIT: AI error: {str(e)}", 'orbit')
            finally:
                self.status_label.config(text="✓ Ready", fg='#2ecc71')
        
        threading.Thread(target=generate_response, daemon=True).start()
    
    def show_calculator(self):
        """Show calculator window"""
        calc_window = tk.Toplevel(self.root)
        calc_window.title("Calculator")
        calc_window.resizable(False, False)
        
        entry = tk.Entry(calc_window, font=('Helvetica', 20), justify='right', bd=10)
        entry.grid(row=0, column=0, columnspan=4, sticky='nsew')
        
        buttons = [
            ('7', '8', '9', '/'),
            ('4', '5', '6', '*'),
            ('1', '2', '3', '-'),
            ('C', '0', '=', '+'),
            ('(', ')', 'π', '√')
        ]
        
        def on_click(char):
            if char == '=':
                try:
                    expr = entry.get()
                    # Replace constants
                    expr = expr.replace('π', str(math.pi))
                    if '√' in expr:
                        expr = expr.replace('√', 'math.sqrt(') + ')'
                    result = eval(expr)
                    entry.delete(0, tk.END)
                    entry.insert(0, str(result))
                except:
                    entry.delete(0, tk.END)
                    entry.insert(0, "Error")
            elif char == 'C':
                entry.delete(0, tk.END)
            elif char == 'π':
                entry.insert(tk.END, str(math.pi))
            elif char == '√':
                entry.insert(tk.END, '√')
            else:
                entry.insert(tk.END, char)
        
        for i, row in enumerate(buttons):
            for j, char in enumerate(row):
                btn = tk.Button(
                    calc_window,
                    text=char,
                    command=lambda c=char: on_click(c),
                    font=('Helvetica', 16),
                    width=3,
                    bg='#f8f9fa',
                    relief=tk.RAISED
                )
                btn.grid(row=i+1, column=j, sticky='nsew', padx=2, pady=2)
        
        # Make buttons expand
        for i in range(5):
            calc_window.grid_rowconfigure(i, weight=1)
        for j in range(4):
            calc_window.grid_columnconfigure(j, weight=1)
    
    def show_task_manager(self):
        """Show task manager window"""
        task_window = tk.Toplevel(self.root)
        task_window.title("Task Manager")
        task_window.geometry("500x400")
        
        # Task list
        self.task_list = tk.Listbox(
            task_window,
            font=('Helvetica', 12),
            selectmode=tk.SINGLE,
            bg=self.text_bg,
            fg=self.fg_color
        )
        self.task_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.refresh_task_list()
        
        # Controls frame
        control_frame = tk.Frame(task_window, bg=self.bg_color)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.task_entry = tk.Entry(
            control_frame,
            font=('Helvetica', 12),
            bg=self.text_bg,
            fg=self.fg_color
        )
        self.task_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.task_entry.bind('<Return>', lambda e: self.add_task_gui())
        
        # Buttons
        btn_frame = tk.Frame(control_frame, bg=self.bg_color)
        btn_frame.pack(side=tk.RIGHT)
        
        tk.Button(
            btn_frame,
            text="Add",
            command=self.add_task_gui,
            bg='#2ecc71',
            fg='white'
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            btn_frame,
            text="Complete",
            command=self.complete_task,
            bg='#e74c3c',
            fg='white'
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            btn_frame,
            text="Clear All",
            command=self.clear_tasks,
            bg='#f39c12',
            fg='white'
        ).pack(side=tk.LEFT, padx=2)
    
    def refresh_task_list(self):
        """Refresh the task list display"""
        self.task_list.delete(0, tk.END)
        for task in self.tasks:
            self.task_list.insert(tk.END, task)
    
    def add_task_gui(self):
        """Add task from GUI"""
        task = self.task_entry.get().strip()
        if task:
            self.tasks.append(task)
            self.task_entry.delete(0, tk.END)
            self.refresh_task_list()
            self.save_tasks()
            self.add_message(f"ORBIT: Added task: {task}", 'orbit')
    
    def add_task(self, query):
        """Add task from voice/text command"""
        task = query.lower().replace('add task', '').replace('new task', '').strip()
        if task:
            self.tasks.append(task)
            self.save_tasks()
            self.add_message(f"ORBIT: Added task: {task}", 'orbit')
    
    def complete_task(self):
        """Mark task as complete"""
        try:
            index = self.task_list.curselection()[0]
            task = self.tasks.pop(index)
            self.refresh_task_list()
            self.save_tasks()
            self.add_message(f"ORBIT: Completed task: {task}", 'orbit')
        except:
            messagebox.showwarning("No Selection", "Please select a task to complete")
    
    def clear_tasks(self):
        """Clear all tasks"""
        if messagebox.askyesno("Confirm", "Clear all tasks?"):
            self.tasks.clear()
            self.refresh_task_list()
            self.save_tasks()
            self.add_message("ORBIT: Cleared all tasks", 'orbit')
    
    def open_browser(self):
        """Open web browser"""
        self.add_message("ORBIT: Opening web browser...", 'orbit')
        webbrowser.open("https://www.google.com")
    
    def play_music(self):
        """Play music from default directory"""
        music_dir = self.settings.get('music_path', os.path.expanduser('~/Music'))
        
        if not os.path.exists(music_dir):
            self.add_message(f"ORBIT: Music directory not found: {music_dir}", 'orbit')
            return
        
        try:
            music_files = [f for f in os.listdir(music_dir) if f.endswith(('.mp3', '.wav'))]
            if not music_files:
                self.add_message("ORBIT: No music files found", 'orbit')
                return
            
            # Play random song
            song = random.choice(music_files)
            os.startfile(os.path.join(music_dir, song))
            self.add_message(f"ORBIT: Playing: {song}", 'orbit')
        except Exception as e:
            self.add_message(f"ORBIT: Error playing music: {str(e)}", 'orbit')
    
    def open_application(self, query):
        """Open application based on query"""
        app_map = {
            'chrome': 'chrome.exe',
            'firefox': 'firefox.exe',
            'word': 'winword.exe',
            'excel': 'excel.exe',
            'vs code': 'code.exe',
            'calculator': 'calc.exe'
        }
        
        app_name = query.lower().replace('open', '').replace('launch', '').strip()
        app_path = app_map.get(app_name, None)
        
        if app_path:
            try:
                subprocess.Popen(app_path)
                self.add_message(f"ORBIT: Opening {app_name}", 'orbit')
            except:
                self.add_message(f"ORBIT: Couldn't open {app_name}", 'orbit')
        else:
            self.add_message(f"ORBIT: Unknown application: {app_name}", 'orbit')
    
    def search_web(self, query):
        """Search the web"""
        search_term = query.lower().replace('search', '').replace('look up', '').strip()
        if search_term:
            webbrowser.open(f"https://www.google.com/search?q={search_term}")
            self.add_message(f"ORBIT: Searching for: {search_term}", 'orbit')
    
    def get_time(self):
        """Get current time"""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.add_message(f"ORBIT: Current time is {current_time}", 'orbit')
    
    def get_date(self):
        """Get current date"""
        current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
        self.add_message(f"ORBIT: Today is {current_date}", 'orbit')
    
    def set_reminder(self, query):
        """Set a reminder"""
        self.add_message("ORBIT: Reminder feature coming soon!", 'orbit')
        # Implementation would parse time/date from query and set reminder
    
    def word_of_the_day(self):
        """Show word of the day"""
        try:
            response = requests.get("https://random-word-api.herokuapp.com/word")
            if response.status_code == 200:
                word = response.json()[0]
                self.add_message(f"ORBIT: Word of the day: {word.capitalize()}", 'orbit')
                
                if self.settings['notifications']:
                    notification.notify(
                        title="Word of the Day",
                        message=f"Today's word: {word.capitalize()}",
                        timeout=10
                    )
        except:
            # Fallback to local word list
            words = ["Serendipity", "Ephemeral", "Quintessential", "Luminous", "Resilience"]
            word = random.choice(words)
            self.add_message(f"ORBIT: Word of the day: {word}", 'orbit')
    
    def show_calendar(self):
        """Show calendar window"""
        calendar_window = tk.Toplevel(self.root)
        calendar_window.title("Calendar")
        
        # Simple calendar implementation
        today = datetime.datetime.now()
        
        tk.Label(
            calendar_window,
            text=today.strftime("%B %Y"),
            font=('Helvetica', 14, 'bold')
        ).pack(pady=5)
        
        # Calendar display would go here
        # (Full implementation would require more complex widget)
        
        tk.Label(
            calendar_window,
            text="Calendar feature coming soon!",
            font=('Helvetica', 12)
        ).pack(pady=20)
    
    def show_system_info(self):
        """Display system information"""
        try:
            import platform
            info = f"""
System Information:
- OS: {platform.system()} {platform.release()}
- Processor: {platform.processor()}
- Python: {platform.python_version()}
- Machine: {platform.machine()}
"""
            self.add_message(info.strip(), 'system')
        except:
            self.add_message("ORBIT: Couldn't get system info", 'orbit')
    
    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        
        # Theme selection
        tk.Label(
            settings_window,
            text="Theme:",
            font=('Helvetica', 12)
        ).grid(row=0, column=0, padx=10, pady=10, sticky='w')
        
        theme_var = tk.StringVar(value=self.settings['theme'])
        tk.Radiobutton(
            settings_window,
            text="Light",
            variable=theme_var,
            value='light',
            command=self.toggle_theme
        ).grid(row=0, column=1, sticky='w')
        
        tk.Radiobutton(
            settings_window,
            text="Dark",
            variable=theme_var,
            value='dark',
            command=self.toggle_theme
        ).grid(row=0, column=2, sticky='w')
        
        # Voice settings
        voice_var = tk.BooleanVar(value=self.settings['voice'])
        tk.Checkbutton(
            settings_window,
            text="Enable Voice",
            variable=voice_var,
            command=lambda: self.toggle_setting('voice', voice_var.get())
        ).grid(row=1, column=0, columnspan=3, sticky='w', padx=10, pady=5)
        
        # Notifications
        notif_var = tk.BooleanVar(value=self.settings['notifications'])
        tk.Checkbutton(
            settings_window,
            text="Enable Notifications",
            variable=notif_var,
            command=lambda: self.toggle_setting('notifications', notif_var.get())
        ).grid(row=2, column=0, columnspan=3, sticky='w', padx=10, pady=5)
        
        # Music path
        tk.Label(
            settings_window,
            text="Music Folder:",
            font=('Helvetica', 12)
        ).grid(row=3, column=0, padx=10, pady=10, sticky='w')
        
        music_path = tk.StringVar(value=self.settings['music_path'])
        tk.Entry(
            settings_window,
            textvariable=music_path,
            width=30
        ).grid(row=3, column=1, columnspan=2)
        
        tk.Button(
            settings_window,
            text="Browse",
            command=lambda: self.browse_music_path(music_path)
        ).grid(row=4, column=1, sticky='e', padx=5)
    
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        self.settings['theme'] = 'dark' if self.settings['theme'] == 'light' else 'light'
        self.save_settings()
        self.setup_theme()
        
        # Reconfigure widget colors
        widgets = [
            (self.header_frame, 'bg'),
            (self.content_frame, 'bg'),
            (self.footer_frame, 'bg'),
            (self.status_frame, 'bg'),
            (self.status_label, 'bg'),
            (self.ai_status, 'bg'),
            (self.input_frame, 'bg'),
            (self.conversation, 'bg'),
            (self.conversation, 'fg'),
            (self.user_input, 'bg'),
            (self.user_input, 'fg')
        ]
        
        for widget, attr in widgets:
            if attr == 'bg':
                widget.config(bg=self.bg_color if attr == 'bg' else self.text_bg)
            else:
                widget.config(fg=self.fg_color)
    
    def toggle_setting(self, key, value):
        """Toggle a setting"""
        self.settings[key] = value
        self.save_settings()
    
    def browse_music_path(self, path_var):
        """Browse for music directory"""
        folder = filedialog.askdirectory(initialdir=path_var.get())
        if folder:
            path_var.set(folder)
            self.settings['music_path'] = folder
            self.save_settings()
    
    def start_background_tasks(self):
        """Start background tasks like reminders"""
        # This would run in a separate thread
        pass
    
    def on_close(self):
        """Handle window close event"""
        if messagebox.askokcancel("Quit", "Do you want to quit ORBIT Assistant?"):
            self.save_settings()
            self.save_tasks()
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ORBITAssistant(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()