from streamlit.runtime.uploaded_file_manager import UploadedFile
from utils.EDF import EDFutils

class EDFConfig:
    def __init__(self) -> None:
        self.name = None


class LabelConfig:
    def __init__(self, file: UploadedFile) -> None:
        pass