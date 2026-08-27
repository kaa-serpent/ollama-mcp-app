<p align="center">
  <img src="docs/assets/portfolio-preview.jpg" alt="Ollama MCP GUI — local model chat and file analysis" width="100%">
</p>

# Ollama MCP GUI

![Application Screenshot](Capture.JPG)

This project provides a graphical user interface (GUI) for interacting with local Ollama models and performing file analysis. It also includes a server component for handling file system operations in a containerized environment.

## Features

- **Ollama Integration**: Connect to a local Ollama instance to run large language models.
- **Model Management**: List available Ollama models and switch between them.
- **Chat Interface**: A simple chat interface to send prompts to Ollama models.
- **File Analysis**: Read local files and use their content in prompts to be analyzed by Ollama.
- **Dockerized Server**: The file operations are handled by a separate FastAPI server running in a Docker container.

## Project Structure

- `main.py`: The main PyQt5 GUI application.
- `ollama_manager.py`: A class to manage interactions with the Ollama API.
- `mcp_client.py`: A client to interact with the file operations server.
- `mcp-server/`: Contains the FastAPI server for file operations.
  - `mcp_server.py`: The FastAPI application.
  - `Dockerfile`: Dockerfile for the server.
- `docker-compose.yml`: Docker Compose file to build and run the `mcp-server`.
- `workspace/`: A directory mounted into the Docker container for file operations.

## Setup and Installation

### Prerequisites

- [Python 3.8+](https://www.python.org/downloads/)
- [Docker](https://www.docker.com/products/docker-desktop/)
- [Ollama](https://ollama.ai/) installed and running on your local machine.

### 1. Install Python Dependencies

Install the required Python packages for the GUI client:

```bash
.\env\Scripts\activate

pip install -r requirements.txt
```

### 2. Build and Run the MCP Server

The file operation server runs in a Docker container. Use Docker Compose to build and start the server:

```bash
docker-compose up --build -d
```

This command will:
- Build the Docker image for the `mcp-server`.
- Start a container named `mcp-server`.
- Mount the local `./workspace` directory into the container at `/app/workspace`.
- Expose the server on port 8000.

### 3. Run the GUI Application

Once the MCP server is running, you can start the GUI application:

```bash
python main.py
```

## How to Use

1.  **Start Ollama**: Make sure your local Ollama instance is running.
2.  **Start the MCP Server**: Use `docker-compose up --build -d`.
3.  **Launch the GUI**: Run `python main.py`.
4.  **Select a Model**: The application will automatically load the available Ollama models. Select one from the dropdown menu.
5.  **Chat with Ollama**: Type your prompt in the chat input box and click "Send to Ollama".
6.  **Analyze Files**:
    - Place the files you want to analyze in the `workspace` directory.
    - Use the "File Tools" tab to read files directly.
    - In the "Chat & File Analysis" tab, you can reference a file in your prompt (e.g., "Summarize test.txt") and click "Analyze File with Ollama". The application will read the file and send its content along with your prompt to the selected Ollama model.
## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
