# server.py
import os
import httpx
import json
from typing import Annotated
import base64
from dotenv import load_dotenv
from pydantic import Field
from fastmcp import FastMCP

load_dotenv()

# Configure logging to suppress Pydantic schema warnings
import logging
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

@mcp.tool(
    description="Performs a health check on the SonarQube server and returns UP, DOWN, or RESTARTING."
)
async def get_status() -> str:
    api_url = f"{sonarqube_url}/api/system/status"
    token_hdr = base64.b64encode(f"{sonarqube_token}:".encode()).decode() if sonarqube_token else None
    headers = {"Accept": "application/json", "Authorization": f"Basic {token_hdr}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        status = response.json().get("status", "UNKNOWN").upper()
        return {
            "UP": "🟢 SonarQube server is UP and running.",
            "DOWN": "🔴 SonarQube server is DOWN.",
            "RESTARTING": "🟡 SonarQube server is restarting..."
        }.get(status, f"⚠️ SonarQube status: {status}")

@mcp.tool(
    description="Retrieves current metrics (bugs, vulnerabilities, code smells, coverage, duplicated lines density) for a given project key."
)
async def get_sonarqube_metrics(
    project_key: Annotated[str, Field(description="Project key, e.g., 'org_repo'.")]
) -> dict:
    if not project_key:
        return {}
    token_hdr = base64.b64encode(f"{sonarqube_token}:".encode()).decode() if sonarqube_token else None
    headers = {"Accept": "application/json", "Authorization": f"Basic {token_hdr}"}
    api_url = f"{sonarqube_url}/api/measures/component"
    params = {"component": project_key, "metricKeys": ",".join(SONARQUBE_METRIC_KEYS)}
    async with httpx.AsyncClient() as client:
        response = await client.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        component = response.json().get("component", {})
        measures = component.get("measures", [])
        return {m['metric']: m.get('value', 'N/A') for m in measures}

@mcp.tool(
    description="Fetches historical metric data for a project over a date range."
)
async def get_sonarqube_metrics_history(
    project_key: Annotated[str, Field(description="Project key in SonarQube.")],
    from_date: Annotated[str | None, Field(description="Start date YYYY-MM-DD.")] = None,
    to_date: Annotated[str | None, Field(description="End date YYYY-MM-DD.")] = None
) -> dict:
    if not project_key:
        return {}
    token_hdr = base64.b64encode(f"{sonarqube_token}:".encode()).decode() if sonarqube_token else None
    headers = {"Accept": "application/json", "Authorization": f"Basic {token_hdr}"}
    api_url = f"{sonarqube_url}/api/measures/search_history"
    results = {}
    async with httpx.AsyncClient() as client:
        for metric in SONARQUBE_METRIC_KEYS:
            params = {"component": project_key, "metrics": metric, "ps": 10}
            if from_date:
                params["from"] = from_date
            if to_date:
                params["to"] = to_date
            response = await client.get(api_url, headers=headers, params=params)
            response.raise_for_status()
            history_data = response.json().get("measures", [])
            history = history_data[0].get("history", []) if history_data else []
            results[metric] = [{"date": e.get("date"), "value": e.get("value", "N/A")} for e in history]
    return results

@mcp.tool(
    description="Retrieves metrics for every component in a project with pagination."
)
async def get_sonarqube_component_tree_metrics(
    project_key: Annotated[str, Field(description="Project key in SonarQube.")],
    metric_keys: Annotated[list[str], Field(description="List of metric keys.")],
    component_type: Annotated[str | None, Field(description="Optional type: FILE, DIRECTORY, MODULE.")] = None,
    page_size: Annotated[int, Field(description="Components per page.")] = 10
) -> dict:
    if not project_key or not metric_keys:
        return {}
    token_hdr = base64.b64encode(f"{sonarqube_token}:".encode()).decode() if sonarqube_token else None
    headers = {"Accept": "application/json", "Authorization": f"Basic {token_hdr}"}
    api_url = f"{sonarqube_url}/api/measures/component_tree"
    results = {}
    page = 1
    total = None
    async with httpx.AsyncClient() as client:
        while True:
            params = {"component": project_key, "metricKeys": ",".join(metric_keys), "ps": page_size, "p": page}
            if component_type:
                params["qualifiers"] = component_type.upper()
            response = await client.get(api_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            if total is None:
                total = data.get("paging", {}).get("total", 0)
            comps = data.get("components", [])
            if not comps:
                break
            for comp in comps:
                path = comp.get("path", comp.get("key"))
                results[path] = {m["metric"]: m.get("value", "N/A") for m in comp.get("measures", [])}
            if page * page_size >= total:
                break
            page += 1
    return results

@mcp.tool(
    description="Lists all accessible SonarQube projects, optionally filtered by substring."
)
async def list_projects(
    query: Annotated[str | None, Field(description="Filter substring.")] = None
) -> dict:
    token_hdr = base64.b64encode(f"{sonarqube_token}:".encode()).decode() if sonarqube_token else None
    headers = {"Accept": "application/json", "Authorization": f"Basic {token_hdr}"}
    api_url = f"{sonarqube_url}/api/projects/search"
    async with httpx.AsyncClient() as client:
        response = await client.get(api_url, headers=headers)
        response.raise_for_status()
        projects = response.json().get("components", [])
        if query:
            ql = query.lower()
            projects = [p for p in projects if ql in (p.get("name", "") + p.get("key", "")).lower()]
        return {"total": len(projects), "projects": [{"key": p["key"], "name": p["name"], "visibility": p.get("visibility")} for p in projects]}

@mcp.tool(
    description="Fetches project issues filterable by type, severity, and resolution status."
)
async def get_project_issues(
    project_key: Annotated[str, Field(description="Project key in SonarQube.")],
    issue_type: Annotated[str | None, Field(description="Issue type filter.")] = None,
    severity: Annotated[str | None, Field(description="Severity filter.")] = None,
    resolved: Annotated[bool, Field(description="Only resolved?")] = False,
    limit: Annotated[int, Field(description="Max issues.")] = 10
) -> dict:
    token_hdr = base64.b64encode(f"{sonarqube_token}:".encode()).decode() if sonarqube_token else None
    headers = {"Accept": "application/json", "Authorization": f"Basic {token_hdr}"}
    url = f"{sonarqube_url}/api/issues/search"
    params = {"componentKeys": project_key, "resolved": str(resolved).lower(), "ps": min(limit, 500)}
    if issue_type:
        params["types"] = issue_type.upper()
    if severity:
        params["severities"] = severity.upper()
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        issues = response.json().get("issues", [])
        formatted = [{
            "key": i.get("key"), "severity": i.get("severity"), "type": i.get("type"),
            "message": i.get("message"), "component": i.get("component"),
            "line": i.get("line"), "status": i.get("status")
        } for i in issues]
        return {"project": project_key, "total_issues": len(formatted), "issues": formatted[:limit], "has_more": len(formatted) > limit}

if __name__ == "__main__":
    mcp.settings.port = 8000
    mcp.run(transport=os.getenv("transport"))
