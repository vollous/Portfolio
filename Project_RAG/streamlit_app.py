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
    st.session_state['chats'] = [Chat("Vanilla chat", False), Chat("RAG powered chat", True)]

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
    ":blue[:material/local_library:] Calculate covariant matrix": (
        "Which function to use to calculate the covariance matrix? Which are its arguments?"
    ),
    ":green[:material/database:] ddof in np.cov function": (
        "What does the ddof argument does in np.cov function?"
    ),
    ":orange[:material/multiline_chart:] Density argument in np.histogram": (
        "What are the option for the density argument in np.histogram?"
    ),
    ":violet[:material/apparel:] Calculate outer product.": (
        "How to calculate the outer product of two arrays?"
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
        "&nbsp;:small[:gray[:material/balance: Legal disclaimer]]",
        type="tertiary",
        on_click=show_disclaimer_dialog,
    )

    st.stop()


def render_chat_column(chat, col):
    with col:
        st.header(chat.name)
        if "prev_question_timestamp" not in st.session_state:
            st.session_state.prev_question_timestamp = datetime.datetime.fromtimestamp(0)

        message_container = st.container()

        # Display chat messages from history as speech bubbles.
        with message_container:
            for i, message in enumerate(chat.messages):
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
                        #time.sleep(2)
                    user_message = user_message.replace("'", "")

                    # Send prompt to LLM.
                    with st.spinner("Thinking..."):
                        response_gen = [chat.chat(user_message)]

                    # Put everything after the spinners in a container to fix the
                    # ghost message bug.
                    with st.empty():
                        # Stream the LLM response.
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





