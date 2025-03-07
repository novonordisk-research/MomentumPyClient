import pandas as pd
import streamlit as st
import MomentumPyClient.ui as stm
import time

st.set_page_config(layout="wide")
st.write("Get containers with all attributes")

# time this for loop
start_time = time.time()

containers = stm.ws.get_containers_with_attributes(flatten=True)

end_time = time.time()
st.write(f"Time taken for the for loop: {end_time - start_time} seconds")
df = pd.DataFrame(containers)
st.write(df)
