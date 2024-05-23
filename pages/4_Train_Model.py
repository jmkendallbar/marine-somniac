import streamlit as st
from modules.ConfigureSession import SessionConfig
from config import *

st.set_page_config(
    page_title=APP_NAME,
    initial_sidebar_state='expanded',
    layout='wide'
)
SessionConfig()