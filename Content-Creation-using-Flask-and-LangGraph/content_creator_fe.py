import streamlit as st
import requests

st.title("AI Content Evaluator")

topic = st.text_input("Enter Topic")

if st.button("Generate and Evaluate"):

    if topic:

        with st.spinner("Processing..."):

            response = requests.post(
                "http://127.0.0.1:5000/generate",
                json={"topic": topic}
            )

            data = response.json()

            st.subheader("Generated Content")
            st.write(data["content"])

            st.subheader("Overall Feedback")
            st.write(data["feedback"])

            st.subheader("Average Score")
            st.write(data["score"])

