from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv


load_dotenv()

# Test Antropic
try:
    claude = ChatAnthropic (model="claude-3-5-sonnet-20241022")
    response = claude.invoke ("Say, 'Langchain is working!'")
    print("✓ Claude:", response.content)
except Exception as e :
    print ("X Claude: ", str(e)) 


# Test OpenAI
try:
    gpt = ChatOpenAI(model="gpt-4")
    response = gpt.invoke ("Say, 'Langchain is working!'")
    print("✓ GPT-4:", response.content)
except Exception as e:
    print ("X GPT-4: ", str(e))
