import os
import s3fs
import time
import math
import datetime
import geoglows
import numpy as np
import xarray as xr
import pandas as pd
import pandas as pd
import sqlalchemy as sql
from dotenv import load_dotenv
from sqlalchemy import create_engine


def update_forecast(date: datetime.datetime, 
                    con: sql.engine.base.Connection) -> None: # type: ignore
    """
    Update forecast data from an S3 Zarr store into partitioned tables. The 
    data is split into ensemble forecasts and forecast records, then inserted 
    into separate tables based on date partitions.

    Parameters
    ----------
     - date (datetime.datetime): Initialization date for the forecast.
     - con (sql.engine.base.Connection): Database connection object pointing 
            to PostgreSQL.
    """

    # Build the S3 Zarr URL from the given date
    params = {"region_name": "us-west-2"}
    datestr = date.strftime("%Y%m%d00")
    url = f"s3://geoglows-v2-forecasts/{datestr}.zarr"
    t0 = time.time()

    # Create an anonymous S3 filesystem interface
    s3 = s3fs.S3FileSystem(anon=True, client_kwargs=params)

    # Map the S3 bucket for Zarr reading
    s3store = s3fs.S3Map(root=url, s3=s3, check=False)

    # Open the dataset using xarray
    ds = xr.open_zarr(s3store)

    # Identify valid REACHIDs
    ds_reachids = set(ds.rivid.values)
    sql = "select distinct reachid from station"
    ec_reachids = set(pd.read_sql(sql, con).reachid)
    reachids = list(ds_reachids.intersection(ec_reachids))

    # Table and partition settings
    table = "ensemble_forecast"
    partitions = {
        "2025-01-01": "2025-02-01",
        "2025-02-01": "2025-03-01",
        "2025-03-01": "2025-04-01",
        "2025-04-01": "2025-05-01",
        "2025-05-01": "2025-06-01",
        "2025-06-01": "2025-07-01",
        "2025-07-01": "2025-08-01",
        "2025-08-01": "2025-09-01",
        "2025-09-01": "2025-10-01",
        "2025-10-01": "2025-11-01",
        "2025-11-01": "2025-12-01",
        "2025-12-01": "2026-01-01",
        "2026-01-01": "2026-02-01",
        "2026-02-01": "2026-03-01",
        "2026-03-01": "2026-04-01",
        "2026-04-01": "2026-05-01",
        "2026-05-01": "2026-06-01",
        "2026-06-01": "2026-07-01",
        "2026-07-01": "2026-08-01",
        "2026-08-01": "2026-09-01",
        "2026-09-01": "2026-10-01",
        "2026-10-01": "2026-11-01",
        "2026-11-01": "2026-12-01",
        "2026-12-01": "2027-01-01"
    }

    # Forecast records table and partitions
    table_fr = "forecast_records"
    partitions_fr = {
        "2025-01-01": "2026-01-01",
        "2026-01-01": "2027-01-01"
    }

    # Process REACHIDs in smaller chunks
    chunk_size = 100
    for start_idx in range(0, len(reachids), chunk_size):
        end_idx = start_idx + chunk_size
        reachids_slice = reachids[start_idx:end_idx]

        # Prepare DataFrame for ensemble forecast
        df = ds["Qout"].sel(rivid=reachids_slice).to_dataframe().reset_index()
        df = df.pivot(
            index=["time", "rivid"],
            columns="ensemble",
            values="Qout"
        ).reset_index()
        df = df.rename(
            columns={
                "time": "datetime",
                "rivid": "reachid",
                **{i: f"ensemble_{i:02d}" for i in range(1, 53)}
            }
        )
        df["initialized"] = date

        # Insert into ensemble forecast partitions
        partition_table = f"{table}_{date.strftime('%Y_%m')}"
        for start_date, end_date in partitions.items():
            mask = ((df["datetime"] >= start_date)
                    & (df["datetime"] < end_date))
            df_partition = df.loc[mask]
            sub_chunk_size = 1000
            for i in range(0, len(df_partition), sub_chunk_size):
                chunk = df_partition.iloc[i:i + sub_chunk_size]
                chunk.to_sql(partition_table,
                             con=con,
                             if_exists="append",
                             index=False)
            con.commit()

        # Prepare DataFrame for forecast records
        fr = df[["datetime", "reachid", "ensemble_01"]].copy()
        fr = fr.loc[fr["datetime"] == date]
        fr = fr.rename(columns={"ensemble_01": "value"})

        # Insert into forecast_records partitions
        for start_date, end_date in partitions_fr.items():
            mask = ((fr["datetime"] >= start_date)
                    & (fr["datetime"] < end_date))
            fr_partition = fr.loc[mask]
            fr_table = f"{table_fr}_{start_date[:4]}_{end_date[:4]}"
            fr_partition.to_sql(fr_table,
                                con=con,
                                if_exists="append",
                                index=False)
            con.commit()

        # Log progress
        progress = round(start_idx / len(reachids) * 100, 3)
        elapsed = time.time() - t0
        print(f"Progress: {progress}% in {elapsed:.2f} s")



