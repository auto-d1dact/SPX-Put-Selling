# SPX-Put-Selling

### Live Data Pulling

Jupyter notebook files for pulling live data for decision making on SPX put trades. Current files are:
  - pulling_live_data.ipynb with scraping functions:
    - latest_yahoo: used to collect latest (with 15 minute delay) data from Yahoo Finance for VIX, VVIX, SKEW, and SPX
    - yahoo_options: used to pull latest data for the nearest regular expiry SPX index options from Yahoo Finance. This function is to be further tested to run during market hours and save data into Data/Options Data folder every 5 minutes for future testing.
