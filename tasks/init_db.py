import os
import s3fs
import time
import datetime
import xarray as xr
import pandas as pd
import pandas as pd
import sqlalchemy as sql
from dotenv import load_dotenv
from sqlalchemy import create_engine



###############################################################################
#                        MODULES AND CUSTOM FUNCTIONS                         #
###############################################################################
def init_db(pg_user:str, pg_pass:str, pg_file:str) -> None:
    """
    Initializes the PostgreSQL database by executing the SQL commands 
    from the provided SQL file.
    
    Parameters:
    -----------
     - pg_user (str): PostgreSQL username
     - pg_pass (str): PostgreSQL password
     - pg_file (str): Path to the SQL file containing the db initialization

    """
    command = f"PGPASSWORD={pg_pass} psql -U {pg_user} -h localhost -f {pg_file}"
    os.system(command)



def insert_stations(con:sql.engine.base.Connection) -> None:
    """
    Inserts station data from a CSV file into a PostgreSQL database.
    
    Parameters:
    -----------
     - con (Connection): SQLAlchemy Connection object
    
    """
    data = pd.read_csv("data_station.csv", sep="\t")
    data.to_sql("station", con=con, if_exists='append', index=False)
    con.commit()



def insert_waterlevel_data(df:pd.DataFrame, con:sql.engine.base.Connection) -> None:
    """
    Inserts water level time series data into partitioned PostgreSQL tables 
    based on date ranges.

    The function splits the input DataFrame into separate date-based 
    partitions, and inserts the data in manageable sub-chunks to avoid 
    memory overload. Each partition corresponds to a specific time range 
    and is stored in a separate table with a name reflecting the range 
    (e.g., 'waterlevel_data_2000_2010').

    Parameters:
    -----------
    - df (pd.DataFrame): Pandas DataFrame containing water level data. 
                      Must include a 'datetime' column.
    - con (sqlalchemy.engine.Connection): SQLAlchemy connection object 
                                          to the PostgreSQL database.
    """
    # Base table name (used to construct partitioned table names)
    table = "waterlevel_data"

    # Dictionary of date ranges for partitioning
    partitions = {
        '2000-01-01': '2010-01-01',
        '2010-01-01': '2020-01-01',
        '2020-01-01': '2030-01-01'
    }

    # Loop through each partition range
    for start_date, end_date in partitions.items():
        # Filter the data for the current date range
        mask = (df['datetime'] >= start_date) & (df['datetime'] < end_date)
        df_partition = df.loc[mask]

        # Construct the name of the partitioned table
        partition_table_name = f"{table}_{start_date[:4]}_{end_date[:4]}"

        # Insert data in small chunks to avoid memory issues
        sub_chunk_size = 1000
        for i in range(0, len(df_partition), sub_chunk_size):
            chunk = df_partition.iloc[i:i + sub_chunk_size]

            # Insert chunk into the partitioned table
            chunk.to_sql(
                partition_table_name,
                con=con,
                if_exists='append',
                index=False
            )

            # Commit the current insert operation
            con.commit()


def insert_historical_simulation(con: sql.engine.base.Connection) -> None:
    """
    Inserts historical simulation data into partitioned tables in a PostgreSQL
    database. The function reads a Zarr dataset stored in an S3 bucket and uses
    a local CSV file to identify specific COMIDs (reach IDs). Data is split by
    COMID in chunks, partitioned by date ranges, and inserted into the related
    partition tables.

    Parameters
    ----------
     - con (sql.engine.base.Connection) Connection object pointing to the 
            target PostgreSQL database.
    """
    # Define parameters for anonymous S3 connection and Zarr store location
    params = {'region_name': 'us-west-2'}
    url = 's3://geoglows-v2-retrospective/retrospective.zarr'
    to = time.time()

    # Create the S3 filesystem interface (anonymous access)
    s3 = s3fs.S3FileSystem(anon=True, client_kwargs=params)

    # Create an S3Map to read Zarr data from the specified S3 bucket
    s3store = s3fs.S3Map(root=url, s3=s3, check=False)

    # Open the dataset from the Zarr store using xarray
    ds = xr.open_zarr(s3store)

    # Retrieve COMIDs from the xarray dataset
    ds_comids = set(ds.rivid.values)

    # Read COMIDs from a local CSV, then find the intersection
    sql = "select distinct reachid from station"
    ec_comids = set(pd.read_sql(sql, con).reachid)
    comids = list(ds_comids.intersection(ec_comids))

    # Define the size of each COMID batch
    chunk_size = 100

    # Name of the base table
    table = "historical_simulation"

    # Dictionary of date ranges for table partitions
    partitions = {
        '2000-01-01': '2010-01-01',
        '2010-01-01': '2020-01-01',
        '2020-01-01': '2030-01-01'
    }

    # Loop over the COMIDs in chunks to avoid excessive memory usage
    for start_idx in range(0, len(comids), chunk_size):
        end_idx = start_idx + chunk_size
        comids_slice = comids[start_idx:end_idx]

        # Access the relevant subset of rows in the dataset
        df = ds['Qout'].sel(rivid=comids_slice).to_dataframe().reset_index()

        # Rename columns for clarity
        df.columns = ["datetime", "reachid", "value"]
        df = df[df["datetime"] >= pd.to_datetime("2000-01-01")]

        # For each time partition, insert matching rows into the partition table
        for start_date, end_date in partitions.items():
            mask = (df['datetime'] >= start_date) & (df['datetime'] < end_date)
            df_partition = df.loc[mask]

            # Build the name of the partitioned table
            partition_table_name = f"{table}_{start_date[:4]}_{end_date[:4]}"

            # Insert data in sub-chunks to limit memory overhead
            sub_chunk_size = 1000
            for i in range(0, len(df_partition), sub_chunk_size):
                chunk = df_partition.iloc[i:i + sub_chunk_size]
                chunk.to_sql(partition_table_name,
                             con=con,
                             if_exists='append',
                             index=False)
                # Commit after inserting into the current partition
                con.commit()

        # Track progress and execution time for the current COMID slice
        progress = round(start_idx / len(comids) * 100, 3)
        print(f"Progress: {progress}% in {(time.time() - to):.2f} s")


def update_forecast(date: datetime.datetime, 
                    con: sql.engine.base.Connection) -> None:
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


# Initialize the database
#sql_file = f"{workdir}/tasks/init_db.sql"
#init_db(DB_USER, DB_PASS, sql_file)

# Generate the conection token
token = "postgresql+psycopg2://{0}:{1}@localhost:{2}/{3}"
token = token.format(DB_USER, DB_PASS, DB_PORT, DB_NAME)

# Establish connection
db = create_engine(token)
con = db.connect()

# Change data directory
#os.chdir("tasks")

# Insert data
#insert_stations(con=con)
#print("Stations inserted on DB")

#df = pd.read_csv("data_hydroweb.csv")
#df = df.drop('reachid', axis=1)
#insert_waterlevel_data(df=df, con=con)
#print("Satellite-based waterlevel data inserted on DB")

#insert_historical_simulation(con=con)
#print("INSERTING FORECAST")
#date = datetime.datetime(2025, 1, 1)
#update_forecast(date, con)
