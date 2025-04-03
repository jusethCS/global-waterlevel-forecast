# GLOBAL WATER LEVEL FORECAST

A web platform providing water level forecasts for over 20,000 stations worldwide, leveraging the GEOGLOWS ECMWF Streamflow Service (GESS) with corrections based on satellite-derived water levels from Hydroweb.

## Structure

The platform is organized into three main components:

- **tasks**  
  Includes scripts for preprocessing and postprocessing GEOGLOWS model data, as well as applying corrections based on water level observations from Hydroweb. Developed in Python, SQL, and Bash.

- **backend**  
  Provides an API for data queries, generation of graphs, and analytical functionalities required by the platform. Developed using Django.

- **frontend**  
  Offers the graphical user interface for interacting with the platform. Developed using Angular.


## Dev Team

Contributors names and contact info:

- Juseth Chancay
  [@jusethCS](https://github.com/jusethCS)

- Jorge Luis Sánchez
  [@jorgessanchez7](https://github.com/jorgessanchez7)

- Darlly Rojas 
  [@DarllyRojas](https://github.com/DarllyRojas)

- Giovanni Romero
  [@romer8](https://github.com/romer8)


## Inspiration

The **Global Water Level Forecast** platform is inspired by the **National Water Level App** developed by Rojas et al. (2025).

> **Darlly Rojas-Lesmes**, Jorge Sanchez-Lozano, E. James Nelson, Juseth E. Chancay, Jhonatan Rodriguez-Chaves, Karina Larco-Erazo, E. Giovanni Romero, Mario Trujillo-Vela, Riley C. Hales, Daniel P. Ames, Angelica L. Gutierrez.(2025)
**National Water Level Forecast (NWLF): An Open-Source Customizable Web Application for the GEOGLOWS ECMWF Global Hydrological Model.** Information Geography [https://doi.org/10.1016/j.infgeo.2025.100008](https://www.sciencedirect.com/science/article/pii/S3050520825000089)
