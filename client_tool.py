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
import threading
import queue
from pathlib import Path
import datetime
import tkinter as tk
from tkinter import Canvas, Entry, Scrollbar, Label, Frame
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = ("""
                    You are an expert SonarQube assistant.
                    Your role is to provide the user with clear and concise answers related to SonarQube metrics and projects.
                    After executing a tool, summarize the results in a straightforward manner,
                    without using any markdown formatting such as asterisks or other punctuation for emphasis.
                    When listing all project, ensure that there is a space between each project. 
                    Ensure the output is easy to read and well-structured, with each metric presented on its own line,
                    followed by a space before the next metric and *NO duplicated projects*.
                    
                """ )

class ChatBackend:
    def __init__(self, input_queue, output_queue):
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]

        if "GEMINI_API_KEY" in os.environ:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=os.environ.get("GEMINI_API_KEY"),
            )
        elif "OPENAI_API_KEY" in os.environ:
            self.llm = ChatOpenAI(model="gpt-4o")
        else:
            print("GEMINI_API_KEY or a OPENAI_API_KEY is missing")
        self.server_script = Path(__file__).with_name("server.py")
        self.server_params = StdioServerParameters(
            command="python",
            args=[str(self.server_script)],
            env=os.environ,
        )

    async def chat_loop(self):
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                self.agent = create_react_agent(self.llm, tools)

                self.output_queue.put(
                    (
                        "AI",
                        "Hi, I'm ArchAI assistant, how can I help you with SonarQube?",
                    )
                )

                while True:
                    text = await asyncio.to_thread(self.input_queue.get)
                    if text.lower() in {"exit", "quit"}:
                        break
                    self.history.append({"role": "user", "content": text})
                    result = await self.agent.ainvoke({"messages": self.history})
                    ai_msg = result["messages"][-1].content
                    self.history.append({"role": "assistant", "content": ai_msg})
                    self.output_queue.put(("AI", ai_msg))

    def run(self):
        asyncio.run(self.chat_loop())


class ChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ArchAI-Chat")
        self.root.configure(bg="#E8F7FF")  # light blue background
        self.root.rowconfigure(1, weight=1)
        self.root.geometry("500x500")
        self.root.columnconfigure(0, weight=1)

        header = Label(
            root,
            text="ArchAI-SonarQube Chat",
            font=("Segoe UI", 16, "bold"),
            bg="#34B7F1",
            fg="white",
        )
        header.grid(row=0, column=0, sticky="ew")

        # canvas frame
        frame = Frame(root, bg="#E8F7FF")
        frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.canvas = Canvas(frame, bg="#E8F7FF", bd=0, highlightthickness=0)
        self.scrollbar = Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.scrollable = Frame(self.canvas, bg="#E8F7FF")
        self.canvas.create_window((0, 0), window=self.scrollable, anchor="nw")
        self.scrollable.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        # input frame
        input_frame = Frame(root, bg="#E8F7FF")
        input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        input_frame.columnconfigure(0, weight=1)

        self.input_entry = Entry(input_frame, font=("Segoe UI", 12))
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.input_entry.bind("<Return>", self.send_message)
        send_btn = tk.Button(
            input_frame,
            text="Send",
            command=self.send_message,
            bg="#34B7F1",
            fg="white",
            font=("Segoe UI", 11),
        )
        send_btn.grid(row=0, column=1)

        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()

        threading.Thread(target=self._start_backend, daemon=True).start()
        self.root.after(100, self._poll_responses)

    def _start_backend(self):
        ChatBackend(self.input_queue, self.output_queue).run()

    def send_message(self, event=None):
        text = self.input_entry.get().strip()
        if not text:
            return
        self._add_message("You", text)
        self.input_queue.put(text)
        self.input_entry.delete(0, "end")

    def _poll_responses(self):
        while not self.output_queue.empty():
            sender, msg = self.output_queue.get()
            self._add_message("AI", msg)
        self.root.after(100, self._poll_responses)

    def _add_message(self, sender, text):
        # timestamp
        now = datetime.datetime.now().strftime("%H:%M")
        # bubble
        bg = "#D0EDFF" if sender == "You" else "#FFFFFF"
        bubble = Frame(self.scrollable, bg=bg, padx=12, pady=8)
        Label(
            bubble, text=f"{sender} ({now})", font=("Segoe UI", 8, "italic"), bg=bg
        ).pack(anchor="w")
        Label(
            bubble,
            text=text,
            font=("Segoe UI", 11),
            bg=bg,
            wraplength=360,
            justify="left",
        ).pack(anchor="w")
        anchor = "e" if sender == "You" else "w"
        bubble.pack(anchor=anchor, pady=4)
        self.canvas.yview_moveto(1.0)


if __name__ == "__main__":
    root = tk.Tk()
    ChatGUI(root)
    root.mainloop()
