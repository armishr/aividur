import sqlite3
import os
from flask import request
from fileops import download_database_from_storage,upload_database_to_storage
from datetime import datetime
import bcrypt
from dotenv import load_dotenv

load_dotenv()


# Azure storage connection
connection_string = os.getenv("CONNECTION_STRING")
container_name = os.getenv("CONTAINER_NAME")
blob_name = os.getenv("BLOB_NAME")
local_path= os.getenv("LOCAL_PATH")
db_name=os.getenv("DB_NAME")

def create_user(userid, password, company, email, phone, city):    

    # Download the database from Azure Storage
    download_database_from_storage(connection_string, container_name, blob_name, local_path)
    conn = sqlite3.connect(db_name)

    cursor = conn.cursor()

    print("In user creation")

    # Use placeholders and execute the query
    insert_data_query = '''
        INSERT INTO users (userid, password, company, email, phone, city) VALUES (?, ?, ?, ?, ?, ?);
    '''
    cursor.execute(insert_data_query, (userid, password, company, email, phone, city))
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    upload_database_to_storage(connection_string, container_name, blob_name, local_path)
    return userid

def update_user_details(user_id, updated_data):    

    # Download the database from Azure Storage
    download_database_from_storage(connection_string, container_name, blob_name, local_path)
    conn = sqlite3.connect(db_name)

    cursor = conn.cursor()

    print("In user creation")

    # Execute an UPDATE query to update user data
    update_query = "UPDATE users SET company = ?, city = ?, email = ?, phone = ? WHERE userid = ?;"
    cursor.execute(update_query, (
        updated_data['company'],
        updated_data['city'],
        updated_data['email'],
        updated_data['phone'],
        user_id
    ))
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    upload_database_to_storage(connection_string, container_name, blob_name, local_path)
    return user_id

def get_user_details(user_id):    

    # Download the database from Azure Storage
    download_database_from_storage(connection_string, container_name, blob_name, local_path)
    conn = sqlite3.connect(db_name)

    cursor = conn.cursor()

    print("In get user details")

    # Execute a SELECT query to fetch user data
    cursor.execute('SELECT userid, company, email, phone, city FROM users WHERE userid = ?;', (user_id,))
    user_data = cursor.fetchone()
    print(user_data)    
    
    # Close the cursor and connection
    cursor.close()
    conn.close()    
    return user_data

def insert_login_details(user_id, session_token, login_time):

    # Download the database from Azure Storage
    download_database_from_storage(connection_string, container_name, blob_name, local_path)
    conn = sqlite3.connect(db_name)

    cursor = conn.cursor()
    logged_in_flag = 'Yes'

    # Use placeholders and execute the query
    insert_data_query = '''
        INSERT INTO login (user_id, session_token, login_time, logged_in)
        VALUES (?, ?, ?, ?);
    '''
    cursor.execute(insert_data_query, (user_id, session_token, login_time, logged_in_flag))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    upload_database_to_storage(connection_string, container_name, blob_name, local_path)

def validate_session_token():
    user_id = request.cookies.get('user_id')
    session_token = request.cookies.get('session_token')
    print("I am in validate session function")

    print(user_id, session_token)

    if user_id and session_token:

        # Download the database from Azure Storage
        download_database_from_storage(connection_string, container_name, blob_name, local_path)
        conn = sqlite3.connect(db_name)

        cursor = conn.cursor()

        # Check if the session token exists for the given user
        cursor.execute("""
            SELECT * FROM login WHERE user_id = ? AND session_token = ? AND logged_in = 'Yes'
        """, (user_id, session_token))
        result = cursor.fetchone()

        conn.close()
        upload_database_to_storage(connection_string, container_name, blob_name, local_path)

        if result:
            return True
        else:
            return False
    else:
        return False
    
def insert_audit_record(assistant_name, input_message, response_message, action_performed, created_by):
   
    # Download the database from Azure Storage
    download_database_from_storage(connection_string, container_name, blob_name, local_path)
    conn = sqlite3.connect(db_name)

    cursor = conn.cursor()

    try:
        sql_insert = """
            INSERT INTO audit_table 
            (AssistantName, InputMessage, ResponseMessage, ActionPerformed, createdBy, CreatedOn) 
            VALUES (?, ?, ?, ?, ?, ?);
        """

        # Values to be inserted
        values = (assistant_name, input_message, response_message, action_performed, created_by, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # Execute the SQL statement
        cursor.execute(sql_insert, values)       

        # Commit the transaction
        conn.commit()
        print("Audit Data inserted successfully!")

    except sqlite3.IntegrityError as e:
        print(f"Error: {e}")        
        return "Duplicate"

    finally:
        # Close the connection
        conn.close()
        upload_database_to_storage(connection_string, container_name, blob_name, local_path)

def authenticate_user(userid, password):
    try:
        # Connect to the PostgreSQL database

        # Download the database from Azure Storage
        download_database_from_storage(connection_string, container_name, blob_name, local_path)
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Query the database for user credentials
        cursor.execute("SELECT password FROM users WHERE userid = ?", (userid,))
        dbpassword = cursor.fetchone()

        if dbpassword is None:
            return {"error": "User not found for the given UserID and Company"}

        stored_password = dbpassword[0]
        print(password, stored_password)
        # Validate the entered password with the stored hashed password
        if bcrypt.checkpw(password.encode('utf-8'), stored_password):            
            print("Authentication successful")
            return {"success": "Authentication successful"}
            
        else:
            print("Authentication failed")
            return {"error": "Incorrect password"}

    except Exception as e:
        print("Authentication error")
        print(str(e))
        return {"error": str(e)}
    

    finally:
        # Close the database connection in the finally block
        if conn is not None:
            conn.close()
            upload_database_to_storage(connection_string, container_name, blob_name, local_path)


def logout_user(user_id):

    # Connect to the SQLite database
    blob_name = "vidurusers/myAssistant.db"

    # Local path for downloaded database
    local_path = "myAssistant.db"

    # Download the database from Azure Storage
    download_database_from_storage(connection_string, container_name, blob_name, local_path)
    conn = sqlite3.connect('myAssistant.db')
    cursor = conn.cursor()

    # Update the logout_time and remove the session_token
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        UPDATE login
        SET logout_time = ?, session_token = NULL, logged_in = 'false'
        WHERE user_id = ? AND session_token IS NOT NULL
    """, (current_time, user_id))

    # Commit the changes
    conn.commit()

    # Close the database connection
    conn.close()
    upload_database_to_storage(connection_string, container_name, blob_name, local_path)