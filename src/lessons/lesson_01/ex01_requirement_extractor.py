"""
Exercise 1: Requirement Extractor

Create a prompt template that extracts functional requirements
from natural language descriptions.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-4", temperature=0)

# TODO: Create your prompt template here
# Hints:
# - Use ChatPromptTemplate.from_messages()
# - Include a system message that defines the AI's role
# - Include a user message with a {description} variable
# - Specify constraints (max 5 requirements, testable, no tech details)

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a requirements analyst specializing in functional specifications.
    Your task is to extract functional requirements from natural language feature descriptions.
    RULES:
    - Extract maximum 5 functional requirements
    - Format each as: FR-XXX: System MUST/SHALL/SHOULD [specific capability]
    - Each requirement MUST be testable and verifiable
    - Focus on WHAT the system must do, NOT HOW it's implemented
    - Avoid technology-specific details (no "database", "API", "React", etc.)
    - Use clear, unambiguous language
    - No more than 20 words per requirement
    """),
    ("user", "{user_description}")
])

# Test cases (user messages)
test_descriptions = [
    """I want to build a user login system where users can sign in with
    their email and password. If they forget their password, they should
    be able to reset it via email. After 3 failed login attempts, their
    account should be temporarily locked for security.""",

    """Create a task management feature where users can create tasks,
    assign them to team members, set due dates, and mark them as complete.
    Users should be able to filter tasks by status and assignee.""",

    """Build a notification system that alerts users when they receive
    a new message, when someone mentions them, or when a task is assigned
    to them. Users should be able to customize which notifications they receive."""
]

# TODO: Run your prompt template on each test case
for i, description in enumerate(test_descriptions, 1):
    print(f"\n{'='*70}")
    print(f"Test Case {i}")
    print(f"{'='*70}")
    print(f"Input: {description[:100]}...")
    print(f"\nExtracted Requirements:")

    chain = prompt | llm
    response = chain.invoke({"user_description": description})
    print(response.content)