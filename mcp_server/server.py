"""MCP server exposing enterprise tools to the agent through a real protocol boundary.

The LangGraph agent uses ``app.mcp.client`` to call these tools over stdio.
Run manually with:
    python -m mcp_server.server
"""

from mcp.server.fastmcp import FastMCP

from app.rag.store import document_store
from app.tools.registry import calculator

mcp = FastMCP("enterprise-agent-tools")


@mcp.tool()
def search_enterprise_documents(query: str) -> dict:
    """Search indexed enterprise knowledge documents."""
    return {"results": document_store.search(query)}


@mcp.tool()
def calculate(expression: str) -> dict:
    """Perform a safe arithmetic calculation."""
    return calculator(expression)


if __name__ == "__main__":
    mcp.run()
