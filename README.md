# Color Categorizer Plugin

**Version**: 1.28\
**Author**: Philippine Statistics Authority\
**License**: MIT

## Overview

The **Color Categorizer** plugin for QGIS allows users to apply categorized colors to layers based on attributes using color data from a JSON file. This tool helps automate the process of applying consistent styling to map layers, particularly useful for thematic mapping.

## Features

* Select a layer and attribute field to categorize.
* Load color data from a JSON file and display it in an editable table.
* Customize colors using a built-in color picker.
* Apply categorized color symbology to the selected layer.
* Save and load settings, including previously selected JSON paths, layers, and attributes.

## Usage

1. Open the plugin from `Plugins > Color Categorizer`.
2.  Use the **Browse** button to select a JSON file containing color data in the following format:

    ```json
    {
        "Health Center": "#ff0000",
        "Daycare Center": "#00ff00",
        "subtype": "#0000ff"
    }
    ```

## Installation

1. Open QGIS.
2. Go to **Plugins > Manage and Install Plugins**.
3. Select **Install from ZIP** and browse to the plugin's ZIP file.
4. Click **Install Plugin**.




