import asyncio
import json
from pathlib import Path

from mcp.types import TextContent

from fastmcp import Client
from fastmcp.exceptions import ClientError

# --- Configuration ---
# Adjust this path if your server script is located elsewhere
SERVER_SCRIPT_PATH = Path("server.py").resolve()
# --- End Configuration ---


async def run_test(project_key: str):
    """Connects to the server, calls the tool, and prints the result."""

    if not SERVER_SCRIPT_PATH.exists():
        print(f"ERROR: Server script not found at '{SERVER_SCRIPT_PATH}'")
        print("Make sure 'server.py' is in the correct directory.")
        return

    print(f"Attempting to connect to server via: {SERVER_SCRIPT_PATH}")
    # The client automatically uses PythonStdioTransport for .py files
    client = Client(SERVER_SCRIPT_PATH)


    try:
        async with client:
            print("Connection established.")
            print(
                f"Calling tool 'list_projects'..."
            )

            # Call the tool
            result = await client.call_tool(
                "list_projects",
                {},
            )

            print("\n--- Tool Result ---")
            if not result:
                print("Received empty result from the tool.")
                return

            # Process the result (expecting TextContent with JSON)
            content = result[0]
            if isinstance(content, TextContent):
                print("Raw response text:")
                print(content.text)
                try:
                    # Try parsing the JSON for pretty printing
                    metrics = json.loads(content.text)
                    print("\nParsed Metrics:")
                    print(json.dumps(metrics, indent=2))
                except json.JSONDecodeError:
                    print("\nWARNING: Response text was not valid JSON.")
            else:
                print(f"Received unexpected content type: {type(content)}")
                print(f"Content: {content!r}")

    except ClientError as e:
        print(f"\n--- MCP Client Error ---")
        # Errors from the tool (like ValueError) are wrapped in ClientError
        print(f"Error: {e}")
        print(
            "Check the server logs and ensure the project key is correct and accessible."
        )
    except FileNotFoundError:
        print(f"ERROR: Server script '{SERVER_SCRIPT_PATH}' not found.")
    except Exception as e:
        print(f"\n--- An Unexpected Error Occurred ---")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {e}")
        print(
            "Check if the server script can run independently and if dependencies are met."
        )

    print("\n--- Test Complete ---")

    try:
        async with client:
            print("Connection established.")
            print(
                f"Calling tool 'get_sonarqube_metrics' for project '{project_key}'..."
            )

            # Call the tool
            result = await client.call_tool(
                "get_sonarqube_metrics", {"project_key": project_key}
            )

            print("\n--- Tool Result ---")
            if not result:
                print("Received empty result from the tool.")
                return

            # Process the result (expecting TextContent with JSON)
            content = result[0]
            if isinstance(content, TextContent):
                print("Raw response text:")
                print(content.text)
                try:
                    # Try parsing the JSON for pretty printing
                    metrics = json.loads(content.text)
                    print("\nParsed Metrics:")
                    print(json.dumps(metrics, indent=2))
                except json.JSONDecodeError:
                    print("\nWARNING: Response text was not valid JSON.")
            else:
                print(f"Received unexpected content type: {type(content)}")
                print(f"Content: {content!r}")

    except ClientError as e:
        print(f"\n--- MCP Client Error ---")
        # Errors from the tool (like ValueError) are wrapped in ClientError
        print(f"Error: {e}")
        print(
            "Check the server logs and ensure the project key is correct and accessible."
        )
    except FileNotFoundError:
        print(f"ERROR: Server script '{SERVER_SCRIPT_PATH}' not found.")
    except Exception as e:
        print(f"\n--- An Unexpected Error Occurred ---")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {e}")
        print(
            "Check if the server script can run independently and if dependencies are met."
        )

    print("\n--- Test Complete ---")

    try:
        async with client:
            print("Connection established.")
            print(
                f"Calling tool 'get_sonarqube_metrics_history' for project '{project_key}'..."
            )

            # Call the tool
            result = await client.call_tool(
                "get_sonarqube_metrics_history",
                {
                    "project_key": project_key,
                    "from_date":"2024-01-01",
                    "to_date":"2024-12-31"
                },
            )

            print("\n--- Tool Result ---")
            if not result:
                print("Received empty result from the tool.")
                return

            # Process the result (expecting TextContent with JSON)
            content = result[0]
            if isinstance(content, TextContent):
                print("Raw response text:")
                print(content.text)
                try:
                    # Try parsing the JSON for pretty printing
                    metrics = json.loads(content.text)
                    print("\nParsed Metrics:")
                    print(json.dumps(metrics, indent=2))
                except json.JSONDecodeError:
                    print("\nWARNING: Response text was not valid JSON.")
            else:
                print(f"Received unexpected content type: {type(content)}")
                print(f"Content: {content!r}")

    except ClientError as e:
        print(f"\n--- MCP Client Error ---")
        # Errors from the tool (like ValueError) are wrapped in ClientError
        print(f"Error: {e}")
        print(
            "Check the server logs and ensure the project key is correct and accessible."
        )
    except FileNotFoundError:
        print(f"ERROR: Server script '{SERVER_SCRIPT_PATH}' not found.")
    except Exception as e:
        print(f"\n--- An Unexpected Error Occurred ---")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {e}")
        print(
            "Check if the server script can run independently and if dependencies are met."
        )

    print("\n--- Test Complete ---")


    try:
        async with client:
            print("Connection established.")
            print(
                f"Calling tool 'get_sonarqube_component_tree_metrics' for project '{project_key}'..."
            )

            # Call the tool
            result = await client.call_tool(
                "get_sonarqube_component_tree_metrics",
                {
                    "project_key": project_key,
                    "metric_keys":["coverage", "bugs", "code_smells"],
                    "page_size":1
                },
            )

            print("\n--- Tool Result ---")
            if not result:
                print("Received empty result from the tool.")
                return

            # Process the result (expecting TextContent with JSON)
            content = result[0]
            if isinstance(content, TextContent):
                print("Raw response text:")
                print(content.text)
                try:
                    # Try parsing the JSON for pretty printing
                    metrics = json.loads(content.text)
                    print("\nParsed Metrics:")
                    print(json.dumps(metrics, indent=2))
                except json.JSONDecodeError:
                    print("\nWARNING: Response text was not valid JSON.")
            else:
                print(f"Received unexpected content type: {type(content)}")
                print(f"Content: {content!r}")

    except ClientError as e:
        print(f"\n--- MCP Client Error ---")
        # Errors from the tool (like ValueError) are wrapped in ClientError
        print(f"Error: {e}")
        print(
            "Check the server logs and ensure the project key is correct and accessible."
        )
    except FileNotFoundError:
        print(f"ERROR: Server script '{SERVER_SCRIPT_PATH}' not found.")
    except Exception as e:
        print(f"\n--- An Unexpected Error Occurred ---")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {e}")
        print(
            "Check if the server script can run independently and if dependencies are met."
        )
    
    # DANGER ZONE! UNCOMMENT TO TRY IT!
    
    # try:
    #     async with client:
    #         print("\n--- Testing create_sonarqube_project ---")
    #         new_project_key = "test-project-mcp-delete-me"  # Unique key
    #         new_project_name = "Test Project MCP Delete Me"
    #         result_create = await client.call_tool(
    #             "create_sonarqube_project",
    #             {"project_key": new_project_key, "project_name": new_project_name, "visibility": "private"},
    #         )
    #         print(f"Create project result: {result_create}")

    # except ClientError as e:
    #     print(f"\n--- MCP Client Error during project creation ---")
    #     print(f"Error: {e}")
    # except Exception as e:
    #     print(f"\n--- An Unexpected Error Occurred during project creation---")
    #     print(f"Error type: {type(e).__name__}")
    #     print(f"Error details: {e}")
    

    # try:
    #     async with client:
    #         print("\n--- Testing delete_sonarqube_project (USE WITH CAUTION) ---")
    #         project_to_delete = new_project_key
    #         result_delete = await client.call_tool(
    #             "delete_sonarqube_project", {"project_key": project_to_delete}
    #         )
    #         print(f"Delete project result: {result_delete}")

    # except ClientError as e:
    #     print(f"\n--- MCP Client Error during project deletion---")
    #     print(f"Error: {e}")
    # except Exception as e:
    #     print(f"\n--- An Unexpected Error Occurred during project deletion---")
    #     print(f"Error type: {type(e).__name__}")
    #     print(f"Error details: {e}")

    print("\n--- Test Complete ---")


if __name__ == "__main__":
    print("--- FastMCP SonarQube Tool Test Client ---")
    # Prompt user for the project key
    default_key = "your-actual-project-key"  # Replace with a common key if you like
    key_to_test = (
        input(
            f"Enter the SonarQube project key to test (e.g., my-org_my-repo) [{default_key}]: "
        )
        or default_key
    )

    # Ensure the server can load the .env file by running from the script's directory context
    script_dir = SERVER_SCRIPT_PATH.parent
    try:
        # Run the async test function
        asyncio.run(run_test(key_to_test))
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
