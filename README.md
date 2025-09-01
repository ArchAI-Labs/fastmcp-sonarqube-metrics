# FastMCP SonarQube Metrics

[![Trust Score](https://archestra.ai/mcp-catalog/api/badge/quality/ArchAI-Labs/fastmcp-sonarqube-metrics)](https://archestra.ai/mcp-catalog/archai-labs__fastmcp-sonarqube-metrics)

[![smithery badge](https://smithery.ai/badge/@ArchAI-Labs/fastmcp-sonarqube-metrics)](https://smithery.ai/server/@ArchAI-Labs/fastmcp-sonarqube-metrics)

![logo](https://github.com/ArchAI-Labs/fastmcp-sonarqube-metrics/blob/main/img/logo.png)

## Overview

This project provides a set of tools for retrieving information about SonarQube projects using the FastMCP (Fast Model Context Protocol) framework. It serves as an interface to SonarQube, allowing users to programmatically access metrics, historical data, and component tree metrics for specified projects. This automated access enables reporting, analysis, and integration of SonarQube data with other systems.

The project distinguishes itself by offering a simplified, message-based approach to interacting with the SonarQube API, abstracting away the complexities of direct API calls and data handling. It's designed for developers, DevOps engineers, and analysts who need to incorporate SonarQube data into their workflows or build custom reporting solutions.

This repository specifically houses the client and server components that facilitate communication and data retrieval. The server exposes tools to fetch data from SonarQube, while the client provides a command-line interface for users to invoke these tools and display the results. Each internal module contributes to this goal by encapsulating specific functionalities, such as API interaction, data processing, and client-server communication.

The client included in the project is only for testing how the code works; we recommend using [Claude Desktop](https://claude.ai/download) or developing your own custom client.

> ***REMEMBER, THIS REPO IS WORK IN PROGRESS, SOME FEATURES MAY NOT BE PERFECT.***

## Supported MCP Tools

* `get_status`: Performs a health check on the configured SonarQube instance.
* `create_sonarqube_project`: Creates a new SonarQube project.  Requires administrator privileges.
* `delete_sonarqube_project`: Deletes a SonarQube project.  Requires administrator privileges. **USE WITH CAUTION!**
* `list_projects`: Lists all accessible SonarQube projects, optionally filtered by name or key.
* `get_sonarqube_metrics`: Retrieves specified metrics (bugs, vulnerabilities, code smells, coverage, duplication density) for a given SonarQube project key.
* `get_sonarqube_metrics_history`: Retrieves historical metrics (bugs, vulnerabilities, code smells, coverage, duplication density) for a given SonarQube project using /api/measures/search_history. Optional date filters can be applied.
* `get_sonarqube_component_tree_metrics`: Retrieves metric values for all components (e.g., files or directories) in a project using /api/measures/component_tree Automatically handles pagination to retrieve all results.
* `get_project_issues`: Fetch SonarQube issues for a given project, optionally filtered by type, severity, and resolution status. Returns up to *limit* results (default: 10).

## Technology Stack

*   **Language:** Python
*   **Frameworks:** FastMCP
*   **Libraries:** httpx, pydantic, dotenv, asyncio, json, pathlib, typing, base64
*   **Tools:** SonarQube API

## Directory Structure

```
├── client_test.py - Client application for testing and interacting with the server.
├── server.py - Server application exposing tools to retrieve SonarQube metrics.
├── client_tool.py - Client with a graphical interface to interact with the SonarQube server.
├── client_langchain.py - Command-line client to interact with the FastMCP server and SonarQube tools via LangChain
├── .env - Environment configuration file (stores SonarQube URL and token).
└── README.md - Project documentation.
```

## Getting Started

### Prerequisites

*   Python 3.7+
*   SonarQube instance with API access
*   A SonarQube API token with appropriate permissions
*   FastMCP installed (`pip install fastmcp`)
*   httpx installed (`pip install httpx`)
*   pydantic installed (`pip install pydantic`)
*   python-dotenv installed (`pip install python-dotenv`)

### General Build Steps

1.  **Clone the repository:** `git clone <repository_url>`
2.  **Navigate to the project directory:** `cd fastmcp-sonarqube-metrics`
3.  **Set up environment variables:** Create a `.env` file in the project root directory with the following content:

    ```
    SONARQUBE_URL=<your_sonarqube_url>
    SONARQUBE_TOKEN=<your_sonarqube_token>
    TRANSPORT=<stdio or sse>
    GEMINI_API_KEY=<your-gemini-api_key>
    GEMINI_MODEL=<your-gemini-model> (Optional)
    ```

    The schema is the same for *OpenAI* and *Groq*, if you want to use *AzureOpenAI*:

    ```
    SONARQUBE_URL=<your_sonarqube_url>
    SONARQUBE_TOKEN=<your_sonarqube_token>
    TRANSPORT=<stdio or sse>
    AZURE_OPENAI_API_KEY=<your-azureopenai-api_key>
    AZURE_OPENAI_ENDPOINT=<your-azureopenai-endpoint>
    AZURE_DEPLOYMENT=<your-azureopenai-deployment>
    AZURE_API_VERSION=<your-azureopenai-api_version>
    ```

    Replace `<your_sonarqube_url>` with the URL of your SonarQube instance (e.g., `http://localhost:9000`) and `<your_sonarqube_token>` with your SonarQube API token.
4.  **Run the server:** `python server.py`
5.  **Run the client:** `python client_test.py` *(Optionally, only for test)*
6.  **Connect to your client:** follow the [official documentation](https://modelcontextprotocol.io/quickstart/user#windows)

### Installing via Smithery

To install FastMCP SonarQube Metrics for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@ArchAI-Labs/fastmcp-sonarqube-metrics):

```bash
npx -y @smithery/cli install @ArchAI-Labs/fastmcp-sonarqube-metrics --client claude
```

### Module Usage

#### Server (`server.py`)

The `server.py` module defines the FastMCP server that exposes tools for retrieving SonarQube metrics. It initializes the server, loads environment variables, defines the available tools, and handles communication with the SonarQube API. To use the server, you need to set the `SONARQUBE_URL` and `SONARQUBE_TOKEN` environment variables. The server is started by running the `server.py` script directly.

#### Client (`client_test.py`)

The `client_test.py` module defines the FastMCP client that interacts with the server. It prompts the user for a SonarQube project key, connects to the server, invokes the `get_sonarqube_metrics` and `get_sonarqube_component_tree_metrics` tools, and displays the results. To use the client, you need to run the `client_test.py` script directly and provide a valid SonarQube project key when prompted and set the transport type in the .env file to *stdio*.

#### Client_tool (`client_tool.py`)
The `client_tool.py` module implements the FastMCP client with a Tkinter-based graphical interface to interact with the SonarQube server. On startup, it configures loggers to suppress non-essential messages, loads environment variables, and launches the chat backend (ChatBackend) in the background, which uses an LLM and the MCP tools exposed by the server via stdio. The frontend (ChatGUI) manages the Tkinter window, displays the message history in a scrollable area, and allows the user to send commands to the server—prompting for a valid SonarQube project key when needed. To use the client, simply run the `client_tool.py` script and interact through the GUI.

#### Client_langchain (`client_langchain.py`)
The `client_langchain.py` module provides a command-line client to interact with the FastMCP server and SonarQube tools via LangChain. On startup, it loads environment variables, and configures the chosen LLM. It establishes a stdio connection to the server (`server.py`), initializes the MCP session, and loads available tools (health check, current and historical metrics, project listing, issue retrieval). A detailed system prompt describes each tool and its parameters. In an interactive loop, it reads user input from the console, updates the message history, invokes the React agent, and prints the formatted response.

### Example: Integrating the `get_sonarqube_metrics` tool in an external project

To use the `get_sonarqube_metrics` tool in an external project, you can create a client that connects to the FastMCP server and invokes the tool. Here's a basic example:

```python
import asyncio
from fastmcp import Client
from fastmcp.types import TextContent

async def get_metrics(project_key: str):
    server_path = "server.py" # Adjust if necessary
    client = Client(server_path)
    try:
        async with client:
            result = await client.call_tool(
                "get_sonarqube_metrics", {"project_key": project_key}
            )
            if result:
                content = result[0]
                if isinstance(content, TextContent):
                    metrics = json.loads(content.text)
                    print(metrics)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(get_metrics("your-project-key")) # Replace with your project key
```

This example demonstrates how to create a client, connect to the server, invoke the `get_sonarqube_metrics` tool with a project key, and process the results. You would need to adapt the `server_path` variable to the actual location of the `server.py` script in your environment.



## ArchAI-SonarQube Chat (GUI)

A lightweight Tkinter client that connects over stdio to the FastMCP server and exposes a real-time chat interface for querying SonarQube metrics, browsing component trees and running health checks via an LLM-driven assistant.

<br>

![img_tool](https://github.com/ArchAI-Labs/fastmcp-sonarqube-metrics/blob/main/img/img_tool.png)

<br>

## Usage with TRANSPORT=SSE
You can switch the client’s transport layer to Server-Sent Events (SSE) by setting the `TRANSPORT` environment variable before launching the GUI. This enables real-time, uni-directional updates from the FastMCP server.
When the server is started in SSE mode, a persistent HTTP connection is opened on port **8001**. This allows you to connect via compatible interfaces such as MCP Inspector.*

1. **Start the server in SSE mode**  
    ```bash
   uv run mcp dev "<server_name>" 
   ```
2. **Open MCP Inspector**
   A link (e.g. `http://127.0.0.1:6274`) will be provided to launch MCP Inspector in your browser.
3. **Configure SSE in MCP Inspector**

   * Select **SSE** as the transport type
   * Enter the URL: `http://localhost:8001/sse`

4. **Initiate the connection**

5. **Browse available tools**
   In the **Tools** section you will see:

   * `get_status`
   * `get_sonarqube_metrics`
   * `get_sonarqube_metrics_history`
   * `get_sonarqube_component_tree_metrics`
   * `list_projects`
   * `get_project_issues`

6. **Select and invoke a tool**
   For example, choose **get\_project\_issues** and provide:

   * `project_key`: the SonarQube project key
   * `issue_type` (optional): e.g. `BUG`, `CODE_SMELL`
   * `severity` (optional): e.g. `MAJOR`, `CRITICAL`
   * `resolved` (optional): `true` or `false`
   * `limit` (optional): maximum number of issues to return

7. **Execute and retrieve results**
   The server will call the appropriate SonarQube API and return a formatted JSON response.

## Usage with Claude Desktop

You can install this server directly into Claude Desktop using fastmcp:

1. Make sure FastMCP is installed (pip install fastmcp or uv pip install fastmcp).
2. Configure Claude for Desktop for whichever MCP servers you want to use (in Windows using VSCode): `code $env:AppData\Claude\claude_desktop_config.json`
3. Add your server and then save:

```json
{
    "mcpServers": {
        "fastmcp-sonarqube-metrics": {
            "command": "uv",
            "args": [
                "--directory",
                "/ABSOLUTE/PATH/TO/PARENT/FOLDER/fastmcp-sonarqube-metrics",
                "run",
                "server.py"
            ]
        }
    }
}
```

4. To launch it by running:

```bash
 uv --directory  /ABSOLUTE/PATH/TO/PARENT/FOLDER/fastmcp-sonarqube-metrics run server.py
```

5. Restart Claude Desktop if it was running. The *"FastMCP SonarQube Metrics"* tool should now be available.

<br>

![claude](https://github.com/ArchAI-Labs/fastmcp-sonarqube-metrics/blob/main/img/img_claude_desktop.png)

<br>

## Functional Analysis

### 1. Main Responsibilities of the System

The system's primary responsibility is to act as a bridge between a user and the SonarQube API, providing a simplified way to retrieve project quality metrics. It encapsulates the complexities of the SonarQube API, offering a set of tools that can be easily invoked and integrated into automated workflows. The core services include fetching metrics, retrieving historical data, and exploring component-level metrics within a SonarQube project. The foundational service is the FastMCP server, which manages the tool definitions and client-server communication.

### 2. Problems the System Solves

The system solves the problem of programmatically accessing SonarQube data without requiring users to directly interact with the SonarQube API. It addresses the need for automated reporting, analysis, and integration of SonarQube metrics with other systems. Specifically, it simplifies tasks such as:

*   Generating regular reports on code quality metrics.
*   Monitoring trends in code quality over time.
*   Identifying problematic components within a project.
*   Integrating SonarQube data with other development tools.

The architecture solves these problems by providing a set of well-defined tools that abstract away the complexities of the SonarQube API and provide a consistent interface for accessing data.

### 3. Interaction of Modules and Components

The system consists of two main components: the client and the server. The client initiates requests to the server, specifying the tool to be executed and any input parameters. The server receives the request, interacts with the SonarQube API, processes the data, and sends the results back to the client.

The interaction between the client and server is facilitated by the FastMCP framework, which handles message passing and serialization. The server defines the available tools using the `@mcp.tool()` decorator, which registers the functions as callable endpoints. The client invokes these tools using the `client.call_tool()` method, which sends a message to the server with the tool name and input parameters.

The server uses the `httpx` library to make asynchronous HTTP requests to the SonarQube API. It constructs the API URLs and request parameters based on the tool being executed and the input parameters provided by the client. The server then parses the JSON responses from the SonarQube API and extracts the relevant metric values.

### 4. User-Facing vs. System-Facing Functionalities

The user-facing functionality of the system is the client application (`client_test.py`), which provides a command-line interface for invoking the SonarQube metric retrieval tools. Users interact with the client by providing a SonarQube project key and, optionally, other parameters such as date ranges or metric keys. The client then displays the retrieved metrics in a human-readable format.

The system-facing functionalities are the server-side tools (`get_sonarqube_metrics`, `get_sonarqube_metrics_history`, `get_sonarqube_component_tree_metrics`) defined in `server.py`. These tools handle the interaction with the SonarQube API, data processing, and formatting. They are not directly visible to end-users but are essential for providing the core functionality of the system.

The `@mcp.tool()` decorator systematically applies common behaviors across all tool functions, ensuring they are registered with the FastMCP server and accessible to clients. Additionally, the use of `Annotated` and `Field` ensures consistent parameter definition and documentation across all tools.

## Architectural Patterns and Design Principles Applied

*   **Client-Server Architecture:** The project follows a client-server architecture, where the client requests services from the server.
*   **Message Passing:** The FastMCP framework facilitates communication between the client and server using message passing.
*   **Asynchronous Programming:** The use of `asyncio` and `httpx` enables asynchronous operations, improving the performance and responsiveness of the application.
*   **Configuration via Environment Variables:** The SonarQube URL and token are configured using environment variables, making it easier to deploy and manage the application in different environments.
*   **Tool-Based Design:** The server exposes functionality through well-defined tools, making it easy to add or modify features.
*   **Error Handling:** The project includes comprehensive error handling to gracefully handle potential issues, such as network errors, API errors, and invalid data.
*   **Logging:** The use of the `logging` module provides detailed logs, aiding in debugging and monitoring.
*   **Dependency Injection:** While not explicitly implemented as a framework, the configuration of the SonarQube URL and token through environment variables allows for easy substitution of different SonarQube instances without modifying the code.

## Code Quality Analysis

Due to the lack of a SonarQube report, a comprehensive code quality analysis cannot be performed. However, based on the code structure and functionality, potential areas of concern include:

*   **Error Handling Granularity:** While error handling is present, the specific error messages could be improved to provide more actionable information to the user.
*   **Test Coverage:** The provided code does not include unit tests. Test coverage should be added to ensure the reliability and correctness of the code.
*   **Code Duplication:** There might be opportunities to reduce code duplication by extracting common logic into reusable functions or classes.

## Weaknesses and Areas for Improvement

*    **Improve error message clarity:** Enhance error messages to provide more specific guidance to users on how to resolve issues.
*    **Add unit tests:** Implement unit tests for the server-side tools to ensure their correctness and reliability.
*    **Refactor common logic:** Identify and refactor duplicated code into reusable functions or classes.
*    **Implement input validation:** Add input validation to the server-side tools to prevent invalid data from being processed.
*    **Improve documentation:** Add more detailed documentation for the server-side tools, including examples and usage instructions.
*    **Implement a more robust configuration system:** Consider using a more robust configuration system, such as a configuration file or a dedicated settings class, instead of relying solely on environment variables.
*    **Add support for additional SonarQube API endpoints:** Extend the system to support additional SonarQube API endpoints, such as those for managing projects, rules, or quality profiles.
*    **Implement a more user-friendly client interface:** Consider developing a graphical user interface (GUI) or a more sophisticated command-line interface (CLI) for the client application.
*    **Address potential security vulnerabilities:** Review the code for potential security vulnerabilities, such as those related to input validation or authentication.

## Further Areas of Investigation

*   **Performance Bottlenecks:** Investigate potential performance bottlenecks in the server-side tools, such as those related to API request handling or data processing.
*   **Scalability Considerations:** Evaluate the scalability of the system and identify potential areas for improvement, such as using a message queue or a distributed caching system.
*   **Integrations with External Systems:** Explore potential integrations with other development tools, such as CI/CD systems or issue trackers.
*   **Advanced Features:** Research and implement advanced features, such as real-time metric monitoring or automated code quality analysis.
*   **Code Smells and Low Test Coverage:** Conduct a thorough analysis of the codebase to identify and address code smells and areas with low test coverage.

## Attribution

Generated with the support of [ArchAI](https://github.com/ArchAI-Labs/code_explainer), an automated documentation system.
