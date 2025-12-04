# Agentic Flow (Session 10)

This repository hosts the latest iteration of our multi-agent reasoning loop. The flow stitches together **Perception → Decision → Execution → Evaluation → Memory** with strong guardrails so the agent returns the exact artifact the user asked for (headlines, metrics, code snippets, etc.) without chasing redundant tool calls.

## Top-Level Architecture

| Stage | File(s) | Responsibility |
| --- | --- | --- |
| Perception | `perception/perception_new.py`, `prompts/perception_prompt.txt` | Convert the raw query or a step result into a structured ERORLL snapshot (entities, required result type, goal status, confidence). |
| Decision | `decision/decision_new.py`, `prompts/decision_prompt.txt` | Build/adjust a short plan, emit the next actionable step, and enforce data-fidelity guardrails (immediate conclusion once the artifact exists, never retry failed tools). |
| Execution | `action/executor.py` (called via `run_user_code`) | Runs the planner’s code block/tools in the Multi-MCP sandbox and returns stdout+metadata. |
| Session Orchestration | `agent/agent_loop3.py` | Drives the loop: memory recall → perception → decision → execution → perception feedback → plan update → memory log. |
| Memory | `memory/memory_search.py`, `memory/session_log.py` | Supplies few-shot context before each run and stores every session (plan versions, tool outputs, final answers). |

## Lifecycle (AgentLoop v3)

1. **Session bootstrap**  
   `agent_loop3.AgentLoop.run()` creates a session, prints the live trace, and queries vector memories that match the prompt.
2. **Perception snapshot**  
   Perception consumes the query + relevant memories and emits ERORLL JSON. If `original_goal_achieved = true`, the loop ends here with that answer.
3. **Initial plan**  
   Decision receives `{plan_mode: "initial", planning_strategy, original_query, perception}` and returns:  
   - `plan_text`: 1‑3 natural-language steps  
   - the first actionable step (CODE/CONCLUDE/NOP) with executable code if needed
4. **Execution + evaluation**  
   - For each CODE step, the executor runs the plan’s code under Multi-MCP.  
   - Perception re-interprets the tool output (`snapshot_type = "step_result"`).  
   - The loop checks:
     - `original_goal_achieved →` mark session complete immediately.  
     - `local_goal_achieved →` request the next step from Decision.  
     - Otherwise → trigger replanning.
5. **Replanning**  
   `agent_loop3` forwards **all completed steps across plan versions**, the current plan, and `step_failed` flag into Decision. The planner must either issue a new CODE step, conclude, or ask for clarification.
6. **Memory logging**  
   Every perception snapshot, plan version, and final answer is persisted via `memory/session_log.py` so future sessions can cite prior work.

## Guardrails & Best Practices

- **Exact artifact delivery**: The decision prompt explicitly forbids “metadata-only” answers. If the query was “top AI summits,” returning only URLs is invalid—fetch or deduce the actual list. Conversely, once that artifact exists anywhere in the working context, planners must skip remaining retrieval steps and conclude.
- **Failed tool handling**: As soon as a tool (e.g., `convert_webpage_url_into_markdown`) errors, Decision must not call it again in that session. Switch to an alternative (RAG search, different API) or summarize the best available snippets.
- **Perception fidelity**: Perception outputs structured ERORLL JSON with aligned `result_requirement`, dual reasoning (global vs local), and “Not ready yet” when the original goal is unresolved.
- **Plan discipline**: Decision emits at most three steps, chains multiple sub-operations inside a single CODE block, and never relies on state from previous steps—everything must be recomputed or re-fetched.

## Running the Agent

```powershell
uv run main_new.py
```

> The CLI walks through each step interactively, showing plan versions, tool executions, perception snapshots, and final answers. Sessions are written to `memory/session_logs/<date>/<session-id>.json`.

## Customizing the Flow

- **Prompts**: Edit `prompts/perception_prompt.txt` and `prompts/decision_prompt.txt` to change reasoning style, guardrails, or output schemas.
- **Loop variants**: `agent_loop3.py` is the recommended orchestrator. `agent_loop2.py` remains for comparison/testing but still contains debug hooks (`pdb.set_trace`) and lacks the newer failure-handling logic.
- **Tooling**: Add or remove MCP tools via `mcp_servers/multiMCP.py` and `config/mcp_server_config.yaml`. Every tool must be invoked through planner-generated code.
- **Memory control**: Adjust how many recent failures are kept in `GLOBAL_PREVIOUS_FAILURE_STEPS` or provide custom retrieval heuristics in `memory/memory_search.py`.

## Key Takeaways for Builders

- Treat Perception as the “single source of truth” for whether a step helped and what the user still needs.
- Treat Decision as a disciplined planner: short plans, aggressive intra-step chaining, and no repetition of failed actions.
- Treat AgentLoop v3 as the conductor: it keeps the pipeline honest, logs everything, and ensures the loop halts the moment the requested artifact is ready.

With these layers working together, the agent delivers fast, reliable answers without wasting tool calls or hallucinating conclusions.

