import pandas as pd
import streamlit as st

import MomentumPyClient.ui as m

st.set_page_config(layout="wide")

st.write(m.ws.get_status())
c1, c2, c3 = st.columns(3)
if c1.button("stop"):
    m.ws.stop()
    st.rerun()
if c2.button("start"):
    m.ws.start()
    st.rerun()
if c3.button("simulate"):
    m.ws.simulate()
    st.rerun()

m.show_process_selector()

c1, c2 = st.columns(2)
template = c1.selectbox("select a template ", m.get_template_names())
instrument = c2.selectbox("select a hotel", m.ws.get_instrument_names())
available_plates = m.ws.get_barcodes(template, instrument)
if available_plates:
    st.write(pd.DataFrame(available_plates))

m.show_store(instrument)
