"""
src/examples/ex04_system_prompts.py

Using system prompts to control AI behavior
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv


load_dotenv()

llm = ChatOpenAI(model="gpt-4", temperature=0)

#Different system prompts for different behaviors
dict_behaviors = {
"concise" : """You are a concise technical writer.
Respond in 1-2 sentences maximum. Be direct and precise.""",

"detailed" : """You are a detailed technical writer.
Provide comprehensive explanations with examples and context.
Break down complex concepts into digestible parts. No more than 2 sentences.""",

"structured" : """You are a structure technical writer.
Always format your response as : 
1. Definition
2. Key components
3. Example
4. Best Practices 
No more than 2 sentences"""
}

user_question = "What is a functional requirement?"

for style, system_prompt in dict_behaviors.items():
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{question}")
    ])

    chain = prompt | llm
    response = chain.invoke({"question": user_question})

    print(f"\n{'='*60}")
    print(f"Style: {style}")
    print(f"{'='*60}")
    print(response.content)