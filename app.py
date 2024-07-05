import os
from flask import Flask, jsonify, make_response, render_template
from flask_cors import CORS
from flask import request

from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains.question_answering import load_qa_chain


from langchain.prompts import PromptTemplate
from langchain.llms import LlamaCpp
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains.question_answering import load_qa_chain


from huggingface_hub import hf_hub_download
import google.generativeai as genai

from functools import wraps
import bcrypt
import logging
from datetime import datetime
import secrets

from sqlite3 import Error
from os.path import join
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient
from functools import wraps

from flask import send_file 
from dotenv import load_dotenv
from users import create_user,insert_login_details,validate_session_token, insert_audit_record,authenticate_user,update_user_details,get_user_details,logout_user

from llms import run_llm, generate_matplotlib_code,analyse_response,create_embeddings
from utils import insert_assistant, get_model_type, get_prompt, save_prompt,get_history_data,get_conversation, get_interview_userlist,get_assistant_data, get_conversation_all_users,delete_assistant_details

# Load environment variables from the .env file
load_dotenv()

# Populate all the Keys
genai.configure(api_key=os.getenv("GOOGLE_API_TOKEN"))
replicate_api_token=os.getenv("REPLICATE_API_TOKEN") 
openai_api_key=os.getenv("OPENAI_API_KEY") 
google_api_key=os.getenv("GOOGLE_API_TOKEN")

# Azure storage connection
connection_string = os.getenv("CONNECTION_STRING")
container_name = os.getenv("CONTAINER_NAME")

app = Flask(__name__)
CORS(app, supports_credentials=True) 
app.logger.info("This is an info message from the Flask logger.")
app.static_folder = 'static'
chat_history = []

# Set logging level to DEBUG
logging.basicConfig(level=logging.DEBUG)

     
def protected_route(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if validate_session_token():
            return func(*args, **kwargs)
        else:
            return jsonify({"error": "Unauthorized"}), 401
    return wrapper

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/loginpage')
def loginpage():
    return render_template('login.html')

@app.route('/signup')
def signuppage():
    return render_template('signup.html')

@app.route('/header')
def header():
    return render_template('header.html')

@app.route('/Dashboard')
def Dashboard():
    return render_template('Dashboard.html')

@app.route('/sidebar')
def sidebar():
    return render_template('sidebar.js')

@app.route('/AskQuestion')
def AskQuestion():
    return render_template('AskQuestion.html')

@app.route('/Chat')
def chat():
    return render_template('chat.html')

@app.route('/chat.css')
def chatcss():
    return render_template('chat.css')

@app.route('/Profile')
def UserManagement():
    return render_template('Profile.html')

@app.route('/setup')
def setup():
    return render_template('Upload.html')

@app.route('/bsstyles.css')
def bsstyles():
    return render_template('bsstyles.css')

@app.route('/common.js')
def common():
    return render_template('common.js')

@app.route('/History')
def history():
    return render_template('History.html')

@app.route('/AIVidurLogo')
def AIVidurLogo():
    return render_template('AIVidurLogoNew.png')

@app.route('/Interview')
def Interview():
    return render_template('Interview.html')

@app.route('/PromptSetup')
def PromptSetup():
    return render_template('Promptsetup.html')

@app.route('/Analyse')
def Analyse():
    return render_template('Analyse.html')

@app.route('/upload/<llmname>', methods=['POST'])
@protected_route
def upload_file(llmname):
    try:
        user_id = request.cookies.get("user_id")
        assistant_name = request.form.get('assistantName')
        assistant_description = request.form.get('assistantDescription')
        privacy = request.form.get('privacy')

        # Get a list of uploaded files
        files = request.files.getlist('file')

        print(files)

        # Create a list to store file paths
        file_paths = []
        

        for file in files:
            file_name = secure_filename(file.filename)

            
            # Create a BlobServiceClient
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)

            # Get a BlobClient for the uploaded file
            blob_client = blob_service_client.get_blob_client(
                container=container_name,
                blob=f"vidurusers/{user_id}/{assistant_name}/input/{file_name}"
            )

            directory_path = f"vidurusers/{user_id}/{assistant_name}/input"
            
            # Create directory only if it does not exist
            if not os.path.exists(directory_path):
                os.makedirs(directory_path)

            file_path = join(directory_path, file_name)
            print("File path for saving:", file_path)

            # Save the file
            file.save(file_path)

            # Upload the file to Azure Blob Storage
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)

            print("File saved at:", file_path)

            # Append file path to the list
            file_paths.append(file_path)
            

        # Use PyPDFLoader with all files in the directory
        combined_data = []
        for file_path in file_paths:
            loader = PyPDFLoader(file_path)
            #loader = DirectoryLoader(directory_path, glob="*.pdf", loader_cls=PyPDFLoader)
            data = loader.load()
            combined_data.extend(data)
            

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
        docs = text_splitter.split_documents(combined_data)      
      
        create_embeddings(docs,llmname,user_id,assistant_name)
        # Assuming you have the embeddings and index_name defined here 
         

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

    result = insert_assistant(assistant_name, assistant_description, user_id, llmname,privacy)

    if result == 'Duplicate':
        response = 'The Assistant with the same name exists already. Please choose another name.'
    else:
        response = 'The Assistant has been created successfully.'
        insert_audit_record(assistant_name,"","","CREATE",user_id)

    return jsonify({"message": response})


