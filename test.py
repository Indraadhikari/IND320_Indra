import streamlit as st

st.title("Hello, Streamlit!")
st.write("This is your first Streamlit app.")

# Try changing the text below and saving the file!
name = st.text_input("What's your name?")
if name:
    st.write(f"Hello, {name}!")