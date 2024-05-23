import streamlit as st
import modules.instructions as instruct
import utils.configure as configure


class ConfigFileLoader:
    def __init__(self, container=st.sidebar) -> None:
        self.container = container
        with self.container:
            self.uploaded_files = st.file_uploader(
                'Drop your config files here',
                accept_multiple_files=True,
                help=instruct.UPLOAD_HELP,
            )

    def route_files(self):
        """
        Check uploaded file types, route their contents to the appropriate
        session variable 
        """
        for file in self.uploaded_files:
            ext = file.name.split('.')[1].lower()
            match ext:
                case 'edfyml':
                    st.session_state['edf_config'] = configure.EDFConfig(file)
                case 'csv':
                    st.session_state['labels'] = file
                case 'labelyml':
                    st.session_state['label_config'] = configure.LabelConfig(file)


    def validate_files(self):
        """
        Check that of the uploaded files:
        1. there is only one of each type (extension)
        2. one contains the data (.edf)
        3. all file types are accepted
        """
        ACCEPTED_TYPES = ('edfyml', 'csv', 'labelyml', 'procyml')
        type_counts = {k: 0 for k in ACCEPTED_TYPES}
        warnings = []
        errors = []

        for file in self.uploaded_files:
            extension = file.name.split('.')[1].lower()
            if not extension in ACCEPTED_TYPES:
                if extension == 'edf':
                    errors.append('EDF files do not belong here. Upload your edf in the "Get Started" page.')
                else:
                    errors.append(f"`{extension}` is not a valid file type. Accepted extensions: {ACCEPTED_TYPES}")
            else:
                type_counts[extension] += 1

        for ext, count in type_counts.items():
            if count == 0:
                warnings.append(f"No {ext} files detected")
            elif count > 1:
                errors.append(f"Too many {ext} files")

        if errors:
            st.error('; '.join(errors))
            st.divider()
            return False
        elif warnings:
            st.warning('; '.join(warnings))
            st.divider()
        return True
                    

    # @staticmethod
    # def global_warning():
    #     st.warning("Please follow the base instructions in the sidebar")