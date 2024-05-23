import streamlit as st
import modules.instructions as instruct
from modules.ConfigureSession import SessionConfig
from config import *

st.set_page_config(
    page_title=APP_NAME,
    initial_sidebar_state='expanded',
    layout='wide'
)
SessionConfig()
SessionConfig.insert_logo()


st.title('Compute Features')
instruct.feature_generation()


