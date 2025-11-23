import os
import json
from typing import Dict, List, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MCPServer:
    def __init__(self):
        self.workspace_dir = "/app/workspace"
        
    def list_tools(self) -> Dict[str, Any]:
        """List available MCP tools"""
        return {
            "tools": [
                {
                    "name": "read_file",
                    "description": "Read contents of a file",
                    "parameters": {
                        "file_path": {"type": "string", "description": "Path to the file"}
                    }
                },
                {
                    "name": "write_file", 
                    "description": "Write content to a file",
                    "parameters": {
                        "file_path": {"type": "string", "description": "Path to the file"},
                        "content": {"type": "string", "description": "Content to write"}
                    }
                },
                {
                    "name": "list_directory",
                    "description": "List contents of a directory",
                    "parameters": {
                        "directory_path": {"type": "string", "description": "Path to directory", "optional": True}
                    }
                },
                {
                    "name": "create_directory",
                    "description": "Create a new directory",
                    "parameters": {
                        "directory_path": {"type": "string", "description": "Path to new directory"}
                    }
                },
                {
                    "name": "web_search",
                    "description": "Perform a web search",
                    "parameters": {
                        "query": {"type": "string", "description": "Search query"}
                    }
                }
            ]
        }
    
    def read_file(self, file_path: str) -> str:
        """Read file contents"""
        try:
            # Security: Ensure the path stays within workspace
            full_path = os.path.normpath(os.path.join(self.workspace_dir, file_path))
            if not full_path.startswith(os.path.abspath(self.workspace_dir)):
                return "Error: Access outside workspace is not allowed"
                
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: File not found: {file_path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def write_file(self, file_path: str, content: str) -> str:
        """Write content to file"""
        try:
            # Security: Ensure the path stays within workspace
            full_path = os.path.normpath(os.path.join(self.workspace_dir, file_path))
            if not full_path.startswith(os.path.abspath(self.workspace_dir)):
                return "Error: Access outside workspace is not allowed"
                
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"
    
    def list_directory(self, directory_path: str = "") -> str:
        """List directory contents"""
        try:
            full_path = os.path.normpath(os.path.join(self.workspace_dir, directory_path))
            if not full_path.startswith(os.path.abspath(self.workspace_dir)):
                return "Error: Access outside workspace is not allowed"
                
            items = os.listdir(full_path)
            result = {
                "path": directory_path,
                "items": []
            }
            
            for item in items:
                item_path = os.path.join(full_path, item)
                item_info = {
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file"
                }
                result["items"].append(item_info)
                
            return json.dumps(result)
        except Exception as e:
            return f"Error listing directory: {str(e)}"
    
    def create_directory(self, directory_path: str) -> str:
        """Create a new directory"""
        try:
            full_path = os.path.normpath(os.path.join(self.workspace_dir, directory_path))
            if not full_path.startswith(os.path.abspath(self.workspace_dir)):
                return "Error: Access outside workspace is not allowed"
                
            os.makedirs(full_path, exist_ok=True)
            return f"Successfully created directory {directory_path}"
        except Exception as e:
            return f"Error creating directory: {str(e)}"
    
    def web_search(self, query: str) -> str:
        """Perform web search (mock implementation)"""
        # This is a mock implementation
        # In a real scenario, you'd integrate with a search API like DuckDuckGo or Google
        mock_results = [
            f"Result 1 for: {query}",
            f"Result 2 for: {query}", 
            f"Result 3 for: {query}"
        ]
        return json.dumps({
            "query": query,
            "results": mock_results
        })

mcp_server = MCPServer()

@app.get("/")
async def root():
    return {"message": "MCP Server is running", "status": "healthy"}

@app.get("/tools")
async def list_tools():
    return mcp_server.list_tools()

@app.post("/tools/read_file")
async def read_file(request: Dict[str, str]):
    file_path = request.get('file_path', '')
    if not file_path:
        raise HTTPException(status_code=400, detail="file_path is required")
    return {"result": mcp_server.read_file(file_path)}

@app.post("/tools/write_file") 
async def write_file(request: Dict[str, str]):
    file_path = request.get('file_path', '')
    content = request.get('content', '')
    if not file_path or not content:
        raise HTTPException(status_code=400, detail="file_path and content are required")
    return {"result": mcp_server.write_file(file_path, content)}

@app.post("/tools/list_directory")
async def list_directory(request: Dict[str, str] = None):
    directory_path = request.get('directory_path', '') if request else ''
    return {"result": mcp_server.list_directory(directory_path)}

@app.post("/tools/create_directory")
async def create_directory(request: Dict[str, str]):
    directory_path = request.get('directory_path', '')
    if not directory_path:
        raise HTTPException(status_code=400, detail="directory_path is required")
    return {"result": mcp_server.create_directory(directory_path)}

@app.post("/tools/web_search")
async def web_search(request: Dict[str, str]):
    query = request.get('query', '')
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    return {"result": mcp_server.web_search(query)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)