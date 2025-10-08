# MomentumPyClient

This package simplifies the connection to the Web Services of the Momentum Scheduler from Thermo Scientific.

## Description

MomentumPyClient is a Python wrapper for the web services Swagger API interface for Momentum. It includes UI functions to facilitate data visualization and control of Momentum directly from simple Streamlit apps.

## Visuals

![screenshot](https://github.com/novonordisk-research/MomentumPyClient/blob/main/screenshot.png?raw=true)

## Prerequisites

- API credentials for Momentum Web Services

## Installation

```sh
pip install MomentumPyClient[streamlit]
```

## Configuration

You can configure MomentumPyClient in several ways, in order of priority:

### 1. Direct parameters (highest priority)
```python
from MomentumPyClient import Momentum

m = Momentum(
    user_name="your_username",
    password="your_password", 
    url="https://your-server.com/api/",
    verify=False
)
```

### 2. .env file (medium priority)
Create a `.env` file in the root directory:
```env
momentum_user=<username>
momentum_passwd=<password>
momentum_verify=False
momentum_url="https://localhost/api/"
```

### 3. Environment variables (fallback)
Set environment variables in your system or application:

**Windows PowerShell:**
```powershell
$env:momentum_user="your_username"
$env:momentum_passwd="your_password"
$env:momentum_url="https://your-server.com/api/"
$env:momentum_verify="False"
```

**Windows Command Prompt:**
```cmd
set momentum_user=your_username
set momentum_passwd=your_password
set momentum_url=https://your-server.com/api/
set momentum_verify=False
```

**Python:**
```python
import os
os.environ["momentum_user"] = "your_username"
os.environ["momentum_passwd"] = "your_password"
os.environ["momentum_url"] = "https://your-server.com/api/"
os.environ["momentum_verify"] = "False"
```

## Usage

```python
from MomentumPyClient import Momentum

m = Momentum()
m.get_status()
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or support, please contact [jsqp@novonordisk.com](mailto:jsqp@novonordisk.com).

## 

## Streamlit example

Here is a simple example of how to use this package with Streamlit:

```python
import streamlit as st
import MomentumPyClient.ui as stm

st.write(stm.ws.get_status())

stm.show_store("Carousel")
```

## Documentation

For detailed API documentation, please refer to the official [Thermo Fisher Lab automation documentation](https://apps.thermofisher.com/apps/lahr/LA_Online_Help_Resource/en-us/Content/Topics/Software/Web%20Services/(General)/WBSV%20about.htm).

## Support

If you encounter any issues or have questions, feel free to open an issue on GitHub or contact the support team.

## Acknowledgements

Special thanks to Søren Furbo, Erik Trygg and the open-source community for their valuable input and support.
