from app.agent.graph import select_tool, should_continue


def test_select_tool_uses_structured_plan():
    state = {
        "plan": [
            {
                "tool": "calculator",
                "input": "12/100*45000",
                "reason": "Arithmetic is required",
            }
        ],
        "current_step": 0,
    }
    assert select_tool(state) == "calculator"


def test_should_continue_when_steps_remain():
    state = {
        "plan": [
            {"tool": "document_search", "input": "leave", "reason": "retrieve"},
            {"tool": "calculator", "input": "20/12*3", "reason": "calculate"},
        ],
        "current_step": 1,
        "iterations": 1,
    }
    assert should_continue(state) == "tool"
