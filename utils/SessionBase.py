import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
import os
import json
import config as cfg

class SessionBase:
    @staticmethod
    def validate_analysis(analysis: str):
        """
        Confirm that analysis string is a valid directory name and
        that it does not already exist.
        """
        if analysis.strip() == '':
            return (False, "Enter an analysis name to get started.")
        elif analysis in SessionBase.get_existing_analyses():
            return (False, "Analysis name already in use.")
        else:
            return (True, "Pass")

    @staticmethod
    def get_existing_analyses() -> list:
        return os.listdir('filestore')
    
    @staticmethod
    def get_edf_from_analysis(analysis: str, path=False) -> str | None:
        if analysis in SessionBase.get_existing_analyses():
            for file in os.listdir(f'{cfg.ANALYSIS_STORE}/{analysis}'):
                ext = file.split('.')[-1].lower()
                if ext == 'edf' and not path:
                    return file
                elif ext == 'edf' and path:
                    return f"{cfg.ANALYSIS_STORE}/{analysis}/{file}"
        return None

    @staticmethod
    def initialize_session() -> None:
        SESSION_VARS = (
            'analysis',
            'edf_path',
            'label_path',
            'EDF',
            'labels',
        )
        for session_var in SESSION_VARS:
            if session_var not in st.session_state:
                st.session_state[session_var] = None

    @staticmethod
    def write_edf(file: UploadedFile, parent_dir):
        session_dir = f'{cfg.ANALYSIS_STORE}/{parent_dir}'
        if parent_dir not in os.listdir(cfg.ANALYSIS_STORE):
            os.mkdir(session_dir)

        existing_file = SessionBase.get_edf_from_analysis(parent_dir)
        if existing_file is not None:
            os.remove(f"{cfg.ANALYSIS_STORE}/{parent_dir}/{existing_file}")

        file_bytes = file.read()
        file_write_path = f'{session_dir}/{file.name}'
        with open(file_write_path, 'wb') as f:
            f.write(file_bytes)

    @staticmethod
    def write_configuration(config: dict, analysis, name):
        path = f"{cfg.ANALYSIS_STORE}/{analysis}/{name}"
        with open(path, "w") as f:
            json.dump(config, f, default=str)
            