def get_format_data(sql_statement, conn):
    """
    Retrieve and format data from a database.

    This function executes an SQL query to retrieve data from a database,
    sets the 'datetime' column as the index of the DataFrame, formats the index
    to a specified datetime string format, and returns the formatted DataFrame.

    Parameters:
    -----------
     - sql_statement (str): SQL query to execute.
     - conn (sqlalchemy.engine.base.Connection): Database connection object.

    Returns:
    --------
     - pd.DataFrame: Formatted DataFrame with 'datetime' as the index.
    """
    # Retrieve data from the database using the SQL query
    data = pd.read_sql(sql_statement, conn)
    
    # Set the 'datetime' column as the DataFrame index
    data.index = pd.to_datetime(data['datetime'])
    
    # Drop the 'datetime' column as it is now the index
    data = data.drop(columns=['datetime'])
    
    # Format the index values to the desired datetime string format
    data.index = pd.to_datetime(data.index)
    data.index = data.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
    data.index = pd.to_datetime(data.index)
    return(data)



def gumbel_1(sd: float, mean: float, rp: float) -> float:
    """
    Calculate the Gumbel Type I distribution value for a given return period.

    This function calculates the Gumbel Type I distribution value based on the
    provided standard deviation, mean, and return period.

    Parameters:
    -----------
     - sd (float): The standard deviation of the dataset.
     - mean (float): The mean of the dataset.
     - return_period (float): The return period for which the value is calculated.

    Returns:
    --------
     - float: The calculated Gumbel Type I distribution value.
    """
    try:
        # Validate input parameters
        if sd <= 0:
            raise ValueError("Standard deviation must be positive.")
        if rp <= 1:
            raise ValueError("Return period must be greater than 1.")
        
        # Calculate the Gumbel reduced variate
        y = -math.log(-math.log(1 - (1 / rp)))
        
        # Calculate the Gumbel Type I distribution value
        gumbel_value = y * sd * 0.7797 + mean - (0.45 * sd)
        return gumbel_value
    
    except Exception as e:
        print(e)
        return 0



