import streamlit as st
import openai
import time

# Import necessary libraries
from openai import OpenAI  # Used for interacting with OpenAI's API
from typing_extensions import override  # Used for overriding methods in subclasses
from openai import AssistantEventHandler  # Used for handling events related to OpenAI assistants

import re # Used for regular expressions

# Initialize OpenAI client

if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

if 'assistant_id' not in st.session_state:
    st.session_state.assistant_id = ""

st.session_state.api_key = st.text_input("Enter your OpenAI API key", type="password", value=st.session_state.api_key)
st.session_state.assistant_id = st.text_input("Enter your Assistant ID", value=st.session_state.assistant_id)

if st.session_state.api_key and st.session_state.assistant_id:
    openai.api_key = st.session_state.api_key

#this bit
client = OpenAI()

# Event handler class to handle events related to streaming output from the assistant
class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
        print(f"\nASSISTANT MESSAGE >\n", end="", flush=True)

    @override
    def on_tool_call_created(self, tool_call):
        print(f"\nASSISTANT MESSAGE >\n{tool_call.type}\n", flush=True)

    @override
    def on_message_done(self, message) -> None:
        # print a citation to the file searched
        message_content = message.content[0].text
        annotations = message_content.annotations
        citations = []
        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(
                annotation.text, f"[{index}]"
            )
            if file_citation := getattr(annotation, "file_citation", None):
                cited_file = client.files.retrieve(file_citation.file_id)
                citations.append(f"[{index}] {cited_file.filename}")

        print(message_content.value)
        print("\n".join(citations))

# Create an assistant using the client library.
assistant = client.beta.assistants.create(
    model="gpt-4o",  # Specify the model to be used.
    
    instructions=""" 
        You are a helpful assistant that answers questions about the data in your files. The data is from a variety of authors. 
        You will answer questions from the user about the data. All you will do is answer questions about the data in the files and provide related information.
        If the user asks you a question that is not related to the data in the files, you should let them know that you can only answer questions about the data.
    """,
    
    name="File Search Demo Assistant - Stories",  # Give the assistant a name.
    
    tools=[{"type": "file_search"}], # Add the file search capability to the assistant.
    
    metadata={  # Add metadata about the assistant's capabilities.
        "can_be_used_for_file_search": "True",
        "can_hold_vector_store": "True",
    },
    temperature=1,  # Set the temperature for response variability.
    top_p=1,  # Set the top_p for nucleus sampling.
)

# Print the details of the created assistant to check its properties.
print(assistant)  # Print the full assistant object.
print("\n\n")
print(assistant.name)  # Print the name of the assistant.
print(assistant.metadata)  # Print the metadata of the assistant.

from contextlib import ExitStack

# Create a vector store with a name for the store.
vector_store = client.beta.vector_stores.create(name="Data Exploration")

# Ready the files for upload to the vector store.
# File uploader widget
        uploaded_files = st.file_uploader("Upload Files for the Assistant", accept_multiple_files=True, key="uploader")
        file_locations = []

        if uploaded_files and title and initiation:
            for uploaded_file in uploaded_files:
                # Read file as bytes
                bytes_data = uploaded_file.getvalue()
                location = f"temp_file_{uploaded_file.name}"
                # Save each file with a unique name
                with open(location, "wb") as f:
                    f.write(bytes_data)
                file_locations.append(location)
                st.success(f'File {uploaded_file.name} has been uploaded successfully.')

            # Upload file and create assistant
            with st.spinner('Processing your file and setting up the assistant...'):
                file_ids = [saveFileOpenAI(location) for location in file_locations]
                assistant_id, vector_id = createAssistant(file_ids, title)
                file_paths = file_locations

# Using ExitStack to manage multiple context managers and ensure they are properly closed.
with ExitStack() as stack:
    # Open each file in binary read mode and add the file stream to the list
    file_streams = [stack.enter_context(open(path, "rb")) for path in file_paths]

    # Use the upload and poll helper method to upload the files, add them to the vector store,
    # and poll the status of the file batch for completion.
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )

    # Print the vector store information
    print(vector_store.name)
    print(vector_store.id)
    
    # Print the status and the file counts of the batch to see the results
    print(file_batch.status)
    print(file_batch.file_counts)

try:
    # Attach the vector store to the assistant to enable file search capabilities.
    assistant = client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )

    # Print the assistant's tools and tool resources to verify the attachment of the vector store.
    print("Assistant Tools:")
    for tool in assistant.tools:
        print(f" - {tool}")

    # Print the assistant's tool resources to verify the attachment of the vector store
    print("\nAssistant Tool Resources:")
    for resource, details in assistant.tool_resources:
        print(f" - {resource}: {details}")

except Exception as e:
    print(f"An error occurred while updating the assistant: {e}")

    # File upload
import streamlit as st
import time
from assistants_api_v2 import *

def process_run(st, thread_id, assistant_id):
    # Run the Assistant
    run_id = runAssistant(thread_id, assistant_id)
    status = 'running'

    # Check Status Session
    while status != 'completed':
        with st.spinner('Waiting for assistant response . . .'):
            time.sleep(20)  # 20-second delay
            status = checkRunStatus(thread_id, run_id)

    # Retrieve the Thread Messages
    thread_messages = retrieveThread(thread_id)
    for message in thread_messages:
        if message['role'] == 'user':
            st.write('User Message:', message['content'])
        else:
            st.write('Assistant Response:', message['content'])

def main():
    st.title("🐙Cirrina Online 💬 Assistant")
    st.write("My name is Cirrina, your many tentacled personal AI Assistant. Please upload your knowledge base to start chatting with your documents.")

    if 'assistant_initialized' not in st.session_state:
        # Input field for the title
        title = st.text_input("Enter the title", key="title")
        initiation = st.text_input("Enter the assistant's first question", key="initiation")

    

            # Start the Thread
            thread_id = startAssistantThread(initiation, vector_id)

            # Save state
            st.session_state.thread_id = thread_id
            st.session_state.assistant_id = assistant_id
            st.session_state.last_message = initiation
            st.session_state.assistant_initialized = True

            st.write("Assistant ID:", assistant_id)
            st.write("Vector ID:", vector_id)
            st.write("Thread ID:", thread_id)

            process_run(st, thread_id, assistant_id)

    # Handling follow-up questions only if assistant is initialized
    if 'assistant_initialized' in st.session_state and st.session_state.assistant_initialized:
        follow_up = st.text_input("Enter your follow-up question", key="follow_up")
        submit_button = st.button("Submit Follow-up")

        if submit_button and follow_up and follow_up != st.session_state.last_message:
            st.session_state.last_message = follow_up
            addMessageToThread(st.session_state.thread_id, follow_up)
            process_run(st, st.session_state.thread_id, st.session_state.assistant_id)

if __name__ == "__main__":
    main()


else:
