# server.py
import os
import httpx
import json
from typing import Annotated
import base64

from dotenv import load_dotenv

from pydantic import Field

from fastmcp import FastMCP
from fastmcp.utilities.logging import get_logger

logger = get_logger(__name__)

load_dotenv()
# Create the FastMCP server instance
mcp = FastMCP(
    name="SonarQube MCP",
    instructions="Provides a tools to retrieve informations about SonarQube projects.",
)

# Define the metric keys we want to fetch
SONARQUBE_METRIC_KEYS = [
    "bugs",
    "vulnerabilities",
    "code_smells",
    "coverage",
    "duplicated_lines_density",
]


sonarqube_token=os.environ.get("SONARQUBE_TOKEN")
sonarqube_url=os.environ.get("SONARQUBE_URL")

# Define the tool using the @mcp.tool decorator
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
                    "metric": metric,
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
    component_type: Annotated[str | None, Field(description="Optional SonarQube component type to filter by (e.g., 'FILE', 'DIRECTORY', 'MODULE').")] = None,
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
            else:
                logger.error(f"SonarQube API error: {e.response.status_code} - {e.response.text}")
                raise RuntimeError(f"SonarQube API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"Network error: {e}")
            raise ConnectionError(f"Failed to connect to SonarQube at {sonarqube_url}") from e
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise RuntimeError("Unexpected error during component tree fetch.") from e



# Standard entry point to run the server
if __name__ == "__main__":
    print(f"Starting SonarQube MCP server, configured for {sonarqube_url}")
    mcp.run() # Runs with default stdio transport