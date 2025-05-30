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
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from pathlib import Path
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp.client.sse import sse_client

load_dotenv()

if "GEMINI_API_KEY" in os.environ:
    self.llm = ChatGoogleGenerativeAI(
        model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
        google_api_key=os.environ.get("GEMINI_API_KEY"),
    )
elif "OPENAI_API_KEY" in os.environ:
    self.llm = ChatOpenAI(model=os.environ.get("OPENAI_MODEL", "gpt-4o"))
elif "GROQ_API_KEY" in os.environ:
    self.llm = ChatGroq(
        model=os.environ.get("GROQ_MODEL", "gemma2-9b-it"),
        temperature=0.7,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )
elif "AZURE_OPENAI_API_KEY" and "AZURE_OPENAI_ENDPOINT" in os.environ:
    self.llm = AzureChatOpenAI(
        azure_deployment=os.environ.get(
            "AZURE_DEPLOYMENT", "gpt-4o"
        ),  # or your deployment
        api_version=os.environ.get("AZURE_API_VERSION"),
        temperature=0.7,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )
else:
    print("Provider _API_KEY is missing")


async def main() -> None:
    transport = os.environ.get("TRANSPORT")
    if transport == "sse":
        client_cm = sse_client("http://localhost:8001/sse")
    else:
        server_script = Path(__file__).with_name("server.py")
        server_params = StdioServerParameters(
            command="python",
            args=[str(server_script)],
            env=os.environ,
        )
        client_cm = stdio_client(server_params)

    async with client_cm as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(llm, tools)

            history = []
            system_prompt = """
            You are an expert SonarQube assistant.
            Your role is to provide the user with clear and concise answers related to SonarQube metrics and projects.
            After executing a tool, summarize the results in a straightforward manner,
            without using any markdown formatting such as asterisks or other punctuation for emphasis.

            When listing the project, ensure that there is a space between the different project and delete duplicates.
            Ensure the output is easy to read and well-structured, with each metric presented on its own line,
            followed by a space before the next metric and *NO duplicated projects*.

            """

            history.append({"role": "system", "content": system_prompt})
            print("Hi, I'm ArchAI assistant, How can I help you with SonarQube?\n")

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
