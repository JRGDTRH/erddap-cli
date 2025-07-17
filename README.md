**ERDDAP-CLI: A Command-Line Interface for ERDDAP Servers**

**Introduction**

ERDDAP-CLI is a command-line interface tool designed to empower users to effortlessly query and download datasets directly from ERDDAP (Environmental Research Division's Data Access Program) servers. This tool simplifies the process of accessing environmental data, providing a convenient way to interact with ERDDAP's extensive data catalog using familiar command-line commands.

**Installation**

To install the `erddap-cli` tool, you can use `pip`. The dependencies are listed in the `requirements.txt` file.

First, navigate to the `erddap-cli` folder in your terminal. Then, run the following commands:

```
pip install -r requirements.txt
pip install -e .

```

This will install the required libraries (`erddapy`, `pandas`, `requests`) and install `erddap-cli` as an editable package, allowing you to run it directly from the command line using the `erddap-cli` command.

**ERDDAP-CLI Help**
   *Example command - "erddap-cli -h/--help", "erddap-cli fetch -h/--help"

**Managing ERDDAP Servers**

The `erddap-cli` provides commands for managing ERDDAP servers you want to interact with. These commands are located in the `erddap_cli/commands/servers.py` file.

  * **Listing Servers:** You can list the known ERDDAP servers, including both default servers and any custom servers you have added.
       *Custom server json "~/.erddap_cli_servers.json"
	   *Default servers:
	       *NOAA CoastWatch: "https://coastwatch.pfeg.noaa.gov/erddap"
           *IOOS Glider DAC: "https://data.ioos.us/gliders/erddap"
           *NOAA NCEI:       "https://www.ncei.noaa.gov/erddap"
           *NOAA PMEL:       "https://ferret.pmel.noaa.gov/pmel/erddap"
           *NOAA SWFSC:      "https://oceanview.pfeg.noaa.gov/erddap"
           *NOAA GOES:       "https://coastwatch.noaa.gov/erddap"
           *PacIOOS:         "https://oos.soest.hawaii.edu/erddap"
           *CeNCOOS:         "https://erddap.cencoos.org/erddap"
           *SECOORA:         "https://erddap.secoora.org/erddap"
           *NERACOOS:        "https://www.neracoos.org/erddap"
  * **Adding Custom Servers:** Add new custom ERDDAP servers to your configuration.
  * **Removing Custom Servers:** Remove existing custom ERDDAP servers from your configuration.
  * **Checking Server Status and Capabilities:** Check the status and capabilities of all configured ERDDAP servers to ensure they are accessible and understand their available data.
  
  * **Example Command - "erddap-cli servers status"

**Searching and Describing ERDDAP Datasets**

The tool includes functionalities for finding and understanding datasets on ERDDAP servers. These commands are found in `erddap_cli/commands/search.py` and `erddap_cli/commands/describe.py`.

  * **Searching Datasets:** Search for datasets on a specified ERDDAP server. You can use various filters, such as spatial and temporal bounds, to narrow down your search results. Limits return window, but provides pagination options.
       *Combine any keywords with a "+", e.g. text1+text2
  * **Example Command - "erddap-cli search --server https://www.neracoos.org/erddap --query temperature+salinity+grid"
  
  * **Describing Datasets:** Retrieve and display detailed metadata for a specific dataset. This includes information about its dimensions, variables, and other relevant attributes. You can choose from different output formats (text, JSON, YAML) and sections (all metadata, variables only, or dimensions only).
  * **Example Command - "erddap-cli describe --server https://www.neracoos.org/erddap" --dataset-id WW3_EastCoast_latest --section all"

**Fetching Data from ERDDAP Datasets**

`erddap-cli` offers an interactive workflow for downloading csv data from ERDDAP datasets, implemented in `erddap_cli/commands/fetch.py`.

The fetch command guides you through the following steps:

1.  **Select Server:** Choose the ERDDAP server you want to fetch data from.
2.  **Select Dataset:** Select the specific dataset on the chosen server.
3.  **Select Protocol:** Choose the data access protocol (TableDAP or GridDAP) supported by the dataset.
4.  **Select Variables:** Choose the variables you want to download.
5.  **Specify Constraints or Slices:** For TableDAP, specify constraints to filter the data. For GridDAP, define slices to select specific ranges of dimensions.
6.  **Generate Download URL:** The tool generates the appropriate download URL based on your selections.
7.  **Fetch and Preview Data (Optional):** The tool fetches the data and provides a preview.
8.  **Save Data (Optional):** You have the option to save the fetched data to a CSV file.

**Usage Examples**
