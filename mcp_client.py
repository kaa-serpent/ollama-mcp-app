import os
import glob
from typing import Dict, Tuple, Any

class MCPClient:
    def __init__(self):
        pass
        
    def check_connection(self) -> Tuple[bool, str]:
        """Check if file operations are available"""
        return True, "File operations are available"
            
    def execute_command(self, command: str, args: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute file operations using Python"""
        try:
            if command == "list_tools":
                return True, "Available tools: read_file, write_file, list_directory, create_directory"
                
            elif command == "read_file":
                file_path = args.get('file_path', '')
                if not file_path:
                    return False, "File path is required"
                return self.read_file(file_path)
                
            elif command == "write_file":
                file_path = args.get('file_path', '')
                content = args.get('content', '')
                if not file_path or not content:
                    return False, "File path and content are required"
                return self.write_file(file_path, content)
                
            elif command == "list_directory":
                dir_path = args.get('directory_path', '.')
                return self.list_directory(dir_path)
                
            elif command == "create_directory":
                dir_path = args.get('directory_path', '')
                if not dir_path:
                    return False, "Directory path is required"
                return self.create_directory(dir_path)
                
            elif command == "web_search":
                query = args.get('query', '')
                if not query:
                    return False, "Search query is required"
                return self.web_search(query)
                
            else:
                return False, f"Unknown command: {command}"
                
        except Exception as e:
            return False, f"Error executing command: {str(e)}"

    def read_file(self, file_path: str) -> Tuple[bool, str]:
        """Read file using Python file operations"""
        try:
            # Handle both absolute paths and relative to workspace
            if not os.path.isabs(file_path):
                # Assume it's relative to workspace directory
                workspace_dir = os.path.join(os.getcwd(), 'workspace')
                file_path = os.path.join(workspace_dir, file_path)
            
            # Normalize path
            file_path = os.path.normpath(file_path)
            
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}"
                
            if not os.path.isfile(file_path):
                return False, f"Path is not a file: {file_path}"
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            return True, content
            
        except PermissionError:
            return False, f"Permission denied: {file_path}"
        except Exception as e:
            return False, f"Error reading file {file_path}: {str(e)}"

    def write_file(self, file_path: str, content: str) -> Tuple[bool, str]:
        """Write file using Python file operations"""
        try:
            # Handle both absolute paths and relative to workspace
            if not os.path.isabs(file_path):
                # Assume it's relative to workspace directory
                workspace_dir = os.path.join(os.getcwd(), 'workspace')
                file_path = os.path.join(workspace_dir, file_path)
            
            # Normalize path
            file_path = os.path.normpath(file_path)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return True, f"Successfully wrote to {file_path}"
            
        except Exception as e:
            return False, f"Error writing file {file_path}: {str(e)}"

    def list_directory(self, directory_path: str) -> Tuple[bool, str]:
        """List directory contents"""
        try:
            # Handle both absolute paths and relative to workspace
            if not os.path.isabs(directory_path):
                # Assume it's relative to workspace directory
                workspace_dir = os.path.join(os.getcwd(), 'workspace')
                directory_path = os.path.join(workspace_dir, directory_path)
            
            # Normalize path
            directory_path = os.path.normpath(directory_path)
            
            if not os.path.exists(directory_path):
                return False, f"Directory not found: {directory_path}"
                
            if not os.path.isdir(directory_path):
                return False, f"Path is not a directory: {directory_path}"
                
            items = os.listdir(directory_path)
            result = {
                "path": directory_path,
                "items": []
            }
            
            for item in items:
                item_path = os.path.join(directory_path, item)
                item_info = {
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0
                }
                result["items"].append(item_info)
                
            import json
            return True, json.dumps(result, indent=2)
            
        except Exception as e:
            return False, f"Error listing directory {directory_path}: {str(e)}"

    def create_directory(self, directory_path: str) -> Tuple[bool, str]:
        """Create a directory"""
        try:
            # Handle both absolute paths and relative to workspace
            if not os.path.isabs(directory_path):
                # Assume it's relative to workspace directory
                workspace_dir = os.path.join(os.getcwd(), 'workspace')
                directory_path = os.path.join(workspace_dir, directory_path)
            
            # Normalize path
            directory_path = os.path.normpath(directory_path)
            
            os.makedirs(directory_path, exist_ok=True)
            return True, f"Successfully created directory {directory_path}"
            
        except Exception as e:
            return False, f"Error creating directory {directory_path}: {str(e)}"

    def web_search(self, query: str) -> Tuple[bool, str]:
        """Mock web search implementation"""
        # This is a mock implementation
        # In a real scenario, you'd integrate with a search API
        mock_results = [
            f"Result 1 for: {query}",
            f"Result 2 for: {query}", 
            f"Result 3 for: {query}"
        ]
        import json
        return True, json.dumps({
            "query": query,
            "results": mock_results
        })