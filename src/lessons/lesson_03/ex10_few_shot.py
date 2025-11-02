"""
src/examples/ex10_few_shot.py

Using few-shot learning for consistent requirement extraction
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-4", temperature=0)

# Define examples (few-shot learning)
examples = [
    {
        "input": "Users can create accounts with email and password",
        "output": """FR-001: System SHALL provide user account creation functionality
FR-002: System SHALL validate email address format during registration
FR-003: System SHALL enforce minimum password length of 8 characters"""
    },
    {
        "input": "Show a list of all products with images and prices",
        "output": """FR-001: System SHALL display product catalog as a paginated list
FR-002: System SHALL show product image thumbnail for each item
FR-003: System SHALL display current price for each product"""
    },
    {
        "input": "Users receive email notifications when someone comments",
        "output": """FR-001: System SHALL send email notification when new comment is posted
FR-002: System SHALL include comment content in notification email
FR-003: System SHALL provide unsubscribe link in notification emails"""
    }
]

# Create few-shot template
example_prompt = ChatPromptTemplate.from_messages([
    ("human", "{input}"),
    ("ai", "{output}")
])


# Create few-shot template
few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt = example_prompt,
    examples=examples
)

# Build final prompt with examples
final_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a requirements analyst. Extract functional requirements from user descriptions.
FORMAT : FR-XXX: System SHALL [specific capability]
RULES : 
- Maximum 3 requirements per feature
- Each requirement must be testable
- No implementation details
- Use SHALL for mandatory requirements"""),
few_shot_prompt,
("human", "{input}")
])

chain = final_prompt | llm

# Test with new input
test_input = "Users can search products by name and filter by category"
result = chain.invoke ({"input": test_input})

print("Input:", test_input)
print("\nOutput:")
print(result.content)