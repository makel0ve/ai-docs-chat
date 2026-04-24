import json
import re

import httpx
import streamlit as st


def stream_response(question: str, session_id: int, provider: str):
    with httpx.Client(timeout=120) as client:
        with client.stream(
            "POST",
            "http://app:8000/chat",
            json={"question": question, "session_id": session_id, "provider": provider},
        ) as response:
            for line in response.iter_lines():
                if "data: " in line:
                    text = json.loads(line.split("data: ")[-1])
                    if "token" in text:
                        token = text.get("token")

                        yield token

                    if "chunks" in text:
                        st.session_state.last_chunks = text.get("chunks")


@st.fragment(run_every=5)
def documents_list():
    with httpx.Client() as client:
        documents = client.get(url="http://app:8000/documents").json()

    for document in documents:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(document["original_filename"])
            st.caption(status[document["status"]])

        with col2:
            if st.button("🗑️", key=document["id"]):
                with httpx.Client() as client:
                    client.delete(url=f"http://app:8000/documents/{document['id']}")

                st.rerun()


status = {"processing": "🟡 processing", "ready": "🟢 ready", "failed": "🔴 failed"}

if "sessions" not in st.session_state:
    st.session_state.sessions = []

if "last_chunks" not in st.session_state:
    st.session_state.last_chunks = None

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if "session_id" not in st.session_state:
    st.session_state.messages = []
    st.session_state.session_id = None

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["role"] == "assistant" and message.get("chunks"):
            with st.expander("📎 Источники"):
                sources = [int(n) for n in re.findall(r"\[(\d+)\]", message["content"])]
                for i, chunk in enumerate(message["chunks"]):
                    if i + 1 in sources:
                        st.write(f"[{i + 1}] {chunk['content']}...")

question = st.chat_input()

with st.sidebar:
    add_radio = st.radio(
        "Выберите модель LLM",
        ("gigachat", "yandex", "ollama"),
        format_func={
            "gigachat": "GigaChat",
            "yandex": "YandexGPT",
            "ollama": "Ollama",
        }.get,
    )

    upload_files = st.file_uploader(
        "Выберите файл",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key=st.session_state.uploader_key,
    )

    if upload_files:
        if st.button("Загрузить файлы"):
            files = [
                ("upload_files", (file.name, file.read())) for file in upload_files
            ]

            with httpx.Client() as client:
                client.post(url="http://app:8000/documents", files=files)

            st.session_state.uploader_key += 1
            st.rerun()

    if st.button("Новый чат"):
        st.session_state.session_id = None
        st.session_state.messages = []
        st.rerun()

    with httpx.Client() as client:
        sessions = client.get(url="http://app:8000/sessions").json()
        st.session_state.sessions = sessions

    for session in st.session_state.sessions:
        col1, col2 = st.columns([4, 1])
        with col1:
            label = session["title"] or session["created_at"][:16]
            if st.button(f"💬 {label}", key=f"session_{session['id']}"):
                st.session_state.session_id = session["id"]

                with httpx.Client() as client:
                    messages = client.get(
                        url=f"http://app:8000/sessions/{st.session_state.session_id}/messages"
                    ).json()

                st.session_state.messages = [
                    {"role": m["role"], "content": m["content"]} for m in messages
                ]
                st.rerun()

        with col2:
            if st.button("🗑️", key=f"del_session_{session['id']}"):
                with httpx.Client() as client:
                    client.delete(url=f"http://app:8000/sessions/{session['id']}")

                if st.session_state.session_id == session["id"]:
                    st.session_state.session_id = None
                    st.session_state.messages = []

                st.rerun()

    with st.expander("📄 Документы"):
        documents_list()

if question:
    if st.session_state.session_id is None:
        with httpx.Client() as client:
            session_id = client.post(url="http://app:8000/sessions").json()[
                "session_id"
            ]
            st.session_state.session_id = session_id

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        answer = st.write_stream(
            stream_response(question, st.session_state.session_id, add_radio)
        )

        with st.expander("📎 Источники"):
            sources = [int(number) for number in re.findall(r"\[(\d+)\]", answer)]
            for i, chunk in enumerate(st.session_state.last_chunks):
                if i + 1 in sources:
                    st.write(f"[{i + 1}] {chunk['content']}...")

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "chunks": st.session_state.last_chunks}
    )
