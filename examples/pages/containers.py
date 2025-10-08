import streamlit as st
from MomentumPyClient import Momentum
import pandas as pd
from datetime import datetime
st.set_page_config(page_title="Momentum Containers", layout="wide")
m = Momentum()
st.write(m.get_status())

nests = m.get_nests()
containers = m.get_containers_with_attributes()

# Enrich the dnest data with container attributes and last update
def update_contents(d: dict, containers: list):
    for container in containers:
        if container["Name"] == d["ContainerName"]:
            d["LastUpdate"] = container['Attributes'][0]['Created']
            for attribute in container["Attributes"]:
                if attribute['Updated']:
                    if attribute['Updated'] > d["LastUpdate"]:
                        d["LastUpdate"] = attribute['Updated']
                d[attribute['Name']] = attribute['Value']
                d['TemplateName'] = container['Inventory']['TemplateName']

for nest in nests:
    if nest["Content"]:
        update_contents(nest["Content"], containers)
    if nest['StackContents']:
        for c in nest['StackContents']:
            update_contents(c, containers)
st.write(pd.DataFrame(m.reformat_container_nests(nests)))
st.write(pd.DataFrame(containers))
st.write(pd.DataFrame(nests))
st.write(nests)