import pandas as pd
import streamlit as st
import MomentumPyClient.ui as stm

st.set_page_config(layout="wide")

st.write(stm.ws.get_status())
c1, c2, c3 = st.columns(3)
if c1.button("stop"):
    stm.ws.stop()
if c2.button("start"):
    stm.ws.start()
if c3.button("simulate"):
    stm.ws.simulate()

stm.show_process_selector()

c1, c2 = st.columns(2)
instrument = c1.selectbox("select a an instrument", stm.ws.get_instrument_names())
template = c2.selectbox("select a template ", stm.ws.get_template_names())
available_plates = stm.ws.get_barcodes(template, instrument)
if available_plates:
    st.write("Available plates:")
    st.write(pd.DataFrame(available_plates))
stm.show_store(instrument)
