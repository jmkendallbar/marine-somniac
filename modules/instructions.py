import streamlit as st

PICK_ANALYSIS_HELP = 'You can create an analysis in the "Start New Analysis" page.'
ANALYSIS_NAME = 'This will be a directory name, special characters may be rejected'
UPLOAD_HELP = "Drop only one of each file type here (only 1 .edf, 1 .edfconfig, 1 .labelconfig)"
CHANNEL_TYPE_HELP = ""

def feature_generation():
    st.markdown('')

def get_started():
    st.title("Mapping your files")
    st.markdown("""
        This application needs to know a few details about your data before we can get started
        with your analysis. This is where you can specify things like which channels you'll
        be exploring and letting the application know what they are. Configurations need to be 
        specified for both your EDF data as well as any label data (if you will be training your
        own models). The returned config files have custom file extensions of `edfyml` and 
        `labelyml`, but this is just for file type detection; the configurations themselves are 
        simply YAML. 
    """)

    with st.expander("Configuration Summary & File Constraints"):
        st.markdown("""
            **Signal Data (must be EDF)**  
            * Config will specify time bracket of your analysis (needed to line up with your labels)
            * Config will specify what your custom channel names represent (are they ECG, motion data?)
                    
            **Label Data (must be CSV)**
            * All rows should be equally spaced time intervals (ex: each row labels 1 second)
            * Config will specify which column refers to your time interval and your label(s)
        """)

    st.markdown("""        
        You only have to do this once per analysis (just make sure to download your config files!).
        If you ever need to edit your configuration, just upload it in the sidebar and modify it
        in this page. You'll need to re-download the configurations after modification.
    """)
    st.subheader("Start a new analysis below")