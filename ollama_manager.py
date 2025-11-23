import requests
import json
import subprocess
import time
from typing import List, Tuple, Callable, Optional

class OllamaManager:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        
    def get_available_models(self) -> Tuple[bool, List[str]]:
        """Get list of available Ollama models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                return True, models
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to Ollama. Make sure it's running on localhost:11434"
        except Exception as e:
            return False, str(e)
            
    def generate_response(self, prompt: str, model: str,
                         progress_callback: Optional[Callable] = None) -> Tuple[bool, str]:
        """Generate response from Ollama with better timeout handling"""
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more focused responses
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            if progress_callback:
                progress_callback(25)
                
            # Use a timeout that scales with model size
            timeout = 120 if "30b" in model.lower() or "70b" in model.lower() else 60
            
            response = requests.post(url, json=payload, timeout=timeout)
            
            if progress_callback:
                progress_callback(75)
                
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '').strip()
                
                # Clean up the response
                response_text = self.clean_response_text(response_text)
                
                if progress_callback:
                    progress_callback(100)
                    
                return True, response_text
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
                
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to Ollama. Make sure it's running on localhost:11434"
        except requests.exceptions.Timeout:
            return False, f"Request to Ollama timed out after {timeout} seconds. Try a smaller model like 'phi3:mini' or 'llama2'."
        except Exception as e:
            return False, str(e)
    
    def clean_response_text(self, text: str) -> str:
        """Clean and format the response text"""
        if not text:
            return text
            
        # Remove excessive code blocks if they don't make sense for the response
        lines = text.split('\n')
        cleaned_lines = []
        in_code_block = False
        code_block_lines = []
        
        for line in lines:
            stripped_line = line.strip()
            
            # Check for code block start/end
            if stripped_line.startswith('```'):
                if in_code_block:
                    # End of code block - check if this code block was useful
                    if len(code_block_lines) > 2:  # If it has actual content
                        cleaned_lines.extend(['```'] + code_block_lines + ['```'])
                    code_block_lines = []
                    in_code_block = False
                else:
                    in_code_block = True
                    code_block_lines = []
            elif in_code_block:
                code_block_lines.append(line)
            else:
                # Regular text line
                if stripped_line and not stripped_line.isspace():
                    cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines)
        
        # If the response is mostly code but we wanted analysis, simplify
        if 'def ' in result and 'class ' in result and len(result) > 500:
            # This looks like generated code, try to extract the meaningful part
            sentences = result.split('. ')
            if sentences:
                # Take the first few sentences that don't look like code
                meaningful = [s for s in sentences if not ('def ' in s or 'class ' in s or 'import ' in s)]
                if meaningful:
                    result = '. '.join(meaningful[:3]) + '.'
        
        return result
            
    def pull_model(self, model_name: str) -> Tuple[bool, str]:
        """Pull a model if not available"""
        try:
            result = subprocess.run(
                ['ollama', 'pull', model_name],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                return True, f"Successfully pulled {model_name}"
            else:
                return False, result.stderr
        except subprocess.TimeoutExpired:
            return False, "Model pull timeout"
        except Exception as e:
            return False, str(e)

    def test_connection(self) -> Tuple[bool, str]:
        """Test connection to Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                return True, "Ollama is running and accessible"
            else:
                return False, f"Ollama returned HTTP {response.status_code}"
        except Exception as e:
            return False, f"Cannot connect to Ollama: {str(e)}"