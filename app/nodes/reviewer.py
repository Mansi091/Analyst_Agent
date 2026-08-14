import json
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from dotenv import load_dotenv

from app.state import AnalystState


load_dotenv()


llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    max_tokens=4096,
    max_retries=10
)


def reviewer_node(state: AnalystState):

    print("\nREVIEWER: Checking progress...")

    completed_steps = ""
    if state["past_steps"]:
        for i, (step, result) in enumerate(state["past_steps"], 1):
            completed_steps += f"Step {i}: {step}\nResult:\n{result}\n\n"
    else:
        completed_steps = "None"

    if not state["plan"]:
        system_prompt = f"""
You are a Senior Data Analyst reviewing the completed analysis.

Original user question:
{state["input"]}

Dataset information:
{state["dataset_context"]}

Completed steps and their results:
{completed_steps}

The analysis plan is fully completed. You MUST now compile a professional final report answering the user's question based on the completed steps and results.

CRITICAL: Do NOT invent or make up any numbers, statistics, or state names. You must extract and quote the exact values and text returned in the Completed steps and their results. (For example, check the exact numbers of missing values, the exact names of the top 3 states and their total sales).

CRITICAL: Your response must be valid JSON. Never use triple double-quotes (\"\"\") for multi-line strings. Use standard double-quotes (\") and represent line breaks with \\n. Escape double-quotes inside string values as \\\".

You must respond with a JSON object matching this schema:
{{
    "final_report": "The comprehensive final report (string)"
}}
"""
    else:
        remaining_plan = "\n".join(f"- {step}" for step in state["plan"])
        system_prompt = f"""
You are a Senior Data Analyst reviewing an ongoing analysis.

Original user question:
{state["input"]}

Dataset information:
{state["dataset_context"]}

Remaining plan:
{remaining_plan}

Completed steps and their results:
{completed_steps}

Your job is to determine whether the user's original question has been completely answered.

If the analysis is complete:
- Create a professional final report summarizing the findings.
- Put the report in final_report.

If the analysis is NOT complete (and we should continue with the remaining plan):
- Set final_report to null.

CRITICAL: Your response must be valid JSON. Never use triple double-quotes (\"\"\") for multi-line strings. Use standard double-quotes (\") and represent line breaks with \\n. Escape double-quotes inside string values as \\\".

You must respond with a JSON object matching this schema:
{{
    "final_report": "The comprehensive final report (string or null)"
}}
"""

    messages = [
        SystemMessage(content=system_prompt)
    ]

    response = llm.invoke(messages)

    decision = None
    try:
        decision = json.loads(response.content)
    except Exception:
        import re
        final_report = None
        report_match = re.search(r'"final_report"\s*:\s*"""(.*?)"""', response.content, re.DOTALL)
        if not report_match:
            report_match = re.search(r'"final_report"\s*:\s*"(.*?)"\s*(?:,|\n|\})', response.content, re.DOTALL)
        if report_match:
            final_report = report_match.group(1).strip()
            if final_report == "null":
                final_report = None
            elif not response.content.count('"""') and final_report:
                try:
                    final_report = final_report.encode().decode('unicode_escape')
                except Exception:
                    pass

        if final_report is not None:
            decision = {"final_report": final_report}

    if decision is None:
        print(f"REVIEWER: Error parsing JSON. Content was:\n{response.content}")
        return {
            "final_report": f"Error: The Reviewer returned invalid JSON: {response.content}"
        }

    if decision.get("final_report"):
        print("REVIEWER: Analysis complete.")
        return {
            "final_report": decision["final_report"],
            "plan": []
        }
    else:
        print("REVIEWER: More analysis required.")
        return {}