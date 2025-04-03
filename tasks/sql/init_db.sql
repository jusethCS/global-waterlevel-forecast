\set ON_ERROR_STOP on

-- Conectar a la base de datos postgres
\c postgres

-- Eliminar y crear la base de datos geoglows
DROP DATABASE IF EXISTS geoglows;
CREATE DATABASE geoglows;

-- Conectar a la base de datos geoglows
\c geoglows


---------------------------------------------------------------------
--                         station table                           --
---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS station (
    hydroweb TEXT NOT NULL PRIMARY KEY,
    reachid INT NOT NULL,
    basin TEXT,
    river TEXT,
    name TEXT,
    latitude NUMERIC,
    longitude NUMERIC,
    elevation NUMERIC,
    state TEXT,
    country TEXT,
    type TEXT
);



---------------------------------------------------------------------
--                      waterlevel data table                      --
---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS waterlevel_data (
    datetime TIMESTAMP NOT NULL,
    hydroweb TEXT NOT NULL,
    waterlevel NUMERIC
) PARTITION BY RANGE (datetime);

CREATE TABLE IF NOT EXISTS waterlevel_data_2000_2010 
    PARTITION OF waterlevel_data
    FOR VALUES FROM ('2000-01-01') TO ('2010-01-01');

CREATE TABLE IF NOT EXISTS waterlevel_data_2010_2020 
    PARTITION OF waterlevel_data
    FOR VALUES FROM ('2010-01-01') TO ('2020-01-01');

CREATE TABLE IF NOT EXISTS waterlevel_data_2020_2030 
    PARTITION OF waterlevel_data
    FOR VALUES FROM ('2020-01-01') TO ('2030-01-01');

CREATE INDEX idx_waterlevel_data_hydroweb_datetime 
    ON waterlevel_data (hydroweb, datetime);



---------------------------------------------------------------------
--             historical simulation data table                  --
---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS historical_simulation (
    datetime TIMESTAMP NOT NULL,
    reachid INT NOT NULL,
    value NUMERIC(10,3) NOT NULL
) PARTITION BY RANGE (datetime);

CREATE TABLE IF NOT EXISTS historical_simulation_2000_2010 
    PARTITION OF historical_simulation
    FOR VALUES FROM ('2000-01-01') TO ('2010-01-01');

CREATE TABLE IF NOT EXISTS historical_simulation_2010_2020 
    PARTITION OF historical_simulation
    FOR VALUES FROM ('2010-01-01') TO ('2020-01-01');

CREATE TABLE IF NOT EXISTS historical_simulation_2020_2030 
    PARTITION OF historical_simulation
    FOR VALUES FROM ('2020-01-01') TO ('2030-01-01');

CREATE INDEX idx_historical_simulation_reachid_datetime 
    ON historical_simulation (reachid, datetime);


