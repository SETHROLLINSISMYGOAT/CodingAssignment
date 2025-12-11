from typing import Callable, Dict, Any, List
from .models import State

# --- Tool Registry ---
TOOL_REGISTRY: Dict[str, Callable] = {}

def register_tool(name: str):
    """Decorator to register a function as a callable tool."""
    def decorator(func: Callable):
        TOOL_REGISTRY[name] = func
        return func
    return decorator

# --- Tool Implementation ---

def node_detect_smells(code: str) -> Dict[str, Any]:
    """A mock tool to detect code issues."""
    score_delta = 0
    issues = []
    
    if "magic_number" in code:
        issues.append("Magic number detected (hardcoded value).")
        score_delta -= 20
    if len(code.split('\n')) > 10:
         issues.append("Function is too long (over 10 lines).")
         score_delta -= 30 # Heavy penalty to ensure the workflow loops

    return {"issues": issues, "score_delta": score_delta}

@register_tool("detect_smells")
def tool_detect_smells(code: str) -> Dict[str, Any]:
    return node_detect_smells(code)

# --- Node Implementation (The Workflow Steps) ---

def extract_functions(state: State) -> State:
    """Node 1: Extract functions (mock implementation)."""
    # Reset state for a new iteration if looping
    if state.iteration > 0:
        state.quality_score = 0
        state.issues = []
        state.suggestions = []
        
    functions = [
        line.strip()
        for line in state.code.split('\n')
        if line.strip().startswith("def ")
    ]
    state.functions = functions
    return state

def check_complexity(state: State) -> State:
    """Node 2: Check complexity (mock implementation)."""
    state.complexity_score = len(state.code.split('\n')) // 5 + len(state.functions) * 3
    return state

def detect_basic_issues(state: State) -> State:
    """Node 3: Use a tool to detect issues and update state."""
    
    result = TOOL_REGISTRY["detect_smells"](state.code)
    
    state.issues.extend(result["issues"])
    
    # Start quality score at 100 and apply penalties
    if state.quality_score == 0:
        state.quality_score = 100 + result["score_delta"]
    else:
        state.quality_score += result["score_delta"]
        
    return state

def suggest_improvements(state: State) -> State:
    """Node 4: Suggest improvements and update the code (mock for loop)."""
    
    if state.issues:
        state.suggestions.append(f"Found {len(state.issues)} issues. Suggestions generated.")
        
        # Mock fixing the 'too long' issue by truncating the code
        if any("too long" in issue for issue in state.issues):
            state.code = "\n".join(state.code.split('\n')[:8]) # Truncate code to 8 lines
            state.suggestions.append("CODE MODIFIED: Truncated code to simulate fixing 'too long' issue for the next iteration.")
        
        if any("magic number" in issue for issue in state.issues):
            state.suggestions.append("Refactor magic numbers into constants.")

    return state

# --- Node Registry (Mapping for the Engine) ---
NODE_REGISTRY: Dict[str, Callable[[State], State]] = {
    "extract_functions": extract_functions,
    "check_complexity": check_complexity,
    "detect_basic_issues": detect_basic_issues,
    "suggest_improvements": suggest_improvements,
}