@app.route('/chat_response/', methods=['POST'])
def get_chat_response():  
    print("I am here -1")
    data = request.get_json()
    print(data)
    query = data.get("question")
    assistantName = data.get("assistantName")
    userId = request.cookies.get("user_id")
    print(assistantName, userId)
    llmname= get_model_type(assistantName)   
             
    template = get_prompt(assistantName)
    print(template)

    # Create a prompt template from the template string
    prompt_template = PromptTemplate.from_template(template)

    max_history_length = 1000
    current_history = "\n".join(chat_history)
    if len(current_history) > max_history_length:
        excess_chars = len(current_history) - max_history_length
        current_history = current_history[excess_chars:]

    new_prompt = prompt_template.format(input=query, history=current_history)  

    # Call run_llm with the formatted prompt
    response = run_llm(new_prompt, userId, assistantName,llmname)   
        
    # Check if the generated response contains an answer key
    if response:
    # Assign the answer to response

        chat_history.append(f"Candidate: {query}\nAI: {response}")
    else:
        response = 'As a generative AI model, I don\'t have an answer to your question. Please refer to specific documentations.'
        
    insert_audit_record(assistantName,response,query,"Q&A",userId) 
    print("Inserted record in history")               

    return jsonify({"message": response})

@app.route('/answer/', methods=['POST'])
@protected_route
def get_answer():  
    print("I am here -1")
    data = request.get_json()
    print(data)
    query = data.get("question")
    assistantName = data.get("assistantName")
    userId = request.cookies.get("user_id")
    print(assistantName, userId)
    llmname= get_model_type(assistantName)
    print("I am here -3.0")
    print(llmname)

    template = "You are an expert in Generative AI. Your job is to provide accurate answer based on context documents provided. If you don't know the answer say 'As a generative AI model, I dont have answer to your question, please refer to course documentions'. Don't make up any answer. Ask question when in doubt. Question :{Question}"
    prompt_template = PromptTemplate.from_template(template)
    new_prompt = prompt_template.format(Question=query)
    
    generated_response = run_llm(new_prompt, userId, assistantName,llmname)
    
    if generated_response:
        response = generated_response
    else:
        response = 'As a generative AI model, I dont have answer to your question, please refer specific documentations.'
      
    print(response)      

    insert_audit_record(assistantName,query,response,"Q&A",userId)      

    return jsonify({"message": response})
       

@app.route('/get_summary_response/', methods=['POST'])

def get_summary_response():  
    print("I am here -1")
    data = request.get_json()
    print(data)
    summaryPrompt = data.get("prompt")    
    interviewText = data.get("conversation")
    
    print(interviewText)

    response = analyse_response(interviewText,summaryPrompt)
          
    print(response)

    return jsonify({"message": response})
    

@app.route('/Login', methods=['POST'])
def login():
    app.logger.info("This is login call - sunil .")
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400

    user_id = data.get("UserID")
    password = data.get("Password")    


    if not user_id or not password:
        return jsonify({"error": "Incomplete login data - coming feom server"}), 400

    
    auth_result = authenticate_user(user_id, password)

    if 'error' in auth_result:
        return jsonify({"error": auth_result['error']}), 401

    else:
        # Generate a session token
        session_token = secrets.token_urlsafe(32)

        # Get the current time
        login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Insert the login details into the login table (replace with your actual database operation)
        insert_login_details(user_id, session_token, login_time)

        # Send the session token back to the client as a cookie
        response = make_response(jsonify({"message": "Login successful-server"}), 200)
        response.set_cookie('user_id', value=user_id, max_age=3600, secure=True, samesite='None')
        #response.set_cookie('session_token', session_token)
        response.set_cookie('session_token', value=session_token, max_age=3600, secure=True, samesite='None')

        print("I have set the cookie")
        print(session_token)
        return response
      

# Function to hash a password
def hash_password(password):
    # Generate a random salt
    salt = bcrypt.gensalt()

    # Hash the password with the salt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

    return hashed_password

