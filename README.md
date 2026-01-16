# Smart Tool Agent

An autonomous AI agent with dynamic tool creation capabilities. The agent can create, modify, and use Python tools at runtime to accomplish any task.

## Features

- **Plan-and-Execute Architecture**: Breaks down tasks into steps, executes them sequentially
- **Dynamic Tool Creation**: Creates new tools on-the-fly when needed
- **Self-Healing**: Automatically detects and fixes broken tools
- **Omnipotent Mindset**: Never says "I cannot" - creates tools to solve any problem

## Quick Start

### 1. Clone and setup virtual environment

```bash
git clone https://github.com/klatort/smart-tool-agent.git
cd smart-tool-agent

python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Create a `.env` file in the root directory:

```env
API_KEY=your_api_key_here
API_URL=https://your-api-endpoint/v2/chat/completions
MODEL_ID=your-model-id
```

### 4. Run the agent

```bash
python main.py
```

## Project Structure

```
├── main.py                 # Entry point
├── src/
│   ├── agent/              # Main agent orchestrator
│   ├── config/             # Settings and environment
│   ├── managers/           # Conversation management
│   ├── parsers/            # Stream and tool call parsing
│   ├── tools/              # Built-in tools
│   │   └── auto/           # Auto-generated tools (gitignored)
│   └── utils/              # Utilities (logging, sandbox)
├── requirements.txt
└── .env                    # API configuration (not committed)
```

## Built-in Tools

- `read_file`, `write_file` - File operations
- `create_tool`, `update_tool`, `remove_tool` - Tool management
- `web_search` - DuckDuckGo search
- `install_package` - pip package installation
- `create_plan`, `mark_step_complete`, `task_complete` - Planning

## License

MIT
