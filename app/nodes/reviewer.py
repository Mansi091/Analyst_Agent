import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

from app.state import AnalystState


load_dotenv()


llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=0,
    max_tokens=4096,
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
    "is_complete": true,
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
- Set is_complete to true.
- Create a professional final report summarizing the findings.
- Put the report in final_report.

If the analysis is NOT complete (and we should continue with the remaining plan):
- Set is_complete to false.
- Set final_report to null.

CRITICAL: Your response must be valid JSON. Never use triple double-quotes (\"\"\") for multi-line strings. Use standard double-quotes (\") and represent line breaks with \\n. Escape double-quotes inside string values as \\\".

You must respond with a JSON object matching this schema:
{{
    "is_complete": boolean,
    "final_report": "The comprehensive final report (string) OR null"
}}
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Please review the progress and provide your decision in JSON format.")
    ]

    response = llm.invoke(messages)

    decision = None
    raw_content = response.content
    if isinstance(raw_content, list):
        texts = []
        for part in raw_content:
            if isinstance(part, dict) and "text" in part:
                texts.append(part["text"])
            else:
                texts.append(str(part))
        raw_content = "\n".join(texts)
    elif not isinstance(raw_content, str):
        raw_content = str(raw_content)

    try:
        content = raw_content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        decision = json.loads(content)
    except Exception:
        import re
        final_report = None
        report_match = re.search(r'"final_report"\s*:\s*"""(.*?)"""', raw_content, re.DOTALL)
        if not report_match:
            report_match = re.search(r'"final_report"\s*:\s*"(.*?)"\s*(?:,|\n|\})', raw_content, re.DOTALL)
        if report_match:
            final_report = report_match.group(1).strip()
            if final_report == "null":
                final_report = None
            elif not raw_content.count('"""') and final_report:
                try:
                    final_report = final_report.encode().decode('unicode_escape')
                except Exception:
                    pass

        if final_report is not None:
            decision = {"final_report": final_report}

    if decision is None:
        print(f"REVIEWER: Error parsing JSON. Content was:\n{raw_content}")
        return {
            "final_report": f"Error: The Reviewer returned invalid JSON: {raw_content}"
        }

    is_complete = decision.get("is_complete")
    
    if is_complete is None:
        if not state["plan"] and decision.get("final_report"):
            is_complete = True
        else:
            is_complete = False

    if is_complete and decision.get("final_report"):
        print("REVIEWER: Analysis complete.")
        return {
            "final_report": decision["final_report"],
            "plan": []
        }
    else:
        print("REVIEWER: More analysis required.")
        return {}
