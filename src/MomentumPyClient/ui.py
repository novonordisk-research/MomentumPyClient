import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from .ws import Momentum

"""
This module provides a class to interact with momentum api with streamlit.

Since streamlit does a lot of page refreshes the api functions are cached with st.cache_data()
"""


# @st.cache_resource()
class StreamlitMomentum:
    def __init__(self, ws: Momentum = None):
        if ws is None:
            ws = Momentum()
        self.ws = ws

    def get_container_definitions(self):
        self.containers = self.ws.get_container_definitions()
        # Assign unique colors to each container definition
        color_names = [
            "orange",
            "yellow",
            "red",
            "gold",
            "green",
            "purple",
            "black",
            "blue",
            "brown",
            "cyan",
            "gray",
        ]
        i = 0
        for container in self.containers:
            container["color"] = color_names[i]
            i += 1
            if i >= len(color_names):
                i = 0
        return self.containers

    def show_process_selector(self):
        with st.expander("Run a process with variables", expanded=True):
            c1, c2 = st.columns(2)
            process = c1.selectbox("select a process", self.ws.get_process_names())
            iterations = c2.number_input("iterations", value=1)
            variables = self.ws.get_process_variables(process_name=process)
            if len(variables) > 0:
                st.write(f"the process {process} has the following variables:")
                variables_df = pd.DataFrame(variables)
                st.write(variables_df)
                variables_df = variables_df.rename(columns={"DefaultValue": "Value"})
                variables_df = variables_df[
                    ["Name", "NativeType", "Value", "Comments"]
                ].set_index("Name")
                variables_edited = st.data_editor(
                    variables_df,
                    disabled=["NativeType", "_index", "Comments"],
                    key="variables_editor",
                    width=700,
                )
                variables_dict = variables_edited["Value"].to_dict()
            else:
                variables_dict = {}
            if st.button(f"Run process {process}"):
                self.ws.run_process(
                    process=process, variables=variables_dict, iterations=iterations
                )

    def show_store(self, storename, numbering_from_bottom=False):
        nests = self.ws.get_nests()
        if "Liconic" in storename:
            numbering_from_bottom = True
        containers = self.get_container_definitions()
        # Create a dictioary to lookup the color
        colorDict = {}
        for container in containers:
            colorDict[container["Name"]] = container["color"]
            colorDict[container["InventoryTemplateName"]] = container["color"]
        inv = pd.DataFrame(self.ws.reformat_container_nests(nests))

        inv = inv[inv["Name"] == storename]
        if inv.empty:
            return
        cols = len(inv.StackName.unique())
        rows = 1
        fig = make_subplots(
            rows=rows, cols=cols, horizontal_spacing=0.01, vertical_spacing=0.03
        )
        # keep track of curve numbers so user can select an item.
        curve_number = 0
        selection_thing = {}
        stack = 1
        for stackName, data in inv.groupby("StackName"):
            slots = len(data)

            colname = data.StackName.values[0]
            isStack = data.IsStack.values[0]
            if isStack:
                columnSort = True
            else:
                columnSort = numbering_from_bottom
            row = 1
            rackHeight = 300
            stack_pos = 0
            stackHeight = 14
            for n in data.sort_values("Nest", ascending=columnSort).to_dict("records"):
                lw = n["Template"]
                position = n["Nest"]
                if lw:
                    barcode = n["Barcode"]
                    stack_pos -= stackHeight
                    if lw in colorDict:
                        color = colorDict[lw]
                    else:
                        color = "blue"
                    fig.add_trace(
                        go.Bar(
                            x=[colname],
                            y=[stackHeight],
                            marker_color=color,
                            marker_line_color="black",
                            marker_line_width=0.5,
                            name="",
                            text=barcode,
                            hovertemplate=f"{position}|{lw}|{barcode}",
                        ),
                        row,
                        stack,
                    )
                    selection_thing[curve_number] = {
                        "stack": colname,
                        "position": position,
                        "barcode": barcode,
                        "template": lw,
                        "curve_number": curve_number,
                    }
                    curve_number += 1
                    fig.add_trace(
                        go.Bar(
                            x=[colname],
                            y=[rackHeight / slots - stackHeight],
                            marker_color="lightgray",
                            marker_line_color="gray",
                            marker_line_width=1,
                            name="",
                            # text="domme",
                            hovertemplate=str(position),
                        ),
                        row,
                        stack,
                    )
                    selection_thing[curve_number] = {
                        "stack": colname,
                        "position": position,
                        "barcode": "",
                        "template": "",
                        "curve_number": curve_number,
                    }
                    curve_number += 1
                    stack_pos -= rackHeight / slots - stackHeight
                else:
                    fig.add_trace(
                        go.Bar(
                            x=[colname],
                            y=[rackHeight / slots],
                            marker_color="lightgray",
                            marker_line_color="gray",
                            marker_line_width=1,
                            name="",
                            text=str(position),
                            hovertemplate=f"{position}|Empty",
                        ),
                        row,
                        stack,
                    )
                    stack_pos -= rackHeight / slots
                    selection_thing[curve_number] = {
                        "name": colname,
                        "position": position,
                        "barcode": "",
                        "template": "",
                        "curve_number": curve_number,
                    }
                    curve_number += 1

            fig.add_trace(
                go.Bar(
                    x=[colname],
                    y=[0],
                    marker_color="lightgray",
                    marker_line_color="gray",
                    marker_line_width=1,
                    name="",
                    hovertemplate="Empty",
                ),
                row,
                stack,
            )
            curve_number += 1
            stack += 1
        fig.update_layout(
            barmode="stack",
            title_text=storename,
            margin=dict(l=1, r=00, t=23, b=1),
            showlegend=False,
            height=500,
        )
        fig.update_yaxes(automargin=True, showticklabels=False)
        fig.update_xaxes(showticklabels=True)
        events = st.plotly_chart(
            fig, use_container_width=True, selection_mode="points", on_select="rerun"
        )
        selected_list = []
        for selection in events["selection"]["points"]:
            if "curve_number" in selection:
                selected_list.append(selection_thing[selection["curve_number"]])
        return selected_list


_stm = StreamlitMomentum()

api = _stm.ws
ws = _stm.ws
show_store = _stm.show_store
show_process_selector = _stm.show_process_selector


# Cached versions of the api functions for use in streamlit
@st.cache_data(ttl=600)
def get_template_names():
    return _stm.ws.get_template_names()


@st.cache_data(ttl=600)
def get_instrument_nests(instrument):
    return _stm.ws.get_instrument_nests(instrument)


@st.cache_data(ttl=600)
def get_nests():
    return _stm.ws.get_nests()


@st.cache_data(ttl=600)
def get_container_definitions():
    return _stm.get_container_definitions()


def run_process(
    process,
    variables,
    batch_name="batch",
    append=True,
    iterations=1,
    minimum_delay=0,
    workunit_name: str | None = None,
):
    return _stm.ws.run_process(
        process=process,
        variables=variables,
        iterations=iterations,
        append=append,
        batch_name=batch_name,
        minimum_delay=minimum_delay,
        workunit_name=workunit_name,
    )
