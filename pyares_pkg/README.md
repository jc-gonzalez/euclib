# PyAres 1.0.0 #
## Requirements ##
- Python 3.4
- Numpy == 1.14.5
- Happybase == 1.1.0
- Pandas == 0.20.3
- PyMySQL == 0.8.0
- Protobuf == 3.0.0
- Pyarrow == 0.9.0

## Best practice ##
- Create a clean Python 3.4.1 virtual environment with pip, wheel and setuptools included
- Activate the virtual environment
- Install the pyares source distribution in the root folder of this repository using pip (`pip install pyares-*.tar.gz`)

## Core Functionality ##
The PyAres library consists of the following three components:
- Data Retrieval
    - Functionality for data retrieval from ARES databases to the client.
- Ares Job submission
    - Functionality for submission of jobs to the ARES cluster.
- Result Retrieval
    - The results from the Ares job can be retrieved back to the client with the result retriever.

For more information about the usage of the different components we refer to the API in the **[Wiki](https://gitlab.esa.int/esoc-infrastructure/pyares/wikis/api).**