---------------------------------------------------------------------
--                     ensemble forecast data                      --
---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ensemble_forecast (
    datetime TIMESTAMP NOT NULL,
    reachid INT NOT NULL,
    ensemble_01 NUMERIC(10,3),
    ensemble_02 NUMERIC(10,3),
    ensemble_03 NUMERIC(10,3),
    ensemble_04 NUMERIC(10,3),
    ensemble_05 NUMERIC(10,3),
    ensemble_06 NUMERIC(10,3),
    ensemble_07 NUMERIC(10,3),
    ensemble_08 NUMERIC(10,3),
    ensemble_09 NUMERIC(10,3),
    ensemble_10 NUMERIC(10,3),
    ensemble_11 NUMERIC(10,3),
    ensemble_12 NUMERIC(10,3),
    ensemble_13 NUMERIC(10,3),
    ensemble_14 NUMERIC(10,3),
    ensemble_15 NUMERIC(10,3),
    ensemble_16 NUMERIC(10,3),
    ensemble_17 NUMERIC(10,3),
    ensemble_18 NUMERIC(10,3),
    ensemble_19 NUMERIC(10,3),
    ensemble_20 NUMERIC(10,3),
    ensemble_21 NUMERIC(10,3),
    ensemble_22 NUMERIC(10,3),
    ensemble_23 NUMERIC(10,3),
    ensemble_24 NUMERIC(10,3),
    ensemble_25 NUMERIC(10,3),
    ensemble_26 NUMERIC(10,3),
    ensemble_27 NUMERIC(10,3),
    ensemble_28 NUMERIC(10,3),
    ensemble_29 NUMERIC(10,3),
    ensemble_30 NUMERIC(10,3),
    ensemble_31 NUMERIC(10,3),
    ensemble_32 NUMERIC(10,3),
    ensemble_33 NUMERIC(10,3),
    ensemble_34 NUMERIC(10,3),
    ensemble_35 NUMERIC(10,3),
    ensemble_36 NUMERIC(10,3),
    ensemble_37 NUMERIC(10,3),
    ensemble_38 NUMERIC(10,3),
    ensemble_39 NUMERIC(10,3),
    ensemble_40 NUMERIC(10,3),
    ensemble_41 NUMERIC(10,3),
    ensemble_42 NUMERIC(10,3),
    ensemble_43 NUMERIC(10,3),
    ensemble_44 NUMERIC(10,3),
    ensemble_45 NUMERIC(10,3),
    ensemble_46 NUMERIC(10,3),
    ensemble_47 NUMERIC(10,3),
    ensemble_48 NUMERIC(10,3),
    ensemble_49 NUMERIC(10,3),
    ensemble_50 NUMERIC(10,3),
    ensemble_51 NUMERIC(10,3),
    ensemble_52 NUMERIC(10,3),
    initialized TIMESTAMP NOT NULL
) PARTITION BY RANGE (initialized);

CREATE TABLE IF NOT EXISTS ensemble_forecast_2025_01
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2025_02
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2025_03
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2025_04
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2025-04-01') TO ('2025-05-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2025_05
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2025-05-01') TO ('2025-06-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2025_06
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2025_07
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2025-07-01') TO ('2025-08-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2025_08
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2025_09
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2025_10
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2025_11
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2025_12
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2026_01
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2026_02
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2026_03
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2026_04
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2026_05
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2026_06
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2026_07
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2026_08
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2026_09
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2026_10
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2026_11
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');

CREATE TABLE IF NOT EXISTS ensemble_forecast_2026_12
    PARTITION OF ensemble_forecast
    FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');

-- add more tables if necessary

CREATE INDEX idx_ensemble_forecast_reachid_initialized
    ON ensemble_forecast (reachid, initialized);



---------------------------------------------------------------------
--                      forecast records data                      --
---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS forecast_records (
    datetime TIMESTAMP NOT NULL,
    reachid INT NOT NULL,
    value NUMERIC(10,3) NOT NULL
) PARTITION BY RANGE (datetime);

CREATE TABLE IF NOT EXISTS forecast_records_2025_2026
    PARTITION OF forecast_records
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

CREATE TABLE IF NOT EXISTS forecast_records_2026_2027
    PARTITION OF forecast_records
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

CREATE INDEX idx_forecast_records_reachid_datetime 
    ON forecast_records (reachid, datetime);



---------------------------------------------------------------------
--                         warning table                           --
---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS warning (
    hydroweb TEXT NOT NULL,
    datetime TIMESTAMP NOT NULL,
    wd01 TEXT, 
    wd02 TEXT, 
    wd03 TEXT, 
    wd04 TEXT,
    wd05 TEXT, 
    wd06 TEXT, 
    wd07 TEXT, 
    wd08 TEXT,
    wd09 TEXT, 
    wd10 TEXT, 
    wd11 TEXT, 
    wd12 TEXT,
    wd13 TEXT, 
    wd14 TEXT, 
    wd15 TEXT
);

CREATE INDEX idx_warning_datetime
    ON warning (datetime);





