# Cortex-R Agent Architecture

This document outlines the architecture of the Cortex-R agent, a modular and extensible system designed to perceive, plan, and execute tasks using a variety of tools.

## 1. Introduction

The Cortex-R agent operates on a perceive-plan-act loop, leveraging a multi-tool orchestration framework (MCP) to interact with external capabilities. It maintains a detailed memory of its interactions and adapts its behavior based on user input and execution results.

## 2. Core Components

The agent's functionality is distributed across several key components:

### 2.1. `AgentLoop` (core/loop.py)

The `AgentLoop` is the orchestrator of the agent's behavior. It manages the execution flow, including:
-   **Perception:** Gathers relevant context and recent memory items.
-   **Planning:** Generates a plan (often Python code) based on the current context and available tools.
-   **Execution:** Runs the generated plan, typically within a sandboxed environment.
-   **Iteration:** Continues the loop until a final answer is produced or an error occurs.

### 2.2. `AgentContext` (core/context.py)

The `AgentContext` holds all session-specific state and data, providing a centralized hub for:
-   **User Input:** Stores the original user query and any overrides.
-   **Agent Profile:** Defines the agent's persona and strategy.
-   **MemoryManager:** Provides access to the session's memory.
-   **Dispatcher (`MultiMCP`):** The interface for calling external tools.
-   **Session ID & Progress:** Tracks the current session and task progress.

### 2.3. `MemoryManager` (modules/memory.py)

The `MemoryManager` is responsible for persistent storage and retrieval of session interactions. It:
-   **Loads/Saves:** Handles loading and saving memory items to a JSON file.
-   **Adds Items:** Appends new `MemoryItem` objects (tool calls, tool outputs, final answers, run metadata) to the session's history.
-   **MemoryItem:** A Pydantic model defining the structure of each memory entry (timestamp, type, text, tool_name, tool_args, tool_result, final_answer, success, tags, metadata).

### 2.4. `MultiMCP` (core/session.py)

`MultiMCP` acts as the agent's tool dispatcher. It:
-   **Discovers Tools:** Scans configured MCP servers to identify available tools.
-   **Routes Tool Calls:** Directs tool calls to the appropriate MCP server.
-   **Stateless Operation:** Reconnects to servers per tool call, ensuring clean sessions.

### 2.5. `run_python_sandbox` (modules/action.py)

This asynchronous function is crucial for executing agent-generated Python code safely. It:
-   **Creates a Sandbox:** Isolates the execution environment to prevent unintended side effects.
-   **Patches MCP Client:** Injects a `SandboxMCP` instance into the sandbox, allowing the sandboxed code to call tools through the main `MultiMCP` dispatcher.
-   **Logs Tool Calls/Outputs:** Records all tool calls and their results made within the sandbox to the session memory.
-   **Executes `solve()`:** Dynamically executes the `solve()` function defined in the agent's plan.

## 3. Data Flow and Execution

The agent's typical execution flow is as follows:

1.  **User Input:** The `main` function in `agent.py` takes user input.
2.  **Context Initialization:** An `AgentContext` is created, initializing the `MemoryManager` and `MultiMCP` (dispatcher).
3.  **AgentLoop Start:** An `AgentLoop` is instantiated with the `AgentContext` and starts its `run()` method.
4.  **Perception & Planning:** The `AgentLoop` gathers perception (current observations) and memory, then uses a decision model to generate a `plan` (Python code containing a `solve()` function).
5.  **Sandbox Execution:** If the plan contains a `solve()` function, it's executed within `run_python_sandbox`.
6.  **Tool Calls within Sandbox:** The `solve()` function can make calls to `mcp.call_tool()`. These calls are intercepted by `SandboxMCP`, which forwards them to the actual `MultiMCP` dispatcher.
7.  **Tool Execution:** `MultiMCP` routes the tool calls to the relevant MCP servers (e.g., `mcp_server_1.py`, `mcp_server_3.py`).
8.  **Result Handling:** The `run_python_sandbox` function captures the result of the `solve()` function.
    -   If the result is `FINAL_ANSWER:`, the loop terminates with the final answer.
    -   If the result is `FURTHER_PROCESSING_REQUIRED:`, the `user_input_override` in `AgentContext` is updated, and the loop continues with the next step.
    -   If a `[sandbox error:]` occurs or the result is uncategorized, the loop terminates with an error message.
9.  **Memory Updates:** Throughout this process, `MemoryItem` objects are added to the `MemoryManager` to record all significant events (run metadata, tool calls, tool outputs, final answers).

## 4. Configuration

The agent's behavior and available MCP servers are configured in `config/profiles.yaml`. This file specifies the `mcp_servers` and their associated scripts and working directories.

<img width="500" height="749" alt="image" src="https://github.com/user-attachments/assets/3cdd9c03-83c0-4c0c-9fc6-1b06ae1ef14a" />
