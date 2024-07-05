from fileops import download_database_from_storage, upload_database_to_storage
import sqlite3
import os
from sqlite3 import Error
from datetime import datetime
from fileops import delete_files_in_folder
from users import insert_audit_record

from dotenv import load_dotenv

load_dotenv()


connection_string = os.getenv("CONNECTION_STRING")
container_name = os.getenv("CONTAINER_NAME")
blob_name = os.getenv("BLOB_NAME")
local_path= os.getenv("LOCAL_PATH")
db_name= os.getenv("DB_NAME")
openai_api_key=os.getenv("OPENAI_API_KEY") 

def get_model_createdBy(assistant_name):
    try:

        # Download the database from Azure Storage
        download_database_from_storage(connection_string, container_name, blob_name, local_path)
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Construct the SQL query with a placeholder for the assistant_name
        query = "SELECT createdBy FROM Assistants WHERE AssistantName = ?"

        # Execute the query with the assistant_name as a parameter
        cursor.execute(query, (assistant_name,))
        result = cursor.fetchone()

        if result:
            model_type = result[0]
            return model_type
        else:
            return None

    except Error as e:
        print("Error:", e)
        return None

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        upload_database_to_storage(connection_string, container_name, blob_name, local_path)


def get_model_type(assistant_name):
    try:
        download_database_from_storage(connection_string, container_name, blob_name, local_path)

        # Use the 'with' statement for the connection and cursor
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()

            query = "SELECT ModelType FROM Assistants WHERE AssistantName = ?"
            cursor.execute(query, (assistant_name,))
            result = cursor.fetchone()

            if result:
                model_type = result[0]
                return model_type
            else:
                return None

    except sqlite3.Error as e:
        # Log the error or print a more informative message
        print("SQLite Error:", e)
        return None
    
def insert_assistant(assistant_name, assistant_description, created_by, llmname, privacy):

    # Download the database from Azure Storage
    download_database_from_storage(connection_string, container_name, blob_name, local_path)
    conn = sqlite3.connect(db_name)
    
    cursor = conn.cursor()

    default_prompt = """I want you to act as an interview agent.
        Ask me questions and wait for my answers like a real person.
        Do not write explanations.
        Ask a question like a real person, only one question at a time.
        Do not ask the same question.
        Do not repeat the question.
        Do ask follow-up questions if necessary. 
        Your name is GPTInterviewer.
        I want you to only reply as an interviewer.
        Do not write all the conversation at once.
        If there is an error, point it out.


        Current Conversation:
        {history}

        Candidate: {input}
        AI: """

    try:
        print("Executing SQL Query:", """
            INSERT INTO Assistants (assistantName, assistantDescription, createdBy, createdOn, modeltype, privacy, prompt)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """)
        # Insert data into the Assistants table
        cursor.execute("""
            INSERT INTO Assistants (assistantName, assistantDescription, createdBy, createdOn, modeltype, privacy,prompt)
            VALUES (?, ?, ?, ?, ?,?,?)
        """, (assistant_name, assistant_description, created_by, str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), llmname,privacy,default_prompt))

        #insert_audit_record(cursor, assistant_name,"","","CREATED",created_by)

        # Commit the transaction
        conn.commit()
        print("Assistant inserted successfully!")

    except sqlite3.IntegrityError as e:
        print(f"Error: {e}")        
        return "Duplicate"

    finally:
        # Close the connection
        conn.close()
        upload_database_to_storage(connection_string, container_name, blob_name, local_path)


def get_assistant_data(userid):

    # Download the database from Azure Storage
    download_database_from_storage(connection_string, container_name, blob_name, local_path)
    conn = sqlite3.connect(db_name)

    print("I am in get assistant data")
    cursor = conn.cursor()


    if userid == 'Admin':
        cursor.execute("SELECT assistantname, assistantdescription, modeltype, privacy, createdby, createdon,prompt FROM Assistants" )

    else:
        cursor.execute("SELECT assistantname, assistantdescription, modeltype, privacy, createdby, createdon,prompt FROM Assistants WHERE createdby = ? OR privacy=?", (userid, "public"))
    
    rows = cursor.fetchall()

    conn.close()   
    
    return rows

def get_interview_userlist(AssistantName):

    # Download the database from Azure Storage
    download_database_from_storage(connection_string, container_name, blob_name, local_path)
    conn = sqlite3.connect(db_name)

    print("I am in get user data")
    cursor = conn.cursor()

    cursor.execute("SELECT createdby from Audit_table where assistantname = ?" , (AssistantName,))
  
    rows = cursor.fetchall()

    conn.close()
        
    return rows

