import streamlit as st

import MomentumPyClient.ui as stm

st.title("Inventory")

instruments = stm.ws.get_instrument_names()

hotel = st.selectbox("Select a hotel", instruments)

stm.show_store(hotel)
