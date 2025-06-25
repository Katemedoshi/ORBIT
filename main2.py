import pyttsx3
import speech_recognition as sr
import datetime
import wikipedia
import webbrowser
import os
import smtplib
from PyDictionary import PyDictionary
import random
import plyer as pl
from youtubesearchpython import VideosSearch
import tkinter as tk
from tkinter import ttk, scrolledtext, PhotoImage
from PIL import Image, ImageTk
import threading
import json
import requests
from gpt4all import GPT4All

os.environ["GPT4ALL_NO_CUDA"] = "1"

# Initialize GPT4All model
gpt4all_model = GPT4All("orca-mini-3b-gguf2-q4_0.gguf")  # Newer Orca model

class ORBITAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("ORBIT Desktop Assistant")
        self.root.geometry("900x600")
        self.root.resizable(True, True)
        self.root.configure(bg='#1e1e2e')
        
        # Initialize speech engine
        self.engine = pyttsx3.init('sapi5')
        self.voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', self.voices[0].id)
        self.engine.setProperty('rate', 180)
        
        # State variables
        self.task_mode = False
        self.reminders = []
        self.settings = {
            'water_reminder': True,
            'word_of_day': True,
            'voice_enabled': True,
            'email': '',
            'password': ''
        }
        
        # Load settings if available
        self.load_settings()
        
        # Setup GUI
        self.setup_gui()
        
        # Initial operations
        self.wish_me(True)
        if self.settings['word_of_day']:
            self.word_for_the_day()
        
        # Start background tasks
        self.start_background_tasks()
    
    def setup_gui(self):
        # Main frames
        self.header_frame = tk.Frame(self.root, bg='#1e1e2e')
        self.header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.content_frame = tk.Frame(self.root, bg='#1e1e2e')
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.footer_frame = tk.Frame(self.root, bg='#1e1e2e')
        self.footer_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Header
        self.logo_img = Image.open("orbit_logo.png").resize((60, 60))
        self.logo_photo = ImageTk.PhotoImage(self.logo_img)
        
        self.logo_label = tk.Label(self.header_frame, image=self.logo_photo, bg='#1e1e2e')
        self.logo_label.grid(row=0, column=0, padx=10)
        
        self.title_label = tk.Label(
            self.header_frame, 
            text="ORBIT Desktop Assistant", 
            font=('Helvetica', 18, 'bold'), 
            fg='#89b4fa', 
            bg='#1e1e2e'
        )
        self.title_label.grid(row=0, column=1, padx=10)
        
        # Status indicators
        self.status_frame = tk.Frame(self.header_frame, bg='#1e1e2e')
        self.status_frame.grid(row=0, column=2, padx=10)
        
        self.mic_status = tk.Label(
            self.status_frame, 
            text="🎤 Ready", 
            font=('Helvetica', 10), 
            fg='#a6e3a1', 
            bg='#1e1e2e'
        )
        self.mic_status.pack(side=tk.LEFT, padx=5)
        
        self.task_mode_status = tk.Label(
            self.status_frame, 
            text="Task Mode: OFF", 
            font=('Helvetica', 10), 
            fg='#f38ba8', 
            bg='#1e1e2e'
        )
        self.task_mode_status.pack(side=tk.LEFT, padx=5)
        
        # Content area
        self.conversation_text = scrolledtext.ScrolledText(
            self.content_frame,
            wrap=tk.WORD,
            width=80,
            height=20,
            font=('Helvetica', 10),
            bg='#313244',
            fg='#cdd6f4',
            insertbackground='white'
        )
        self.conversation_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.conversation_text.configure(state='disabled')
        
        # Input area
        self.input_frame = tk.Frame(self.content_frame, bg='#1e1e2e')
        self.input_frame.pack(fill=tk.X, pady=5)
        
        self.input_entry = tk.Entry(
            self.input_frame,
            font=('Helvetica', 12),
            bg='#45475a',
            fg='#cdd6f4',
            insertbackground='white'
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.input_entry.bind('<Return>', self.process_text_input)
        
        self.voice_button = tk.Button(
            self.input_frame,
            text="🎤",
            font=('Helvetica', 12),
            bg='#89b4fa',
            fg='#1e1e2e',
            command=self.start_voice_input
        )
        self.voice_button.pack(side=tk.LEFT, padx=5)
        
        # Quick actions frame
        self.quick_actions_frame = tk.Frame(self.footer_frame, bg='#1e1e2e')
        self.quick_actions_frame.pack(fill=tk.X, pady=5)
        
        quick_actions = [
            ("🌐 Open Browser", self.open_browser),
            ("🎵 Play Music", self.play_music),
            ("📅 Set Reminder", self.set_reminder_gui),
            ("📧 Send Email", self.send_email_gui),
            ("⚙️ Settings", self.open_settings)
        ]
        
        for text, command in quick_actions:
            btn = tk.Button(
                self.quick_actions_frame,
                text=text,
                font=('Helvetica', 10),
                bg='#585b70',
                fg='#cdd6f4',
                command=command
            )
            btn.pack(side=tk.LEFT, padx=5, ipadx=5, ipady=3)
    
    def start_background_tasks(self):
        # Start reminder checks in background
        threading.Thread(target=self.check_background_tasks, daemon=True).start()
    
    def check_background_tasks(self):
        while True:
            if self.settings['water_reminder']:
                self.water_reminder()
            self.check_reminder()
            self.root.update()
            datetime.datetime.now().second % 5 == 0  # Check every 5 seconds
    
    def add_to_conversation(self, text, sender="ORBIT"):
        self.conversation_text.configure(state='normal')
        if sender == "ORBIT":
            self.conversation_text.insert(tk.END, f"ORBIT: {text}\n", 'orbit')
        else:
            self.conversation_text.insert(tk.END, f"You: {text}\n", 'user')
        self.conversation_text.configure(state='disabled')
        self.conversation_text.see(tk.END)
        
        if sender == "ORBIT" and self.settings['voice_enabled']:
            self.speak(text)
    
    def speak(self, audio):
        self.engine.say(audio)
        self.engine.runAndWait()
    
    def wish_me(self, start):
        hour = datetime.datetime.now().hour
        if start:
            if 0 <= hour < 12:
                greeting = "Good Morning!"
            elif 12 <= hour < 18:
                greeting = "Good Afternoon!"
            else:
                greeting = "Good Evening!"
            
            self.add_to_conversation(f"{greeting} I am ORBIT. Good to see you again.")
        else:
            self.add_to_conversation('Goodbye!')
            if 0 <= hour < 12:
                self.add_to_conversation("Have a good day!")
            elif 18 <= hour < 24:
                self.add_to_conversation("Have a good night!")
    
    def start_voice_input(self):
        threading.Thread(target=self.take_command, daemon=True).start()
    
    def take_command(self):
        self.mic_status.config(text="🎤 Listening...", fg='#f9e2af')
        self.root.update()
        
        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.pause_threshold = 1
            audio = r.listen(source)
        
        try:
            self.mic_status.config(text="🎤 Recognizing...", fg='#f9e2af')
            self.root.update()
            
            query = r.recognize_google(audio, language='en-in')
            self.add_to_conversation(query, "user")
            
            if 'hey orbit' in query.lower() and not self.task_mode:
                self.enter_task_mode()
            elif 'thank you orbit' in query.lower() and self.task_mode:
                self.exit_task_mode()
            elif 'goodbye orbit' in query.lower():
                self.close_assistant()
            elif self.task_mode:
                self.process_query(query.lower())
            
        except Exception as e:
            self.add_to_conversation("Could not understand audio. Please try again.")
        finally:
            self.mic_status.config(text="🎤 Ready", fg='#a6e3a1')
    
    def process_text_input(self, event=None):
        query = self.input_entry.get()
        if query:
            self.add_to_conversation(query, "user")
            self.input_entry.delete(0, tk.END)
            
            if 'hey orbit' in query.lower() and not self.task_mode:
                self.enter_task_mode()
            elif 'thank you orbit' in query.lower() and self.task_mode:
                self.exit_task_mode()
            elif 'goodbye orbit' in query.lower():
                self.close_assistant()
            elif self.task_mode:
                self.process_query(query.lower())
    
    def enter_task_mode(self):
        self.task_mode = True
        self.task_mode_status.config(text="Task Mode: ON", fg='#a6e3a1')
        self.add_to_conversation("Hello! How can I help you?")
    
    def exit_task_mode(self):
        self.task_mode = False
        self.task_mode_status.config(text="Task Mode: OFF", fg='#f38ba8')
        self.add_to_conversation("You're welcome! Let me know if you need anything else.")
    
    def process_query(self, query):
        # Process all commands
        if 'search in browser' in query:
            self.search_web(query.replace('search in browser', '').strip())
        elif 'search in youtube' in query:
            self.search_youtube(query.replace('search in youtube', '').strip())
        elif 'search in wikipedia' in query:
            self.search_wikipedia(query.replace('search in wikipedia', '').strip())
        elif 'open youtube' in query:
            self.open_website("youtube.com")
        elif 'play in youtube' in query:
            self.play_youtube(query.replace('play in youtube', '').strip())
        elif 'open google' in query:
            self.open_website("google.com")
        elif 'open stackoverflow' in query:
            self.open_website("stackoverflow.com")
        elif 'open vierp' in query:
            self.open_website("learner.vierp.in/home")
        elif 'play music' in query:
            self.play_music()
        elif 'what is the time' in query:
            self.get_time()
        elif 'open vs code' in query:
            self.open_app("C:\\Users\\omkar\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe")
        elif 'open whatsapp' in query:
            self.open_app("C:\\Users\\omkar\\AppData\\Local\\WhatsApp\\WhatsApp.exe")
        elif 'email to' in query:
            self.send_email(query.replace('email to', '').strip())
        elif 'set reminder' in query or 'set a reminder' in query:
            self.set_reminder()
        elif 'introduce yourself' in query:
            self.introduce()
        elif 'ask ai' in query:
            self.ask_ai(query.replace('ask ai', '').strip())
        else:
            self.add_to_conversation("I'm not sure how to help with that. Try being more specific.")
    
    # Task implementations
    def search_web(self, query):
        try:
            webbrowser.open(f'https://www.google.com/search?q={query}')
            self.add_to_conversation(f"Searching the web for {query}")
        except:
            self.add_to_conversation("Could not perform the search. Please try again.")
    
    def search_youtube(self, query):
        try:
            webbrowser.open(f'https://www.youtube.com/results?search_query={query}')
            self.add_to_conversation(f"Searching YouTube for {query}")
        except:
            self.add_to_conversation("Could not search YouTube. Please try again.")
    
    def search_wikipedia(self, query):
        try:
            self.add_to_conversation("Searching Wikipedia...")  
            results = wikipedia.summary(query, sentences=2)
            self.add_to_conversation(f"According to Wikipedia: {results}")
        except:
            self.add_to_conversation("Could not find Wikipedia results. Please try a different query.")
    
    def open_website(self, url):
        try:
            webbrowser.open(url)
            self.add_to_conversation(f"Opening {url}")
        except:
            self.add_to_conversation(f"Could not open {url}")
    
    def play_youtube(self, query):
        try:
            videosSearch = VideosSearch(query, limit=1)
            url = videosSearch.result()['result'][0]['link']
            webbrowser.open(url)
            self.add_to_conversation(f"Playing {query} on YouTube")
        except:
            self.add_to_conversation("Could not play the video. Please try again.")
    
    def play_music(self):
        music_dir = 'D:\\Music\\timepass'
        try:
            songs = os.listdir(music_dir)
            if songs:
                os.startfile(os.path.join(music_dir, songs[0]))
                self.add_to_conversation("Playing music")
            else:
                self.add_to_conversation("No music files found in the directory")
        except:
            self.add_to_conversation("Could not play music. Please check the music directory.")
    
    def get_time(self):
        strTime = datetime.datetime.now().strftime("%H:%M:%S")
        self.add_to_conversation(f"The current time is {strTime}")
    
    def open_app(self, path):
        try:
            os.startfile(path)
            self.add_to_conversation("Opening application")
        except:
            self.add_to_conversation("Could not open the application. Please check the path.")
    
    def send_email(self, recipient):
        try:    
            if not self.settings['email'] or not self.settings['password']:
                self.add_to_conversation("Email credentials not set. Please configure in settings.")
                return
                
            self.add_to_conversation("What should I say?")
            content = self.take_command()
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.ehlo()
            server.starttls()
            server.login(self.settings['email'], self.settings['password'])
            server.sendmail(self.settings['email'], f"{recipient}@gmail.com", content)
            server.close()
            self.add_to_conversation("Email has been sent!")
        except Exception as e:
            self.add_to_conversation(f"Sorry, could not send the email. Error: {str(e)}")
    
    def set_reminder(self):
        self.add_to_conversation("At what time do you want me to remind you?")
        reminder_time = self.take_command().lower()
        self.add_to_conversation('What do you want me to remind you of?')
        content = self.take_command()
        
        try:
            reminder_time = reminder_time.replace(':', ' ').split()
            hour = int(reminder_time[0])
            minute = int(reminder_time[1])
            
            if 'p.m.' in reminder_time and hour < 12:
                hour += 12
            elif 'a.m.' in reminder_time and hour == 12:
                hour = 0
                
            self.reminders.append({
                'hour': hour,
                'minute': minute,
                'content': content
            })
            self.add_to_conversation(f'Reminder set for {hour}:{minute:02d} - {content}')
        except:
            self.add_to_conversation('Could not set the reminder. Please try again.')
    
    def check_reminder(self):
        now = datetime.datetime.now()
        for reminder in self.reminders[:]:
            if now.hour == reminder['hour'] and now.minute == reminder['minute']:
                pl.notification.notify(
                    title='Reminder from ORBIT',
                    message=reminder['content'],
                    timeout=60
                )
                self.add_to_conversation(f"Reminder: {reminder['content']}")
                self.reminders.remove(reminder)
    
    def water_reminder(self):
        now = datetime.datetime.now()
        if now.minute == 0 or now.minute == 30:
            pl.notification.notify(
                title='Break Reminder',
                message='Hey, take a break and drink some water.',
                timeout=60
            )
            self.add_to_conversation("Time to take a short break and drink some water!")
    
    def word_for_the_day(self):
        try:
            response = requests.get("https://random-words-api.vercel.app/word")
            if response.status_code == 200:
                word_data = response.json()[0]
                word = word_data['word']
                meaning = word_data['definition']
                
                pl.notification.notify(
                    title='Word for the Day',
                    message=f'{word.capitalize()}: {meaning}',
                    timeout=60
                )
                self.add_to_conversation(f"Word for the day: {word.capitalize()} - {meaning}")
                return
        
        except:
            pass
        
        # Fallback if API fails
        try:
            with open('words.txt', 'r') as f:
                wordlist = f.readlines()
                word = random.choice(wordlist).strip()
                meanings = PyDictionary.meaning(word)
                
                if meanings:
                    means = '\n'.join([f"{k}: {v[0]}" for k, v in meanings.items()])
                    pl.notification.notify(
                        title='Word for the Day',
                        message=f'{word.capitalize()}: {means}',
                        timeout=60
                    )
                    self.add_to_conversation(f"Word for the day: {word.capitalize()} - {means}")
        except:
            self.add_to_conversation("Could not fetch word for the day.")
    
    def introduce(self):
        intro = """Hello! I am ORBIT, your desktop assistant. I can help you with various tasks including:
- Opening applications and websites
- Searching the web, YouTube, and Wikipedia
- Setting reminders and alarms
- Sending emails
- Playing music
- Providing the time and date
- Giving you a word of the day
- Answering questions with AI

To get started, say "Hey ORBIT" to enter task mode, then give me a command. 
When finished, say "Thank you ORBIT" to exit task mode."""
        self.add_to_conversation(intro)
    
    def ask_ai(self, query):
        try:
            self.add_to_conversation("Thinking...")
            response = gpt4all_model.generate(query, max_tokens=200)
            self.add_to_conversation(response)
        except Exception as e:
            self.add_to_conversation(f"Sorry, I couldn't process that request. Error: {str(e)}")
    
    # GUI-specific methods
    def open_browser(self):
        self.open_website("google.com")
    
    def set_reminder_gui(self):
        reminder_window = tk.Toplevel(self.root)
        reminder_window.title("Set Reminder")
        reminder_window.geometry("400x300")
        reminder_window.resizable(False, False)
        reminder_window.configure(bg='#313244')
        
        tk.Label(reminder_window, text="Set a Reminder", font=('Helvetica', 14), bg='#313244', fg='#89b4fa').pack(pady=10)
        
        # Time entry
        time_frame = tk.Frame(reminder_window, bg='#313244')
        time_frame.pack(pady=5)
        
        tk.Label(time_frame, text="Time (HH:MM):", bg='#313244', fg='#cdd6f4').pack(side=tk.LEFT)
        time_entry = tk.Entry(time_frame, bg='#45475a', fg='#cdd6f4', insertbackground='white')
        time_entry.pack(side=tk.LEFT, padx=5)
        
        # AM/PM
        ampm_var = tk.StringVar(value="AM")
        tk.Radiobutton(time_frame, text="AM", variable=ampm_var, value="AM", bg='#313244', fg='#cdd6f4', selectcolor='#45475a').pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(time_frame, text="PM", variable=ampm_var, value="PM", bg='#313244', fg='#cdd6f4', selectcolor='#45475a').pack(side=tk.LEFT, padx=5)
        
        # Content
        tk.Label(reminder_window, text="Reminder Content:", bg='#313244', fg='#cdd6f4').pack(pady=5)
        content_entry = tk.Text(reminder_window, height=5, width=40, bg='#45475a', fg='#cdd6f4', insertbackground='white')
        content_entry.pack(pady=5)
        
        # Save button
        def save_reminder():
            try:
                time_str = time_entry.get()
                hour, minute = map(int, time_str.split(':'))
                
                if ampm_var.get() == "PM" and hour < 12:
                    hour += 12
                elif ampm_var.get() == "AM" and hour == 12:
                    hour = 0
                
                content = content_entry.get("1.0", tk.END).strip()
                
                self.reminders.append({
                    'hour': hour,
                    'minute': minute,
                    'content': content
                })
                
                self.add_to_conversation(f"Reminder set for {hour}:{minute:02d} - {content}")
                reminder_window.destroy()
            except:
                tk.messagebox.showerror("Error", "Invalid time format. Please use HH:MM")
        
        tk.Button(
            reminder_window,
            text="Set Reminder",
            bg='#89b4fa',
            fg='#1e1e2e',
            command=save_reminder
        ).pack(pady=10)
    
    def send_email_gui(self):
        email_window = tk.Toplevel(self.root)
        email_window.title("Send Email")
        email_window.geometry("500x400")
        email_window.resizable(False, False)
        email_window.configure(bg='#313244')
        
        tk.Label(email_window, text="Send Email", font=('Helvetica', 14), bg='#313244', fg='#89b4fa').pack(pady=10)
        
        # Recipient
        recipient_frame = tk.Frame(email_window, bg='#313244')
        recipient_frame.pack(pady=5, fill=tk.X, padx=20)
        
        tk.Label(recipient_frame, text="To:", bg='#313244', fg='#cdd6f4').pack(side=tk.LEFT)
        recipient_entry = tk.Entry(recipient_frame, bg='#45475a', fg='#cdd6f4', insertbackground='white')
        recipient_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        recipient_entry.insert(0, "@gmail.com")
        
        # Subject
        subject_frame = tk.Frame(email_window, bg='#313244')
        subject_frame.pack(pady=5, fill=tk.X, padx=20)
        
        tk.Label(subject_frame, text="Subject:", bg='#313244', fg='#cdd6f4').pack(side=tk.LEFT)
        subject_entry = tk.Entry(subject_frame, bg='#45475a', fg='#cdd6f4', insertbackground='white')
        subject_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Content
        tk.Label(email_window, text="Message:", bg='#313244', fg='#cdd6f4').pack(pady=5)
        content_entry = tk.Text(email_window, height=10, width=50, bg='#45475a', fg='#cdd6f4', insertbackground='white')
        content_entry.pack(pady=5, padx=20)
        
        # Send button
        def send_email():
            try:
                if not self.settings['email'] or not self.settings['password']:
                    tk.messagebox.showerror("Error", "Email credentials not set. Please configure in settings.")
                    return
                
                recipient = recipient_entry.get()
                subject = subject_entry.get()
                content = content_entry.get("1.0", tk.END)
                
                full_content = f"Subject: {subject}\n\n{content}"
                
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.ehlo()
                server.starttls()
                server.login(self.settings['email'], self.settings['password'])
                server.sendmail(self.settings['email'], recipient, full_content)
                server.close()
                
                self.add_to_conversation(f"Email sent to {recipient}")
                email_window.destroy()
            except Exception as e:
                tk.messagebox.showerror("Error", f"Could not send email: {str(e)}")
        
        tk.Button(
            email_window,
            text="Send Email",
            bg='#89b4fa',
            fg='#1e1e2e',
            command=send_email
        ).pack(pady=10)
    
    def open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x400")
        settings_window.resizable(False, False)
        settings_window.configure(bg='#313244')
        
        tk.Label(settings_window, text="ORBIT Settings", font=('Helvetica', 14), bg='#313244', fg='#89b4fa').pack(pady=10)
        
        # Settings frame
        settings_frame = tk.Frame(settings_window, bg='#313244')
        settings_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        # Water reminder
        water_var = tk.BooleanVar(value=self.settings['water_reminder'])
        water_cb = tk.Checkbutton(
            settings_frame,
            text="Enable Water Reminder (every 30 mins)",
            variable=water_var,
            bg='#313244',
            fg='#cdd6f4',
            selectcolor='#45475a'
        )
        water_cb.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # Word of the day
        word_var = tk.BooleanVar(value=self.settings['word_of_day'])
        word_cb = tk.Checkbutton(
            settings_frame,
            text="Enable Word of the Day",
            variable=word_var,
            bg='#313244',
            fg='#cdd6f4',
            selectcolor='#45475a'
        )
        word_cb.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # Voice enabled
        voice_var = tk.BooleanVar(value=self.settings['voice_enabled'])
        voice_cb = tk.Checkbutton(
            settings_frame,
            text="Enable Voice Responses",
            variable=voice_var,
            bg='#313244',
            fg='#cdd6f4',
            selectcolor='#45475a'
        )
        voice_cb.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        # Email settings
        tk.Label(settings_frame, text="Email Settings", font=('Helvetica', 12), bg='#313244', fg='#89b4fa').grid(row=3, column=0, sticky=tk.W, pady=10)
        
        email_frame = tk.Frame(settings_frame, bg='#313244')
        email_frame.grid(row=4, column=0, sticky=tk.W, pady=5)
        
        tk.Label(email_frame, text="Email:", bg='#313244', fg='#cdd6f4').grid(row=0, column=0)
        email_entry = tk.Entry(email_frame, bg='#45475a', fg='#cdd6f4', insertbackground='white')
        email_entry.grid(row=0, column=1, padx=5)
        email_entry.insert(0, self.settings['email'])
        
        tk.Label(email_frame, text="Password:", bg='#313244', fg='#cdd6f4').grid(row=1, column=0, pady=5)
        password_entry = tk.Entry(email_frame, show="*", bg='#45475a', fg='#cdd6f4', insertbackground='white')
        password_entry.grid(row=1, column=1, padx=5)
        password_entry.insert(0, self.settings['password'])
        
        # Save button
        def save_settings():
            self.settings = {
                'water_reminder': water_var.get(),
                'word_of_day': word_var.get(),
                'voice_enabled': voice_var.get(),
                'email': email_entry.get(),
                'password': password_entry.get()
            }
            self.save_settings_to_file()
            settings_window.destroy()
            self.add_to_conversation("Settings updated successfully")
        
        tk.Button(
            settings_window,
            text="Save Settings",
            bg='#89b4fa',
            fg='#1e1e2e',
            command=save_settings
        ).pack(pady=20)
    
    def load_settings(self):
        try:
            with open('orbit_settings.json', 'r') as f:
                self.settings = json.load(f)
        except:
            # Default settings
            self.settings = {
                'water_reminder': True,
                'word_of_day': True,
                'voice_enabled': True,
                'email': '',
                'password': ''
            }
    
    def save_settings_to_file(self):
        with open('orbit_settings.json', 'w') as f:
            json.dump(self.settings, f)
    
    def close_assistant(self):
        self.wish_me(False)
        self.root.after(2000, self.root.destroy)

if __name__ == "__main__":
    root = tk.Tk()
    app = ORBITAssistant(root)
    
    # Configure tags for conversation text colors
    app.conversation_text.tag_config('orbit', foreground='#89b4fa')
    app.conversation_text.tag_config('user', foreground='#a6e3a1')
    
    root.mainloop()