def get_history_data(userid):

    # Download the database from Azure Storage
    download_database_from_storage(connection_string, container_name, blob_name, local_path)
    conn = sqlite3.connect(db_name)

    print("I am in get history data")
    cursor = conn.cursor()

    if userid == 'Admin':
        cursor.execute("select assistantname,inputmessage,responsemessage,actionperformed,createdby,createdon from Audit_table" )
    else:
        cursor.execute("select assistantname,inputmessage,responsemessage,actionperformed,createdby,createdon from Audit_table where createdby=?", (userid, ))

    
    rows = cursor.fetchall()

    conn.close()    
    print(rows)
    return rows

def get_prompt(assistant_name):

    # Download the database from Azure Storage
    download_database_from_storage(connection_string, container_name, blob_name, local_path)

    conn = sqlite3.connect(db_name)
    print("In get_prompt function")
    cursor = conn.cursor()
    cursor.execute('SELECT prompt FROM assistants WHERE assistantName = ?', (assistant_name,))
    result = cursor.fetchone()
    print(result)
    print("Out of get_prompt function")
    conn.close()
    return result[0] if result else None

def get_conversation_all_users(assistant_name):
    raw_userlist = get_interview_userlist(assistant_name)

    userlist = list(set(user[0] for user in raw_userlist if user and user[0] is not None))

    conversation_strings = []
    print(userlist)
    for user in userlist:
        try:
            print("I am in get_conversation_all_user")
            print(user)
            conversation_strings.append(f"\nInterview for user {user}\n")
            conversation_strings.append("======================\n")
            conversation_strings.append(get_conversation(assistant_name, user))
        except Exception as e:
            # Handle the exception (e.g., log the error)
            print(f"Error fetching conversation for user {user}: {e}")

    return '\n'.join(conversation_strings)   

def get_conversation(assistant_name,user):

    # Download the database from Azure Storage
    download_database_from_storage(connection_string, container_name, blob_name, local_path)

    conn = sqlite3.connect(db_name)
    print("In get_conversation function")
    cursor = conn.cursor()
        # Use parameterized queries to prevent SQL injection
    query = """
        SELECT createdby || ' : ' ||responsemessage || '\n\n' ||assistantName ||' : ' || inputmessage AS conversation
        FROM Audit_Table
        WHERE assistantName = ? AND createdby = ?
    """
    cursor.execute(query, (assistant_name, user))

    # Fetch all rows
    rows = cursor.fetchall()

    # Concatenate conversations into one string
    conversation_string = "\n\n".join(row[0] for row in rows)

    print(conversation_string)

    # Return the concatenated conversation string
    conn.close()
    return conversation_string 

def save_prompt(assistant_name, prompt):

    download_database_from_storage(connection_string, container_name, blob_name, local_path)
    conn = sqlite3.connect(db_name)
    
    cursor = conn.cursor()
    print("Before Inserting Prompt")
    print(assistant_name)
    try:
        # Insert data into the Assistants table
        cursor.execute('UPDATE assistants SET prompt = ? WHERE assistantName = ?', (prompt, assistant_name))
         # Commit the transaction
        conn.commit()
        print("Assistant prompt  successfully!")

    except sqlite3.IntegrityError as e:
        print(f"Error: {e}")        
        return "Duplicate"

    finally:
        # Close the connection
        conn.close()
        upload_database_to_storage(connection_string, container_name, blob_name, local_path)       

def delete_assistant_details(user_id,assistant_name):
    
    print("I am deleting")
    print(user_id, assistant_name)

    
    # Connect to Azure Storage
    blob_name = "vidurusers/myAssistant.db"

    # Local path for downloaded database
    local_path = "myAssistant.db"

    # Download the database from Azure Storage
    download_database_from_storage(connection_string, container_name, blob_name, local_path)

    # Connect to the SQLite database
    conn = sqlite3.connect(local_path)
    cursor = conn.cursor()

    # Delete the assistant record from the database
    delete_query = "DELETE FROM assistants WHERE createdby = ? AND assistantname = ?;"
    print(delete_query)
    cursor.execute(delete_query, (user_id, assistant_name))

    if cursor.rowcount > 0:
        # Commit the changes to the SQLite database
        
        conn.commit() 

        # Close the database connection
        cursor.close()
        conn.close()
        upload_database_to_storage(connection_string, container_name, blob_name, local_path)
        insert_audit_record(assistant_name,"","","DELETED",user_id)

        folder_path = f"vidurusers/{user_id}/{assistant_name}"
        delete_files_in_folder(folder_path)
        
    else:
        # Close the database connection
        cursor.close()
        conn.close()

    
            
    