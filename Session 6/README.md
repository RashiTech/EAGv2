# Enhanced AI Agent (EAG) V2

A sophisticated AI agent system that implements a reasoning loop through perception, decision making, action execution, and memory retention. The system uses Google's Gemini model for natural language understanding and processing.

## 🌟 Features

- **Chain of Thought Processing**: Iterative reasoning with step-by-step analysis
- **Multi-Layer Architecture**: Modular design with specialized components
- **Tool Integration**: Rich set of mathematical and system interaction tools
- **Memory Management**: Preference storage and context retention
- **Visual Interaction**: Paint application integration for drawing and text
- **Email Communication**: Built-in email notification system

## 🏗️ Architecture

The system is built on four primary layers:

### 1. Perception Layer (`perception.py`)
- Processes input queries using Gemini LLM
- Extracts key facts and context
- Handles fallback scenarios with alternative models

### 2. Decision Layer (`decision.py`)
- Parses LLM responses
- Determines appropriate actions
- Validates function calls and parameters

### 3. Action Layer (`action.py`)
- Executes mathematical operations
- Handles system interactions (Paint, Email)
- Provides reasoning and verification tools

### 4. Memory Layer (`memory.py`)
- Stores user preferences
- Maintains conversation context
- Supports persistent state management

## 🛠️ Available Tools

### Mathematical Operations
- Basic arithmetic (`add`, `subtract`, `multiply`, `divide`)
- Advanced math (`power`, `sqrt`, `cbrt`, `factorial`, `log`)
- Trigonometry (`sin`, `cos`, `tan`)
- List operations (`add_list`, `strings_to_chars_to_int`, `int_list_to_exponential_sum`)
- Sequence generation (`fibonacci_numbers`)

### System Interaction
- Paint operations (`open_paint`, `draw_rectangle`, `add_text_in_paint`)
- Email communication (`send_email`)
- Reasoning display (`show_reasoning`)
- Calculation and verification (`calculate`, `verify`)

## 🚀 Getting Started

### Prerequisites
```bash
# Install required dependencies
pip install -r requirements.txt
```

### Environment Setup
Create a `.env` file with:
```env
GEMINI_API_KEY=your_api_key_here
GMAIL_APP_PASSWORD=your_app_password_here  # For email functionality
```

### Running the System
```bash
python main.py
```

## 💡 Example Usage

```python
# Sample query
query = """Find the ASCII values of characters in INDIA and then return sum 
          of exponentials of those values. After that, Open Microsoft paint, 
          then draw a rectangle with 607, 425, 940, 619 coordinates, then use 
          the final answer to add text in paint. At last, send email with the 
          final answer."""

# The system will:
1. Extract ASCII values from "INDIA"
2. Calculate exponential sums
3. Interact with Paint
4. Send email notification
```

## 🔄 Processing Flow

1. **Input Processing**
   - Query received and parsed
   - Facts extracted using Gemini

2. **Decision Making**
   - LLM generates next action
   - Response parsed into function calls

3. **Action Execution**
   - Tools executed based on decisions
   - Results validated and verified

4. **Memory Management**
   - User preferences maintained
   - Context preserved across iterations

## 📝 Logging

The system maintains detailed logs in:
- `logs/cot_process.log`: Chain of thought processing
- `logs/mcp_server.log`: Model communication protocol

## ⚙️ Configuration

Key configuration files:
- `pyproject.toml`: Project metadata and dependencies
- `.env`: Environment variables and API keys

## 🔒 Security Notes

- API keys should be stored securely in `.env`
- Email functionality requires Gmail app-specific password
- System permissions needed for Paint interaction

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.