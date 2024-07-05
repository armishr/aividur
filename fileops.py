from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv

load_dotenv()


# Azure storage connection
connection_string = os.getenv("CONNECTION_STRING")  
container_name = os.getenv("CONTAINER_NAME")


def download_database_from_storage(connection_string, container_name, blob_name, local_path):
    # Connect to Azure Storage
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)

    # Download the database from Azure Storage
    blob_client = container_client.get_blob_client(blob_name)
    with open(local_path, "wb") as data_file:
        data = blob_client.download_blob()
        data.readinto(data_file)

def upload_database_to_storage(connection_string, container_name, blob_name, local_path):
    # Connect to Azure Storage
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)

    # Upload the database to Azure Storage
    blob_client = container_client.get_blob_client(blob_name)
    with open(local_path, "rb") as data_file:
        blob_client.upload_blob(data_file, overwrite=True)

def delete_folder_and_files(folder_path):
    try:
        # Check if the folder exists
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            # Iterate over all files in the folder and delete them
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"Deleted file: {file_path}")
                    else:
                        print(f"Skipped: {file_path} (not a file)")

                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

            # Delete the folder itself
            os.rmdir(folder_path)
            print(f"Deleted folder: {folder_path}")

        else:
            print(f"The specified path '{folder_path}' does not exist or is not a folder.")
    except Exception as e:
        print(f"Error: {e}")

def download_faiss_from_storage(blob_name, local_path):
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    with open(local_path, 'wb') as file:
        file.write(blob_client.download_blob().readall())


def create_directory(directory_path):
    try:
        # Check if the directory already exists
        if os.path.exists(directory_path):
            raise FileExistsError(f"Directory '{directory_path}' already exists.")
        
        # Create the directory
        os.makedirs(directory_path)
        print(f"Directory '{directory_path}' created successfully.")
    except Exception as e:
        print(f"Error: {e}")

def delete_files_in_folder(folder_name):
    print("I am deleting the folder now")
    print(folder_name)
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)

    # List blobs in the specified folder and its subfolders
    blob_prefix = folder_name + "/"
    blobs = container_client.list_blobs(name_starts_with=blob_prefix)

    print(blobs)

    # Delete each blob in the specified folder and its subfolders
    for blob in blobs:
        blob_client = container_client.get_blob_client(blob)
        blob_client.delete_blob()

    return True