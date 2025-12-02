import requests
import streamlit as st

st.set_page_config(page_title="Dual-Response Medical Chatbot", page_icon="🤖")
st.title("Dual-Response Medical Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = st.text_input("Enter your User ID:", value="user_1")

user_input = st.text_input("Ask a medical question:", key="input")

if st.button("Send") and user_input:
    if not st.session_state.session_id:
        st.warning("Please enter a User ID.")
    else:
        st.session_state.messages.append({"role": "user", "content": user_input})
        payload = {
            "session_id": st.session_state.session_id,
            "question": user_input,
            # "db_type": db_type,
            "message": user_input,
            "thread_id": "thread_1",
        }
        try:
            response = requests.post("http://localhost:8000/medical_chat_stream", json=payload)
            print("Status code:", response.status_code)
            print("Response text:", response.text)
            if response.status_code == 200:
                data = response.json()
                st.session_state.messages.append({"role": "ai", "message": data})
            else:
                st.error(f"error: {response.text}")

        except Exception as e:
            st.error(f"Connection error: {e}")

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"**User:** {msg['content']}")
    else:
        if isinstance(msg["message"], dict):
            if "allopathy" in msg["message"] and "ayurveda" in msg["message"]:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Allopathy Response:**")
                    st.markdown(msg["message"]["allopathy"])
                with col2:
                    st.markdown("**Ayurveda Response:**")
                    st.markdown(msg["message"]["ayurveda"])
            if "general" in msg["message"]:
                st.markdown(f"**General Response:** {msg['message']['general']}")
        else:
            st.markdown(f"**AI:** {msg['message']}")
