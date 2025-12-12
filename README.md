# Enterprise Triage Assistant - MCP Server

A comprehensive Model Context Protocol (MCP) server demonstrating enterprise-grade patterns for ticket triage and support management. Built with FastMCP and ready for cloud deployment.

## 🚀 Features

### **Tools (Actions)**
- `create_ticket` - Create new support tickets with Pydantic validation
- `update_ticket_status` - Update ticket status with error handling
- `search_knowledge_base` - Search knowledge base articles by keywords

### **Resources (Data Reading)**
- `system://health` - System health status and metrics
- `system://ticket_queue` - JSON list of all open tickets
- `system://logs` - Last 5 server activity logs

### **Prompts (Templates)**
- `triage_expert` - Senior Support Engineer prompt template

## 📋 Requirements

- Python 3.8+
- fastmcp
- pydantic

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/sherry-royal/demo-triage-mcp.git
cd demo-triage-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 🏃 Running Locally

```bash
python server.py
```

Or using FastMCP CLI:

```bash
fastmcp run server.py
```

The server will start and be available for MCP client connections.

## ☁️ Deploying to FastMCP Cloud

This server is ready for deployment to [FastMCP Cloud](https://fastmcp.cloud):

1. **Push to GitHub** (this repository)
2. **Connect to FastMCP Cloud**:
   - Visit [fastmcp.cloud](https://fastmcp.cloud)
   - Sign in with GitHub
   - Select this repository
   - Deploy!

FastMCP Cloud will automatically:
- Detect `server.py` as the entry point
- Install dependencies from `requirements.txt`
- Provide an HTTPS endpoint
- Handle authentication and scaling

## 📖 Usage Examples

### Creating a Ticket

```python
# Via MCP client
result = await client.call_tool("create_ticket", {
    "title": "API Rate Limiting Issue",
    "priority": "HIGH",
    "description": "Users experiencing 429 errors"
})
```

### Reading Resources

```python
# Get ticket queue
tickets = await client.read_resource("system://ticket_queue")

# Get system health
health = await client.read_resource("system://health")

# Get logs
logs = await client.read_resource("system://logs")
```

### Using Prompts

```python
# Get triage expert prompt
prompt = await client.get_prompt("triage_expert")
```

## 🏗️ Architecture

- **State Management**: In-memory database with pre-populated tickets
- **Validation**: Pydantic models for type safety
- **Error Handling**: Graceful error responses with helpful messages
- **Logging**: Activity tracking with configurable log retention
- **Type Safety**: Full type hints throughout

## 📝 Pre-populated Data

The server initializes with 3 sample tickets:
- **HIGH Priority**: System Outage - Payment Processing Down
- **LOW Priority**: Feature Request - Dark Mode
- **MEDIUM Priority**: Login Page Loading Slowly

## 🔧 Configuration

The server uses standard Python logging. Configure via environment variables:

```bash
export LOG_LEVEL=INFO
```

## 📄 License

MIT License - feel free to use this as a template for your own MCP servers!

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a pull request.

---

