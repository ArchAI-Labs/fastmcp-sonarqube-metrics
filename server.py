import os
import httpx
import json
from typing import Annotated
import base64
from dotenv import load_dotenv
from pydantic import Field
from fastmcp import FastMCP
import logging
from fastmcp.utilities.logging import get_logger

logger = get_logger(__name__)

load_dotenv()

# Configure logging to suppress Pydantic schema warnings
logging.getLogger("pydantic.error_wrappers").setLevel(logging.ERROR)
logging.getLogger("fastmcp").setLevel(logging.ERROR)

# Create the FastMCP server instance with global config to ignore extra fields
mcp = FastMCP(
    name="SonarQube MCP",
    instructions="Provides tools to retrieve information about SonarQube projects.",
    tool_model_config={"extra": "ignore"},
    model_config={"extra": "ignore"}
)

# Define the metric keys we want to fetch
SONARQUBE_METRIC_KEYS = [
    "bugs",
    "vulnerabilities",
    "code_smells",
    "coverage",
    "duplicated_lines_density",
]

sonarqube_token = os.environ.get("SONARQUBE_TOKEN")
sonarqube_url = os.environ.get("SONARQUBE_URL")

@mcp.tool()
async def get_status() -> str:
    """
    Performs a health check on the configured SonarQube instance using /api/system/status.
    Returns a readable status message.
    """
    api_url = f"{sonarqube_url}/api/system/status"

    if sonarqube_token:
        base64_token = base64.b64encode(f"{sonarqube_token}:".encode()).decode("utf-8")

    headers = {
        "Accept": "application/json",
        "Authorization": f"Basic {base64_token}"
    }

    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Performing SonarQube health check at: {api_url}")
            response = await client.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()

            status = response.json().get("status", "UNKNOWN").upper()
            logger.info(f"SonarQube status: {status}")

            if status == "UP":
                return "🟢 SonarQube server is UP and running."
            elif status == "DOWN":
                return "🔴 SonarQube server is DOWN."
            elif status == "RESTARTING":
                return "🟡 SonarQube server is restarting..."
            else:
                return f"⚠️ SonarQube status: {status}"
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed (401). Check token.")
                raise PermissionError("Authentication failed. Check your token.") from e
            elif e.response.status_code == 403:
                logger.error("Access denied (403). Token may lack required permissions.")
                raise PermissionError("Access denied. Check token roles.") from e
            else:
                logger.error(f"SonarQube API error: {e.response.status_code} - {e.response.text}")
                raise RuntimeError(f"SonarQube API error: {e.response.status_code}") from e

        except httpx.RequestError as e:
            logger.error(f"Connection error: {e}")
            raise ConnectionError(f"Failed to connect to SonarQube at {sonarqube_url}") from e

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during health check: {e.response.status_code} - {e.response.text}")
            return f"HTTP error: {e.response.status_code} - {e.response.reason_phrase}"

        except Exception as e:
            logger.error(f"Unexpected error during health check: {e}", exc_info=True)
            return f"Unexpected error: {str(e)}"

