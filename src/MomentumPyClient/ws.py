import datetime
import xml.etree.ElementTree as ET
import asyncio
import requests
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from dotenv import dotenv_values
from typing import Iterable

import re


class Momentum:
    """
    A class to interact with the Momentum Web Services (ws) API.

    Input parameters are optional and can be provided as arguments or in a .env file With the following content

        momentum_user=<username>
        momentum_passwd=<password>
        momentum_verify=False
        momentum_url="https://localhost/api/"

    Attributes:
        url (str): The base URL for the Momentum API.
        user_name (str): The username for authentication.
        password (str): The password for authentication.
        verify (bool/str): Whether to verify SSL certificates or path to certificate file.
        headers (dict): The headers to include in API requests.
        login (dict): The login payload for authentication.
        token (str): The authentication token.
    Methods:
        _get(url):
            Sends a GET request to the specified URL.
        _post(url, data={}):
            Sends a POST request to the specified URL with the given data.
        _get_token() -> str:
            Retrieves an authentication token.
        stop():
            Stops the automation system.
        start():
            Starts the automation system in normal mode.
        simulate():
            Starts the automation system in simulation mode.
        get_version():
            Retrieves the version of the Momentum system.
        get_status():
            Retrieves the status of the automation system.
        get_devices():
            Retrieves the list of devices.
        get_containers():
            Retrieves the list of containers.
        add_inventory_items(items):
            Adds inventory items to the system.
        get_item_attribute(itemId):
            Retrieves the attributes of a specific item.
        get_experiments():
            Retrieves the list of experiments.
        get_container_definitions():
            Retrieves the container definitions.
        get_nests():
            Retrieves the list of nests.
        get_processes():
            Retrieves the list of processes.
        get_workqueue():
            Retrieves the work queue with batches.
        get_process_variables(id=0, process_name=""):
            Retrieves the variables for a specific process.
        runProcess(process, variables={}, batch_name="batch", append=False, iterations=1, minimum_delay=0, workunit_name=""):
            Runs a specific process with the given variables.
        runExperiment(experiment, variables={}, workunit_name="", batch_name="Batch"):
            Runs a specific experiment with the given variables.
        get_template_names():
            Retrieves the names of inventory templates.
        get_process_names():
            Retrieves the names of processes.
        get_instrument_names():
            Retrieves the names of instruments.
        get_barcodes(template_name, instrument=""):
            Retrieves the barcodes for a specific template and instrument.
        list_available_nests(location):
            Lists the empty nests in the specified location.
        reformat_container_nests(nests):
            Reformats the structure of the containers to a more useful format.
    """

    timeout: int = 1

    def __init__(
        self,
        url: str | None = None,
        user_name: str | None = None,
        password: str | None = None,
        verify: str | bool | None = None,
        timeout=5,
    ) -> None:
        """ """
        secrets = dotenv_values(".env")
        self._headers = {}
        if user_name is not None:
            self.user_name = user_name
        elif "momentum_user" in secrets:
            self.user_name = secrets["momentum_user"]
        else:
            raise Exception("No username specified")
        if password is not None:
            self.password = password
        elif "momentum_passwd" in secrets:
            self.password = secrets["momentum_passwd"]
        else:
            raise Exception("No password specified")

        self.login = {
            "Username": self.user_name,
            "Password": self.password,
            "OfflineAccess": False,
        }

        if verify is not None:
            self.verify = verify
        elif "momentum_verify" in secrets:
            if secrets["momentum_verify"].upper() == "FALSE":
                self.verify = False
            elif secrets["momentum_verify"].upper() == "TRUE":
                self.verify = True
            else:
                self.verify = secrets["momentum_verify"]
        else:
            self.verify = False
        if isinstance(self.verify, bool) and not self.verify:
            disable_warnings(InsecureRequestWarning)
        if url is not None:
            self.url = url
        elif "momentum_url" in secrets:
            self.url = secrets["momentum_url"]
        if self.url == "":
            raise Exception("No URL provided")

        self._token = ""
        self._headers = {}
        self.timeout = timeout

    def _send_get_request(self, url: str) -> dict:
        resp = requests.get(
            url, verify=self.verify, timeout=self.timeout, headers=self._headers
        )
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 401:
            # Retry once if to check if the token has expired
            self._token = self._get_token()
            self._headers = {"Authorization": "Bearer {}".format(self._token)}
            resp = requests.get(
                url, verify=self.verify, headers=self._headers, timeout=1
            )
            if resp.status_code == 200:
                return resp.json()
        raise Exception(f"Error {resp.status_code} getting {url} ")

    def _send_post_request(self, url: str, data: dict | str = None) -> dict | None:
        if isinstance(data, dict):
            resp = requests.post(
                url,
                json=data,
                verify=self.verify,
                headers=self._headers,
                timeout=self.timeout,
            )
        else:
            resp = requests.post(
                url,
                data=data,
                verify=self.verify,
                headers=self._headers,
                timeout=self.timeout,
            )
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 202:
            return  # No return value
        raise Exception(
            f"Error {resp.status_code}: {resp.text} posting {url} with {data}"
        )

    def _send_delete_request(self, url: str) -> dict | None:
        resp = requests.delete(
            url, verify=self.verify, headers=self._headers, timeout=1
        )
        if resp.status_code == 204:
            return None
        elif resp.status_code == 200:
            return resp.json()
        raise Exception(f"Error {resp.status_code}:{resp.text}, deleting {url}")

    def _get_token(self) -> str:
        url = self.url + "token/accesstoken"
        return self._send_post_request(url, self.login)["Token"]

    def stop(self):
        """
        Stops the automation system.
        """
        url = self.url + "momentum/automationsystem/stop"
        return self._send_post_request(url)

    def start(self):
        """
        Starts the automation system in normal mode.
        """
        url = self.url + "momentum/automationsystem/start?Mode=Normal"
        return self._send_post_request(url)

    def simulate(self):
        """
        Starts the automation system in simulation mode.
        """
        url = self.url + "momentum/automationsystem/start?Mode=Simulate"
        return self._send_post_request(url)

    def get_version(self) -> dict:
        """
        Retrieves the version of the Momentum system.
        """
        url = self.url + "momentum/version"
        return self._send_get_request(url)

    def get_status(self) -> dict:
        """
        Retrieves the status of the automation system.
        """
        url = self.url + "momentum/automationsystem"
        return self._send_get_request(url)

    def get_devices(self) -> list:
        """
        Retrieves the list of devices on the system.
        """
        url = self.url + "momentum/devices"
        return self._send_get_request(url)

    def get_containers(self) -> list:
        """
        Retrieves a list of the containers on the system.
        """
        url = self.url + "momentum/containers"
        return self._send_get_request(url)

    def add_inventyory_items(self, items: dict) -> list:
        """
        Adds inventory items to the system.

        Example of items:
        {
            "TemplateIdentifier": "I_Plate_1",
            "StartingNestName": "CybioStack:Stack 2",
            "NumberOfItems": 2,
            "ReserveNests": true,
            "ReadBarcodeOnFirstRelocation": true,
            "SkipNestsWithMismatchTemplate": true,
            "StackNestAccessDirection": "Bottom",
            "Barcodes" : [ "ABC123", "XYZ987" ]
        }
        """
        url = self.url + "momentum/inventory/items"
        resp = requests.post(
            url, json=items, verify=self.verify, headers=self._headers, timeout=1
        )
        # Here the return can be code #400 if the nest is occupied
        if resp.status_code == 200 or resp.status_code == 400:
            return resp.json()
        raise Exception(
            f"error adding inventory items {resp.status_code} with {url} and {items}"
        )

    def delete_inventory_item(self, barcode: str = "", template: str = "*"):
        """
        Deletes an inventory item from the system based on a barcode or a template
        """
        url = self.url + f"momentum/inventory/items?template={template}"
        if barcode != "":
            url = url + f"&barcode={barcode}"
        return self._send_delete_request(url)

    def get_item_attribute(self, itemId: int) -> list:
        """
        Retrieves the attributes of a specific container on the system.
        """
        url = self.url + f"momentum/inventory/items/{itemId}/attributes"
        return self._send_get_request(url)

    async def async_get_item_attribute(self, itemId: int) -> list:
        """
        Retrieves the attributes of a specific container on the system.
        """
        return await asyncio.to_thread(self.get_item_attribute, itemId)

    async def get_container_attributes(self, container: dict) -> dict:
        """
        Async function to get the attributes of a container and add them to the container dictionary.
        """
        id = container["Inventory"]["ItemId"]
        attributes = await self.async_get_item_attribute(id)
        container["Attributes"] = attributes
        return container

    async def fetch_all_attributes(self, containers: Iterable[dict]):
        """
        Async function to fetch all the attributes of a list of containers.
        """
        containers = await asyncio.gather(
            *[self.get_container_attributes(container) for container in containers]
        )
        return containers

    def get_containers_with_attributes(
        self, filter: str = "", flatten: bool = False
    ) -> list:
        """
        Get containers and fetch attributes for each container.
        Uses async io to speed up the process.

        parameters
            filter = plate name must contain this string .
            flatten == False -> attributes are added as a field called "Attributes"
            flatten == True => each attribute value is added with the attribute name as key.

        """
        containers = self.get_containers()
        if filter != "":
            containers = [c for c in containers if filter in c["Name"]]
        containers_with_attributes = asyncio.run(self.fetch_all_attributes(containers))
        if flatten:
            for container in containers_with_attributes:
                for attribute in container["Attributes"]:
                    container[attribute["Name"]] = attribute["Value"]
                del container["Attributes"]
        return containers_with_attributes

    def get_experiments(self) -> list:
        """
        Retrieves the list of experiments on the system.
        """
        url = self.url + "momentum/experiments"
        return self._send_get_request(url)

    def get_container_definitions(self) -> list:
        """
        Retrieves the container definitions on the system.
        """
        url = self.url + "momentum/containers/definition"
        return self._send_get_request(url)

    def get_nests(self) -> list:
        """
        Retrieves the list of nests on the system.
        """
        url = self.url + "momentum/nests"
        return self._send_get_request(url)

    def get_processes(self) -> list:
        """
        Retrieves the list of processes on the system.
        """
        url = self.url + "momentum/processes"
        return self._send_get_request(url)

    def get_workqueue(self) -> list:
        """
        Retrieves the work queue with batches.
        """
        url = self.url + "momentum/workqueue/workunits?batches=true"
        return self._send_get_request(url)

    def get_process_variables(
        self, process_name: str = "", process_id: int = 0
    ) -> list:
        """
        Retrieves the variables for a specific process.
        """
        if process_id > 0:
            url = self.url + f"/momentum/variables?processId={process_id}"
        else:
            processes = self.get_processes()
            for p in processes:
                if p["Name"] == process_name:
                    process_id = p["Id"]
        url = self.url + f"momentum/variables?process={process_id}"
        return self._send_get_request(url)

    def create_worklist_xml(self, worklist: dict) -> str:
        """
        Creates an XML string from a worklist dictionary.
        """
        worklist_root = ET.Element("worklist")

        keywords_dict = dict(
            name=worklist["Name"],
            auto_load="true",
            auto_verify="true",
            auto_verify_load="true",
            auto_unload="true",
            append="false",
        )

        for key in keywords_dict:
            if key in worklist:
                keywords_dict[key] = "true" if worklist[key] else "false"
        workunit = ET.SubElement(worklist_root, "workunit", keywords_dict)
        for batch in worklist["Batches"]:
            batch_node = ET.SubElement(
                workunit,
                "batch",
                {
                    "process": batch["Process"],
                    "name": batch["Name"],
                    "iterations": str(batch["Iterations"]),
                    "minimumDelay": str(batch["MinimumDelay"]),
                },
            )
            for variable in batch["Variables"]:
                if "Value" in variable:
                    # This is a single variable
                    ET.SubElement(
                        batch_node, "variable", {"name": variable["Name"]}
                    ).text = str(variable["Value"])
                elif "Values" in variable:
                    # This is a list of variables for each iteration
                    variable_node = ET.SubElement(
                        batch_node, "variable", {"name": variable["Name"]}
                    )
                    i = 1
                    for value in variable["Values"]:
                        if isinstance(value, dict):
                            if "Iteration" in value:
                                i = value["Iteration"]
                            value = value["Value"]
                        ET.SubElement(
                            variable_node, "value", {"iteration": str(i)}
                        ).text = str(value)
                        i += 1
        return ET.tostring(worklist_root)

    def run_worklist(self, worklist: dict, verbose: bool = False) -> dict:
        """
        Starts a worklist on the system.

        Args:
            worklist (dict): The worklist to start.
        """
        url = self.url + "momentum/worklist"
        xml = self.create_worklist_xml(worklist)
        if verbose:
            print(xml)
        return self._send_post_request(url, xml)

    def run_process(
        self,
        process: str,
        variables: dict = {},
        batch_name: str = "batch",
        append: bool = True,
        iterations: int = 1,
        minimum_delay: int = 0,
        workunit_name: str | None = None,
    ):
        """
        Runs a specific process with the given variables.

        Args:
            process (str): The name of the process to run.
            variables (list7dict): A list variables to use in the process, as dictionaries with keys "Name" and "Value" and "Iteration".
            batch_name (str): The name of the batch to run.
            append (bool): Whether to append the process to an existing workunit.
            iterations (int): The number of iterations to run.
            minimum_delay (int): The minimum delay between iterations.
            workunit_name (str): The name of the workunit to run.
        """
        if workunit_name is None or workunit_name == "":
            # Create a new workunit number each day by counting the number of days since january 1 2020
            today = datetime.date.today()
            someday = datetime.date(2020, 1, 1)
            diff = today - someday
            workunit_name = "Work Unit " + str(diff.days)

        attributes = {
            "name": workunit_name,
            "auto_load": "true",
            "auto_verify": "true",
            "auto_verify_load": "true",
            "auto_unload": "true",
        }
        if append:
            wq = self.get_workqueue()
            for wu in wq:
                if wu["State"] == "Running" or wu["State"] == "Waiting":
                    attributes["name"] = wu["Name"]
                    attributes["append"] = "true"

        worklist = ET.Element("worklist")

        workunit = ET.SubElement(worklist, "workunit", attributes)

        batch = ET.SubElement(
            workunit,
            "batch",
            {
                "process": process,
                "name": batch_name,
                "iterations": str(iterations),
                "minimumDelay": str(minimum_delay),
            },
        )
        if isinstance(variables, dict):
            for variable in variables:
                variable_node = ET.SubElement(batch, "variable", {"name": variable})
                if isinstance(variables[variable], list):
                    i = 1
                    for value in variables[variable]:
                        ET.SubElement(
                            variable_node, "value", {"iteration": str(i)}
                        ).text = str(value)
                        i += 1
                elif (
                    isinstance(variables[variable], str) and ";" in variables[variable]
                ):
                    values = variables[variable].split(";")
                    for value in values:
                        ET.SubElement(variable_node, "value").text = str(value)
                else:
                    variable_node.text = str(variables[variable])
        else:
            # assume that the variables are a list of dictionaries with "name" and "value" keys - and may contain other keys such as "iteration" or "set_position"
            for variable in variables:
                # create a copy where all keys are lowercase
                variable_node = ET.SubElement(
                    batch, "variable", {"name": variable["Name"]}
                )
                i = 1
                if "Values" in variable:
                    if (
                        isinstance(variable["Values"], str)
                        and ";" in variable["Values"]
                    ):
                        values = variable["values"].split(";")
                    else:
                        values = variable["Values"]
                    for value in values:
                        if isinstance(value, dict):
                            if "Iteration" in variable:
                                i = variable["Iteration"]
                        ET.SubElement(
                            variable_node, "value", {"iteration": str(i)}
                        ).text = str(value)
                        i += 1
                else:
                    variable_node.text = str(variable["Value"])

        xmlstr = ET.tostring(worklist)
        url = self.url + "momentum/worklist"
        return self._send_post_request(url, xmlstr)

    def run_experiment(
        self,
        experiment: int,
        variables: dict = {},
        workunit_name: str = "",
        batch_name: str = "Batch",
    ):
        """
        Runs a specific experiment with the given variables.

        Args:
            experiment (str): The name of the experiment to run.
            variables (dict): The variables to use in the experiment.
            batch_name (str): The name of the batch to run.
            append (bool): Whether to append the process to an existing workunit.
            iterations (int): The number of iterations to run.
            minimum_delay (int): The minimum delay between iterations.
            workunit_name (str): The name of the workunit to run.
        """

        if workunit_name == "":
            # Create a new workunit number each day by counting the number of days since january 1 2020
            today = datetime.date.today()
            someday = datetime.date(2020, 1, 1)
            diff = today - someday
            workunit_name = "Work Unit " + str(diff.days)
        worklist = ET.Element("worklist")
        workunit = ET.SubElement(
            worklist,
            "workunit",
            {
                "name": workunit_name,
                "auto_load": "true",
                "auto_verify": "true",
                "auto_verify_load": "true",
            },
        )
        batch = ET.SubElement(
            workunit,
            "batch",
            {
                "experiment": experiment,
                "name": batch_name,
                "iterations": "15",
                "minimumDelay": "0",
            },
        )
        for v in variables:
            variable = ET.SubElement(batch, "variable", {"name": v})
            variable.text = str(variables[v])
        xmlstr = ET.tostring(worklist)
        url = self.url + "momentum/worklist"
        return self._send_post_request(url, xmlstr)

    def get_template_names(self) -> list:
        """
        Retrieves the names of inventory templates.
        """
        containers = self.get_container_definitions()
        return sorted(
            {
                c["InventoryTemplateName"]
                for c in containers
                if c["InventoryTemplateName"]
            }
        )

    def get_process_names(self) -> list:
        """
        Retrieves the names of processes.
        """
        processes = self.get_processes()
        return [p["Name"] for p in processes]

    def get_instrument_names(self) -> list:
        """
        Retrieves the names of devices that are instruments (i.e. can hold plates).
        """
        devices = self.get_devices()
        return [d["Name"] for d in devices if d["IsInstrument"]]

    def get_instrument_nests(self, instrument: str) -> dict:
        """
        Return a dictionary with stacks names as keys and a list of Nests names as values.
        TODO make this work if there is a single Nest or nests are named "Bucket N" or "Stack N"
        """
        nests = self.get_nests()
        stacks = {}
        for nest in nests:
            if instrument == nest["DeviceName"]:
                # Check if the nest name ends with "nest N" where N is a number
                parts = nest["Name"].split(":")
                if len(parts) == 3:
                    if re.match(r".*Nest \d+$", nest["Name"]):
                        if parts[1] not in stacks:
                            stacks[parts[1]] = []
                        stacks[parts[1]].append(parts[2])
                if len(parts) == 2:
                    if "Stack1" in parts[1]:  # Cannot give a nest for a stack
                        continue
                    if parts[0] not in stacks:
                        stacks[parts[0]] = []
                    stacks[parts[0]].append(parts[1])
        return stacks

    def get_barcodes(self, template_name: str, instrument: str = "") -> list:
        """
        Retrieves the plate barcodes for a specific template and instrument.
        """
        containers = self.get_containers()
        x = []
        for c in containers:
            if c["Inventory"]["TemplateName"] == template_name:
                if instrument in c["Location"]:
                    x.append({"Barcode": c["Barcode"], "Location": c["Location"]})

        return x

    def list_available_nests(self, location: str) -> list:
        """
        List the empty nests in the hotel
        """
        nests = self.get_nests()
        availablePositions = []
        for nest in nests:
            if location in nest["Name"] and nest["Content"] is None:
                availablePositions.append(nest["Name"])
        return availablePositions

        # Reformat the stucture of the containers to a more usefull format

    def reformat_container_nests(self, nests: Iterable[dict]) -> list:
        """
        Reformats the structure of the containers to a more useful format.
        """
        slots = []
        for n in nests:
            if "Waste" in n["Name"]:
                continue
            m = n["Name"].replace("\n", "").split(":")
            col = 1
            nest = 1
            barcode = ""
            template = ""
            name = m[0]
            if len(m) == 2:
                stack_name = m[0]
            else:
                stack_name = m[1]
            if "Column" in m[1]:
                col = int(m[1].split("_")[0].replace("Column", ""))
                stack_name = m[1]
            if "Stack " in m[1]:
                col = int(m[1].replace("Stack ", ""))
            if "Bucket " in m[1]:
                nest = int(m[1].replace("Bucket ", ""))
            if "Lid Storage" in m[1]:
                name = "Lid Storage"
            if "Nest " in m[1]:
                nest = int(m[1].replace("Nest ", ""))
            if len(m) > 2 and "Nest" in m[2]:
                nest = int(m[2].replace("Nest ", ""))
            if n["Content"] is not None and "Barcode" in n["Content"]:
                barcode = n["Content"]["Barcode"]
                template = n["Content"]["ContainerName"].split(" (Id:")[0]
            if "Shovel" in m[1]:
                name = name + "_Shovel"
                continue
            if "Transfer" in m[1]:
                name = name + "_Transfer"
                continue
            if n["IsStack"]:
                if len(n["StackContents"]) == 0:
                    s = {
                        "Name": name,
                        "Stack": col,
                        "StackName": stack_name,
                        "Nest": 1,
                        "Barcode": "",
                        "Template": "",
                        "IsStack": n["IsStack"],
                    }
                    slots.append(s)
                else:
                    for sc in n["StackContents"]:
                        template = sc["ContainerName"].split(" (Id:")[0]
                        barcode = sc["Barcode"]
                        nest = sc["Position"]
                        s = {
                            "Name": name,
                            "Stack": col,
                            "StackName": stack_name,
                            "Nest": nest,
                            "Barcode": barcode,
                            "Template": template,
                            "IsStack": n["IsStack"],
                        }
                        slots.append(s)
            else:
                s = {
                    "Name": name,
                    "Stack": col,
                    "StackName": stack_name,
                    "Nest": nest,
                    "Barcode": barcode,
                    "Template": template,
                    "IsStack": n["IsStack"],
                }
                slots.append(s)
        return slots


