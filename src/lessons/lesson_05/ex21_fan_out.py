"""
src/examples/ex21_fan_out.py

Parallel requirement extraction
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END

class FanOutState(TypedDict):
    features: List[str]
    results : List[dict]

def process_feature_1(state: FanOutState) -> FanOutState:
    """ Process first feature"""
    first_feature = state["features"][0]

    return {"results":  [{
        "feature": first_feature,
        "requirements": ["FR-001", "FR-002"]
    }]} # return the first feature and the requirements as a list of dictionaries

def process_feature_2(state: FanOutState) -> FanOutState:
    """ Process second feature"""
    second_feature = state["features"][1]
    return {"results": [{"feature": second_feature, "requirements": ["FR-003"]}]} # return the second feature and the requirements as a list of dictionaries

# These nodes run in parallel
# (LangGraph detects no dependencies and executes concurrently)

