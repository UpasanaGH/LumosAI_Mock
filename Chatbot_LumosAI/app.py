import os
from dotenv import load_dotenv
import openai
import streamlit as st
from PyPDF2 import PdfReader
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_chains import LLMChain
from htmlTemplates import bot_template, css
import certifi

# Load the environment variables from .env file
load_dotenv()

# Set the correct API key and base URL
api_base = "https://genai-nexus.api.corpinter.net/apikey/openai/deployments/gpt-4o-mini/chat/completions"
api_key = os.getenv("NEXUS_API_KEY")

# Ensure SSL certificate
os.environ['CURL_CA_BUNDLE'] = certifi.where()

def get_pdf_text(pdf_files):
    """Extract text from the provided PDF files (paths or file-like objects)."""
    text = ""
    for pdf_file in pdf_files:
        if isinstance(pdf_file, str):  # If it's a file path
            with open(pdf_file, "rb") as f:
                pdf_reader = PdfReader(f)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        else:  # If it's a file-like object
            pdf_reader = PdfReader(pdf_file)
            for page in pdf_reader.pages:
                text += page.extract_text()
    return text

def load_pre_uploaded_pdfs(folder_path):
    """Load pre-uploaded PDFs from a local folder."""
    pdf_files = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            pdf_files.append(os.path.join(folder_path, filename))
    return pdf_files

def create_chain():
    """Create and return a LangChain chain for Azure OpenAI."""
    model = AzureChatOpenAI(
        openai_api_version="2024-06-01",
        openai_api_key=api_key,
        azure_endpoint=api_base,
        openai_api_type="azure",
        deployment_name="gpt-4o-mini"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant."),
        ("user", "Here is the document content:\n\n{context}\n\nQuestion: {question}")
    ])
    
    chain = LLMChain(
        llm=model,
        prompt=prompt
    )
    return chain

def handle_user_input(question, pdf_content):
    """Handle user input and provide responses using LangChain's model."""
    try:
        chain = create_chain()
        
        # Combine the question with the extracted PDF content for context
        context = f"{pdf_content}\n\nQuestion: {question}"
        
        # Run the LangChain chain with the combined context
        result = chain.invoke({"context": pdf_content, "question": question})
        
        # Extract and display the response from the model
        answer = result.get('text', str(result))
        st.write(bot_template.replace("{{MSG}}", answer), unsafe_allow_html=True)

    except Exception as e:
        st.write(f"An unexpected error occurred: {str(e)}")

def main():
    """Main function to handle the Streamlit app."""
    st.set_page_config(page_title='Chat with Your own PDFs', page_icon=':books:')

    st.write(css, unsafe_allow_html=True)

    if "pdf_content" not in st.session_state:
        st.session_state.pdf_content = ""

    pre_uploaded_folder = r"C:\Users\upghosh\Downloads\Chatbot_LumosAI\Chatbot_LumosAI\documents"

    # Load and process pre-uploaded PDFs on app startup
    pre_uploaded_files = load_pre_uploaded_pdfs(pre_uploaded_folder)
    pre_uploaded_text = get_pdf_text(pre_uploaded_files)
    st.session_state.pdf_content = pre_uploaded_text

    st.header('Chat with Your own PDFs :books:')
    question = st.text_input("Ask anything to your PDF: ")

    if question:
        if st.session_state.pdf_content:
            handle_user_input(question, st.session_state.pdf_content)
        else:
            st.write("Please upload a PDF file to analyze.")

    with st.sidebar:
        st.subheader("Upload your Documents Here: ")
        uploaded_files = st.file_uploader("Choose your PDF Files and Press OK", type=['pdf'], accept_multiple_files=True)

        if st.button("OK"):
            with st.spinner("Processing your PDFs..."):
                # Get PDF Text from manual uploads
                if uploaded_files:
                    manual_uploaded_files = [pdf_file for pdf_file in uploaded_files]
                    raw_text = get_pdf_text(manual_uploaded_files)
                    
                    # Combine text from pre-uploaded files first, then manual uploads
                    st.session_state.pdf_content += raw_text
                    st.write("DONE! You can now ask questions about the documents.")

    # Display the list of pre-uploaded files
    st.sidebar.subheader("Pre-uploaded Documents:")
    pre_uploaded_files = load_pre_uploaded_pdfs(pre_uploaded_folder)
    for file_path in pre_uploaded_files:
        st.sidebar.write(os.path.basename(file_path))
    
    # Display the list of manually uploaded files
    st.sidebar.subheader("Manually Uploaded Documents:")
    if uploaded_files:
        for uploaded_file in uploaded_files:
            st.sidebar.write(uploaded_file.name)

if __name__ == '__main__':
    main()