@mcp.tool()
async def get_sonarqube_metrics(
    project_key: Annotated[str, Field(description="The unique key of the project in SonarQube (e.g., 'my-org_my-repo').")],
    # Optional: Allow overriding metric keys via tool argument
    # metric_keys: Annotated[list[str] | None, Field(description="Specific metric keys to fetch.")] = None
) -> dict:
    """
    Retrieves specified metrics (bugs, vulnerabilities, code smells, coverage,
    duplication density) for a given SonarQube project key.
    """
    logger.info(f"Fetching SonarQube metrics for project: {project_key}")

    # Use default keys if none provided
    keys_to_fetch = SONARQUBE_METRIC_KEYS # if metric_keys is None else metric_keys
    if not project_key:
         logger.warning("Received empty project_key, returning empty result.")
         # Return empty dict instead of empty string for consistency
         return {}

    # Use token for auth if provided
    if sonarqube_token:
        # auth = sonarqube_token # HTTP Basic Auth: token as user, empty password
        base64_token = base64.b64encode(f"{sonarqube_token}:".encode()).decode("utf-8")
    headers = {"Accept": "application/json",
               "Authorization": f"Basic {base64_token}"}

    api_url = f"{sonarqube_url}/api/measures/component"
    params = {
        "component": project_key,
        "metricKeys": ",".join(keys_to_fetch),
    }

    async with httpx.AsyncClient() as client:
        try:
            logger.debug(f"Requesting SonarQube API: {api_url} with params {params}")
            response = await client.get(api_url, headers=headers, params=params)
            response.raise_for_status() # Raise HTTPStatusError for 4xx/5xx responses

            data = response.json()
            logger.debug(f"Received SonarQube API response: {data}")

            component_data = data.get("component")
            if not component_data:
                 logger.warning(f"No 'component' data found for project '{project_key}' in SonarQube response.")
                 # Raising error provides more info than empty result
                 raise ValueError(f"Project '{project_key}' not found or has no component data in SonarQube.")

            measures = component_data.get("measures", [])
            if not measures:
                 logger.warning(f"No 'measures' found for project '{project_key}'.")
                 # Return an empty dict if measures are empty but project exists
                 return {}

            # Format results nicely
            results = {
                measure["metric"]: measure.get("value", "N/A") # Use get for robustness
                for measure in measures
            }

            logger.info(f"Successfully fetched metrics for {project_key}: {results}")
            return results

        except httpx.HTTPStatusError as e:
            # Provide more specific error messages based on status code
            if e.response.status_code == 404:
                logger.error(f"Project '{project_key}' not found in SonarQube (404).")
                raise ValueError(f"Project '{project_key}' not found in SonarQube.") from e
            elif e.response.status_code == 401:
                 logger.error("SonarQube authentication failed (401). Check token.")
                 raise PermissionError("SonarQube authentication failed. Check token.") from e
            elif e.response.status_code == 403:
                logger.error("SonarQube authentication failed (403). Access denied: Token doesn't have permission. Check roles.")
                raise PermissionError("SonarQube authentication failed. Access denied: Token doesn't have permission. Check roles.") from e
            else:
                logger.error(f"SonarQube API request failed: {e.response.status_code} - {e.response.text}")
                raise RuntimeError(f"SonarQube API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"Network error connecting to SonarQube: {e}")
            raise ConnectionError(f"Could not connect to SonarQube at {sonarqube_url}") from e
        except json.JSONDecodeError as e:
             logger.error(f"Failed to decode JSON response from SonarQube: {e}. Response text: {response.text}")
             raise ValueError("Received invalid JSON response from SonarQube.") from e
        except Exception as e:
             logger.error(f"Unexpected error fetching SonarQube metrics: {e}", exc_info=True)
             raise RuntimeError("An unexpected error occurred.") from e

@mcp.tool()
async def get_sonarqube_metrics_history(
    project_key: Annotated[str, Field(description="The unique key of the project in SonarQube (e.g., 'my-org_my-repo').")],
    from_date: Annotated[str | None, Field(description="Start date for metric history in YYYY-MM-DD format.")] = None,
    to_date: Annotated[str | None, Field(description="End date for metric history in YYYY-MM-DD format.")] = None
) -> dict:
    """
    Retrieves historical metrics (bugs, vulnerabilities, code smells, coverage,
    duplication density) for a given SonarQube project using /api/measures/search_history.
    Optional date filters can be applied.
    """
    logger.info(f"Fetching SonarQube metric history for project: {project_key}")

    if not project_key:
        logger.warning("Received empty project_key, returning empty result.")
        return {}

    keys_to_fetch = SONARQUBE_METRIC_KEYS

    if sonarqube_token:
        base64_token = base64.b64encode(f"{sonarqube_token}:".encode()).decode("utf-8")

    headers = {
        "Accept": "application/json",
        "Authorization": f"Basic {base64_token}"
    }

    api_url = f"{sonarqube_url}/api/measures/search_history"
    results = {}

    async with httpx.AsyncClient() as client:
        try:
            for metric in keys_to_fetch:
                params = {
                    "component": project_key,
                    "metrics": metric,
                    "ps": 10  # Optional: limit to last 10 entries
                }

                if from_date:
                    params["from"] = from_date
                if to_date:
                    params["to"] = to_date

                logger.debug(f"Requesting history for metric '{metric}' with params: {params}")
                response = await client.get(api_url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()
                history = data.get("measures", [])[0].get("history", []) if data.get("measures") else []

                results[metric] = [
                    {"date": entry.get("date"), "value": entry.get("value", "N/A")}
                    for entry in history
                ]

            logger.info(f"Successfully fetched historical metrics for {project_key}")
            return results

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.error(f"Project '{project_key}' not found in SonarQube (404).")
                raise ValueError(f"Project '{project_key}' not found in SonarQube.") from e
            elif e.response.status_code == 401:
                logger.error("SonarQube authentication failed (401). Check token.")
                raise PermissionError("SonarQube authentication failed. Check token.") from e
            elif e.response.status_code == 403:
                logger.error("SonarQube authentication failed (403). Access denied: Token doesn't have permission. Check roles.")
                raise PermissionError("SonarQube authentication failed. Access denied: Token doesn't have permission. Check roles.") from e
            else:
                logger.error(f"SonarQube API request failed: {e.response.status_code} - {e.response.text}")
                raise RuntimeError(f"SonarQube API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"Network error connecting to SonarQube: {e}")
            raise ConnectionError(f"Could not connect to SonarQube at {sonarqube_url}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}. Response text: {response.text}")
            raise ValueError("Invalid JSON received from SonarQube.") from e
        except Exception as e:
            logger.error(f"Unexpected error fetching SonarQube metric history: {e}", exc_info=True)
            raise RuntimeError("An unexpected error occurred.") from e

@mcp.tool()
async def get_sonarqube_component_tree_metrics(
    project_key: Annotated[str, Field(description="The unique key of the project in SonarQube (e.g., 'my-org_my-repo').")],
    metric_keys: Annotated[list[str], Field(description="List of metric keys to fetch (e.g., 'coverage', 'bugs', etc.).")],
    component_type: Annotated[str | None, Field(description="Optional SonarQube component type to filter by (e.g., 'DIR', 'FIL', 'UTS').")] = None,
    page_size: Annotated[int, Field(description="Number of components per page. Defaults to 10.")] = 10
) -> dict:
    """
    Retrieves metric values for all components (e.g., files or directories) in a project using /api/measures/component_tree.
    Automatically handles pagination to retrieve all results.
    """
    logger.info(f"Fetching component tree metrics for project: {project_key}")

    if not project_key:
        logger.warning("Received empty project_key, returning empty result.")
        return {}

    if not metric_keys:
        logger.warning("No metric_keys provided, returning empty result.")
        return {}

    if sonarqube_token:
        base64_token = base64.b64encode(f"{sonarqube_token}:".encode()).decode("utf-8")

    headers = {
        "Accept": "application/json",
        "Authorization": f"Basic {base64_token}"
    }

    api_url = f"{sonarqube_url}/api/measures/component_tree"
    results = {}
    page = 1
    total = None

    async with httpx.AsyncClient() as client:
        try:
            while True:
                params = {
                    "component": project_key,
                    "metricKeys": ",".join(metric_keys),
                    "ps": page_size,
                    "p": page,
                }

                if component_type:
                    params["qualifiers"] = component_type.upper()

                logger.debug(f"Requesting page {page} from SonarQube API: {api_url} with params {params}")
                response = await client.get(api_url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()

                if total is None:
                    total = data.get("paging", {}).get("total", 0)
                    logger.debug(f"Total components to fetch: {total}")

                components = data.get("components", [])
                if not components:
                    break

                for comp in components:
                    key = comp.get("key")
                    path = comp.get("path", key)
                    metrics = {
                        measure["metric"]: measure.get("value", "N/A")
                        for measure in comp.get("measures", [])
                    }
                    results[path] = metrics

                fetched_so_far = page * page_size
                if fetched_so_far >= total:
                    break

                page += 1

            logger.info(f"Fetched metrics for {len(results)} components in project {project_key}")
            return results

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.error(f"Project '{project_key}' not found (404).")
                raise ValueError(f"Project '{project_key}' not found.") from e
            elif e.response.status_code == 401:
                logger.error("Authentication failed (401). Check token.")
                raise PermissionError("Authentication failed. Check your token.") from e
            elif e.response.status_code == 403:
                logger.error("SonarQube authentication failed (403). Access denied: Token doesn't have permission. Check roles.")
                raise PermissionError("SonarQube authentication failed. Access denied: Token doesn't have permission. Check roles.") from e
            else:
                logger.error(f"SonarQube API error: {e.response.status_code} - {e.response.text}")
                raise RuntimeError(f"SonarQube API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"Network error: {e}")
            raise ConnectionError(f"Failed to connect to SonarQube at {sonarqube_url}") from e
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise RuntimeError("Unexpected error during component tree fetch.") from e

@mcp.tool()
async def list_projects(
    query: Annotated[str | None, Field(description="Optional substring to filter projects by key or name. Case-insensitive.")] = None
) -> dict:
    """Lists all accessible SonarQube projects, optionally filtered by name or key."""

    logger.info("Fetching list of accessible SonarQube projects.")

    if not sonarqube_token:
        raise ValueError("Missing SonarQube token. Cannot authenticate.")

    base64_token = base64.b64encode(f"{sonarqube_token}:".encode()).decode("utf-8")
    headers = {
        "Accept": "application/json",
        "Authorization": f"Basic {base64_token}"
    }

    api_url = f"{sonarqube_url}/api/projects/search"

    async with httpx.AsyncClient() as client:
        try:
            logger.debug(f"Requesting SonarQube API: {api_url}")
            response = await client.get(api_url, headers=headers)
            response.raise_for_status()

            data = response.json()
            all_projects = data.get("components", [])

            # Apply optional query filter
            if query:
                query_lower = query.lower()
                projects = [
                    p for p in all_projects
                    if query_lower in (p.get("name", "").lower() + p.get("key", "").lower())
                ]
                logger.info(f"Filtered projects using query: '{query}' — {len(projects)} match(es) found.")
            else:
                projects = all_projects
                logger.info(f"No query filter applied. {len(projects)} total project(s) returned.")

            result = {
                "total": len(projects),
                "projects": [
                    {
                        "key": p.get("key"),
                        "name": p.get("name"),
                        "visibility": p.get("visibility")
                    } for p in projects
                ]
            }

            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed (401). Check token.")
                raise PermissionError("Authentication failed. Check your token.") from e
            elif e.response.status_code == 403:
                logger.error("Access denied (403). Token may lack required permissions.")
                raise PermissionError("Access denied. Check token roles.") from e
            else:
                logger.error(f"SonarQube API error: {e.response.status_code} - {e.response.text}")
                raise RuntimeError(f"SonarQube API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"Connection error: {e}")
            raise ConnectionError(f"Failed to connect to SonarQube at {sonarqube_url}") from e
        except Exception as e:
            logger.error(f"Unexpected error while fetching projects: {e}", exc_info=True)
            raise RuntimeError("An unexpected error occurred while listing projects.") from e


@mcp.tool()
async def get_project_issues(
    project_key: Annotated[str, Field(description="The unique key of the SonarQube project.")],
    issue_type: Annotated[str | None, Field(description="Filter by issue type (e.g., BUG, CODE_SMELL, VULNERABILITY).")] = None,
    severity: Annotated[str | None, Field(description="Filter by severity (e.g., INFO, MINOR, MAJOR, CRITICAL, BLOCKER).")] = None,
    resolved: Annotated[bool, Field(description="Whether to fetch only resolved issues. Default: false.")] = False,
    limit: Annotated[int, Field(description="Max number of issues to return. Default: 10, Max recommended: 100.")] = 10
) -> dict:
    """
    Fetch SonarQube issues for a given project, optionally filtered by type, severity, and resolution status.
    Returns up to `limit` results (default: 10).
    """
    logger.info(f"Fetching issues for {project_key} | type={issue_type}, severity={severity}, resolved={resolved}, limit={limit}")

    if not project_key:
        return {"error": "Missing project key."}

    headers = {
        "Accept": "application/json",
        "Authorization": f"Basic {base64.b64encode(f'{sonarqube_token}:'.encode()).decode('utf-8')}"
    }

    issues_url = f"{sonarqube_url}/api/issues/search"
    params = {
        "componentKeys": project_key,
        "resolved": str(resolved).lower(),
        "ps": min(limit, 500)  # API safety cap
    }

    if issue_type:
        params["types"] = issue_type.upper()
    if severity:
        params["severities"] = severity.upper()

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(issues_url, headers=headers, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()
            issues = data.get("issues", [])

            if not issues:
                # Double-check if the project exists
                check_url = f"{sonarqube_url}/api/projects/search"
                check_response = await client.get(check_url, headers=headers)
                check_response.raise_for_status()

                known_keys = [p["key"] for p in check_response.json().get("components", [])]
                if project_key not in known_keys:
                    return {
                        "project": project_key,
                        "error": f"Project '{project_key}' not found. Try one of: {known_keys[:5]}..."
                    }

            formatted = [{
                "key": i.get("key"),
                "severity": i.get("severity"),
                "type": i.get("type"),
                "message": i.get("message"),
                "component": i.get("component"),
                "line": i.get("line"),
                "status": i.get("status")
            } for i in issues]

            return {
                "project": project_key,
                "filters": {
                    "type": issue_type,
                    "severity": severity,
                    "resolved": resolved
                },
                "total_issues": len(formatted),
                "issues": formatted[:limit],
                "has_more": len(formatted) > limit
            }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed (401). Check token.")
                raise PermissionError("Authentication failed. Check your token.") from e
            elif e.response.status_code == 403:
                logger.error("Access denied (403). Token may lack required permissions.")
                raise PermissionError("Access denied. Check token roles.") from e
            else:
                logger.error(f"SonarQube API error: {e.response.status_code} - {e.response.text}")
                raise RuntimeError(f"SonarQube API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"Connection error: {e}")
            raise ConnectionError(f"Failed to connect to SonarQube at {sonarqube_url}") from e
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return {"error": f"Unexpected error: {str(e)}"}

# Standard entry point to run the server
if __name__ == "__main__":
    print(f"Starting SonarQube MCP server, configured for {sonarqube_url}")
    mcp.settings.port = 8001
    mcp.run(transport=os.environ.get("TRANSPORT"))
