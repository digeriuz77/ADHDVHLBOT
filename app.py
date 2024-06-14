import streamlit as st
import openai
import time

# Initialize OpenAI client
st.title("🧑‍💻 Cirrina Online 💬 Assistant")
st.write("My name is Cirrina, your many tentacled personal AI Assistant. Please upload your knowledge base to start chatting with your documents.")

if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

if 'assistant_id' not in st.session_state:
    st.session_state.assistant_id = ""

st.session_state.api_key = st.text_input("Enter your OpenAI API key", type="password", value=st.session_state.api_key)
st.session_state.assistant_id = st.text_input("Enter your Assistant ID", value=st.session_state.assistant_id)

if st.session_state.api_key and st.session_state.assistant_id:
    openai.api_key = st.session_state.api_key
    
    # File upload
    uploaded_files = st.file_uploader("Upload Files", accept_multiple_files=True)

    def save_file_openai(file):
        response = openai.File.create(file=open(file.name, "rb"), purpose='assistants')
        return response["id"]

    if uploaded_files:
        file_ids = []
        for uploaded_file in uploaded_files:
            file_id = save_file_openai(uploaded_file)
            file_ids.append(file_id)
            st.success(f'File {uploaded_file.name} has been uploaded with ID {file_id}')
        
        def create_assistant():
            assistant = openai.Assistant.create(
                model="gpt-3.5-turbo-1106",
                instructions="You are a personal assistant. Use your knowledge base to best respond to user queries.",
                name="Personal Assistant",
                tools=[{"type": "retrieval"}]
            )
            return assistant
        
        def create_thread():
            thread = openai.Thread.create()
            return thread
        
        def add_message_to_thread(thread_id, user_input, file_ids):
            message = openai.ThreadMessage.create(
                thread_id=thread_id,
                role="user",
                content=user_input,
                file_ids=file_ids
            )
            return message

        def run_assistant(thread_id, assistant_id):
            run = openai.ThreadRun.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
                instructions="Please address the user as Rok Benko."
            )
            return run

        def retrieve_run_status(thread_id, run_id):
            return openai.ThreadRun.retrieve(thread_id=thread_id, run_id=run_id)

        def list_messages(thread_id):
            return openai.ThreadMessage.list(thread_id=thread_id)

        # Start a conversation with the assistant
        initiation = st.text_input("Start the conversation with an initial prompt")
        if st.button("Start Conversation"):
            if initiation:
                assistant = create_assistant()
                thread = create_thread()
                add_message_to_thread(thread.id, initiation, file_ids)
                run = run_assistant(thread.id, assistant.id)

                st.write("Conversation started. Checking assistant's response...")

                # Polling for the assistant's response
                while run.status in ["queued", "in_progress"]:
                    run_status = retrieve_run_status(thread.id, run.id)
                    if run_status.status == "completed":
                        messages = list_messages(thread.id)
                        st.write("------------------------------------------------------------")
                        st.write(f"User: {initiation}")
                        for message in messages.data:
                            if message.role == "assistant":
                                st.write(f"Assistant: {message.content}")
                        break
                    elif run_status.status in ["queued", "in_progress"]:
                        time.sleep(2)  # Wait before checking the status again
                    else:
                        st.error(f"Run status: {run_status.status}")
                        break
            else:
                st.error("Please enter an initial prompt to start the conversation.")

else:
    st.warning("Please enter both your OpenAI API key and Assistant ID to proceed.")
