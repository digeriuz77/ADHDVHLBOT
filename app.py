import streamlit as st
import openai
import os
import time

# Load OpenAI API key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

# OpenAI functions for assistant creation and file handling
def create_assistant(file_ids, title):
    client = openai.OpenAI(api_key=openai.api_key)
    instructions = """
    You are a helpful assistant. Use your knowledge base to answer user questions.
    """
    model = "gpt-4-turbo"
    tools = [{"type": "file_search"}]
    assistant = client.beta.assistants.create(
        name=title,
        instructions=instructions,
        model=model,
        tools=tools,
        tool_resources={"file_search": {"vector_store_ids": file_ids}}
    )
    return assistant.id

def save_file_openai(file):
    client = openai.OpenAI(api_key=openai.api_key)
    response = client.beta.files.create(file=file, purpose='assistants')
    return response["id"]

def start_assistant_thread(prompt):
    client = openai.OpenAI(api_key=openai.api_key)
    thread = client.beta.threads.create(messages=[{"role": "user", "content": prompt}])
    return thread["id"]

def run_assistant(thread_id, assistant_id):
    client = openai.OpenAI(api_key=openai.api_key)
    run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)
    return run["id"]

def check_run_status(thread_id, run_id):
    client = openai.OpenAI(api_key=openai.api_key)
    run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
    return run["status"]

def retrieve_thread(thread_id):
    client = openai.OpenAI(api_key=openai.api_key)
    thread_messages = client.beta.threads.messages.list(thread_id=thread_id)
    list_messages = thread_messages["data"]
    thread_messages = []
    for message in list_messages:
        obj = {
            'content': message["content"],
            'role': message["role"]
        }
        thread_messages.append(obj)
    return thread_messages[::-1]

def add_message_to_thread(thread_id, prompt):
    client = openai.OpenAI(api_key=openai.api_key)
    client.beta.threads.messages.create(thread_id=thread_id, role="user", content=prompt)

# Function to process the assistant run and return messages
def process_run(thread_id, assistant_id):
    run_id = run_assistant(thread_id, assistant_id)
    status = 'running'

    while status != 'completed':
        time.sleep(20)
        status = check_run_status(thread_id, run_id)

    thread_messages = retrieve_thread(thread_id)
    responses = []
    for message in thread_messages:
        if message['role'] == 'user':
            responses.append(('User', message['content']))
        else:
            responses.append(('Assistant', message['content']))
    return responses

# Streamlit app
st.title("🧑‍💻 Cirrina Online 💬 Assistant")
st.write("My name is Cirrina, your many tentacled personal AI Assistant. I create file_search assistants, just upload your knowledge base and start chatting to your documents.")

if 'assistant_initialized' not in st.session_state:
    title = st.text_input("Enter the title")
    initiation = st.text_input("Enter the assistant's first question")
    uploaded_files = st.file_uploader("Upload Files for the Assistant", accept_multiple_files=True)

    if st.button("Initialize Assistant") and title and initiation and uploaded_files:
        file_ids = []
        for uploaded_file in uploaded_files:
            file_id = save_file_openai(uploaded_file)
            file_ids.append(file_id)
            st.success(f'File {uploaded_file.name} has been uploaded successfully.')

        assistant_id = create_assistant(file_ids, title)
        thread_id = start_assistant_thread(initiation)

        st.session_state.assistant_id = assistant_id
        st.session_state.thread_id = thread_id
        st.session_state.assistant_initialized = True
        st.session_state.last_message = initiation

        st.write("Assistant initialized successfully!")

if 'assistant_initialized' in st.session_state and st.session_state.assistant_initialized:
    follow_up = st.text_input("Enter your follow-up question")
    
    if st.button("Submit Follow-up") and follow_up and follow_up != st.session_state.last_message:
        st.session_state.last_message = follow_up
        add_message_to_thread(st.session_state.thread_id, follow_up)
        responses = process_run(st.session_state.thread_id, st.session_state.assistant_id)
        for role, content in responses:
            st.write(f"{role}: {content}")
