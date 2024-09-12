import os
import json 
from dotenv import load_dotenv
import openai
import streamlit as st
from PyPDF2 import PdfReader
from UI import bot_template, user_template, css
import certifi
import psycopg2

load_dotenv()

api_base = "https://genai-nexus.api.corpinter.net/apikey/openai/deployments/gpt-4o-mini/chat/completions"
api_key = os.getenv("NEXUS_API_KEY")

openai.api_type = "azure"
openai.api_base = api_base
openai.api_version = "2024-06-01"
openai.api_key = api_key

os.environ['CURL_CA_BUNDLE'] = certifi.where()

def connect_db():
    """Connect to the PostgreSQL database and return the connection object.""" 
    conn = psycopg2.connect(
        dbname="Hackutsav",
        user="postgres",
        password="Root@12345",
        host="localhost"
    )
    return conn

def create_user_profile(username):
    """Create a user profile in the database if it doesn't exist.""" 
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS user_profiles (
            username VARCHAR PRIMARY KEY,
            history TEXT
        )
    ''')
    cursor.execute('''
        INSERT INTO user_profiles (username, history) VALUES (%s, %s)
        ON CONFLICT (username) DO NOTHING
    ''', (username, '[]'))  
    conn.commit()
    conn.close()

def get_user_history(username):
    """Retrieve the interaction history for a given user."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT history FROM user_profiles WHERE username=%s', (username,))
    row = cursor.fetchone()
    conn.close()

    if row and row[0]:
        return json.loads(row[0])
    return []  

def save_user_history(username, history):
    """Save or update the interaction history for a given user."""
    conn = connect_db()
    cursor = conn.cursor()
    
    serialized_history = json.dumps(history)
    
    cursor.execute('''
        INSERT INTO user_profiles (username, history) VALUES (%s, %s)
        ON CONFLICT (username) DO UPDATE SET history = EXCLUDED.history
    ''', (username, serialized_history))
    conn.commit()
    conn.close()

def get_pdf_text(pdf_files):
    """Extract text from the provided PDF files (paths or file-like objects).""" 
    text = ""
    for pdf_file in pdf_files:
        if isinstance(pdf_file, str):  
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
    """Return the deployment name.""" 
    deployment_name = "gpt-4o-mini"  
    return deployment_name

def handle_user_input(username, question, pdf_content):
    """Handle user input and provide responses using OpenAI's GPT-4o-mini model.""" 
    try:
        deployment_name = st.session_state.conversation

        full_question = f"Here is the document content:\n\n{pdf_content}\n\nQuestion: {question}"

        response = openai.ChatCompletion.create(
            deployment_id=deployment_name,  
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": full_question}
            ]
        )

        answer = response.choices[0].message["content"].strip()

        st.session_state.chat_history.append({"role": "user", "content": question})
        st.session_state.chat_history.append({"role": "assistant", "content": answer})

        save_user_history(username, st.session_state.chat_history)

    except openai.error.APIError as e:
        st.write(f"APIError: {e}")
    except openai.error.InvalidRequestError as e:
        st.write(f"InvalidRequestError: {e}")
    except Exception as e:
        st.write(f"An unexpected error occurred: {str(e)}")

def display_chat_history():
    """Display the chat history using the predefined templates for user and bot."""
    for chat in reversed(st.session_state.chat_history):
        if chat["role"] == "user":
            st.write(user_template.replace("{{MSG}}", chat["content"]), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace("{{MSG}}", chat["content"]), unsafe_allow_html=True)

def main():
    """Main function to handle the Streamlit app."""
    st.set_page_config(page_title='Chat with Your own PDFs', page_icon=':books:')

    st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = create_chain()

    if "pdf_content" not in st.session_state:
        st.session_state.pdf_content = ""

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []  

    pre_uploaded_folder = r"C:\Users\upghosh\Downloads\Chatbot_LumosAI\Chatbot_LumosAI\documents"

    st.header('Chat with Your own PDFs :books:')
    username = st.text_input("Enter your username: ")

    if username:
        stored_history = get_user_history(username)
        if stored_history:
            st.session_state.chat_history = stored_history

        create_user_profile(username)

        question = st.text_input("Ask anything to your PDF: ")

        if question:
            if st.session_state.pdf_content:
                handle_user_input(username, question, st.session_state.pdf_content)
            else:
                st.write("Please upload a PDF file to analyze.")

        display_chat_history()

    with st.sidebar:
        st.subheader("Upload your Documents Here: ")
        uploaded_files = st.file_uploader("Choose your PDF Files", type=['pdf'], accept_multiple_files=True)

        if st.button("START CONVERSING"):
            with st.spinner("Processing your PDFs..."):
                pre_uploaded_files = load_pre_uploaded_pdfs(pre_uploaded_folder)
                pre_uploaded_text = get_pdf_text(pre_uploaded_files)
                
                manual_uploaded_files = [pdf_file for pdf_file in uploaded_files]
                raw_text = get_pdf_text(manual_uploaded_files)
                
                st.session_state.pdf_content = pre_uploaded_text + raw_text
                st.write("DONE! You can now ask questions about the documents.")

    st.sidebar.subheader("Pre-uploaded Documents:")
    pre_uploaded_files = load_pre_uploaded_pdfs(pre_uploaded_folder)
    for file_path in pre_uploaded_files:
        st.sidebar.write(os.path.basename(file_path))
    
    st.sidebar.subheader("Manually Uploaded Documents:")
    if uploaded_files:
        for uploaded_file in uploaded_files:
            st.sidebar.write(uploaded_file.name)

if __name__ == '__main__':
    main()