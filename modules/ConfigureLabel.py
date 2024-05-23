import streamlit as st
import pandas as pd
import modules.instructions as instruct
from utils.SessionBase import SessionBase


class ConfigureLabel(SessionBase):
    def __init__(self, analysis) -> None:
        self.analysis = analysis
        # self.csvpath = self.get_edf_from_analysis(analysis, path=True)

    def upload_file(self) -> None:
        file = st.file_uploader('Drop your lable CSV file here')
        if st.button('Save labels to analysis', disabled=file is None):
            with st.spinner('Writing file to disk, this may take a minute...'):
                self.write_edf(file, self.analysis)

        existing_edf = self.get_edf_from_analysis(self.analysis)
        if existing_edf:
            st.warning("An EDF file already exists in this analysis. "
                       "Clicking the save button will overwrite it")
        self.edfpath = self.get_edf_from_analysis(self.analysis, path=True)
    
    def save_configuration(self) -> None:
        pass

    def get_configuration(self) -> dict:
        pass

    def validate_configuration(self) -> tuple:
        pass