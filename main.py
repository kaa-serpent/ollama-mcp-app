import sys
import os
import json
import threading
from typing import Dict, List, Optional
from dotenv import load_dotenv

from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QTextEdit, QLineEdit, QPushButton, QComboBox, 
                             QWidget, QLabel, QSplitter, QFrame,
                             QProgressBar, QMessageBox, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QTextCursor

from ollama_manager import OllamaManager
from mcp_client import MCPClient

load_dotenv()

class WorkerThread(QThread):
    """Thread for running background tasks"""
    output_signal = pyqtSignal(str, str)  # message, type
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, task_type, **kwargs):
        super().__init__()
        self.task_type = task_type
        self.kwargs = kwargs
        
    def run(self):
        try:
            if self.task_type == "ollama":
                self.run_ollama_task()
            elif self.task_type == "file_then_ollama":
                self.run_file_then_ollama_task()
            elif self.task_type == "test_ollama":
                self.run_test_ollama_task()
        except Exception as e:
            self.finished_signal.emit(False, str(e))
    
    def run_ollama_task(self):
        manager = self.kwargs['manager']
        prompt = self.kwargs['prompt']
        model = self.kwargs['model']
        
        def progress_callback(progress):
            self.progress_signal.emit(progress)
            
        success, result = manager.generate_response(
            prompt, model, progress_callback
        )
        self.finished_signal.emit(success, result)
    
    def run_file_then_ollama_task(self):
        """Read file first, then use result with Ollama"""
        client = self.kwargs['client']
        file_path = self.kwargs['file_path']
        manager = self.kwargs['manager']
        ollama_prompt = self.kwargs['ollama_prompt']
        model = self.kwargs['model']
        
        # Step 1: Read file
        self.output_signal.emit(f"Reading file: {file_path}", "system")
        success, file_content = client.read_file(file_path)
        
        if not success:
            self.output_signal.emit(f"File read error: {file_content}", "error")
            self.finished_signal.emit(False, file_content)
            return
            
        self.output_signal.emit(f"File content ({len(file_content)} characters read)", "system")
        
        # Step 2: Use file content with Ollama
        enhanced_prompt = f"{ollama_prompt}\n\nDocument content:\n```\n{file_content}\n```"
        
        self.output_signal.emit(f"Sending to Ollama with model: {model}", "system")
        
        def progress_callback(progress):
            self.progress_signal.emit(progress)
            
        success, ollama_result = manager.generate_response(
            enhanced_prompt, model, progress_callback
        )
        
        if success:
            self.output_signal.emit(f"Analysis Result: {ollama_result}", "ollama")
        else:
            self.output_signal.emit(f"Ollama Error: {ollama_result}", "error")
            
        self.finished_signal.emit(success, ollama_result)

    def run_test_ollama_task(self):
        """Test Ollama connection with a simple prompt"""
        manager = self.kwargs['manager']
        model = self.kwargs['model']
        
        self.output_signal.emit(f"Testing Ollama with model: {model}", "system")
        
        def progress_callback(progress):
            self.progress_signal.emit(progress)
            
        # Use a simple test prompt
        test_prompt = "Please respond with just 'OK' to confirm you're working."
        success, result = manager.generate_response(
            test_prompt, model, progress_callback
        )
        
        if success:
            self.output_signal.emit(f"Test successful: {result}", "system")
        else:
            self.output_signal.emit(f"Test failed: {result}", "error")
            
        self.finished_signal.emit(success, result)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ollama_manager = OllamaManager()
        self.mcp_client = MCPClient()
        self.current_worker = None
        self.init_ui()
        self.load_models()
        
    def init_ui(self):
        self.setWindowTitle("Ollama + File Analysis")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Create tabs
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Chat tab
        chat_tab = QWidget()
        self.setup_chat_tab(chat_tab)
        tab_widget.addTab(chat_tab, "Chat & File Analysis")
        
        # File Operations tab
        file_tab = QWidget()
        self.setup_file_tab(file_tab)
        tab_widget.addTab(file_tab, "File Tools")
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress_bar)
        
    def setup_chat_tab(self, parent):
        layout = QVBoxLayout(parent)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Model selection
        controls_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(200)
        controls_layout.addWidget(self.model_combo)
        
        # Refresh models button
        self.refresh_btn = QPushButton("Refresh Models")
        self.refresh_btn.clicked.connect(self.load_models)
        controls_layout.addWidget(self.refresh_btn)
        
        # Test Ollama button
        self.test_ollama_btn = QPushButton("Test Ollama")
        self.test_ollama_btn.clicked.connect(self.test_ollama)
        controls_layout.addWidget(self.test_ollama_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Model info
        model_info_layout = QHBoxLayout()
        self.model_info_label = QLabel("Recommended: Use smaller models like 'phi3:mini' for faster responses")
        self.model_info_label.setStyleSheet("color: gray; font-style: italic;")
        model_info_layout.addWidget(self.model_info_label)
        model_info_layout.addStretch()
        layout.addLayout(model_info_layout)
        
        # Splitter for chat and output
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # Chat area
        chat_frame = QFrame()
        chat_frame.setFrameStyle(QFrame.StyledPanel)
        chat_layout = QVBoxLayout(chat_frame)
        
        chat_layout.addWidget(QLabel("Chat:"))
        self.chat_input = QTextEdit()
        self.chat_input.setMaximumHeight(100)
        self.chat_input.setPlaceholderText("Enter your prompt here...\nExamples:\n- 'Analyze test.txt'\n- 'Summarize workspace/document.md'\n- 'What does C:\\path\\to\\file.txt contain?'")
        chat_layout.addWidget(self.chat_input)
        
        chat_buttons_layout = QHBoxLayout()
        self.send_btn = QPushButton("Send to Ollama")
        self.send_btn.clicked.connect(self.send_to_ollama)
        chat_buttons_layout.addWidget(self.send_btn)
        
        self.file_chat_btn = QPushButton("Analyze File with Ollama")
        self.file_chat_btn.clicked.connect(self.analyze_file_with_ollama)
        chat_buttons_layout.addWidget(self.file_chat_btn)
        
        chat_buttons_layout.addStretch()
        chat_layout.addLayout(chat_buttons_layout)
        
        splitter.addWidget(chat_frame)
        
        # Output area
        output_frame = QFrame()
        output_frame.setFrameStyle(QFrame.StyledPanel)
        output_layout = QVBoxLayout(output_frame)
        
        output_layout.addWidget(QLabel("Output:"))
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_text)
        
        # Clear output button
        clear_btn = QPushButton("Clear Output")
        clear_btn.clicked.connect(self.output_text.clear)
        output_layout.addWidget(clear_btn)
        
        splitter.addWidget(output_frame)
        
        # Set splitter proportions
        splitter.setSizes([200, 600])
        
    def setup_file_tab(self, parent):
        layout = QVBoxLayout(parent)
        
        # File operation section
        file_layout = QVBoxLayout()
        
        file_layout.addWidget(QLabel("File Path:"))
        self.file_path_input = QLineEdit()
        self.file_path_input.setText(r"C:\Users\Sico\Documents\IA\ollama-mcp-app\workspace\test.txt")
        self.file_path_input.setPlaceholderText(r"Enter full file path (e.g., C:\Users\Sico\Documents\IA\ollama-mcp-app\workspace\test.txt)")
        file_layout.addWidget(self.file_path_input)
        
        # Test file button
        test_btn = QPushButton("Use Test File")
        test_btn.clicked.connect(self.use_test_file)
        file_layout.addWidget(test_btn)
        
        # Operation buttons
        buttons_layout = QHBoxLayout()
        
        self.read_file_btn = QPushButton("Read File")
        self.read_file_btn.clicked.connect(self.read_file_direct)
        buttons_layout.addWidget(self.read_file_btn)
        
        self.analyze_file_btn = QPushButton("Analyze File with Ollama")
        self.analyze_file_btn.clicked.connect(self.analyze_file_direct)
        buttons_layout.addWidget(self.analyze_file_btn)
        
        file_layout.addLayout(buttons_layout)
        
        # Quick test section
        quick_test_layout = QVBoxLayout()
        quick_test_layout.addWidget(QLabel("Quick Tests:"))
        
        test_buttons_layout = QHBoxLayout()
        
        test1_btn = QPushButton("Test: Read test.txt")
        test1_btn.clicked.connect(lambda: self.test_file_operation("read"))
        test_buttons_layout.addWidget(test1_btn)
        
        test2_btn = QPushButton("Test: Analyze test.txt")
        test2_btn.clicked.connect(lambda: self.test_file_operation("analyze"))
        test_buttons_layout.addWidget(test2_btn)
        
        quick_test_layout.addLayout(test_buttons_layout)
        file_layout.addLayout(quick_test_layout)
        
        layout.addLayout(file_layout)
        layout.addStretch()
        
    def use_test_file(self):
        """Set the file path to the test file"""
        test_path = r"C:\Users\Sico\Documents\IA\ollama-mcp-app\workspace\test.txt"
        self.file_path_input.setText(test_path)
        
    def test_file_operation(self, operation_type):
        """Test file operations with the test file"""
        test_path = r"C:\Users\Sico\Documents\IA\ollama-mcp-app\workspace\test.txt"
        self.file_path_input.setText(test_path)
        
        if operation_type == "read":
            self.read_file_direct()
        else:
            self.analyze_file_direct()
    
    def test_ollama(self):
        """Test Ollama connection with selected model"""
        model = self.model_combo.currentText()
        if not model:
            QMessageBox.warning(self, "Error", "Please select a model first")
            return
            
        self.current_worker = WorkerThread(
            "test_ollama",
            manager=self.ollama_manager,
            model=model
        )
        self.connect_worker_signals()
        self.current_worker.start()
        
    def load_models(self):
        """Load available Ollama models"""
        self.status_label.setText("Loading models...")
        self.refresh_btn.setEnabled(False)
        self.test_ollama_btn.setEnabled(False)
        
        def load_models_thread():
            success, models = self.ollama_manager.get_available_models()
            return success, models
            
        thread = threading.Thread(target=lambda: self.handle_model_load(load_models_thread()))
        thread.start()
        
    def handle_model_load(self, result):
        success, models = result
        if success:
            self.model_combo.clear()
            self.model_combo.addItems(models)
            
            # Select a smaller model by default if available
            small_models = [m for m in models if any(name in m.lower() for name in ['phi3', 'llama2', 'mistral', 'gemma'])]
            if small_models:
                self.model_combo.setCurrentText(small_models[0])
                
            self.status_label.setText(f"Loaded {len(models)} models")
        else:
            self.status_label.setText("Failed to load models")
            QMessageBox.warning(self, "Error", f"Failed to load models: {models}")
            
        self.refresh_btn.setEnabled(True)
        self.test_ollama_btn.setEnabled(True)
            
    def send_to_ollama(self):
        """Send prompt directly to Ollama"""
        prompt = self.chat_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Input Error", "Please enter a prompt")
            return
            
        model = self.model_combo.currentText()
        if not model:
            QMessageBox.warning(self, "Input Error", "Please select a model")
            return
            
        self.append_output(f">> User: {prompt}\n", "user")
        self.chat_input.clear()
        
        # Start worker thread
        self.current_worker = WorkerThread(
            "ollama",
            manager=self.ollama_manager,
            prompt=prompt,
            model=model
        )
        self.connect_worker_signals()
        self.current_worker.start()
        
    def analyze_file_with_ollama(self):
        """Analyze file with Ollama based on chat input"""
        prompt = self.chat_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Input Error", "Please enter a prompt")
            return
            
        model = self.model_combo.currentText()
        if not model:
            QMessageBox.warning(self, "Input Error", "Please select a model")
            return
            
        self.append_output(f">> User: {prompt}\n", "user")
        self.chat_input.clear()
        
        # Extract file path from prompt or use default
        file_path = self.extract_file_path_from_prompt(prompt)
        if not file_path:
            # Use the test file as default
            file_path = r"C:\Users\Sico\Documents\IA\ollama-mcp-app\workspace\test.txt"
            
        ollama_prompt = self.extract_processing_prompt(prompt)
        
        # Check if file exists
        if not os.path.exists(file_path):
            self.append_output(f">> Error: File not found: {file_path}\n", "error")
            return
            
        # Use direct file read approach
        self.current_worker = WorkerThread(
            "file_then_ollama",
            client=self.mcp_client,
            file_path=file_path,
            manager=self.ollama_manager,
            ollama_prompt=ollama_prompt,
            model=model
        )
        self.connect_worker_signals()
        self.current_worker.start()
        
    def extract_file_path_from_prompt(self, prompt):
        """Extract file path from user prompt"""
        import re
        
        # Windows paths
        windows_path = re.search(r'[A-Za-z]:[\\/](?:[^\\/\s]+[\\/])*[^\\/\s]+', prompt)
        if windows_path:
            return windows_path.group(0)
            
        # Unix-like paths
        unix_path = re.search(r'/(?:[^/\s]+/)*[^/\s]+', prompt)
        if unix_path:
            return unix_path.group(0)
            
        # Relative paths or filenames
        if any(ext in prompt.lower() for ext in ['.txt', '.md', '.py', '.json', '.csv']):
            file_match = re.search(r'[\w\-\_]+\.\w+', prompt)
            if file_match:
                filename = file_match.group(0)
                # Check if it exists in current directory
                if os.path.exists(filename):
                    return filename
                # Check in workspace
                workspace_path = os.path.join(os.getcwd(), 'workspace', filename)
                if os.path.exists(workspace_path):
                    return workspace_path
                    
        return None
        
    def extract_processing_prompt(self, prompt):
        """Extract the processing instruction from prompt"""
        prompt_lower = prompt.lower()
        
        if 'summar' in prompt_lower:
            return "Please provide a clear and concise summary of the following document. Focus on the main content and purpose:"
        elif 'analyze' in prompt_lower or 'analysis' in prompt_lower:
            return "Please analyze the following document and provide key insights. Describe what the document is about and its main purpose:"
        elif 'explain' in prompt_lower:
            return "Please explain the following document in simple terms:"
        elif 'what' in prompt_lower and 'contain' in prompt_lower:
            return "What does this document contain? Please describe its content and purpose:"
        else:
            return "Please analyze the following document and describe its content and purpose:"
            
    def read_file_direct(self):
        """Read file directly"""
        file_path = self.file_path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "Input Error", "Please enter a file path")
            return
            
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Error", f"File not found: {file_path}")
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.append_output(f">> File content of {file_path}:\n{content}\n", "system")
            self.status_label.setText(f"Successfully read file ({len(content)} characters)")
            
        except Exception as e:
            self.append_output(f">> Error reading file: {str(e)}\n", "error")
            self.status_label.setText("File read failed")
        
    def analyze_file_direct(self):
        """Read file and process with Ollama"""
        file_path = self.file_path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "Input Error", "Please enter a file path")
            return
            
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Error", f"File not found: {file_path}")
            return
            
        model = self.model_combo.currentText()
        if not model:
            QMessageBox.warning(self, "Input Error", "Please select a model")
            return
            
        self.current_worker = WorkerThread(
            "file_then_ollama",
            client=self.mcp_client,
            file_path=file_path,
            manager=self.ollama_manager,
            ollama_prompt="Please analyze the following document and provide a clear summary of its content and purpose:",
            model=model
        )
        self.connect_worker_signals()
        self.current_worker.start()
        
    def connect_worker_signals(self):
        """Connect signals for the current worker"""
        if self.current_worker:
            self.current_worker.output_signal.connect(self.append_output)
            self.current_worker.progress_signal.connect(self.update_progress)
            self.current_worker.finished_signal.connect(self.task_finished)
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.set_ui_enabled(False)
            
    def append_output(self, message, message_type):
        """Append message to output with appropriate formatting"""
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Color coding based on message type
        if message_type == "user":
            formatted_message = f'<span style="color: blue; font-weight: bold;">{message}</span>'
        elif message_type == "ollama":
            formatted_message = f'<span style="color: green;">{message}</span>'
        elif message_type == "system":
            formatted_message = f'<span style="color: gray; font-style: italic;">{message}</span>'
        elif message_type == "error":
            formatted_message = f'<span style="color: red; font-weight: bold;">{message}</span>'
        else:
            formatted_message = message
            
        self.output_text.append(formatted_message)
        
        # Auto-scroll to bottom
        cursor.movePosition(QTextCursor.End)
        self.output_text.setTextCursor(cursor)
        
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
        
    def task_finished(self, success, result):
        """Handle task completion"""
        self.progress_bar.setVisible(False)
        self.set_ui_enabled(True)
        
        if not success:
            self.status_label.setText("Task failed")
        else:
            self.status_label.setText("Task completed")
            
        self.current_worker = None
        
    def set_ui_enabled(self, enabled):
        """Enable/disable UI elements during operations"""
        self.send_btn.setEnabled(enabled)
        self.file_chat_btn.setEnabled(enabled)
        self.read_file_btn.setEnabled(enabled)
        self.analyze_file_btn.setEnabled(enabled)
        self.refresh_btn.setEnabled(enabled)
        self.test_ollama_btn.setEnabled(enabled)
        
    def closeEvent(self, event):
        """Handle application close"""
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.terminate()
            self.current_worker.wait()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
