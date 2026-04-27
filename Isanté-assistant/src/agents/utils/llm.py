import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Make sure we load the environment variables from .env file
load_dotenv()

# Check if API key is available and print status
api_key = os.environ.get("OPENAI_API_KEY")
if api_key:
    print("OpenAI API key found in environment variables")
else:
    print("Warning: No OpenAI API key found in environment variables")

# Initialize the LLM 
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2,
    openai_api_key=api_key,
) 