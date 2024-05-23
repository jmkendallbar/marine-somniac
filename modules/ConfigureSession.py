import streamlit as st
import modules.instructions as instruct
from utils.SessionBase import SessionBase

# idea:
# could decorate class such that all returns are stored in the session_state...
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

