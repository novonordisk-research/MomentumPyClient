import streamlit as st
import MomentumPyClient.ui as stm

st.header("Scan barcodes")
# stm.set_template_colors(
#     {
#         "T_OrangeGTest": "orange",
#         "T_384_Assay": "yellow",
#         "T_SaltTitration_Source": "red",
#     }
# )
# allowed scan instruments
instrument_names = ["Carousel", "Liconic_1", "Liconic_2", "Liconic_3"]
instrument = st.selectbox("Instrument", instrument_names)
stm.show_store(instrument)

# get names of templates
template_names = stm.get_template_names()

c1, c2, c3 = st.columns(3)  # Create three columns
# Find the nests for the selected device.
stacks = stm.get_instrument_nests(instrument)
stack = c1.selectbox("Stack / Column", list(stacks.keys()), key="stack")
template = c2.selectbox("Template", template_names)
lidded = c3.checkbox("With lid")

selected_nests = st.multiselect("Nests", stacks[stack], key="nests")
selected_nests = ", ".join([f"{stack}:{x}" for x in selected_nests])

if st.button("Scan Barcodes"):
    variables = {
        "Instrument": instrument,
        "Template": template,
        "Nests": selected_nests,
        "Lidded": "true" if lidded else "false",
    }
    stm.run_process(
        process="ScanBarcodes2",
        variables=variables,
        batch_name="ScanBarcodes",
        append=True,
        iterations=1,
    )
    st.success("Scan started")
