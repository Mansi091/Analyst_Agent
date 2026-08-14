import os
import json
import shutil
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Analyst Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def send_event(event: dict) -> str:
    """Format an event as an NDJSON line."""
    return json.dumps(event) + "\n"


async def event_streamer(initial_state: dict | None, thread_id: str):
    from app.graph import graph

    config = {"configurable": {"thread_id": thread_id}}
    
    if initial_state is not None:
        yield send_event({"type": "thread", "thread_id": thread_id})
        yield send_event({"type": "status", "phase": "planner", "message": "Decomposing your question into an analysis plan"})

    try:
        async for update in graph.astream(initial_state, config, stream_mode="updates"):
            for node, state_update in update.items():
                if node == "Planner":
                    yield send_event({"type": "plan", "plan": state_update["plan"]})
                    yield send_event({"type": "status", "phase": "cleaner", "message": "Cleaning the dataset"})
                    yield send_event({"type": "step", "step": {"id": "clean", "title": "Clean the dataset", "status": "running", "result": ""}})
                elif node == "Cleaner":
                    yield send_event({"type": "step", "step": {"id": "clean", "title": "Clean the dataset", "status": "done", "result": "Cleaned dataset successfully."}})
                elif node == "Executor":
                    past_steps = state_update.get("past_steps", []) if state_update else []
                    if past_steps:
                        desc, res = past_steps[-1]
                        yield send_event({"type": "step", "step": {"id": f"exec-{len(past_steps)}", "title": desc, "status": "done", "result": str(res)}})
                    yield send_event({"type": "status", "phase": "reviewer", "message": "Reviewing results"})
                elif node == "Reviewer":
                    if state_update and state_update.get("final_report"):
                        yield send_event({"type": "report", "report": state_update["final_report"]})
        
        state_snap = graph.get_state(config)
        if "Executor" in state_snap.next:
            plan = state_snap.values.get("plan", [])
            next_step = plan[0] if plan else "Unknown step"
            past_len = len(state_snap.values.get("past_steps", []))
            exec_id = f"exec-{past_len + 1}"
            
            yield send_event({"type": "status", "phase": "executor", "message": "Waiting for human approval..."})
            yield send_event({"type": "step", "step": {"id": exec_id, "title": next_step, "status": "running", "result": ""}})
            
            yield send_event({"type": "paused", "thread_id": thread_id, "next_step": next_step})
            return

        yield send_event({"type": "done"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        yield send_event({"type": "error", "message": f"Pipeline failed: {str(e)}"})
        yield send_event({"type": "done"})


@app.post("/api/analyze")
async def analyze(
    file: UploadFile = File(...),
    question: str = Form(...),
    schema_context: str = Form(...),
):
    """
    Accepts a CSV file upload + question, runs the LangGraph pipeline,
    and streams NDJSON events back to the frontend.
    """
    os.makedirs("data", exist_ok=True)
    dataset_path = f"data/{file.filename}"

    with open(dataset_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    name, ext = os.path.splitext(file.filename)
    cleaned_dataset_path = f"data/{name}_cleaned{ext}"

    from app.state import AnalystState
    import uuid
    
    initial_state: AnalystState = {
        "input": question,
        "dataset_path": dataset_path,
        "cleaned_dataset_path": cleaned_dataset_path,
        "dataset_context": schema_context,
        "plan": [],
        "past_steps": [],
        "final_report": None,
    }
    
    thread_id = str(uuid.uuid4())

    return StreamingResponse(
        event_streamer(initial_state, thread_id),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache, no-transform"},
    )

@app.post("/api/resume")
async def resume(thread_id: str = Form(...)):
    """
    Resumes a paused thread after user approval.
    """
    return StreamingResponse(
        event_streamer(None, thread_id),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache, no-transform"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
