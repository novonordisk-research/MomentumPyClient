# MomentumPyClient

This package simplifies the connection to the Web Services of the Momentum Scheduler from Thermo Scientific.

## Description

MomentumPyClient is a Python wrapper for the web services Swagger API interface for Momentum. It includes UI functions to facilitate data visualization and control of Momentum directly from simple Streamlit apps.

## Visuals

![screenshot](https://github.com/novonordisk-research/MomentumPyClient/blob/main/screenshot.png)

## Prerequisites

- API credentials for Momentum Web Services

## Installation

    ```sh
    pip install MomentumPyClient[streamlit]
    ```

## Configuration

1. Create a `.env` file in the root directory.
2. Add your API credentials to the `.env` file:
    ```env
    momentum_user=<username>
    momentum_passwd=<password>
    momentum_verify=False
    momentum_url="https://localhost/api/"
    ```

## Usage

    ```sh
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

Special thanks to the contributors and the open-source community for their valuable input and support.
