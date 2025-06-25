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
import platform
import calendar as cal
import psutil
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk import pos_tag, ne_chunk
from nltk.tree import Tree
from textblob import TextBlob
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')

class ORBITAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("ORBIT Desktop Assistant v4.0 (NLP Enhanced)")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)
        
        # Initialize NLP components
        self.setup_nlp()
        
        # Initialize other components
        self.setup_ai()
        self.setup_voice()
        self.load_settings()
        
        # Task manager data
        self.tasks = self.load_tasks()
        
        # Knowledge base for question answering
        self.knowledge_base = self.load_knowledge_base()
        self.setup_tfidf_vectorizer()
        
        # Setup GUI
        self.setup_gui()
        
        # Initial greeting
        self.greet_user()
        
        # Start background tasks
        self.start_background_tasks()
    
    def setup_nlp(self):
        """Initialize NLP components using NLTK and TextBlob"""
        # Initialize NLTK components
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        self.stemmer = PorterStemmer()
        
        # Initialize text similarity components
        self.vectorizer = TfidfVectorizer()
    
    def extract_entities(self, text):
        """Extract named entities from text using NLTK"""
        entities = []
        blob = TextBlob(text)
        for word, pos in blob.tags:
            if pos in ['NNP', 'NNPS']:  # Proper nouns
                entities.append((word, 'PERSON'))
        
        # Additional entity extraction using NLTK's ne_chunk
        tokenized = word_tokenize(text)
        tagged = pos_tag(tokenized)
        chunks = ne_chunk(tagged)
        
        for chunk in chunks:
            if isinstance(chunk, Tree):
                entity = ' '.join([c[0] for c in chunk])
                label = chunk.label()
                entities.append((entity, label))
        
        return list(set(entities))  # Remove duplicates
    
    def analyze_sentiment(self, text):
        """Sentiment analysis using TextBlob"""
        analysis = TextBlob(text)
        polarity = analysis.sentiment.polarity
        
        if polarity > 0.1:
            return 'positive'
        elif polarity < -0.1:
            return 'negative'
        else:
            return 'neutral'

    def setup_tfidf_vectorizer(self):
        """Setup TF-IDF vectorizer with knowledge base"""
        documents = [q['question'] for q in self.knowledge_base]
        self.vectorizer.fit(documents)
    
    def load_knowledge_base(self):
        """Load question-answer knowledge base"""
        default_kb = [
            {
                "question": "what is your name",
                "answer": "My name is ORBIT, your desktop assistant.",
                "tags": ["name", "identity"]
            },
            {
                "question": "what can you do",
                "answer": "I can help with tasks, calculations, reminders, web searches, and answer your questions.",
                "tags": ["capabilities", "help"]
            },
            {
                "question": "how do I add a task",
                "answer": "You can say 'add task [your task]' or use the task manager in the tools menu.",
                "tags": ["task", "add"]
            },
            {
                "question": "what time is it",
                "answer": "I can tell you the current time. Just ask 'what time is it?'",
                "tags": ["time", "current"]
            }
        ]
        
        try:
            with open('knowledge_base.json', 'r') as f:
                return json.load(f)
        except:
            return default_kb
    
    def save_knowledge_base(self):
        """Save knowledge base to file"""
        with open('knowledge_base.json', 'w') as f:
            json.dump(self.knowledge_base, f, indent=4)
    
    def preprocess_text(self, text):
        """Preprocess text for NLP tasks"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and numbers
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and lemmatize
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens if token not in self.stop_words]
        
        return ' '.join(tokens)
    
    def find_most_similar_question(self, query):
        """Find the most similar question in knowledge base using TF-IDF and cosine similarity"""
        query_vec = self.vectorizer.transform([query])
        doc_vecs = self.vectorizer.transform([q['question'] for q in self.knowledge_base])
        
        similarities = cosine_similarity(query_vec, doc_vecs)
        most_similar_idx = np.argmax(similarities)
        
        # Only return if similarity is above threshold
        if similarities[0, most_similar_idx] > 0.6:
            return self.knowledge_base[most_similar_idx]['answer']
        return None
    
    def setup_ai(self):
        """Initialize the AI model with error handling"""
        try:
            # Using a larger model - adjust based on your system capabilities
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
        default_settings = {
            'theme': 'light',
            'voice': True,
            'notifications': True,
            'ai_enabled': True,
            'music_path': os.path.expanduser('~/Music'),
            'documents_path': os.path.expanduser('~/Documents'),
            'downloads_path': os.path.expanduser('~/Downloads'),
            'voice_rate': 180,
            'startup_greeting': True
        }
        
        try:
            with open('orbit_settings.json', 'r') as f:
                loaded_settings = json.load(f)
                # Merge with default settings
                self.settings = {**default_settings, **loaded_settings}
        except:
            self.settings = default_settings
    
    def save_settings(self):
        """Save user settings to file"""
        with open('orbit_settings.json', 'w') as f:
            json.dump(self.settings, f, indent=4)
    
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
            self.button_bg = '#3d566e'
        else:
            self.bg_color = '#ecf0f1'
            self.fg_color = '#2c3e50'
            self.accent_color = '#2980b9'
            self.text_bg = '#ffffff'
            self.button_bg = '#dfe6e9'
        
        self.root.config(bg=self.bg_color)
    
    def setup_menu(self):
        """Create the menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open File", command=self.open_file_dialog)
        file_menu.add_command(label="Open Folder", command=self.open_folder_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="System Info", command=self.show_system_info)
        tools_menu.add_command(label="Word of the Day", command=self.word_of_the_day)
        tools_menu.add_command(label="Task Manager", command=self.show_task_manager)
        tools_menu.add_command(label="Calculator", command=self.show_calculator)
        tools_menu.add_command(label="Calendar", command=self.show_calendar)
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
            ("📂 Files", self.open_file_dialog),
            ("⚙ Settings", self.show_settings)
        ]
        
        for text, cmd in actions:
            btn = tk.Button(
                self.footer_frame,
                text=text,
                command=cmd,
                bg=self.button_bg,
                fg=self.fg_color,
                relief=tk.FLAT,
                font=('Helvetica', 10)
            )
            btn.pack(side=tk.LEFT, padx=5, pady=5)
    
    def greet_user(self):
        """Display initial greeting"""
        if not self.settings.get('startup_greeting', True):
            return
            
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
        """Enhanced process_input with NLP capabilities"""
        query = self.user_input.get().strip()
        if not query:
            return
        
        self.add_message(f"You: {query}", 'user')
        self.user_input.delete(0, tk.END)
        
        # Preprocess the query
        processed_query = self.preprocess_text(query)
        
        # Analyze sentiment
        sentiment = self.analyze_sentiment(query)
        if sentiment == 'negative':
            self.add_message("ORBIT: I'm sorry you're feeling that way. How can I help?", 'orbit')
        
        # Extract entities
        entities = self.extract_entities(query)
        if entities:
            self.log_entities(entities)
        
        # First try to find answer in knowledge base
        kb_answer = self.find_most_similar_question(processed_query)
        if kb_answer:
            self.add_message(f"ORBIT: {kb_answer}", 'orbit')
            return
        
        # Process commands with enhanced NLP understanding
        if self.is_calculation_query(query):
            self.calculate(query)
        elif self.is_task_query(query):
            self.handle_task_query(query)
        elif self.is_reminder_query(query):
            self.handle_reminder_query(query)
        elif self.is_information_query(query):
            self.handle_information_query(query)
        elif self.is_application_query(query):
            self.handle_application_query(query)
        elif self.ai_ready and len(query.split()) > 3:  # Only use AI for complex queries
            self.generate_ai_response(query)
        else:
            self.add_message("ORBIT: I'm not sure how to help with that. Can you rephrase?", 'orbit')
    
    def is_calculation_query(self, query):
        """Determine if query is a calculation request using NLP"""
        calc_keywords = ['calculate', 'compute', 'solve', 'what is', 'math', '+', '-', '*', '/']
        return any(keyword in query.lower() for keyword in calc_keywords)
    
    def is_task_query(self, query):
        """Determine if query is about tasks using NLP"""
        task_keywords = ['task', 'todo', 'reminder', 'remember', 'add', 'new']
        return any(keyword in query.lower() for keyword in task_keywords)
    
    def is_reminder_query(self, query):
        """Determine if query is about reminders using NLP"""
        reminder_keywords = ['remind', 'alert', 'notify', 'remember']
        time_keywords = ['at', 'in', 'on', 'tomorrow', 'today', 'after']
        return (any(keyword in query.lower() for keyword in reminder_keywords) and
                any(keyword in query.lower() for keyword in time_keywords))
    
    def is_information_query(self, query):
        """Determine if query is requesting information using NLP"""
        info_keywords = ['what', 'when', 'where', 'who', 'why', 'how', 'tell me', 'explain']
        return any(keyword in query.lower() for keyword in info_keywords)
    
    def is_application_query(self, query):
        """Determine if query is about opening applications using NLP"""
        app_keywords = ['open', 'launch', 'start', 'run']
        app_names = ['notepad', 'calculator', 'browser', 'chrome', 'firefox', 'word', 'excel']
        return (any(keyword in query.lower() for keyword in app_keywords) and
                any(name in query.lower() for name in app_names))
    
    def handle_task_query(self, query):
        """Handle task-related queries with NLP"""
        # Using TextBlob for parsing instead of spaCy
        blob = TextBlob(query.lower())
        
        # Extract task description - simple approach
        task = ""
        for sentence in blob.sentences:
            words = sentence.words
            if 'add' in words or 'create' in words or 'new' in words:
                task = ' '.join([word for word in words if word not in ['add', 'task', 'create', 'new']])
                break
        
        if not task:
            # Fallback to simple string replacement
            task = query.lower().replace('add task', '').replace('new task', '').replace('create task', '').strip()
        
        if task:
            self.tasks.append(task)
            self.save_tasks()
            self.add_message(f"ORBIT: Added task: {task}", 'orbit')
        else:
            self.add_message("ORBIT: Please specify a task to add", 'orbit')
    
    def handle_reminder_query(self, query):
        """Handle reminder queries with NLP"""
        # Using NLTK for time entity extraction
        tokens = word_tokenize(query.lower())
        tagged = pos_tag(tokens)
        
        # Extract time information (simple approach)
        time_entity = None
        time_keywords = ['minute', 'hour', 'day', 'tomorrow', 'today']
        for i, (word, pos) in enumerate(tagged):
            if word in time_keywords:
                # Try to get the number before the time keyword
                if i > 0 and tagged[i-1][1] == 'CD':  # CD = cardinal number
                    time_entity = f"{tagged[i-1][0]} {word}"
                else:
                    time_entity = word
                break
        
        # Extract reminder text (simple approach)
        reminder_text = ""
        reminder_keywords = ['remind', 'alert', 'notify']
        for word in tokens:
            if word in reminder_keywords:
                start_idx = tokens.index(word)
                reminder_text = ' '.join(tokens[start_idx+1:])
                break
        
        if not reminder_text:
            reminder_text = query.lower().replace('remind me', '').replace('alert me', '').strip()
        
        if time_entity and reminder_text:
            # Simple implementation - would need more sophisticated time parsing
            if 'minute' in time_entity:
                try:
                    minutes = int(re.search(r'\d+', time_entity).group())
                    self.set_reminder(reminder_text, minutes)
                except:
                    self.add_message("ORBIT: I couldn't understand the time. Please specify like 'in 5 minutes'", 'orbit')
            else:
                self.add_message(f"ORBIT: I'll remind you to '{reminder_text}' at {time_entity}", 'orbit')
        else:
            self.add_message("ORBIT: Please specify both the reminder and time (e.g. 'remind me in 5 minutes to take a break')", 'orbit')
    
    def handle_information_query(self, query):
        """Handle information requests with NLP"""
        # Using TextBlob for question analysis
        blob = TextBlob(query.lower())
        
        # Identify question type
        question_type = "general"
        wh_words = ['what', 'when', 'where', 'who', 'why', 'how']
        for word in blob.words:
            if word in wh_words:
                question_type = word
                break
        
        # Try to answer based on question type
        if question_type == "what" and "your name" in query.lower():
            self.add_message("ORBIT: My name is ORBIT, your desktop assistant.", 'orbit')
        elif question_type == "what" and "time" in query.lower():
            self.get_time()
        elif question_type == "what" and "date" in query.lower():
            self.get_date()
        elif question_type in ["who", "what"] and "you" in query.lower():
            self.add_message("ORBIT: I'm ORBIT, your intelligent desktop assistant. I can help with tasks, calculations, and answer questions.", 'orbit')
        else:
            # Fall back to AI or web search
            if self.ai_ready:
                self.generate_ai_response(query)
            else:
                self.search_web(query)
    
    def handle_application_query(self, query):
        """Handle application opening requests with NLP"""
        # Using NLTK for parsing
        tokens = word_tokenize(query.lower())
        tagged = pos_tag(tokens)
        
        # Extract application name (simple approach)
        app_name = ""
        for i, (word, pos) in enumerate(tagged):
            if word in ['open', 'launch', 'start']:
                # Look for the next noun
                for j in range(i+1, len(tagged)):
                    if tagged[j][1] in ['NN', 'NNP']:  # Noun
                        app_name = tagged[j][0]
                        break
                break
        
        if not app_name:
            # Fallback to simple string replacement
            app_name = query.lower().replace('open', '').replace('launch', '').replace('start', '').strip()
        
        if app_name:
            self.open_application(app_name)
        else:
            self.add_message("ORBIT: Please specify an application to open", 'orbit')
    
    def log_entities(self, entities):
        """Log extracted entities for debugging"""
        entity_str = ", ".join([f"{ent[0]} ({ent[1]})" for ent in entities])
        self.add_message(f"System: Detected entities - {entity_str}", 'system')
    
    def calculate(self, query):
        """Perform calculations"""
        try:
            # Extract math expression
            expr = query.lower().replace('calculate', '').replace('what is', '').replace('math', '').strip()
            if not expr:
                self.add_message("ORBIT: Please provide a calculation", 'orbit')
                return
            
            # Safety check - only allow certain characters
            allowed_chars = set('0123456789+-*/.()^% ')
            if not all(c in allowed_chars for c in expr):
                raise ValueError("Invalid characters in expression")
            
            # Replace ^ with ** for exponentiation
            expr = expr.replace('^', '**')
            
            # Handle percentage calculations
            if '%' in expr:
                parts = expr.split('%')
                if len(parts) == 2 and parts[1].strip() == '':
                    expr = f"{parts[0]}/100"
            
            result = eval(expr)
            self.add_message(f"ORBIT: {expr} = {result}", 'orbit')
        except Exception as e:
            self.add_message(f"ORBIT: Calculation error: {str(e)}", 'orbit')
    
    def generate_ai_response(self, prompt):
        """Generate response from AI model"""
        if not self.ai_ready:
            self.add_message("ORBIT: AI is currently unavailable", 'orbit')
            return
        
        def generate_response():
            self.status_label.config(text="AI: Thinking...", fg='#f39c12')
            try:
                with self.ai_model.chat_session():
                    response = self.ai_model.generate(prompt, max_tokens=400, temp=0.7)
                    self.add_message(f"ORBIT: {response}", 'orbit')
            except Exception as e:
                self.add_message(f"ORBIT: AI error: {str(e)}", 'orbit')
            finally:
                self.status_label.config(text="✓ Ready", fg='#2ecc71')
        
        threading.Thread(target=generate_response, daemon=True).start()
    
    def show_calculator(self):
        """Show advanced calculator window"""
        calc_window = tk.Toplevel(self.root)
        calc_window.title("Scientific Calculator")
        calc_window.resizable(False, False)
        
        # Result display
        self.calc_entry = tk.Entry(
            calc_window,
            font=('Helvetica', 24),
            justify='right',
            bd=10,
            bg='#f8f9fa',
            fg='#2c3e50'
        )
        self.calc_entry.grid(row=0, column=0, columnspan=5, sticky='nsew')
        self.calc_entry.insert(0, '0')
        
        # Button layout
        buttons = [
            ('7', '8', '9', '/', 'sin'),
            ('4', '5', '6', '*', 'cos'),
            ('1', '2', '3', '-', 'tan'),
            ('0', '.', '=', '+', '√'),
            ('C', '(', ')', '^', 'π'),
            ('log', 'ln', '!', '%', '±')
        ]
        
        # Button creation
        for i, row in enumerate(buttons):
            for j, char in enumerate(row):
                btn = tk.Button(
                    calc_window,
                    text=char,
                    command=lambda c=char: self.on_calc_click(c),
                    font=('Helvetica', 16),
                    width=4,
                    bg='#e9ecef',
                    fg='#2c3e50',
                    relief=tk.RAISED,
                    bd=3
                )
                btn.grid(row=i+1, column=j, sticky='nsew', padx=2, pady=2)
        
        # Make buttons expand
        for i in range(len(buttons)+1):
            calc_window.grid_rowconfigure(i, weight=1)
        for j in range(len(buttons[0])):
            calc_window.grid_columnconfigure(j, weight=1)
    
    def on_calc_click(self, char):
        """Handle calculator button clicks"""
        current = self.calc_entry.get()
        
        try:
            if char == 'C':
                self.calc_entry.delete(0, tk.END)
                self.calc_entry.insert(0, '0')
            elif char == '=':
                # Replace special symbols with math operations
                expr = current.replace('^', '**').replace('√', 'math.sqrt(')
                if '√' in current:
                    expr += ')'
                if 'π' in current:
                    expr = expr.replace('π', 'math.pi')
                
                # Handle functions
                if 'sin(' in expr:
                    expr = expr.replace('sin(', 'math.sin(')
                if 'cos(' in expr:
                    expr = expr.replace('cos(', 'math.cos(')
                if 'tan(' in expr:
                    expr = expr.replace('tan(', 'math.tan(')
                if 'log(' in expr:
                    expr = expr.replace('log(', 'math.log10(')
                if 'ln(' in expr:
                    expr = expr.replace('ln(', 'math.log(')
                if '!' in expr:
                    num = int(expr.replace('!', ''))
                    expr = f'math.factorial({num})'
                
                result = eval(expr)
                self.calc_entry.delete(0, tk.END)
                self.calc_entry.insert(0, str(result))
            elif char == '±':
                if current.startswith('-'):
                    self.calc_entry.delete(0)
                else:
                    self.calc_entry.insert(0, '-')
            elif char == 'π':
                self.calc_entry.insert(tk.END, 'π')
            elif char == '√':
                self.calc_entry.insert(tk.END, '√(')
            elif char in ('sin', 'cos', 'tan', 'log', 'ln'):
                self.calc_entry.insert(tk.END, f'{char}(')
            elif char == '!':
                self.calc_entry.insert(tk.END, '!')
            else:
                if current == '0':
                    self.calc_entry.delete(0, tk.END)
                self.calc_entry.insert(tk.END, char)
        except Exception as e:
            self.calc_entry.delete(0, tk.END)
            self.calc_entry.insert(0, "Error")
    
    def show_calendar(self):
        """Show interactive calendar window"""
        cal_window = tk.Toplevel(self.root)
        cal_window.title("Calendar")
        cal_window.geometry("400x400")
        
        today = datetime.datetime.now()
        self.cal_year = today.year
        self.cal_month = today.month
        
        # Navigation frame
        nav_frame = tk.Frame(cal_window)
        nav_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(
            nav_frame,
            text="<",
            command=lambda: self.change_calendar_month(-1, cal_window)
        ).pack(side=tk.LEFT)
        
        self.month_label = tk.Label(
            nav_frame,
            text=f"{today.strftime('%B %Y')}",
            font=('Helvetica', 12, 'bold')
        )
        self.month_label.pack(side=tk.LEFT, expand=True)
        
        tk.Button(
            nav_frame,
            text=">",
            command=lambda: self.change_calendar_month(1, cal_window)
        ).pack(side=tk.RIGHT)
        
        # Calendar display
        self.cal_frame = tk.Frame(cal_window)
        self.cal_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.update_calendar_display(cal_window)
    
    def change_calendar_month(self, delta, window):
        """Change the displayed month"""
        self.cal_month += delta
        if self.cal_month > 12:
            self.cal_month = 1
            self.cal_year += 1
        elif self.cal_month < 1:
            self.cal_month = 12
            self.cal_year -= 1
        
        self.month_label.config(text=f"{datetime.date(1900, self.cal_month, 1).strftime('%B')} {self.cal_year}")
        self.update_calendar_display(window)
    
    def update_calendar_display(self, window):
        """Update the calendar display for the current month/year"""
        # Clear existing widgets
        for widget in self.cal_frame.winfo_children():
            widget.destroy()
        
        # Create weekday headers
        weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i, day in enumerate(weekdays):
            tk.Label(
                self.cal_frame,
                text=day,
                font=('Helvetica', 10),
                width=5,
                relief=tk.RIDGE
            ).grid(row=0, column=i, sticky='nsew')
        
        # Get month calendar
        month_cal = cal.monthcalendar(self.cal_year, self.cal_month)
        
        # Add days to calendar
        for week_num, week in enumerate(month_cal, start=1):
            for day_num, day in enumerate(week):
                if day != 0:
                    day_btn = tk.Button(
                        self.cal_frame,
                        text=str(day),
                        relief=tk.RAISED,
                        command=lambda d=day: self.on_calendar_day_select(d)
                    )
                    
                    # Highlight current day
                    today = datetime.datetime.now()
                    if (day == today.day and 
                        self.cal_month == today.month and 
                        self.cal_year == today.year):
                        day_btn.config(bg='#3498db', fg='white')
                    
                    day_btn.grid(row=week_num, column=day_num, sticky='nsew', padx=1, pady=1)
        
        # Configure grid
        for i in range(7):  # columns
            self.cal_frame.grid_columnconfigure(i, weight=1)
        for i in range(len(month_cal)+1):  # rows
            self.cal_frame.grid_rowconfigure(i, weight=1)
    
    def on_calendar_day_select(self, day):
        """Handle day selection in calendar"""
        selected_date = f"{day:02d}/{self.cal_month:02d}/{self.cal_year}"
        self.add_message(f"ORBIT: Selected date: {selected_date}", 'orbit')
    
    def open_file_dialog(self):
        """Open file dialog to select and open a file"""
        file_path = filedialog.askopenfilename(
            initialdir=self.settings.get('documents_path', os.path.expanduser('~/Documents')),
            title="Select file to open",
            filetypes=(("All files", "*.*"), 
                      ("Text files", "*.txt"),
                      ("PDF files", "*.pdf"),
                      ("Images", "*.jpg *.png *.gif"))
        )
        
        if file_path:
            try:
                os.startfile(file_path)
                self.add_message(f"ORBIT: Opened file: {os.path.basename(file_path)}", 'orbit')
            except Exception as e:
                self.add_message(f"ORBIT: Error opening file: {str(e)}", 'orbit')
    
    def open_folder_dialog(self):
        """Open folder dialog to select and open a folder"""
        folder_path = filedialog.askdirectory(
            initialdir=self.settings.get('documents_path', os.path.expanduser('~/Documents')),
            title="Select folder to open"
        )
        
        if folder_path:
            try:
                os.startfile(folder_path)
                self.add_message(f"ORBIT: Opened folder: {os.path.basename(folder_path)}", 'orbit')
            except Exception as e:
                self.add_message(f"ORBIT: Error opening folder: {str(e)}", 'orbit')
    
    def show_settings(self):
        """Show enhanced settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x450")
        
        # Notebook for multiple settings tabs
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Appearance Tab
        appearance_frame = ttk.Frame(notebook)
        notebook.add(appearance_frame, text="Appearance")
        
        # Theme selection
        ttk.Label(appearance_frame, text="Theme:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        
        self.theme_var = tk.StringVar(value=self.settings['theme'])
        ttk.Radiobutton(
            appearance_frame,
            text="Light",
            variable=self.theme_var,
            value='light'
        ).grid(row=0, column=1, sticky='w')
        
        ttk.Radiobutton(
            appearance_frame,
            text="Dark",
            variable=self.theme_var,
            value='dark'
        ).grid(row=0, column=2, sticky='w')
        
        # Voice Tab
        voice_frame = ttk.Frame(notebook)
        notebook.add(voice_frame, text="Voice")
        
        self.voice_var = tk.BooleanVar(value=self.settings['voice'])
        ttk.Checkbutton(
            voice_frame,
            text="Enable Voice",
            variable=self.voice_var
        ).grid(row=0, column=0, columnspan=2, sticky='w', padx=10, pady=5)
        
        ttk.Label(voice_frame, text="Voice Speed:").grid(row=1, column=0, padx=10, pady=5, sticky='w')
        
        self.voice_rate = tk.IntVar(value=self.settings.get('voice_rate', 180))
        ttk.Scale(
            voice_frame,
            from_=100,
            to=300,
            variable=self.voice_rate,
            orient=tk.HORIZONTAL
        ).grid(row=1, column=1, padx=10, pady=5, sticky='ew')
        
        # Paths Tab
        paths_frame = ttk.Frame(notebook)
        notebook.add(paths_frame, text="Paths")
        
        # Music path
        ttk.Label(paths_frame, text="Music Folder:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        
        self.music_path_var = tk.StringVar(value=self.settings['music_path'])
        ttk.Entry(paths_frame, textvariable=self.music_path_var, width=30).grid(row=0, column=1)
        
        ttk.Button(
            paths_frame,
            text="Browse",
            command=lambda: self.browse_path(self.music_path_var, 'music_path')
        ).grid(row=0, column=2, padx=5)
        
        # Documents path
        ttk.Label(paths_frame, text="Documents Folder:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        
        self.doc_path_var = tk.StringVar(value=self.settings['documents_path'])
        ttk.Entry(paths_frame, textvariable=self.doc_path_var, width=30).grid(row=1, column=1)
        
        ttk.Button(
            paths_frame,
            text="Browse",
            command=lambda: self.browse_path(self.doc_path_var, 'documents_path')
        ).grid(row=1, column=2, padx=5)
        
        # Startup Tab
        startup_frame = ttk.Frame(notebook)
        notebook.add(startup_frame, text="Startup")
        
        self.startup_greeting_var = tk.BooleanVar(value=self.settings.get('startup_greeting', True))
        ttk.Checkbutton(
            startup_frame,
            text="Show greeting on startup",
            variable=self.startup_greeting_var
        ).grid(row=0, column=0, columnspan=2, sticky='w', padx=10, pady=5)
        
        self.word_of_day_var = tk.BooleanVar(value=self.settings.get('word_of_day', True))
        ttk.Checkbutton(
            startup_frame,
            text="Show word of the day",
            variable=self.word_of_day_var
        ).grid(row=1, column=0, columnspan=2, sticky='w', padx=10, pady=5)
        
        # Save button
        ttk.Button(
            settings_window,
            text="Save Settings",
            command=lambda: self.save_settings_from_dialog(
                settings_window,
                {
                    'theme': self.theme_var.get(),
                    'voice': self.voice_var.get(),
                    'voice_rate': self.voice_rate.get(),
                    'music_path': self.music_path_var.get(),
                    'documents_path': self.doc_path_var.get(),
                    'startup_greeting': self.startup_greeting_var.get(),
                    'word_of_day': self.word_of_day_var.get()
                }
            )
        ).pack(side=tk.BOTTOM, pady=10)
    
    def save_settings_from_dialog(self, window, new_settings):
        """Save settings from dialog and update application"""
        self.settings.update(new_settings)
        self.save_settings()
        
        # Update voice rate if changed
        if self.voice_enabled:
            self.engine.setProperty('rate', self.settings['voice_rate'])
        
        # Update theme if changed
        if new_settings['theme'] != self.settings['theme']:
            self.setup_theme()
            # Would need to update all widget colors here
        
        window.destroy()
        self.add_message("ORBIT: Settings updated", 'orbit')
    
    def browse_path(self, path_var, setting_key):
        """Browse for a directory path"""
        folder = filedialog.askdirectory(initialdir=path_var.get())
        if folder:
            path_var.set(folder)
            self.settings[setting_key] = folder
    
    def show_system_info(self):
        """Display system information"""
        mem = psutil.virtual_memory()
        system_info = f"""
        System Information:
        OS: {platform.system()} {platform.release()}
        Architecture: {platform.architecture()[0]}
        Processor: {platform.processor()}
        Memory: {mem.used//(1024**3)}GB / {mem.total//(1024**3)}GB used
        Python Version: {platform.python_version()}
        """
        messagebox.showinfo("System Info", system_info)

    def word_of_the_day(self):
        """Show word of the day"""
        words = [
            ("Serendipity", "The occurrence of events by chance in a happy way"),
            ("Ephemeral", "Lasting for a very short time"),
            ("Quintessential", "Representing the most perfect example"),
            ("Perpetual", "Never ending or changing"),
            ("Eloquence", "Fluent and persuasive speaking")
        ]
        word, definition = random.choice(words)
        self.add_message(f"ORBIT: Word of the Day - {word}: {definition}", 'orbit')

    def set_reminder(self, reminder_text, minutes):
        """Set a reminder for specified minutes"""
        def create_reminder():
            notification.notify(
                title="ORBIT Reminder",
                message=reminder_text,
                timeout=10
            )
        
        threading.Timer(minutes * 60, create_reminder).start()
        self.add_message(f"ORBIT: Reminder set for {minutes} minute(s)", 'orbit')

    def toggle_theme(self):
        """Toggle between light and dark theme"""
        current_theme = self.settings['theme']
        new_theme = 'dark' if current_theme == 'light' else 'light'
        self.settings['theme'] = new_theme
        self.save_settings()
        self.setup_theme()
        self.add_message(f"ORBIT: Switched to {new_theme} theme", 'orbit')

    def open_browser(self):
        """Open default web browser"""
        webbrowser.open("https://www.google.com")
        self.add_message("ORBIT: Opened web browser", 'orbit')

    def play_music(self):
        """Open music directory"""
        music_path = self.settings.get('music_path', os.path.expanduser('~/Music'))
        try:
            os.startfile(music_path)
            self.add_message(f"ORBIT: Opened music folder: {music_path}", 'orbit')
        except Exception as e:
            self.add_message(f"ORBIT: Error opening music folder: {str(e)}", 'orbit')

    def show_task_manager(self):
        """Show task manager window"""
        task_window = tk.Toplevel(self.root)
        task_window.title("Task Manager")
        task_window.geometry("500x400")

        # Task list
        self.task_listbox = tk.Listbox(
            task_window,
            font=('Helvetica', 12),
            selectmode=tk.SINGLE
        )
        self.task_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Populate with existing tasks
        for task in self.tasks:
            self.task_listbox.insert(tk.END, task)

        # Button frame
        button_frame = tk.Frame(task_window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        # Add task button
        tk.Button(
            button_frame,
            text="Add Task",
            command=self.add_task_dialog
        ).pack(side=tk.LEFT, padx=5)

        # Remove task button
        tk.Button(
            button_frame,
            text="Remove Task",
            command=self.remove_task
        ).pack(side=tk.LEFT, padx=5)

        # Complete task button
        tk.Button(
            button_frame,
            text="Mark Complete",
            command=self.complete_task
        ).pack(side=tk.LEFT, padx=5)

    def add_task_dialog(self):
        """Show dialog to add a new task"""
        task = simpledialog.askstring("Add Task", "Enter task description:")
        if task:
            self.tasks.append(task)
            self.task_listbox.insert(tk.END, task)
            self.save_tasks()
            self.add_message(f"ORBIT: Added task: {task}", 'orbit')

    def remove_task(self):
        """Remove selected task"""
        selection = self.task_listbox.curselection()
        if selection:
            task = self.task_listbox.get(selection)
            self.tasks.remove(task)
            self.task_listbox.delete(selection)
            self.save_tasks()
            self.add_message(f"ORBIT: Removed task: {task}", 'orbit')

    def complete_task(self):
        """Mark selected task as complete"""
        selection = self.task_listbox.curselection()
        if selection:
            task = self.task_listbox.get(selection)
            self.task_listbox.itemconfig(selection, {'bg': '#d4edda', 'fg': '#155724'})
            self.add_message(f"ORBIT: Completed task: {task}", 'orbit')

    def search_web(self, query):
        """Search the web based on query"""
        search_terms = query.replace('search', '').replace('look up', '').strip()
        if search_terms:
            url = f"https://www.google.com/search?q={search_terms.replace(' ', '+')}"
            webbrowser.open(url)
            self.add_message(f"ORBIT: Searching for: {search_terms}", 'orbit')
        else:
            self.add_message("ORBIT: Please specify what to search for", 'orbit')

    def open_application(self, app_name):
        """Open application based on name"""
        # Map common application names to their executable names
        app_map = {
            'notepad': 'notepad.exe',
            'calculator': 'calc.exe',
            'paint': 'mspaint.exe',
            'word': 'winword.exe',
            'excel': 'excel.exe',
            'powerpoint': 'powerpnt.exe',
            'chrome': 'chrome.exe',
            'firefox': 'firefox.exe',
            'edge': 'msedge.exe',
            'browser': 'chrome.exe'
        }
        
        app_name = app_name.lower()
        if app_name in app_map:
            try:
                subprocess.Popen(app_map[app_name])
                self.add_message(f"ORBIT: Opening {app_name}", 'orbit')
            except Exception as e:
                self.add_message(f"ORBIT: Error opening {app_name}: {str(e)}", 'orbit')
        else:
            self.add_message(f"ORBIT: I don't know how to open {app_name}", 'orbit')

    def get_time(self):
        """Get current time"""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.add_message(f"ORBIT: The current time is {current_time}", 'orbit')

    def get_date(self):
        """Get current date"""
        current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
        self.add_message(f"ORBIT: Today is {current_date}", 'orbit')

    def start_background_tasks(self):
        """Start background tasks like checking for reminders"""
        def check_reminders():
            # This would check for scheduled reminders and notify
            pass
        
        # Run every minute
        reminder_thread = threading.Thread(target=check_reminders, daemon=True)
        reminder_thread.start()

    def on_close(self):
        """Handle window close event"""
        if messagebox.askokcancel("Quit", "Do you want to quit ORBIT Assistant?"):
            self.save_settings()
            self.save_tasks()
            self.save_knowledge_base()
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ORBITAssistant(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()