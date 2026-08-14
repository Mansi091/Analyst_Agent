import json
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

from app.state import AnalystState
from app.tool import execute_pandas


load_dotenv()


llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    max_tokens=4096,
    max_retries=10
)


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
2. If you need to run Python/Pandas code to analyze the data, fill in the `code` field. 
3. The dataset is loaded inside the sandbox as `df`. Do not try to read it yourself using `pd.read_csv`.
4. Make sure your Python code uses `print()` to output the results of your calculations.
5. You must execute Python code to get the actual numbers if the task requires calculating, checking, sorting, or analyzing data. Do NOT answer theoretically or explain how to do it in the `answer` field without running the code first.
6. Once you have run the necessary code and have the actual results from the execution output, provide the final answer (including the real numbers/results) in the `answer` field and leave `code` as null.
7. CRITICAL: Do NOT use your prior knowledge or make assumptions. You must use the EXACT numbers and categories returned in the sandbox execution output. If you make up or guess any numbers or states (like Lagos/Abuja), you will fail.
8. CRITICAL: Your response must be valid JSON. Never use triple double-quotes (\"\"\") for multi-line strings. Use standard double-quotes (\") and represent line breaks with \\n. Escape double-quotes inside string values as \\\".

You must respond with a JSON object matching this schema:
{{
    "code": "Python/Pandas code to run (string or null)",
    "answer": "The final response answering the current task (string or null)"
}}
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Please execute the current task: {current_step}")
    ]

    code_executed = False
    while True:
        response = llm.invoke(messages)
        
        action = None
        try:
            action = json.loads(response.content)
        except Exception:
            import re
            code = None
            code_match = re.search(r'"code"\s*:\s*"""(.*?)"""', response.content, re.DOTALL)
            if not code_match:
                code_match = re.search(r'"code"\s*:\s*"(.*?)"\s*(?:,|\n|\})', response.content, re.DOTALL)
            if code_match:
                code = code_match.group(1).strip()
                if code == "null":
                    code = None
                elif not response.content.count('"""') and code:
                    try:
                        code = code.encode().decode('unicode_escape')
                    except Exception:
                        pass

            answer = None
            answer_match = re.search(r'"answer"\s*:\s*"""(.*?)"""', response.content, re.DOTALL)
            if not answer_match:
                answer_match = re.search(r'"answer"\s*:\s*"(.*?)"\s*(?:,|\n|\})', response.content, re.DOTALL)
            if answer_match:
                answer = answer_match.group(1).strip()
                if answer == "null":
                    answer = None
                elif not response.content.count('"""') and answer:
                    try:
                        answer = answer.encode().decode('unicode_escape')
                    except Exception:
                        pass

            if code is not None or answer is not None:
                action = {"code": code, "answer": answer}

        if action is None:
            print(f"EXECUTOR: Error parsing JSON. Content was:\n{response.content}")
            final_answer = f"Error executing task. Invalid JSON returned: {response.content}"
            break

        code = action.get("code")
        answer = action.get("answer")
        if code_executed and answer:
            final_answer = answer
            break

        if code:
            print(f"EXECUTOR: Running Pandas Code...")
            print("-" * 40)
            print(code)
            print("-" * 40)

            tool_output = execute_pandas.invoke({"code": code})

            print(f"SANDBOX OUTPUT:\n{tool_output}\n")
            messages.append(response)
            messages.append(HumanMessage(content=f"Execution output of the code:\n{tool_output}"))
            code_executed = True
            continue

        if answer:
            final_answer = answer
            break

        final_answer = "No response was generated by the Executor."
        break

    print("EXECUTOR: Step complete.")

    return {
        "past_steps": [
            (current_step, final_answer)
        ],
        "plan": state["plan"][1:]
    }
