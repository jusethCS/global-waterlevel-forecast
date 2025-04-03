import os
import shutil
import zipfile
import pandas as pd
import py_hydroweb


def download_hydroweb(api_key:str, basket_name:str, collections:list, 
                      bbox:list, zip_filename:str, extract_folder:str) -> str:
    """
    Create a py_hydroweb client, add collections to the download basket,
    submit the basket, and extract the downloaded zip file.

    Parameters:
    -----------
        - api_key (str): API key for py_hydroweb.
        - basket_name (str): Name of the download basket.
        - collections (list): List of collection names to add.
        - bbox (list): Bounding box coordinates.
        - zip_filename (str): Name of the zip file to download.
        - extract_folder (str): Destination folder for extraction.
    """
    # Create client and download basket
    client = py_hydroweb.Client(api_key=api_key)
    basket = py_hydroweb.DownloadBasket(basket_name)
    for collection in collections:
        basket.add_collection(collection, bbox=bbox)

    # Download the zip file
    client.submit_and_download_zip(basket, zip_filename=zip_filename)

    # Create extraction folder if it does not exist
    os.makedirs(extract_folder, exist_ok=True)

    # Extract the zip file
    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        zip_ref.extractall(extract_folder)

    # Remove the zip file after extraction
    os.unlink(zip_filename)
    return extract_folder



def process_hydroweb_files(base_dir:str, max_skip:int=100) -> None:
    """
    Process all .txt files starting with 'hydroprd' found recursively in
    base_dir. Tries to read the CSV by incrementing the number of skipped
    rows until successful. Converts the datetime index and filters/renames
    columns before saving.

    Parameters:
    -----------
        - base_dir (str): Base directory to search for text files.
        - max_skip (int): Maximum skip attempts to avoid infinite loops.
    """
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.startswith('hydroprd') and file.endswith('.txt'):
                source_path = os.path.join(root, file)
                dest_path = os.path.join(base_dir, file)
                skip = 40  # initial skip count

                while skip < max_skip:
                    try:
                        # Read CSV with current skip value
                        data = pd.read_csv(source_path, skiprows=skip,
                                           sep=' ', header=None,
                                           index_col=0)

                        # Convert index to datetime and format as date only
                        data.index = pd.to_datetime(data.index).strftime(
                            "%Y-%m-%d")
                        data.index = pd.to_datetime(data.index)

                        # Select only columns with labels <= 2
                        selected_cols = [col for col in data.columns if col <= 2]
                        data = data[selected_cols]

                        # Drop column 1 if it exists
                        if 1 in data.columns:
                            data.drop(columns=1, inplace=True)

                        # Rename column 2 to 'waterlevel' if it exists
                        if 2 in data.columns:
                            data.rename(columns={2: 'waterlevel'}, inplace=True)

                        # Set index name
                        data.index.name = 'datetime'

                        # Write processed data to CSV
                        data.to_csv(dest_path)
                        print(f"Processed file: {dest_path} (skip={skip})")
                        break  # Exit loop if successful
                    except Exception as e:
                        # Increment skip and try again on exception
                        skip += 1
                else:
                    print(f"Failed to process file: {source_path} after "
                          f"{max_skip} attempts.")



def remove_directories(base_dir:str, directories:list) -> None:
    """
    Remove specified directories within base_dir.

    Parameters:
    -----------
        - base_dir (str): Base directory containing directories to remove.
        - directories (list): List of directory names to remove.
    """
    for dir_name in directories:
        dir_path = os.path.join(base_dir, dir_name)
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            print(f"Removed directory: {dir_path}")
        else:
            print(f"Directory not found: {dir_path}")



def compile_observed_data(hydroweb_txt_path:str, 
                          data_folder:str) -> pd.DataFrame:
    """
    Description

    Parameters:
    -----------
        - hydroweb_txt_path (str): Path to the hydroweb.txt file.
        - data_folder (str): Folder where processed data files are stored.
    """
    # Read hydroweb metadata
    df = pd.read_csv(hydroweb_txt_path, sep="\t")
    results = []

    # Iterate over each row in the DataFrame
    for _, row in df.iterrows():
        name = row['name']
        code = row['hydroweb']
        reachid = row['reachid']
        fp = f"hydroprd_R_{name.upper()}_exp.txt"
        file_path = os.path.join(data_folder,fp)
        try:
            # Attempt to read the corresponding CSV file
            df = pd.read_csv(file_path)
            df["hydroweb"] = code
            df["reachid"] = reachid
            results.append(df)
        except Exception as e:
            pass
    
    return pd.concat(results, ignore_index=True)




if __name__ == '__main__':
    # Parameters for download
    API_KEY = ("kFb4XBaZX7d4RnWccF4jJugGQpAyeWvbLS1u09ngrHBqEF4gco")
    BASKET_NAME = "global_waterlevel_forecast"
    COLLECTIONS = ["HYDROWEB_RIVERS_RESEARCH", "HYDROWEB_RIVERS_OPE"]
    BBOX = [-180, -90, 180, 90]
    ZIP_FILENAME = "out.zip"
    EXTRACT_FOLDER = "hydroweb"

    # Download and extract the zip file
    base_dir = download_hydroweb(API_KEY, BASKET_NAME, COLLECTIONS, BBOX,
                                 ZIP_FILENAME, EXTRACT_FOLDER)

    # Process all hydroweb files within the extracted directory
    process_hydroweb_files(base_dir)

    # Remove original collection directories after processing
    remove_directories(base_dir, COLLECTIONS)

    # Process hydroweb.txt to read final processed files
    base_dir="hydroweb"
    df = compile_observed_data("stations.csv", base_dir)
    df.to_csv("hydroweb.csv", index=False)
