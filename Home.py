import streamlit as st
from config import *

__PAPER_LINK = ''

st.set_page_config(
    page_title=APP_NAME,
    initial_sidebar_state='expanded',
    layout='centered',
    page_icon='assets/logo_dark.jpeg'
)

title, image = st.columns([4,2])
with title:
    st.title(APP_NAME)
    st.subheader('Sleep scoring for our aquatic pals')
with image:
    st.image('assets/logo_dark.jpeg', use_column_width=True)


st.markdown(
    f"Welcome to {APP_NAME}! This is a tool for partially automating sleep stage scoring. "
    "While this app was built with Northern elephant seals in mind, many utilities are "
    "generalizeable to other organisms, namely the computation of aggregate/windowed features "
    "from electrophysiological data (EEG, ECG) such as frequency power or heart rate."
)

st.subheader('Getting Started')
st.markdown(
    "Please note, this tool only functions on data of the .edf format. "
    "We have found that most feature computations are more effective on electrophysiological data "
    f"that has already undergone [some degree of processing (ICA)]({__PAPER_LINK}). "
)