from pydantic import BaseModel, Field
from typing import Dict, Any, List, Literal, Optional

# --- Core Engine Models ---

class State(BaseModel):
    """The shared state that flows between nodes."""
    code: str = Field(..., description="The code snippet being analyzed.")
    functions: List[str] = Field(default_factory=list, description="Extracted functions.")
    complexity_score: int = 0
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    quality_score: int = 0
    iteration: int = 0

class EdgeDefinition(BaseModel):
    """Defines a transition from one node to the next."""
    source: str
    target: str
    condition: Optional[Dict[str, Any]] = None

class GraphDefinition(BaseModel):
    """Defines the entire workflow graph."""
    name: str
    nodes: Dict[str, str] = Field(..., description="Mapping of node_name to function_name in the registry.")
    edges: List[EdgeDefinition]
    initial_node: str

class RunLogEntry(BaseModel):
    """A single entry in the execution log."""
    node: str
    status: Literal["START", "END", "LOOP_CONTINUE", "TERMINATED", "MAX_ITERATIONS_REACHED"]
    message: str = ""

class ExecutionResult(BaseModel):
    """Result of a workflow run."""
    run_id: str
    final_state: State
    log: List[RunLogEntry]

# --- API Request Models ---

class GraphCreateRequest(BaseModel):
    """Input for POST /graph/create."""
    graph: GraphDefinition

class GraphRunRequest(BaseModel):
    """Input for POST /graph/run."""
    graph_id: str
    initial_state: State