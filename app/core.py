from typing import Dict, Any, Optional, Tuple, Callable, List
import uuid

from .models import State, GraphDefinition, EdgeDefinition, RunLogEntry
from .registry import NODE_REGISTRY

# --- In-Memory Stores ---
GRAPH_STORE: Dict[str, GraphDefinition] = {}
RUN_STORE: Dict[str, Tuple[State, List[RunLogEntry]]] = {}

# --- Engine Logic ---

def create_graph(graph_def: GraphDefinition) -> str:
    """Registers a new workflow graph."""
    graph_id = str(uuid.uuid4())
    GRAPH_STORE[graph_id] = graph_def
    return graph_id

def _get_next_node(graph_def: GraphDefinition, current_node: str, state: State) -> Optional[str]:
    """Determines the next node based on edges and conditions."""
    
    possible_edges = [e for e in graph_def.edges if e.source == current_node]

    # 1. Check Conditional Edges (Branching/Looping)
    for edge in possible_edges:
        if edge.condition:
            # Check for the looping condition: loop if state.quality_score < threshold
            if "quality_score" in edge.condition:
                threshold = edge.condition["quality_score"]
                if state.quality_score < threshold:
                    return edge.target

    # 2. Check Default/Unconditional Edge (Simple Sequence)
    default_edge = next((e for e in possible_edges if not e.condition), None)
    if default_edge:
        return default_edge.target
        
    return None # Termination if no transition matches

def run_workflow_sync(graph_id: str, initial_state: State) -> Tuple[str, State, List[RunLogEntry]]:
    """Synchronously executes the entire workflow."""
    
    if graph_id not in GRAPH_STORE:
        raise ValueError(f"Graph ID {graph_id} not found.")

    graph_def = GRAPH_STORE[graph_id]
    state = initial_state.model_copy(deep=True)
    current_node_name = graph_def.initial_node
    log: List[RunLogEntry] = []
    MAX_ITERATIONS = 5 # Safety limit for loops

    run_id = str(uuid.uuid4())
    
    log.append(RunLogEntry(node="ENGINE", status="START", message=f"Starting run {run_id}"))

    for i in range(MAX_ITERATIONS):
        
        if current_node_name is None:
            break # Workflow completed (clean exit)
        
        # Validation checks
        if current_node_name not in graph_def.nodes:
            log.append(RunLogEntry(node="ENGINE_ERROR", status="TERMINATED", message=f"Node '{current_node_name}' not defined."))
            break
            
        node_func_name = graph_def.nodes[current_node_name]
        node_func = NODE_REGISTRY.get(node_func_name)
        
        if not node_func:
            log.append(RunLogEntry(node="ENGINE_ERROR", status="TERMINATED", message=f"Function '{node_func_name}' not found in registry."))
            break

        # --- Node Execution ---
        log.append(RunLogEntry(node=current_node_name, status="START", message=f"Executing function: {node_func_name} (Iteration {state.iteration})"))
        
        try:
            new_state = node_func(state.model_copy(deep=True))
            state = new_state
        except Exception as e:
            log.append(RunLogEntry(node=current_node_name, status="TERMINATED", message=f"Error: {str(e)}"))
            break
            
        log.append(RunLogEntry(node=current_node_name, status="END", message=f"State updated. Quality Score: {state.quality_score}"))
        
        # --- Transition ---
        next_node_name = _get_next_node(graph_def, current_node_name, state)
        
        # Check if the transition is a loop back to the initial node
        if next_node_name == graph_def.initial_node:
            state.iteration += 1
            log.append(RunLogEntry(node="ENGINE", status="LOOP_CONTINUE", message=f"Looping back. Condition met: quality_score < 80. Next Iteration: {state.iteration}"))

        current_node_name = next_node_name
    else:
        # Loop terminated because max iterations were reached
        if current_node_name is not None:
             log.append(RunLogEntry(node="ENGINE", status="MAX_ITERATIONS_REACHED", message=f"Exceeded max iterations ({MAX_ITERATIONS}). Terminating."))

    # --- Finalization ---
    if current_node_name is None:
        log.append(RunLogEntry(node="ENGINE", status="TERMINATED", message="Workflow completed successfully."))
    
    RUN_STORE[run_id] = (state, log)
    
    return run_id, state, log