def get_return_periods(reachid: int, data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate return period values for a given REACHID based on annual maximum 
    flow data.

    This function calculates the annual maximum flow statistics (mean and 
    standard deviation), computes the corrected return period values using the 
    Gumbel Type I distribution, and returns these values in a DataFrame.

    Parameters:
    -----------
     - reachid (int): The REACHID (unique identifier for a river segment).
     - data (pd.DataFrame): DataFrame containing flow data with a datetime index.

    Returns:
    --------
     - pd.DataFrame: DataFrame containing the corrected return period values for 
        the specified REACHID.
    """
    if data.empty:
        raise ValueError("The input data is empty.")
    
    # Calculate the maximum annual flow
    max_annual_flow = data.groupby(data.index.strftime("%Y")).max()
    
    if max_annual_flow.empty:
        raise ValueError("No annual maximum flow data available.")
    
    # Calculate the mean and standard deviation of the maximum annual flow
    mean_value = np.mean(max_annual_flow.iloc[:, 0].values)
    std_value = np.std(max_annual_flow.iloc[:, 0].values)
    
    # Define the return periods to calculate
    return_periods = [100, 50, 25, 10, 5, 2]
    return_periods_values = []
    
    # Compute the corrected return period values using the Gumbel Type I distribution
    for rp in return_periods:
        return_periods_values.append(gumbel_1(std_value, mean_value, rp))
    
    # Create a dictionary to store the return period values
    data_dict = {
        'rivid': [reachid],
        'return_period_100': [return_periods_values[0]],
        'return_period_50': [return_periods_values[1]],
        'return_period_25': [return_periods_values[2]],
        'return_period_10': [return_periods_values[3]],
        'return_period_5': [return_periods_values[4]],
        'return_period_2': [return_periods_values[5]]
    }
    
    # Convert the dictionary to a DataFrame and set 'rivid' as the index
    rperiods_df = pd.DataFrame(data=data_dict)
    rperiods_df.set_index('rivid', inplace=True)
    return rperiods_df



def ensemble_quantile(ensemble: pd.DataFrame, quantile: float, 
                      label: str) -> pd.DataFrame:
    """
    Calculate the specified quantile for an ensemble and return it as a 
    DataFrame.

    This function computes the specified quantile for each row in the ensemble
    DataFrame and returns the results in a new DataFrame with the specified 
    label as the column name.

    Parameters:
    -----------
     - ensemble (pd.DataFrame): DataFrame containing the ensemble data.
     - quantile (float): The quantile to compute (between 0 and 1).
     - label (str): The label for the resulting quantile column.

    Returns:
    --------
     - pd.DataFrame: DataFrame containing the computed quantile with the 
        specified label.
    """
    # Calculate the quantile along the columns (axis=1) and convert to a DataFrame
    quantile_df = ensemble.quantile(quantile, axis=1).to_frame()
    
    # Rename the column to the specified label
    quantile_df.rename(columns={quantile: label}, inplace=True)
    return quantile_df



def get_ensemble_stats(ensemble: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate various statistical measures for an ensemble and return them in a 
    DataFrame.

    This function calculates the maximum, 75th percentile, median, 25th percentile,
    and minimum flows for the ensemble. It also includes the high-resolution flow 
    data (ensemble_52).

    Parameters:
    -----------
     - ensemble (pd.DataFrame): DataFrame containing the ensemble data.

    Returns:
    --------
     - pd.DataFrame: DataFrame containing the statistical measures and 
        high-resolution flow data.
    """
    # Extract the high-resolution data and remove it from the ensemble
    high_res_df = ensemble['ensemble_52'].to_frame()
    ensemble.drop(columns=['ensemble_52'], inplace=True)
    
    # Remove rows with NaN values in both the ensemble and high-resolution data
    ensemble.dropna(inplace=True)
    high_res_df.dropna(inplace=True)
    
    # Rename the column for high-resolution data
    high_res_df.rename(columns={'ensemble_52': 'high_res'}, inplace=True)
    
    # Calculate various quantiles and concatenate them into a single DataFrame
    stats_df = pd.concat([
        ensemble_quantile(ensemble, 1.00, 'flow_max'),
        ensemble_quantile(ensemble, 0.75, 'flow_75%'),
        ensemble_quantile(ensemble, 0.50, 'flow_avg'),
        ensemble_quantile(ensemble, 0.25, 'flow_25%'),
        ensemble_quantile(ensemble, 0.00, 'flow_min'),
        high_res_df
    ], axis=1)
    return stats_df


def get_bias_corrected_data(sim, obs):
    outdf = geoglows.bias.correct_historical(sim.dropna(), obs.dropna())
    outdf.index = pd.to_datetime(outdf.index)
    outdf.index = outdf.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
    outdf.index = pd.to_datetime(outdf.index)
    return(outdf)

def get_corrected_forecast(simulated_df, ensemble_df, observed_df):
    # Determina el mes objetivo basado en el primer registro del ensemble
    target_month = ensemble_df.index[0].month

    # Filtra los DataFrames simulados y observados para el mes objetivo
    monthly_simulated = simulated_df[simulated_df.index.month == target_month].dropna()
    monthly_observed = observed_df[observed_df.index.month == target_month].dropna()

    # Obtén los valores mínimo y máximo simulados (se asume que se usa la primera columna)
    min_simulated = monthly_simulated.iloc[:, 0].min()
    max_simulated = monthly_simulated.iloc[:, 0].max()

    # Crea el DataFrame de forecast limitado entre [min_simulated, max_simulated]
    forecast_ens_df = ensemble_df.clip(lower=min_simulated, upper=max_simulated)

    # Calcula el factor mínimo:
    # Para cada valor, si es menor que min_simulated, el factor es (valor / min_simulated), de lo contrario es 1.
    min_factor_df = pd.DataFrame(
        np.where(ensemble_df < min_simulated, ensemble_df / min_simulated, 1),
        index=ensemble_df.index,
        columns=ensemble_df.columns
    )
    # Se preservan los NaN
    min_factor_df[ensemble_df.isna()] = np.nan

    # Calcula el factor máximo:
    # Para cada valor, si es mayor que max_simulated, el factor es (valor / max_simulated), de lo contrario es 1.
    max_factor_df = pd.DataFrame(
        np.where(ensemble_df > max_simulated, ensemble_df / max_simulated, 1),
        index=ensemble_df.index,
        columns=ensemble_df.columns
    )
    max_factor_df[ensemble_df.isna()] = np.nan
    corrected_ensembles = geoglows.bias.correct_forecast(forecast_ens_df, simulated_df, observed_df)
    corrected_ensembles = corrected_ensembles.multiply(min_factor_df).multiply(max_factor_df)
    return corrected_ensembles


def get_warnings(reachid, hydroweb, date, con):
    """
    Retrieve and process hydrological data to generate warnings based on
    ensemble forecast exceedances of return period thresholds.

    Parameters:
    - reachid (int): Identifier for the river reach.
    - date (str): Initialization date of the ensemble forecast.
    - con (sqlalchemy.engine.Connection): Database connection.

    Returns:
    - pd.DataFrame: A single-row DataFrame with columns alert_day01..alert_day14,
      plus 'datetime' and 'reachid'.
    """
    # Retrieve data
    sql = f"SELECT datetime, value FROM historical_simulation WHERE reachid={reachid}"
    sim = get_format_data(sql, con)
    sim[sim < 0.1] = 0.1

    sql = f"SELECT datetime, waterlevel FROM waterlevel_data WHERE hydroweb='{hydroweb}'"
    obs = get_format_data(sql, con)
    obs = obs - obs.min()
    obs[obs < 0.1] = 0.1

    cor = get_bias_corrected_data(sim, obs)
    return_periods = get_return_periods(reachid, cor)
    
    # Retrieve ensemble forecast data and drop unused columns
    sql = f"SELECT * FROM ensemble_forecast WHERE initialized='{date}' AND reachid={reachid}"
    ensemble = get_format_data(sql, con).drop(columns=['reachid', "initialized"])

    # Corrected forecast
    corrected_ensemble = get_corrected_forecast(sim, ensemble, obs)
    max_ensemble_forecast = corrected_ensemble.resample('D').max()
    
    # Compute percentage of ensemble members exceeding each threshold
    n_members = 52  # Number of ensemble members per day
    threshold_cols = [
        "return_period_2", 
        "return_period_5", 
        "return_period_10",
        "return_period_25", 
        "return_period_50", 
        "return_period_100"
    ]
    exceedance_df = pd.DataFrame(index=max_ensemble_forecast.index)
    for col in threshold_cols:
        thr_val = return_periods[col].values[0]
        exceedance_df[col] = (
            (max_ensemble_forecast > thr_val).sum(axis=1) * 100 / n_members
        )
    
    # Define the alert threshold percentage
    cond = 40

    # Conditions from highest to lowest threshold so higher alerts override
    conditions = [
        exceedance_df["return_period_100"] >= cond,
        exceedance_df["return_period_50"]  >= cond,
        exceedance_df["return_period_25"]  >= cond,
        exceedance_df["return_period_10"]  >= cond,
        exceedance_df["return_period_5"]   >= cond,
        exceedance_df["return_period_2"]   >= cond
    ]
    choices = ["R100", "R50", "R25", "R10", "R5", "R2"]
    exceedance_df["alert"] = np.select(conditions, choices, default="R0")

    # Build the final DataFrame for 14 days of alerts
    # If you have fewer or more days, adjust the slice accordingly
    results = exceedance_df["alert"].iloc[:14]

    # Transpose so each day becomes a column
    out = pd.DataFrame(results).T

    # Rename columns to alert_day01, alert_day02, ..., alert_day14
    out.columns = [f"wd{i+1:02d}" for i in range(len(out.columns))]

    # Add date and reachid columns
    out["datetime"] = date
    out["hydroweb"] = hydroweb

    # Reset index for a clean DataFrame
    out.reset_index(drop=True, inplace=True)
    return(out)





###############################################################################
#                                MAIN ROUTINE                                 #
###############################################################################

# Change the work directory
user = os.getlogin()
workdir = os.path.expanduser('~{}'.format(user))
workdir = os.path.join(workdir, 'global-waterlevel-forecast') 
os.chdir(workdir)

# Import enviromental variables
load_dotenv()
DB_USER = os.getenv('POSTGRES_USER')
DB_PASS = os.getenv('POSTGRES_PASSWORD')
DB_NAME = os.getenv('POSTGRES_DB')
DB_PORT = os.getenv('POSTGRES_PORT')

# Generate the conection token
token = "postgresql+psycopg2://{0}:{1}@localhost:{2}/{3}"
token = token.format(DB_USER, DB_PASS, DB_PORT, DB_NAME)

# Establish connection
db = create_engine(token)
con = db.connect()

# Update ensemble forecast and forecast records
sql = "select * from station"
stations = pd.read_sql(sql, con)
datetarget = datetime.datetime(2025, 4, 3)
update_forecast(datetarget, con)

# Compute warnings
for i in range(len(stations.hydroweb)):
    try:
        warnings = get_warnings(
            stations.reachid[i],
            stations.hydroweb[i],
            datetarget,
            con)
    except:
        print(f"Error en: {stations.hydroweb[i]}")
        warnings = pd.DataFrame({
            "hydroweb" : [stations.hydroweb[i]],
            "datetime": [datetarget],
            "wd01": ["R0"], "wd02": ["R0"], 
            "wd03": ["R0"], "wd04": ["R0"],
            "wd05": ["R0"], "wd06": ["R0"], 
            "wd07": ["R0"], "wd08": ["R0"],
            "wd09": ["R0"], "wd10": ["R0"], 
            "wd11": ["R0"], "wd12": ["R0"],
            "wd13": ["R0"], "wd14": ["R0"]
        })
    warnings.to_sql('warning', con=con, 
                    if_exists='append', index=False)
    con.commit()


# nohup python update_warning.py > out.txt 2>&1 &