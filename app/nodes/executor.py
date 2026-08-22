import json
import os
import urllib.error
import urllib.request

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from dotenv import load_dotenv

from app.state import AnalystState
from app.tool import execute_pandas


load_dotenv()


llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=0,
    max_tokens=4096,
)

llm_with_tools = llm.bind_tools([execute_pandas])


def authorize_pandas_execution(dataset_path: str, code: str) -> dict:
    """Ask AIAuth for permission before running generated code."""
    passport = os.getenv("ANALYST_EXECUTOR_PASSPORT")
    if not passport:
        return {"status": "failed", "reason": "ANALYST_EXECUTOR_PASSPORT is not configured"}

    request = urllib.request.Request(
        f"{os.getenv('AI_AUTH_URL', 'http://localhost:8080').rstrip('/')}/actions",
        data=json.dumps({
            "passport": passport,
            "capability": "execute_pandas",
            "resource": dataset_path,
            "payload": {"code": code},
            "idempotency_key": f"analyst-pandas-{os.urandom(16).hex()}",
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        return {"status": "failed", "reason": f"AIAuth returned HTTP {error.code}: {detail}"}
    except (urllib.error.URLError, TimeoutError) as error:
        return {"status": "failed", "reason": f"AIAuth unavailable: {error}"}
    except json.JSONDecodeError:
        return {"status": "failed", "reason": "AIAuth returned invalid JSON"}


def executor_node(state: AnalystState):
    print(f"\nEXECUTOR")
    current_step = state["plan"][0]
    print(f"Current task: {current_step}")

    completed_steps = ""
    if state["past_steps"]:
        for i, (step, result) in enumerate(state["past_steps"], 1):
            completed_steps += f"Step {i}: {step}\nResult:\n{result}\n\n"
    else:
        completed_steps = "None"

    system_prompt = f"""
You are a Data Analyst Executor.
Your job is to execute the current task from the analysis plan.

Original user question:
{state["input"]}

Dataset description:
{state["dataset_context"]}

Previous findings:
{completed_steps}

Your current task is:
{current_step}

Rules:
1. Solve ONLY this task.
2. If you need to analyze the dataset, use the execute_pandas tool.
3. The cleaned dataset is saved at `{state["cleaned_dataset_path"]}`. You MUST read this cleaned dataset using `df = pd.read_csv('{state["cleaned_dataset_path"]}')` at the beginning of your code. Do NOT use the raw dataset directly.
4. Make sure your Python code uses `print()` to output the results of your calculations.
5. You must execute Python code to get the actual numbers if the task requires calculating, checking, sorting, or analyzing data. Do NOT answer theoretically without running the code first.
6. CRITICAL: Do NOT use your prior knowledge or make assumptions. You must use the EXACT numbers and categories returned by the tool execution. If you make up or guess any numbers, you will fail.
7. After receiving the tool execution result, provide a concise final answer using the exact values returned.
8. If the task does not require code execution, provide the answer directly.
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Execute the current task: {current_step}")
    ]

    tools = {
        "execute_pandas": execute_pandas
    }

    while True:
        response = llm_with_tools.invoke(messages)
        messages.append(response)
        if response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                print(f"EXECUTOR: Tool requested: {tool_name}")

                tool = tools.get(tool_name)

                if tool is None:
                    tool_result = f"Unknown tool: {tool_name}. Only execute_pandas is available."
                else:
                    print("EXECUTOR: Running Pandas Code...")
                    print("-" * 40)
                    code = tool_call["args"].get("code", "")
                    print(code)
                    print("-" * 40)

                    authorization = authorize_pandas_execution(
                        state["cleaned_dataset_path"],
                        code,
                    )
                    if authorization.get("status") != "succeeded":
                        reason = authorization.get(
                            "reason", authorization.get("status", "unknown")
                        )
                        raise RuntimeError(
                            f"AIAuth did not authorize Pandas execution: {reason}"
                        )

                    tool_result = tool.invoke(tool_call["args"])

                    print(f"SANDBOX OUTPUT:\n{tool_result}\n")

                messages.append(
                    ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call["id"]
                    )
                )
            continue

        if isinstance(response.content, str):
            final_answer = response.content
        elif isinstance(response.content, list):
            texts = []
            for part in response.content:
                if isinstance(part, dict) and "text" in part:
                    texts.append(part["text"])
                else:
                    texts.append(str(part))
            final_answer = "\n".join(texts)
        else:
            final_answer = str(response.content) if response.content else "No response generated."

        break

    print("EXECUTOR: Step complete.")

    return {
        "past_steps": [
            (current_step, final_answer)
        ],
        "plan": state["plan"][1:]
    }
