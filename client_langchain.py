import logging

loggers_to_silence = [
    "pydantic",
    "pydantic_core",
    "langchain",
    "langchain_core",
    "langchain_community",
    "langchain_google_genai",
    "langgraph",
    "langchain_mcp_adapters",
    "mcp",
    "httpx",
]
for logger_name in loggers_to_silence:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
#from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()

#enter your model provider (OpenAI or Gemini)

#llm = ChatOpenAI(model="gpt-4o")

llm =ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", google_api_key=os.environ.get("GEMINI_API_KEY"),
    )

server_script = Path(__file__).with_name("server.py")

server_params = StdioServerParameters(
    command="python",
    args=[str(server_script)],
    env=os.environ,
)
async def main() -> None:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(llm, tools)

            history = []
            system_prompt = (
                "You are an expert SonarQube assistant. "
                "You have access to these tools:\n"
                "- get_status: performs a health check on the SonarQube server.\n"
                "- get_sonarqube_metrics: retrieves current metrics (bugs, vulnerabilities, code smells, coverage, duplicated lines density) for a specified project.\n"
                "- get_sonarqube_metrics_history: fetches historical metric data over a given date range.\n"
                "- get_sonarqube_component_tree_metrics: retrieves metrics for every component (file/directory) in a project, handling pagination automatically.\n"
                "- list_projects: lists all accessible SonarQube projects, with optional filtering by name or key.\n"
                "- get_project_issues: fetches project issues (BUG, CODE_SMELL, VULNERABILITY, etc.), filterable by type, severity, and resolution status.\n"
                "When responding, choose the most appropriate tool and format the call as valid JSON. "
                "After executing the tool, provide the user with a clear, concise summary of the results."
            )

            history.append({"role": "system", "content": system_prompt})
            print("Hi, I'm ArchAI assistent, How can I help you with SonarQube?\n")

            while True:
                user_text = input("> ").strip()
                if user_text.lower() in {"exit", "quit"}:
                    break

                history.append({"role": "user", "content": user_text})
                result = await agent.ainvoke({"messages": history})
                ai_msg = result["messages"][-1].content
                print(ai_msg)
                history.append({"role": "assistant", "content": ai_msg})

if __name__ == "__main__":
    asyncio.run(main())
