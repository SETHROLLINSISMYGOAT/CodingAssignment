from fastapi import FastAPI, HTTPException
from typing import Dict, Any

from .models import (
    State, GraphDefinition, EdgeDefinition, GraphCreateRequest, 
    GraphRunRequest, ExecutionResult
)
from .core import create_graph, run_workflow_sync, RUN_STORE

app = FastAPI(title="Minimal Agent Workflow Engine")

# --- Sample Workflow Definition (Code Review Mini-Agent) ---

CODE_REVIEW_GRAPH_DEF = GraphDefinition(
    name="Code Review Mini-Agent",
    initial_node="extract",
    nodes={
        "extract": "extract_functions",
        "complexity": "check_complexity",
        "issues": "detect_basic_issues",
        "suggest": "suggest_improvements",
    },
    edges=[
        # Simple sequence
        EdgeDefinition(source="extract", target="complexity"),
        EdgeDefinition(source="complexity", target="issues"),
        EdgeDefinition(source="issues", target="suggest"),
        
        # Looping/Branching (If quality_score < 80, go back to 'extract')
        EdgeDefinition(
            source="suggest", 
            target="extract", 
            condition={"quality_score": 80} # Loop condition: if state.quality_score < 80
        ),
        
        # Termination: No unconditional edge from 'suggest' means the workflow stops
    ]
)

# Pre-load the sample graph on startup
SAMPLE_GRAPH_ID = create_graph(CODE_REVIEW_GRAPH_DEF)
print(f"Sample Graph 'Code Review Mini-Agent' created with ID: {SAMPLE_GRAPH_ID}")

# --- API Endpoints ---

@app.post("/graph/create", response_model=Dict[str, str], status_code=201)
async def api_create_graph(request: GraphCreateRequest):
    """Registers a new workflow graph definition."""
    graph_id = create_graph(request.graph)
    return {"graph_id": graph_id}

@app.post("/graph/run", response_model=ExecutionResult)
async def api_run_graph(request: GraphRunRequest):
    """
    Executes a registered graph with an initial state.
    Returns the final state and execution log.
    """
    try:
        run_id, final_state, log = run_workflow_sync(request.graph_id, request.initial_state)
        
        return ExecutionResult(
            run_id=run_id,
            final_state=final_state,
            log=log
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
@app.get("/graph/state/{run_id}", response_model=Dict[str, Any])
async def api_get_state(run_id: str):
    """Return the final state of a completed workflow."""
    if run_id not in RUN_STORE:
        raise HTTPException(status_code=404, detail=f"Run ID {run_id} not found.")
        
    state, log = RUN_STORE[run_id]
    
    return {
        "run_id": run_id,
        "status": log[-1].status,
        "final_state": state.model_dump(exclude_defaults=True)
    }

@app.get("/")
def get_info():
    return {
        "engine_status": "Operational",
        "sample_graph_id": SAMPLE_GRAPH_ID,
        "instructions": "Go to /docs for interactive API testing.",
        "example_run_payload_to_LOOP": {
            "graph_id": SAMPLE_GRAPH_ID,
            "initial_state": {
                # This code is long enough (12 lines) to trigger a -30 score (Quality = 70) 
                # which is < 80, forcing a loop back to extract (which then fixes the length).
                "code": "def long_func():\n    a = 1\n    b = 2\n    c = 3\n    d = 4\n    e = 5\n    f = 6\n    g = 7\n    h = 8\n    i = 9\n    j = 10\n    k = 11\n    return k",
                "quality_score": 0
            }
        }
    }