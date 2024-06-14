import streamlit as st
from openai import OpenAI

# Initialize OpenAI client
if 'api_key' not in st.session_state:
    st.session_state.api_key = st.text_input("Enter your OpenAI API key", type="password")

if 'assistant_id' not in st.session_state:
    st.session_state.assistant_id = st.text_input("Enter your Assistant ID")

if st.session_state.api_key and st.session_state.assistant_id:
    client = OpenAI(api_key=st.session_state.api_key)
    
    st.title("🧑‍💻 Cirrina Online 💬 Assistant")
    st.write("My name is Cirrina, your many tentacled personal AI Assistant. Please upload your knowledge base to start chatting with your documents.")

    # File upload
    uploaded_files = st.file_uploader("Upload Files", accept_multiple_files=True)

    def save_file_openai(file):
        response = client.files.create(file=file, purpose='assistants')
        return response["id"]

    if uploaded_files:
        file_ids = []
        for uploaded_file in uploaded_files:
            file_id = save_file_openai(uploaded_file)
            file_ids.append(file_id)
            st.success(f'File {uploaded_file.name} has been uploaded with ID {file_id}')
        
        def create_thread_and_run(user_input):
            thread = client.threads.create()
            message = client.threads.messages.create(thread_id=thread.id, role="user", content=user_input)
            run = client.threads.runs.create(thread_id=thread.id, assistant_id=st.session_state.assistant_id)
            return thread, run

        # Start a conversation with the assistant
        initiation = st.text_input("Start the conversation with an initial prompt")
        if st.button("Start Conversation"):
            if initiation:
                thread, run = create_thread_and_run(initiation)
                st.write(f"Conversation started. Thread ID: {thread.id}")

                # Fetch and display the assistant's response
                time.sleep(2)  # wait for the assistant to process
                messages = client.threads.messages.list(thread_id=thread.id, order="asc")
                for message in messages["data"]:
                    st.write(f"{message['role']}: {message['content'][0]['text']['value']}")
            else:
                st.error("Please enter an initial prompt to start the conversation.")

else:
    st.error("Please enter both your OpenAI API key and Assistant ID to proceed.")
