import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

load_dotenv()

# Load API key from environment
api_key = os.getenv("NEXUS_API_KEY")
api_base = "https://genai-nexus.api.corpinter.net/apikey/"
api_version = "2024-06-01"

def create_chain():
    """Create and return a LangChain chain using AzureChatOpenAI."""
    model = AzureChatOpenAI(
        openai_api_key=api_key,
        azure_endpoint=api_base,
        openai_api_version=api_version,
        deployment_name="gpt-4o-mini"  # Replace with your actual deployment name
    )
    
    prompt = PromptTemplate.from_template(
        "You are a helpful assistant. {context}"
    )
    
    # Using LLMChain instead of RunnableSequence
    chain = LLMChain(
        llm=model,
        prompt=prompt
    )
    return chain

def main():
    """Main function to test LangChain with Azure OpenAI."""
    chain = create_chain()

    try:
        # Define the context and prompt for the model
        context = "wish me good morning"
        
        # Run the chain
        result = chain.invoke({"context": context})
        
        # Print the result
        print(result['text'] if 'text' in result else str(result))

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
