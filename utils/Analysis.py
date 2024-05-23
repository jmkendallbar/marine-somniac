import streamlit as st
from utils.EDF import EDFutils
class Analysis:
    def __init__(self, edf_config, label_config, labels) -> None:
        pass

    def edf() -> EDFutils:
        if (edf := st.session_state.get('EDF')):
            return edf
        else:
            create_edf(st.session_state())