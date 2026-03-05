"""Airbnb MCP Server."""

import sys
import os
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from dotenv import load_dotenv
import base_tools
from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio
import time
from IPython.display import Markdown, display

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

chat_openrouter = ChatOpenAI(
    api_key=API_KEY,
    base_url= "https://openrouter.ai/api/v1",
    model="gpt-4.1-nano"
)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


AIRBNB_PROMPT = """
You are a travel planning assistant.

Instructions:
- Search Airbnb listings immediately when user asks for accommodations
- Use defaults: adults=2, no dates if not specified
- Present top 5 results with link: https://www.airbnb.com/rooms/{listing_id}
- Use web_search for attractions, events, or travel info
- Use get_weather to check destination weather
- Be proactive, don't ask for details unless search fails
- Always include the price per night for the results
"""

async def get_tools():
    client = MultiServerMCPClient(
        {
            "airbnb": {
                "command": "cmd.exe",
                "args": [
                    "/c",
                    "npx",
                    "-y", 
                    "@openbnb/mcp-server-airbnb", 
                    "--ignore-robots-txt"
                ],
                "transport": "stdio",
            }
        }
    )
    mcp_tools = await client.get_tools()

    tools = mcp_tools + [base_tools.web_search, base_tools.get_weather]

    print(f"Loaded {len(mcp_tools)} Tools")
    
    #print(f"Tools Available\n{mcp_tools}")

    return tools


async def hotel_search(query):
    tools = await get_tools()

    agent = create_agent(
        model=chat_openrouter,
        tools=tools,
        system_prompt=AIRBNB_PROMPT
    )
    result = await agent.ainvoke(
        {'messages': [HumanMessage(query)]}
    )

    response = result['messages'][-1].text
    print(f"AI: {response}\n")

async def ask():
    print("\nChat mode started. Type 'q' or 'quit'")
    while True:
        query = input("You: ").strip()
        print()
        if query.lower() == 'q' or query.lower() == 'quit':
            print("Exiting chat mode...")
            break
            
        await hotel_search(query=query)


if __name__ == "__main__":
    asyncio.run(ask())