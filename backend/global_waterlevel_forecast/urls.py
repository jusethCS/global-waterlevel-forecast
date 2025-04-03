from django.urls import path
from .controllers import *

urlpatterns = [
    path('water-level-alerts', get_water_level_alerts,  name="water-level-alerts"),
    path('plot-data', get_plot_data,  name="plot-data"),
    path('forecast-table', get_forecast_table,  name="forecast-table"),
    path('historical-simulation-csv', get_historical_simulation_csv,  name="historical-simulation-csv"),
    path('corrected-simulation-csv', get_corrected_simulation_csv,  name="corrected-simulation-csv"),
    path('forecast-csv', get_forecast_csv,  name="forecast-csv"),
    path('observed-data-csv', get_observed_data_csv,  name="observed-data-csv"),
]


# http://35.171.239.25/api/geoglows/water-level-alerts?date=2025-03-31

# http://35.171.239.25/api/geoglows/plot-data?reachid=470527869&hydroweb=416-0001-001-001&name=Operational_Aakol_emel_km0063&date=2025-03-31&width=1000

# http://35.171.239.25/api/geoglows/forecast-table?reachid=470527869&hydroweb=416-0001-001-001&date=2025-03-31
