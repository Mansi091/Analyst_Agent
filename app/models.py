from pydantic import BaseModel, Field
from typing import List, Optional


class AnalysisPlan(BaseModel):
    """
    The structured plan created by the Planner.
    """

    steps: List[str] = Field(
        description="Sequential analytical steps required to answer the user's question."
    )


class ReviewerDecision(BaseModel):
    """
    The structured decision made by the Reviewer.
    """

    final_report: Optional[str] = Field(
        default=None,
        description="Final report if the analysis is complete."
    )

    plan: Optional[List[str]] = Field(
        default=None,
        description="Remaining steps if more analysis is required."
    )


class ExecutorAction(BaseModel):
    """
    The structured action decided by the Executor.
    """

    code: Optional[str] = Field(
        default=None,
        description="Python/Pandas code to run on the dataset 'df' to analyze it. Use print() to output results. Leave empty if no code execution is needed."
    )

    answer: Optional[str] = Field(
        default=None,
        description="The final response answering the current task. Provide this only after you have run the code and analyzed the results."
    )
