import pandas as pd
from pandas import DataFrame
import requests
import numpy
import io
import os
import boto3
import configparser
from datetime import datetime

#call the configparser to read the config.conf file
config = configparser.ConfigParser()
config.read('config.conf')
aws_access_key = config.get('aws', 'AWS_ACCESS_KEY')
aws_secret_key = config.get('aws', 'AWS_SECRET_KEY')
region_name = config.get('aws', 'REGION_NAME')

# Define the file path for the CSV file
file_path=os.getcwd() + "/data/exoplanets.csv"

# Define the API URL and query
api_url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
first_day_current_month = str(datetime.today().replace(day=1).strftime('%Y-%m-%d'))
query = f"""select 
    pl_name,
    hostname,
    disc_year,
    discoverymethod,
    disc_facility,
    pl_rade,
    pl_masse,
    pl_orbper,
    pl_orbsmax,
    sy_dist,
    st_teff,
    sy_pnum 
from ps
WHERE rowupdate >= '{first_day_current_month}'"""

# Function to get raw data from the NASA Exoplanet Archive API
def get_raw_data() -> DataFrame:
    try:
        response = requests.get(
            api_url,
            params={
                "query": query, 
                "format": "csv"
                },
            timeout=120
        )
        response.raise_for_status()

        df = pd.read_csv(io.BytesIO(response.content))
        print(f"Data fetched successfully. Number of records: {len(df)}")
        return df

    except Exception as e:
        print("Error getting data from API: ", str(e))
        return None

# Function to convert DataFrame to CSV
def convert_to_csv(df: DataFrame) -> None:
    try:
        df.to_csv(file_path, index=False)
        print(f"Data saved to {file_path}")
    except Exception as e:
        print("Error saving data to CSV: ", str(e))

# Function to upload file to S3
def upload_to_S3(bucket_name:str, object_name:str):
    try:
        s3_client = boto3.client('s3',
                                 aws_access_key_id=aws_access_key, 
                                 aws_secret_access_key=aws_secret_key,
                                 region_name=region_name
                                )
        s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=open(file_path, 'rb'))
        print(f"File uploaded to S3: {bucket_name}/{object_name}")
    except Exception as e:
        print("Error uploading file to S3: ", str(e))

# Main execution
if __name__ == "__main__":
    df = get_raw_data()

    try:
        if df is not None:
            convert_to_csv(df)
    except Exception as e:
        print("Error in main execution: ", str(e))
        raise 

    try:
        upload_to_S3("nasa-exoplanets-data", f"bronze/exoplanets_{pd.Timestamp.now().strftime('%Y-%m-%d')}.csv")
    except Exception as e:
        print("Error uploading to S3: ", str(e))
        raise