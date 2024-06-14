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
        response = openai.File.create(file=openai.File(file.read(), filename=file.name), purpose='fine-tune')
        return response["id"]

    if uploaded_files:
        file_ids = []
        for uploaded_file in uploaded_files:
            file_id = save_file_openai(uploaded_file)
            file_ids.append(file_id)
            st.success(f'File {uploaded_file.name} has been uploaded with ID {file_id}')
        
        def create_thread_and_run(user_input):
            # Create a chat completion
            response = openai.ChatCompletion.create(
                model="gpt-4",  # or the specific model you are using
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_input}
                ]
            )
            return response

        # Start a conversation with the assistant
        initiation = st.text_input("Start the conversation with an initial prompt")
        if st.button("Start Conversation"):
            if initiation:
                response = create_thread_and_run(initiation)
                st.write(f"Conversation started. Assistant's response:")

                # Display the assistant's response
                for message in response['choices']:
                    st.write(f"Assistant: {message['message']['content']}")
            else:
                st.error("Please enter an initial prompt to start the conversation.")
else:
    st.warning("Please enter both your OpenAI API key and Assistant ID to proceed.")
