# MomentumPyClient

This package makes it easy to connect to Web Services of the Momentum Scheduler from Thermo Scientific.

## Description

Python wrapper for the web services swagger api interface for momentum, and  functions to make visualization in streamlit apps.

## Visuals

![screenshot](screenshot.png)

## Prerequisites

- API credentials for Momentum Web Services

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/novonordisk-research/MomentumPyClient.git
    ```
2. Navigate to the project directory:
    ```sh
    cd MomentumPyClient
    ```
3. Install :
    ```sh
    pip install .[streamlit]
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

1. Start the application:
    ```sh 
    cd examples/
    streamlit run testing.py 
    ```
2. The application will connect to the Momentum Scheduler API and perform the necessary operations.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or support, please contact [jsqp@novonordisk.com](mailto:jsqp@novonordisk.com).

## 

## Example

Here is a simple example of how to use this package:

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


































