import streamlit as st
from PIL import Image
import os
import requests
from models.blindness_model import BlindnessModel
from models.caption_generator import extract_image_description

# Set up Groq API Key
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Streamlit config
st.set_page_config(page_title="Blindness Detection App", layout="wide")
st.title("👁️ Blindness Detection from Retina Image")

# Upload
uploaded_file = st.sidebar.file_uploader("Upload an Eye Image (Retinal Scan)", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file).convert('RGB')

    # Reset on new image
    if "last_uploaded_filename" not in st.session_state or st.session_state.last_uploaded_filename != uploaded_file.name:
        st.session_state.result = None
        st.session_state.chat_history = []
        st.session_state.last_uploaded_filename = uploaded_file.name

    # Display image
    cols = st.columns(3)
    with cols[1]:
        st.image(image, caption="Uploaded Image", use_container_width=True)

    st.write("Analyzing...")

    if st.session_state.result is None:
        model = BlindnessModel()
        try:
            label, confidence = model.predict(image)
            st.session_state.result = {"label": label, "confidence": confidence}
        except Exception as e:
            st.error(f"Prediction failed: {str(e)}")
            st.stop()
    else:
        label = st.session_state.result["label"]
        confidence = st.session_state.result["confidence"]

    st.success(f"**Prediction:** {label}")
    st.info(f"**Confidence:** {confidence:.2f}")
    ###@st.cache_resource
    def explain_with_image_llm(image, label, confidence):
        visual_description = extract_image_description(image)

        prompt = f"""
        A retina scan image was analyzed. Here's what the AI vision model observed:
        "{visual_description}".

        Based on this, the model predicted: **{label}** with **{confidence*100:.2f}% confidence**.

        Explain in layman's terms:
        - What this condition means
        - How serious it might be
        - What the person should consider doing next

        Use clear, non-technical language.
        """

        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-70b-8192",
                "messages": [
                    {"role": "system", "content": "You are a helpful medical assistant specialized in retinal diseases."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
            }
        )

        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            st.session_state.chat_history = [
                {"role": "system", "content": "You are a helpful medical assistant specialized in retinal diseases."},
                {"role": "assistant", "content": content}
            ]
            return content
        else:
            return "Sorry, we couldn't generate an explanation at the moment."

    if st.button("Explain Diagnosis with AI"):
        with st.spinner("Generating image-aware explanation..."):
            explanation = explain_with_image_llm(image, label, confidence)

    if "chat_history" in st.session_state and len(st.session_state.chat_history) > 1:
        st.markdown("### 💬 🧠 AI Explanation ChatBot")

        for msg in st.session_state.chat_history[1:]:
            st.chat_message(msg["role"]).markdown(msg["content"])

        user_input = st.chat_input("Ask a question about the condition...")

        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.spinner("AI is typing..."):
                response = requests.post(
                    GROQ_API_URL,
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama3-70b-8192",
                        "messages": st.session_state.chat_history,
                        "temperature": 0.7,
                    }
                )
                if response.status_code == 200:
                    reply = response.json()["choices"][0]["message"]["content"]
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    st.chat_message("assistant").markdown(reply)
                else:
                    error_msg = "Sorry, the AI couldn't respond at the moment."
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
                    st.chat_message("assistant").markdown(error_msg)
