import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

from app.state import AnalystState
from app.tool import execute_pandas

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=0,
    max_tokens=4096,
)

def Cleaner_node(state: AnalystState):
    print("\nCLEANER: Cleaning the dataset...")

    system_prompt = f"""
You are a Data Engineer.
Your job is to write a Python script using pandas to clean the dataset BEFORE analysis begins.

Dataset Schema:
{state["dataset_context"]}

Raw dataset path: {state["dataset_path"]}
Cleaned dataset save path: {state["cleaned_dataset_path"]}

Instructions:
1. Load the raw dataset using `df = pd.read_csv('{state["dataset_path"]}')`.
2. Impute missing values for numeric columns (e.g. median).
3. Clean column string values (e.g. strip whitespace and standardize capitalization to Title Case).
4. Standardize any date columns to YYYY-MM-DD format.
5. You MUST save the cleaned DataFrame to: `{state["cleaned_dataset_path"]}` using `df.to_csv('{state["cleaned_dataset_path"]}', index=False)`.

You must respond with a JSON object matching this schema:
{{
    "code": "Python code to run (string)"
}}
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Please write the code to clean the dataset and save it.")
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

    action = None
    try:
        content = raw_content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        action = json.loads(content)
    except Exception:
        print(f"CLEANER: Error parsing JSON. Content was:\n{raw_content}")
        import re
        code = None
        
        if "```python" in raw_content:
            match = re.search(r'```python(.*?)```', raw_content, re.DOTALL)
            if match:
                code = match.group(1).strip()
        
        if not code:
            code_match = re.search(r'"code"\s*:\s*"""(.*?)"""', raw_content, re.DOTALL)
            if not code_match:
                code_match = re.search(r'"code"\s*:\s*"(.*?)"\s*(?:,|\n|\})', raw_content, re.DOTALL)
            if code_match:
                code = code_match.group(1).strip()
                if code == "null":
                    code = None
                elif not raw_content.count('"""') and code:
                    try:
                        code = code.encode().decode('unicode_escape')
                    except Exception:
                        pass
        
        if code is not None:
            action = {"code": code}

    if action and action.get("code"):
        tool_output = execute_pandas.invoke({"code": action["code"]})
        print(f"CLEANER: Cleaning complete. Sandbox Output:\n{tool_output}\n")
    
    return state
