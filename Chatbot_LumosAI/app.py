from dotenv import load_dotenv
import os
import openai
import streamlit as st
from PyPDF2 import PdfReader
from htmlTemplates import bot_template, user_template, css
import certifi
import faiss
import numpy as np
import tiktoken

# Load environment variables from .env file
load_dotenv()

# Set the correct API key and base URL
api_base = "https://genai-nexus.api.corpinter.net/apikey/openai/deployments/gpt-4o-mini/chat/completions"
api_key = os.getenv("NEXUS_API_KEY")

openai.api_type = "azure"
openai.api_base = api_base
openai.api_version = "2024-06-01"
openai.api_key = api_key

# Ensure SSL certificate
os.environ['CURL_CA_BUNDLE'] = certifi.where()

# Tokenizer for splitting text into chunks
tokenizer = tiktoken.get_encoding("cl100k_base")

def create_embeddings(text, model="text-embedding-ada-002"):
    """Creates embeddings for the given text using OpenAI."""
    response = openai.Embedding.create(
        input=[text],
        model=model
    )
    return np.array(response['data'][0]['embedding'], dtype='float32')

def split_text_into_chunks(text, chunk_size=500):
    """Splits the text into manageable chunks."""
    tokens = tokenizer.encode(text)
    chunks = [tokens[i:i + chunk_size] for i in range(0, len(tokens), chunk_size)]
    return [tokenizer.decode(chunk) for chunk in chunks]

def get_pdf_text(pdf_files):
    """Extract text from the uploaded PDF files."""
    text = ""
    if pdf_files is not None:
        for pdf_file in pdf_files:
            pdf_reader = PdfReader(pdf_file)
            for page in pdf_reader.pages:
                text += page.extract_text()
    return text

def create_faiss_index(pdf_text):
    """Create a FAISS index and store the embeddings."""
    chunks = split_text_into_chunks(pdf_text)
    embeddings = [create_embeddings(chunk) for chunk in chunks]

    # Initialize FAISS index
    dimension = len(embeddings[0])
    index = faiss.IndexFlatL2(dimension)  # L2 distance (Euclidean)

    # Add embeddings to the FAISS index
    index.add(np.array(embeddings))

    return index, chunks

def search_similar_chunks(faiss_index, chunks, query, top_k=5):
    """Search FAISS index for the most relevant chunks."""
    query_embedding = create_embeddings(query)
    distances, indices = faiss_index.search(np.array([query_embedding]), top_k)
    
    # Retrieve the top matching chunks
    relevant_chunks = [chunks[i] for i in indices[0]]
    return relevant_chunks

def create_chain():
    """Return the deployment name."""
    deployment_name = "gpt-4o-mini"  # Correct model deployment name
    return deployment_name

def handle_user_input(question, faiss_index, chunks):
    """Handle user input and provide responses using OpenAI's GPT-4o-mini model."""
    try:
        deployment_name = st.session_state.conversation

        # Search for the most relevant document chunks using FAISS
        relevant_chunks = search_similar_chunks(faiss_index, chunks, question)

        # Combine the top results to create context for GPT-4o-mini
        context = "\n\n".join(relevant_chunks)

        # Combine the question with the relevant PDF content for context
        full_question = f"Here is the relevant document content:\n\n{context}\n\nQuestion: {question}"

        # API call to GPT-4o-mini with the combined context and user question
        response = openai.ChatCompletion.create(
            deployment_id=deployment_name,  # Specify the deployment_id
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": full_question}
            ]
        )

        # Extract and display the response from the model
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

    if "faiss_index" not in st.session_state:
        st.session_state.faiss_index = None
        st.session_state.chunks = None

    st.header('Chat with Your own PDFs :books:')
    question = st.text_input("Ask anything to your PDF: ")

    if question:
        if st.session_state.faiss_index is not None:
            handle_user_input(question, st.session_state.faiss_index, st.session_state.chunks)
        else:
            st.write("Please upload a PDF file to analyze.")

    with st.sidebar:
        st.subheader("Upload your Documents Here: ")
        pdf_files = st.file_uploader("Choose your PDF Files and Press OK", type=['pdf'], accept_multiple_files=False)

        if st.button("OK"):
            if pdf_files is not None:
                with st.spinner("Processing your PDF..."):
                    # Get PDF Text
                    raw_text = get_pdf_text([pdf_files])  # Pass the uploaded file as a list

                    # Create FAISS index and store the chunks and embeddings
                    faiss_index, chunks = create_faiss_index(raw_text)
                    st.session_state.faiss_index = faiss_index
                    st.session_state.chunks = chunks
                    st.write("DONE! You can now ask questions about the document.")

if __name__ == '__main__':
    main()
