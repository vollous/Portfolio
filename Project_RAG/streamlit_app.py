# Copyright 2025 Snowflake Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import requests
from htbuilder.units import rem
from htbuilder import div, styles
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
import datetime
import textwrap
import time

import streamlit as st

class Chat:
    def __init__(self, name:str, rag:bool):
        self.name = name
        self.rag = rag
        self.history = []

    def chat(self, message):
        self.history.append({"role": "user", "content": message})
        r = requests.post(
                "http://127.0.0.1:8000/chat/",          # trailing slash matters
                json={"question": message},
                timeout=300,                             # LLM calls are slow
            )
        
        r.raise_for_status()
        data = r.json()
        response = data["response"]["message"]["content"]
        self.history.append({"role": "assistant", "content": response})
        return(response)

    def clear_chat(self):
        self.history.clear()

if 'chats' not in st.session_state:
    st.session_state['chats'] = [Chat("Vanilla chat", False), Chat("RAG powerd chat", True)]

st.set_page_config(page_title="Streamlit AI assistant", page_icon="✨")

MIN_TIME_BETWEEN_REQUESTS = datetime.timedelta(seconds=3)

INSTRUCTIONS = textwrap.dedent("""
    - You are a helpful AI chat assistant focused on answering quesions about
      Streamlit, Streamlit Community Cloud, Snowflake, and general Python.
    - You will be given extra information provided inside tags like this
      <foo></foo>.
    - Use context and history to provide a coherent answer.
    - Use markdown such as headers (starting with ##), code blocks, bullet
      points, indentation for sub bullets, and backticks for inline code.
    - Don't start the response with a markdown header.
    - Assume the user is a newbie.
    - Be brief, but clear. If needed, you can write paragraphs of text, like
      a documentation website.
    - Avoid experimental and private APIs.
    - Provide examples.
    - Include related links throughout the text and at the bottom.
    - Don't say things like "according to the provided context".
    - Streamlit is a product of Snowflake.
    - Offer alternatives within the Streamlit and Snowflake universe.
    - For information about deploying in Snowflake, see
      https://www.snowflake.com/en/product/features/streamlit-in-snowflake/
""")

SUGGESTIONS = {
    ":blue[:material/local_library:] What is 1+1?": (
        "What is 1+1? Write the answer in english, french and german. Next, generate a random number between 0 and 10."
    ),
    ":green[:material/database:] Random number": (
        "Generate a random number between 0 and 10, be very direct."
    ),
    ":orange[:material/multiline_chart:] Supersimple question?": (
        "What is 1+1? Be very direct."
    ),
    ":violet[:material/apparel:] How do I customize my app?": (
        "How do I customize my app? What does Streamlit offer? No hacks please."
    ),
    ":red[:material/deployed_code:] Deploying an app at work": (
        "How do I deploy an app at work? Give me easy and performant options."
    ),
}

@st.dialog("Legal disclaimer")
def show_disclaimer_dialog():
    st.caption("""
            This AI chatbot is powered by Snowflake and public Streamlit
            information. Answers may be inaccurate, inefficient, or biased.
            Any use or decisions based on such answers should include reasonable
            practices including human oversight to ensure they are safe,
            accurate, and suitable for your intended purpose. Streamlit is not
            liable for any actions, losses, or damages resulting from the use
            of the chatbot. Do not enter any private, sensitive, personal, or
            regulated data. By using this chatbot, you acknowledge and agree
            that input you provide and answers you receive (collectively,
            “Content”) may be used by Snowflake to provide, maintain, develop,
            and improve their respective offerings. For more
            information on how Snowflake may use your Content, see
            https://streamlit.io/terms-of-service.
        """)


# -----------------------------------------------------------------------------
# Draw the UI.


st.html(div(style=styles(font_size=rem(5), line_height=1))["❉"])

title_row = st.container(
    horizontal=True,
    vertical_alignment="bottom",
)

with title_row:
    st.title(
        # ":material/cognition_2: Streamlit AI assistant", anchor=False, width="stretch"
        "Lets compare a vanilla LLM with a RAG powered one... about stuff",
        anchor=False,
        width="stretch",
    )

user_just_asked_initial_question = (
    "initial_question" in st.session_state and st.session_state.initial_question
)

user_just_clicked_suggestion = (
    "selected_suggestion" in st.session_state and st.session_state.selected_suggestion
)

user_first_interaction = (
    user_just_asked_initial_question or user_just_clicked_suggestion
)

has_message_history = (
    len(st.session_state["chats"][0].history) > 0 and len(st.session_state["chats"][1].history) > 0
)

# Show a different UI when the user hasn't asked a question yet.
if not user_first_interaction and not has_message_history:

    with st.container():
        st.chat_input("Ask a question...", key="initial_question")

        selected_suggestion = st.pills(
            label="Examples",
            label_visibility="collapsed",
            options=SUGGESTIONS.keys(),
            key="selected_suggestion",
        )

    st.button(
        "&nbsp;:small[:gray[:material/balance: Legal disclaimer]]",
        type="tertiary",
        on_click=show_disclaimer_dialog,
    )

    st.stop()


cols = st.columns(2)
for chat, col in zip(st.session_state.chats , cols):
    with col:
        st.header(chat.name)


        if "prev_question_timestamp" not in st.session_state:
            st.session_state.prev_question_timestamp = datetime.datetime.fromtimestamp(0)


        # Display chat messages from history as speech bubbles.
        for i, message in enumerate(chat.history):
            with st.chat_message(message["role"]):
                if message["role"] == "assistant":
                    st.container()  # Fix ghost message bug.
                st.markdown(message["content"])

        user_message = st.chat_input("Ask a follow-up...", key="user_followup" + chat.name)

        if not user_message:
            if user_just_asked_initial_question:
                user_message = st.session_state.initial_question
            if user_just_clicked_suggestion:
                user_message = SUGGESTIONS[st.session_state.selected_suggestion]

        if user_message:
            # When the user posts a message...

            # Streamlit's Markdown engine interprets "$" as LaTeX code (used to
            # display math). The line below fixes it.
            user_message = user_message.replace("$", r"\$")

            # Display message as a speech bubble.
            with st.chat_message("user"):
                st.text(user_message)

            # Display assistant response as a speech bubble.
            with st.chat_message("assistant"):
                with st.spinner("Waiting..."):
                    # Rate-limit the input if needed.
                    question_timestamp = datetime.datetime.now()
                    time_diff = question_timestamp - st.session_state.prev_question_timestamp
                    st.session_state.prev_question_timestamp = question_timestamp

                    #if time_diff < MIN_TIME_BETWEEN_REQUESTS:
                    #    time.sleep(time_diff.seconds + time_diff.microseconds * 0.001)

                    user_message = user_message.replace("'", "")

                # Send prompt to LLM.
                with st.spinner("Thinking..."):
                    response_gen = [chat.chat(user_message)]

                    # Put everything after the spinners in a container to fix the
                    # ghost message bug.
                    with st.container():
                        # Stream the LLM response.
                        response = st.write_stream(response_gen)


# Clear the chat
with title_row:
        def clear_conversation():
            for chat in st.session_state['chats']:
                chat.clear_chat() 
            st.session_state.initial_question = None
            st.session_state.selected_suggestion = None
        st.button(
            "Restart",
            icon=":material/refresh:",
            on_click=clear_conversation,
        )





