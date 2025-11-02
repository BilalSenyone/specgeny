"""
src/examples/ex26_block_approval.py

Approve blocks one at a time, with regeneration on rejection
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()

class BlockState(TypedDict):
    blocks: List[dict]
    current_index: int
    approved_blocks: List[dict]
    user_approved: bool
    user_feedback: str

def generate_block(state: BlockState) -> BlockState:
    """ Generate next block """
    