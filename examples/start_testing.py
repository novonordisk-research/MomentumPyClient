import streamlit as st
import MomentumPyClient.ui as stm

st.header("Staring process with variables")
status = stm.ws.get_status()
st.write(status)
stm.show_process_selector()
