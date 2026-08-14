from langgraph.graph import StateGraph,START,END
from typing import TypedDict,Annotated,List,Tuple,Optional
import operator

class AnalystState(TypedDict):
    input: str
    dataset_path: str
    dataset_context: str
    plan: List[str]
    past_steps: Annotated[
        List[Tuple[str, str]],
        operator.add
    ]
    final_report: Optional[str]