@app.route('/signup', methods=['POST'])
def signup():

    print("I have reached here")
    data = request.get_json()
    print("I have reached here -2")
    if not data:
        return jsonify({"error": "No data provided"}), 400

    user_id = data.get("UserID")
    password = hash_password(data.get("Password"))
    company = data.get("Company")
    email = data.get("Email")
    phone = data.get("Phone")
    city = data.get("City")

    if not user_id or not password or not company:
        return jsonify({"error": "Incomplete login data - coming feom server"}), 400

    user = create_user(user_id, password, company,email,phone,city)

    if user:
        return jsonify({"message": "User registered successfully"}), 200
    else:
        return jsonify({"error": "User registration error"}), 491
    
@app.route('/get_history_data', methods=['GET'])
def api_get_history_data():
    userid = request.cookies.get('user_id')

    history_data = get_history_data(userid)
    return jsonify({'history': history_data})

@app.route('/get_assistants_data', methods=['GET'])
def api_get_assistant_data():
    userid = request.cookies.get('user_id')
    assistant_data = get_assistant_data(userid)
    return jsonify({'assistant_data': assistant_data})

@app.route('/get_interview_user/<assistant_selected>', methods=['GET'])
def api_get_interview_user(assistant_selected):
    assistantName = assistant_selected
    interview_users = get_interview_userlist(assistantName)
    return jsonify({'interview_users': interview_users})

@app.route('/get_conversation/<assistant_name>/<user>', methods=['GET'])
def api_get_conversation(assistant_name,user):
    assistantName = assistant_name
    userName = user
    if user=='ALL':
        conversation = get_conversation_all_users(assistant_name)
    else:
        conversation = get_conversation(assistantName,userName)
    return jsonify({'conversation': conversation})

@app.route('/logout', methods=['POST'])
def logout():
    # Get user_id from the cookie (replace 'user_id' with your actual cookie name)
    user_id = request.cookies.get('user_id')

    if user_id is None:
        return jsonify({"error": "User not authenticated"}), 401

    try:
        logout_user(user_id)

        return jsonify({"message": "Logout successful"}), 200
    except Exception as e:
        return jsonify({"error": f"Error during logout: {str(e)}"}), 500


# Endpoint to delete an assistant by name
@app.route('/delete_assistants_data/<string:assistant_name>', methods=['DELETE'])
def delete_assistant(assistant_name):
    user_id = request.cookies.get('user_id')
    print("I am deleting")
    print(user_id, assistant_name)

    try:
        delete_assistant_details(user_id,assistant_name)
        return jsonify({'message': 'Assistant and associated files deleted successfully'}), 200
        
    except Error as e:
        return jsonify({'message': f'Error deleting assistant: {str(e)}'}), 500


# Route for fetching user data
@app.route('/user_data', methods=['GET'])
def get_user_data():
    try:
        user_id = request.cookies.get('user_id')    
        user_data = get_user_details(user_id)
        if user_data:
            return jsonify(user_data)
        else:
            return jsonify({"error": "User data updation error"}), 491
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route for updating user data
@app.route('/update_user_data', methods=['PUT'])
def update_user_data():
    try:
        user_id = request.cookies.get('user_id')
        updated_data = request.get_json()
        # Azure Storage details

        user = update_user_details(user_id,updated_data)

        if user:
            return jsonify({"message": "User data updated successfully"}), 200
        else:
            return jsonify({"error": "User data updation error"}), 491
    except Exception as e:
        return jsonify({'error': str(e)}), 500 


@app.route('/save_prompt/', methods=['POST'])
def save_prompt_endpoint():
    data = request.json
    assistant_name = data.get('assistantName')
    prompt = data.get('prompt')
    print("Assistant prompt update")

    if not assistant_name or not prompt:
        return jsonify({'error': 'Missing assistantName or prompt parameter'}), 400

    save_prompt(assistant_name, prompt)
    return jsonify({'success': 'Prompt saved successfully'})

@app.route('/get_prompt/<string:assistant_name>', methods=['GET'])
def get_prompt_endpoint(assistant_name):
    prompt = get_prompt(assistant_name)
    if prompt is not None:
        return jsonify({'prompt': prompt})
    else:
        return jsonify({'error': 'Assistant not found'}), 404
    

@app.route('/get_chart/', methods=['POST'])
def get_chart():  
    print("I am here -1")
    data = request.get_json()
    print(data)
    chartPrompt = data.get("prompt")
    assistantName = data.get("assistantName")
    interviewText = data.get("conversation")
    userId = request.cookies.get("user_id")
    print(interviewText)          
           
    matplotlib_code = generate_matplotlib_code(interviewText, chartPrompt)
    print(matplotlib_code)

    exec(matplotlib_code)
    
    return send_file("chart.png", mimetype='image/png', as_attachment=True)
    
if __name__ == '__main__':
    app.run(debug=True)


