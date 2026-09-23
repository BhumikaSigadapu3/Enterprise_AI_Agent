"""Minimal stdio MCP client used by the LangGraph agent.

The client intentionally starts the local MCP server as a subprocess for each
request. This keeps the project self-contained and demonstrates a real MCP
client/server boundary without requiring an additional service to be deployed.
"""

import json
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


TOOL_NAME_MAP = {
    "document_search": "search_enterprise_documents",
    "calculator": "calculate",
}


async def call_mcp_tool(tool_name: str, tool_input: str) -> dict[str, Any]:
    if tool_name not in TOOL_NAME_MAP:
        raise ValueError(f"No MCP mapping configured for tool '{tool_name}'.")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_server.server"],
    )

    arguments = {"query": tool_input}
    if tool_name == "calculator":
        arguments = {"expression": tool_input}

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(TOOL_NAME_MAP[tool_name], arguments)

            structured = getattr(result, "structuredContent", None)
            if structured is not None:
                return dict(structured)

            content = getattr(result, "content", [])
            for item in content:
                text = getattr(item, "text", None)
                if not text:
                    continue
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    return {"result": text}

            return {"result": None, "raw_content": [str(item) for item in content]}
