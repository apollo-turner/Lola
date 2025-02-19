import streamlit as st
import requests

st.title("Lola - AI Assistant")

query = st.text_input("Ask Lola something:")

if st.button("Send"):
    response = requests.post("http://localhost:8000/query", json={"text": query})
    st.write(response.json()["response"])
