"""
Advanced: Build a chain that not only extracts requirements but also:

1. Analyzes dependencies between requirements
2. Builds a dependency graph (which requirements block others)
3. Suggests implementation order based on dependencies
4. Detects circular dependencies and warns the user

"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict, Set
import networkx as nx 
from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI(model="gpt-4", temperature=0)


class RequirementGraph(BaseModel):
    """Requirement dependency graph"""
    requirements: List[Requirement]
    adjacency_list: Dict[str, List[str]]  # req_id -> [dependent_req_ids]
    implementation_order: List[str]  # Topologically sorted
    circular_dependencies: List[List[str]]  # Any cycles detected

def build_dependency_graph(requirements: List[Requirement]) -> RequirementGraph:
    """Build graph and detect issues"""
    # TODO: Implement graph building
    # TODO: Use topological sort for implementation order
    # TODO: Detect cycles using DFS
    pass

# TODO: Integrate into your extraction chain