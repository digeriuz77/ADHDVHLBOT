import streamlit as st
import openai
import time

# Streamlit app
st.title("🧑‍💻 Cirrina Online 💬 Assistant")
st.write("My name is Cirrina, your many tentacled personal AI Assistant. Please provide your assistant ID and upload your knowledge base to start chatting with your documents.")

# Input for OpenAI API key
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''

if st.session_state.api_key == '':
    st.session_state.api_key = st.text_input("Enter your OpenAI API key", type="password")
    if st.button("Save API key"):
        openai.api_key = st.session_state.api_key
        st.success("API key saved!")
else:
    openai.api_key = st.session_state.api_key

if openai.api_key:
    # OpenAI functions for file handling and interacting with the assistant
    def save_file_openai(file):
        response = openai.File.create(file=file, purpose='assistants')
        return response["id"]

    def start_assistant_thread(prompt):
        thread = openai.Thread.create(messages=[{"role": "user", "content": prompt}])
        return thread["id"]

    def run_assistant(thread_id, assistant_id):
        run = openai.Thread.run(thread_id=thread_id, assistant_id=assistant_id)
        return run["id"]

    def check_run_status(thread_id, run_id):
        run = openai.Thread.run_retrieve(thread_id=thread_id, run_id=run_id)
        return run["status"]

    def retrieve_thread(thread_id):
        thread_messages = openai.Thread.messages_list(thread_id=thread_id)
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
        openai.Thread.messages_create(thread_id=thread_id, role="user", content=prompt)

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

    # Add input for existing assistant ID
    if 'assistant_initialized' not in st.session_state:
        assistant_id = st.text_input("Enter an existing assistant ID")
        initiation = st.text_input("Enter the assistant's first question")
        uploaded_files = st.file_uploader("Upload Files for the Assistant", accept_multiple_files=True)

        if st.button("Initialize Assistant") and assistant_id and initiation and uploaded_files:
            file_ids = []
            for uploaded_file in uploaded_files:
                file_id = save_file_openai(uploaded_file)
                file_ids.append(file_id)
                st.success(f'File {uploaded_file.name} has been uploaded successfully.')

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

else:
    st.warning("Please enter your OpenAI API key to proceed.")
