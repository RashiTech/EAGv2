
import asyncio
import yaml
import os

from mcp_servers.multiMCP import MultiMCP
from agent.agent_loop3 import AgentLoop
from pprint import pprint

# Assuming .env setup is required for MultiMCP or other components
from dotenv import load_dotenv
load_dotenv()

BANNER = """
──────────────────────────────────────────────────────
🔸  Agentic Query Assistant  🔸
Type your question and press Enter.
Type 'exit' or 'quit' to leave.
──────────────────────────────────────────────────────
"""

async def interactive() -> None:
    print(BANNER)
    print("Loading MCP Servers...")
    
    # Load MCP server configurations
    config_path = "config/mcp_server_config.yaml"
    if not os.path.exists(config_path):
        print(f"Error: MCP server config file not found at {config_path}")
        return

    with open(config_path, "r") as f:
        profile = yaml.safe_load(f)
        mcp_servers_list = profile.get("mcp_servers", [])
        configs = list(mcp_servers_list)

    # Initialize MultiMCP
    multi_mcp = MultiMCP(server_configs=configs)
    await multi_mcp.initialize()
    
    # Initialize the new AgentLoop, passing the multi_mcp instance
    loop = AgentLoop(
        perception_prompt_path="prompts/perception_prompt.txt",
        decision_prompt_path="prompts/decision_prompt.txt",
        multi_mcp=multi_mcp,
        strategy="exploratory")
    
    print("MCP Servers loaded. Ready to chat.\n")

    while True:
        query = input("🟢  You: ").strip()
        if query.lower() in {"exit", "quit"}:
            print("👋  Goodbye!")
            break

        # The new AgentLoop.run_loop directly returns the final response string
        response = await loop.run(query)
        print(f"🔵 Agent: {response}\n")

        follow = input("\n\nContinue? (press Enter) or type 'exit': ").strip()
        if follow.lower() in {"exit", "quit"}:
            print("👋  Goodbye!")
            break

if __name__ == "__main__":
    asyncio.run(interactive())
