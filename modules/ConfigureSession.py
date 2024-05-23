import streamlit as st
from streamlit_theme import st_theme
import modules.instructions as instruct
from utils.SessionBase import SessionBase


class SessionConfig(SessionBase):
    def __init__(self, sidebar_widget=True) -> None:
        self.initialize_session()
        if sidebar_widget:
            with st.sidebar:
                self.chosen_analysis = st.selectbox(
                    "Pick your analysis",
                    options=self.get_existing_analyses(),
                    help=instruct.PICK_ANALYSIS_HELP
                )
            self.set_session()

    def set_session(self):
        if self.chosen_analysis:
            pass

    @staticmethod
    def insert_logo(sidebar=True):
        theme = st_theme()['base']
        if sidebar:
            st.sidebar.image(f'assets/sidebar_logo_{theme}.jpeg')
        else:
            st.image(f'assets/logo_{theme}.jpeg')

