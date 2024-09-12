from dotenv import load_dotenv
import os
import openai
import streamlit as st
from PyPDF2 import PdfReader
from htmlTemplates import bot_template, user_template, css
import certifi

load_dotenv()

api_base = "https://genai-nexus.api.corpinter.net/apikey/openai/deployments/gpt-4o-mini/chat/completions"
api_key = os.getenv("NEXUS_API_KEY")

openai.api_type = "azure"
openai.api_base = api_base
openai.api_version = "2024-06-01"
openai.api_key = api_key

# Ensure SSL certificate
os.environ['CURL_CA_BUNDLE'] = certifi.where()

def get_pdf_text(pdf_files):
    """Extract text from the uploaded PDF files."""
    text = ""
    if pdf_files:
        for pdf_file in pdf_files:
            pdf_reader = PdfReader(pdf_file)
            for page in pdf_reader.pages:
                text += page.extract_text()
    return text

def create_chain():
    """Return the deployment name."""
    deployment_name = "gpt-4o-mini"  
    return deployment_name

def handle_user_input(question, pdf_content):
    """Handle user input and provide responses using OpenAI's GPT-4o-mini model."""
    try:
        deployment_name = st.session_state.conversation

        full_question = f"Here is the document content:\n\n{pdf_content}\n\nQuestion: {question}"

        response = openai.ChatCompletion.create(
            deployment_id=deployment_name,  # Specify the deployment_id
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": full_question}
            ]
        )

        answer = response.choices[0].message["content"]
        st.write(bot_template.replace("{{MSG}}", answer), unsafe_allow_html=True)

    except openai.error.APIError as e:
        st.write(f"APIError: {e}")
    except openai.error.InvalidRequestError as e:
        st.write(f"InvalidRequestError: {e}")
    except Exception as e:
        st.write(f"An unexpected error occurred: {str(e)}")

def main():
    """Main function to handle the Streamlit app."""
    st.set_page_config(page_title='Chat with Your own PDFs', page_icon=':books:')

    st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = create_chain()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.header('Chat with Your own PDFs :books:')
    question = st.text_input("Ask anything to your PDF: ")

    if question:
        if "pdf_content" in st.session_state:
            handle_user_input(question, st.session_state.pdf_content)
        else:
            st.write("Please upload a PDF file to analyze.")

    with st.sidebar:
        st.subheader("Upload your Documents Here: ")
        pdf_files = st.file_uploader("Choose your PDF Files and Press OK", type=['pdf'], accept_multiple_files=True)

        if st.button("OK"):
            if pdf_files:
                with st.spinner("Processing your PDFs..."):
                    raw_text = get_pdf_text(pdf_files)  
                    st.session_state.pdf_content = raw_text  
                    st.write("DONE! You can now ask questions about the documents.")

if __name__ == '__main__':
    main()
