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


def planner_node(state: AnalystState):

    print("\nPLANNER: Creating analysis plan...")

    system_prompt = f"""
You are a Lead Data Analyst.

The user wants an answer to:
{state["input"]}

The available dataset is:
{state["dataset_path"]}

Dataset information:
{state["dataset_context"]}

Create a clear, sequential plan for answering the user's question.

Rules:
1. Break the problem into specific analytical tasks.
2. Each task should be something that can be executed using Python/Pandas.
3. Do not actually perform the analysis.
4. Do not invent columns that are not present in the dataset.
5. Keep the plan as short as possible while still completely answering the question.

You must respond with a JSON object matching this schema:
{{
    "steps": ["step 1", "step 2", ...]
}}
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["input"])
    ]

    response = llm.invoke(messages)
    
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
        
        plan_data = json.loads(content)
        steps = plan_data.get("steps", [])
    except Exception as e:
        print(f"PLANNER: Error parsing JSON, fallback to default step. Error: {e}")
        steps = [f"Analyze the dataset to answer: {state['input']}"]

    print("\n--- PLAN GENERATED ---")

    for i, step in enumerate(steps, start=1):
        print(f"{i}. {step}")

    return {
        "plan": steps
    }
