**Dash Volatility Surface App**

This is a demo of the Dash interactive Python framework developed by [Plotly](https://plot.ly/).

Dash abstracts away all of the technologies and protocols required to build an interactive web-based application and is a simple and effective way to bind a user interface around your Python code.

This demo fetches CBOE options chain data through Pandas Datareader/Yahoo, and calculates the implied volatility of each option using the py_vollib library that implements an extremely fast, 2-pass Black-Scholes-Merton algorithm for finding option IVs initially designed by Peter Jackel. All parameters of the IV calculation are adjustable, from whether or not options decay annually or based on the US trading calendar, to the dividend and risk free rates. The resulting volatility curve is rendered using a Mesh3D object and also plotted from the x-y axis as a heatmap, and the x-z axis as a scatter/box plot.

Note that initially fetching the options data and calculating the IV might take a few seconds due to the sheer number of calculations required to fetch.

To learn more check out our [documentation](https://plot.ly/dash).

The following are screenshots for the app in this repo:

![Alt desc](https://github.com/aspiringfastlaner/SPX-Put-Selling/blob/master/Volatility%20Explorer/screenshots/Screenshot1.png)
