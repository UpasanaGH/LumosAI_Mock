import os
import openai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("NEXUS_API_KEY")
api_base = "https://genai-nexus.api.corpinter.net/apikey/"

openai.api_type = "azure"
openai.api_base = api_base
openai.api_version = "2024-06-01"
openai.api_key = api_key

def main():
    try:
        completion = openai.ChatCompletion.create(
            deployment_id="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Generate a java code for adding two numbers"}
            ]
        )
        print(completion.choices[0].message["content"])

    except openai.error.APIError as e:
        print(f"APIError: {e}")
    except openai.error.InvalidRequestError as e:
        print(f"InvalidRequestError: {e}")

if __name__ == "__main__":
    main()

