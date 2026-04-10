# Steam Inventory Analyzer

A desktop application built with Python that fetches Steam inventories and provides real-time market data with price history visualization.

## Features
* **Multi-threading:** UI remains responsive during API calls.
* **Price Tracking:** Integrated with SteamAPIs and CSFloat(in progress) for live pricing and float data.
* **Data Visualization:** Interactive charts using Matplotlib.
* **Caching:** Local image caching for improved performance.

## How to run
1. Install dependencies: `pip install -r requirements.txt`
2. Add your API key to a `.env` file.
3. Run `python steamanalize.py`