# make some code to test if this is run as main
#
## example of a worklist dictionary
# worklist = {
#     "Name": "Work Unit 1",
#     "Batches": [
#         {
#             "Process": "Process 1",
#             "Name": "Batch 1",
#             "Iterations": 1,
#             "MinimumDelay": 0,
#             "Variables": [
#                 {"Name": "Variable 1", "Value": 1},
#                 {"Name": "Variable 2", "Value": 2},
#             ],
#         },
#         {
#             "Process": "Process 2",
#             "Name": "Batch 2",

#             "Iterations": 1,
#             "MinimumDelay": 0,
#             "Variables": [
#                 {"Name": "Variable 1", "Value": 1},
#                 {"Name": "Variable 2", "Value": 2},
#             ],
#         },
#     ],
# }

if __name__ == "__main__":
    print("Running as main")
    m = Momentum()
    print(m.get_status())
    worklist = {
        "Name": "Work Unit 1",
        "auto_load": True,
        "auto_verify": True,
        "auto_verify_load": True,
        "auto_unload": True,
        "append": False,
        "Batches": [
            {
                "Process": "Process8",
                "Name": "Batch 1",
                "Iterations": 3,
                "MinimumDelay": 10,
                "Priority": 1,
                "Variables": [
                    {"Name": "integer1", "Value": 10},
                    {
                        "Name": "integer1",
                        "Values": [
                            {"Iteration": 2, "Value": 5},
                            {"Iteration": 3, "Value": 6},
                        ],
                    },
                    {"Name": "string1", "Values": ["a1", "a2", "a3"]},
                    {
                        "Name": "duration1",
                        "Values": ["00:10:00", "00:20:00", "00:30:00"],
                    },
                    {
                        "Name": "time1",
                        "Values": ["12/8/2024 10:00:00", "11:00:00", "12:00:00"],
                    },
                    {
                        "Name": "double1",
                        "Values": [1.1, 2.2, 3.3],
                    },
                    {
                        "Name": "boolean1",
                        "Values": [True, False, True],
                    },
                ],
            },
            {
                "Process": "Process1",
                "Name": "Batch 2",
                "Iterations": 3,
                "MinimumDelay": 30,
                "Variables": [
                    {"Name": "integer1", "Value": 10},
                    {
                        "Name": "integer1",
                        "Values": [
                            {"Iteration": 2, "Value": 5},
                            {"Iteration": 3, "Value": 6},
                        ],
                    },
                    {"Name": "string1", "Values": ["a1", "a2", "a3"]},
                    {
                        "Name": "duration1",
                        "Values": ["00:10:00", "00:20:00", "00:30:00"],
                    },
                    {
                        "Name": "time1",
                        "Values": ["12/8/2024 10:00:00", "11:00:00", "12:00:00"],
                    },
                    {
                        "Name": "double1",
                        "Values": [1.1, 2.2, 3.3],
                    },
                    {
                        "Name": "boolean1",
                        "Values": [True, False, True],
                    },
                ],
            },
        ],
    }
    print(worklist)
    print(m.create_worklist_xml(worklist))
    m.run_worklist(worklist, True)
#    worklist["append"] = True
#   m.run_worklist(worklist, True)
