import streamlit as st
import pinecone
from sentence_transformers import SentenceTransformer
from typorec import texto, generate_qr_code
import base64
import json
from streamlit_modal import Modal
import streamlit.components.v1 as components

st.set_page_config(page_title="Chatbot", page_icon=":robot_face:", layout="wide")
st.markdown('<style>' + open('static/styles.css').read() + '</style>', unsafe_allow_html=True)
from streamlit_javascript import st_javascript

# Initialize st.session_state if not already done
if "conversations" not in st.session_state:
    st.session_state.conversations = []
if "current_conversation" not in st.session_state:
    st.session_state.current_conversation = []
if "history" not in st.session_state:
    st.session_state.history = []

# Create a header element
st.header("MAGHA: Where Infinite Curiosity Meets Infinite Conversations!")

st.sidebar.title("CSCI 350 Project - Chatbot 🤖")

# About section
st.sidebar.markdown("### About")
st.sidebar.markdown("This is a chatbot designed for the Intro to AI Project. It can respond to specific prompts and engage in conversations with users that have been using:")

# Used Technologies section
st.sidebar.markdown("### Used Technologies")
st.sidebar.markdown("- Sentence Transformers (MPNet)")
st.sidebar.markdown("- Vector Database")
st.sidebar.markdown("- Stanford Question Answering Dataset (SQuAD)")

# # Used Technologies section
# st.sidebar.markdown("### Used Technologies")
# st.sidebar.markdown("- [Streamlit](https://streamlit.io/)\n - [Ghaleb's Killer Knowledge, Super Strength, and Integrity](https://www.shutterstock.com/shutterstock/photos/1552486565/display_1500/stock-photo-muscled-male-model-in-studio-1552486565.jpg)")

st.sidebar.markdown("&nbsp;")
st.sidebar.markdown("---")

modal = Modal(
    "Scan the QR code!",
    key="demo-modal",

    # Optional
    padding=20,    # default value
    max_width=350  # default value
)

# Generate QR Code Button
url = st_javascript("await fetch('').then(r => window.parent.location.href)")
open_modal = st.sidebar.button("Generate QR Code")
if open_modal:
    modal.open()
if modal.is_open():
    with modal.container():
        st.write("Scan the code to use our chatbot in your browser!")
        qr_image = generate_qr_code(url)
        st.image(qr_image)

# New Conversation Button
if st.sidebar.button("New Conversation"):
    # Save the current conversation
    st.session_state.conversations.append(st.session_state.current_conversation.copy())
    # Reset the current conversation
    st.session_state.current_conversation = []

# Display Old Conversations Drop Down
selected_conversation = st.sidebar.selectbox("Select Conversation", ["None"] + [f"Conversation {i}" for i in range(1, len(st.session_state.conversations) + 1)])
if selected_conversation != "None":
    # Load the selected conversation
    st.session_state.current_conversation = st.session_state.conversations[int(selected_conversation.split()[-1]) - 1]

@st.cache_resource
def init_retriever():
    return SentenceTransformer('model')

@st.cache_resource
def init_index():
    pinecone.init(
        api_key='e3f17445-26ae-4276-8f86-7328c122e8a2', environment='gcp-starter'
    )
    return pinecone.Index('squad-index')

retriever = init_retriever()
index = init_index()


def add_to_conversation(role, content):
    message = {"role": role, "content": str(content)}
    st.session_state.current_conversation.append(message)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "How may I help you today?"}
    ]

if "current_response" not in st.session_state:
    st.session_state.current_response = ""

user_prompt = st.chat_input("Your message here", key="user_input")

if user_prompt:
    # Add your input to the session state
    st.session_state.messages.append(
        {"role": "user", "content": user_prompt}
    )

    with open('responses.json', 'r') as file:
        responses_data = json.load(file)

    # Check if user input matches any question in the responses dictionary
    user_input_lower = texto(str(user_prompt)).lower()

    matching_response = None

    for key, data in responses_data.items():
        if isinstance(data['question'], list):
            if any(user_input_lower in question.lower() for question in data['question']):
                matching_response = data['response']
                break
        else:
            if user_input_lower == data['question'].lower():
                matching_response = data['response']
                break

    if matching_response:
        response = matching_response
    elif texto(user_prompt).isdigit():
        response = f"The result is: {texto(user_prompt)}"
    else:
        # If not in responses, perform the query
        xq = retriever.encode([texto(str(user_prompt))]).tolist()
        # get relevant contexts
        xc = index.query(xq, top_k=5, include_metadata=True)
        highest_score_match = max(xc['matches'], key=lambda x: x['score'])
        if highest_score_match['score'] < 0.45:
            response = "I'm afraid I don't have much information on that topic at the moment."
        else:
            response = highest_score_match['metadata']['text']

    # Add the response to the session state
    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )

    # Add the response to the conversation
    add_to_conversation("user", user_prompt)
    add_to_conversation("assistant", response)


# Display messages in the current conversation
with st.container():
    for chat in st.session_state.current_conversation:
        image_path = 'static/ai_icon.png' if chat["role"] == 'assistant' else 'static/user_icon.png'
        div = f"""
        <div class="chat-row {'' if chat["role"] == 'assistant' else 'row-reverse'}">
            <img class="chat-icon" src="data:image/png;base64,{base64.b64encode(open(image_path, "rb").read()).decode()}"
                width=32 height=32>
            <div class="chat-bubble {'ai-bubble' if chat["role"] == 'assistant' else 'human-bubble'}">
                &#8203;{chat["content"]}
        </div>
        """
        st.markdown(div, unsafe_allow_html=True)

for _ in range(3):
    st.markdown("")
