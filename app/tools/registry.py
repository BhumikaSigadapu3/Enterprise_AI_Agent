import ast
import operator
from typing import Any, Callable

import httpx


def document_search(query: str) -> dict[str, Any]:
    # Lazy import keeps calculator/unit tests independent from the embedding model.
    from app.rag.store import document_store

    return {"results": document_store.search(query)}


def calculator(expression: str) -> dict[str, Any]:
    allowed = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }

    def evaluate(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in allowed:
            return allowed[type(node.op)](evaluate(node.left), evaluate(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in allowed:
            return allowed[type(node.op)](evaluate(node.operand))
        raise ValueError("Unsupported expression")

    tree = ast.parse(expression, mode="eval")
    return {"expression": expression, "result": evaluate(tree.body)}


async def research(query: str) -> dict[str, Any]:
    print(f"\n[DEBUG] Research tool called with query: {query}")

    try:
        async with httpx.AsyncClient(
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        ) as client:

            response = await client.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": query,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1,
                },
            )

            print(f"[DEBUG] Status code: {response.status_code}")

            response.raise_for_status()
            data = response.json()
            print("[DEBUG] Full response:", data)

        abstract = data.get("AbstractText", "")
        source = data.get("AbstractURL", "")
        heading = data.get("Heading", "")

        print(f"[DEBUG] Abstract: {abstract}")
        print(f"[DEBUG] Heading: {heading}")

        if not abstract:
            related_topics = data.get("RelatedTopics", [])

            for topic in related_topics:
                if isinstance(topic, dict) and topic.get("Text"):
                    abstract = topic.get("Text", "")
                    source = topic.get("FirstURL", "")
                    heading = topic.get("Text", "").split(" - ")[0]
                    break

        if not abstract:
            abstract = "No direct research result was found for this query."
            heading = "Research Result"

        result = {
            "abstract": abstract,
            "source": source,
            "heading": heading,
        }

        print(f"[DEBUG] Final research result: {result}")

        return result

    except Exception as e:
        print(f"[DEBUG] Research error: {e}")

        return {
            "abstract": f"Research failed: {str(e)}",
            "source": "",
            "heading": "Research Error",
        }

TOOL_REGISTRY: dict[str, Callable] = {
    "document_search": document_search,
    "calculator": calculator,
    "research": research,
}
