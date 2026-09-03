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

from htbuilder.units import rem
from htbuilder import div, styles
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
from chat import Chat
import datetime
import textwrap
import time
from threading import Thread

import streamlit as st

st.set_page_config(layout="wide")

if 'chats' not in st.session_state:
    st.session_state['chats'] = [Chat("Normal chat", False), Chat("RAG powered chat", True)]

st.set_page_config(page_title="Numpy AI assistant", page_icon="🤖")

SUGGESTIONS = {
    ":blue[:material/local_library:] Which function to use to calculate the covariance matrix using numpy? Which are its arguments?": (
        "Which function to use to calculate the covariance matrix using numpy? Which are its arguments?"
    ),
    ":green[:material/database:] What does the `ddof` argument do in `np.cov` function?": (
        "What does the `ddof` argument do in `np.cov` function?"
    ),
    ":orange[:material/multiline_chart:] What are the option for the density argument in `np.histogram`?": (
        "What are the option for the density argument i `np.histogram`?"
    ),
    ":violet[:material/apparel:] How to calculate the outer product of two numpy arrays?": (
        "How to calculate the outer product of two numpy arrays?"
    ),
    ":red[:material/deployed_code:] What does the `out` argument of `np.clip` do?": (
        "What does the `out` argument of `np.clip` do?"
    ),
    ":blue[:material/local_library:] How to fit a Chebyshev polynomial with numpy?": ("How to fit a Chebyshev polynomial with numpy?"),
    ":red[:material/multiline_chart:] How big is a football field?": ("How big is a football field?")
}

@st.dialog("Info")
def show_disclaimer_dialog():
    st.caption("""
            This AI chatbot is powered by a qwen3.5:0.8b small LLM coupled with a ChromaDB RAG backbone to provide usefull context to the LLM. The backend was developed using FastAPI which exposes a REST API framework that allows one to use a Streamlit webapp as frontend. We provide two option, a "normal" chat (not RAG powered) and a RAG powered version, so compare between the two methods. """)


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
        "A Numpy RAG powered AI assistant",
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
    len(st.session_state["chats"][0].messages) > 0 and len(st.session_state["chats"][1].messages) > 0
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
        "&nbsp;:small[:gray[:material/balance: Disclaimer]]",
        type="tertiary",
        on_click=show_disclaimer_dialog,
    )

    st.stop()

def render_chat_column(chat, col):
    with col:
        colsinside = st.columns([2, 1])
        with colsinside[0]:
            st.header(chat.name)
        if (chat.rag):
            with colsinside[1]: 
                @st.dialog("Show context", width="large")
                def show_context():
                    st.text("\n".join(st.session_state.chats[1].messages[0]["content"].split("\n")[1:-1]))


                st.text("\n\n")
                st.button(
                    "Show context",
                    icon=":material/refresh:",
                    on_click=show_context,
                )

        if "prev_question_timestamp" not in st.session_state:
            st.session_state.prev_question_timestamp = datetime.datetime.fromtimestamp(0)

        message_container = st.container()

        # Display chat messages from history as speech bubbles.
        with message_container:
            for i, message in enumerate(chat.messages):
                if message["role"] == "system":
                    continue
                with st.chat_message(message["role"]):
                    if message["role"] == "assistant":
                        st.container()  # Fix ghost message bug.
                    st.markdown(message["content"])

        user_message = st.chat_input("Ask a follow-up...", key="user_followup_" + chat.name)

        with message_container:
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
                    st.markdown(user_message)

                # Display assistant response as a speech bubble.
                with st.chat_message("assistant"):
                    with st.spinner("Waiting..."):
                        question_timestamp = datetime.datetime.now()
                        time_diff = question_timestamp - st.session_state.prev_question_timestamp
                        st.session_state.prev_question_timestamp = question_timestamp
                        
                    user_message = user_message.replace("'", "")

                    with st.spinner("Thinking..."):
                        response_gen = [chat.chat(user_message)]

                    with st.empty():
                        st.write_stream(response_gen)

cols = st.columns(2)

threads = []
for chat, col in zip(st.session_state.chats , cols):
    thread = Thread(target=render_chat_column, args=(chat, col))
    add_script_run_ctx(thread, get_script_run_ctx())
    thread.start()
    threads.append(thread)

for thread in threads:      # join ALL of them, not just the last
    thread.join()

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





