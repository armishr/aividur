import os
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.llms import HuggingFaceHub
from langchain.memory import ConversationBufferMemory
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.embeddings import HuggingFaceEmbeddings
import google.generativeai as genai
from langchain.llms import Replicate
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
import openai
from azure.storage.blob import BlobServiceClient
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from utils import get_model_createdBy
from fileops import download_faiss_from_storage,delete_folder_and_files
from dotenv import load_dotenv

load_dotenv()

# Populate all the Keys
genai.configure(api_key=os.getenv("GOOGLE_API_TOKEN"))
replicate_api_token=os.getenv("REPLICATE_API_TOKEN") 
openai_api_key=os.getenv("OPENAI_API_KEY") 
google_api_key=os.getenv("GOOGLE_API_TOKEN")

# Azure storage connection
connection_string = os.getenv("CONNECTION_STRING")
container_name = os.getenv("CONTAINER_NAME")



llama_model = Replicate(
    model= "meta/llama-2-13b-chat:f4e2de70d66816a838a89eeeb621910adffb0dd0baba3976c96980970978018d",
    replicate_api_token=replicate_api_token,
    input={"temperature": 0.9, "max_length": 512, "top_p": 1},
)

'''
llama_model = Replicate(
    model= "meta/meta-llama-3-70b:83c5bdea9941e83be68480bd06ad792f3f295612a24e4678baed34083083a87f",
    replicate_api_token=replicate_api_token,
    input={"temperature": 0.9, "max_length": 100, "top_p": 1},
)
'''

def run_llm(query: str,  userid, assistantName, llmname):
    createdBy = get_model_createdBy(assistantName)
    directory_path = f"/faiss_{createdBy}_{assistantName}"

    # Create directory only if it does not exist
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    local_path_filename = f"{directory_path}/index.faiss"

    # Download the index.faiss file from Azure Storage
    download_faiss_from_storage(f"vidurusers/{createdBy}/{assistantName}/output/index.faiss", local_path_filename)

    local_path_filename = f"{directory_path}/index.pkl"

    # Download the index.pkl file from Azure Storage
    download_faiss_from_storage(f"vidurusers/{createdBy}/{assistantName}/output/index.pkl", local_path_filename)

    if llmname=='OpenAI':
    # Initialize OpenAI Embeddings
        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        docsearch = FAISS.load_local(directory_path, embeddings)
        # Create a ChatOpenAI instance
        chat = ChatOpenAI(
            verbose=True,
            openai_api_key=openai_api_key,
            temperature=0.8,
        )

        # Create a ConversationalRetrievalChain using the chat model and faiss_index retriever
        qa = ConversationalRetrievalChain.from_llm(
            llm=chat,
            retriever=docsearch.as_retriever()
        )

        input_data = {
            "question": query,
            "chat_history": []
        }

        print("Run the query through the ConversationalRetrievalChain")
        response = qa(input_data)
        print("I am in OpenAI query 1.0")

        print(response)
        final_response = response['answer']
    elif llmname=='Llama':

        # Use HuggingFaceEmbeddings
        #embeddings = HuggingFaceEmbeddings(model_name = 'sentence-transformers/all-MiniLM-L6-v2', model_kwargs = {'device':'cpu'})
        embeddings = HuggingFaceEmbeddings(model_name = 'sentence-transformers/all-mpnet-base-v2', model_kwargs = {'device':'cpu'})
        print("I am in Llama query 1.1")
        docsearch = FAISS.load_local(directory_path, embeddings)
        print("I am in Llama query 1.2")

        chain = ConversationalRetrievalChain.from_llm(llama_model, docsearch.as_retriever())
        print("I am in Llama query 1.3")
        chat_history = []
        response = chain({"question":query, "chat_history":[]})
        
        print(response['answer'])
        print("I am in Llama query 1.4")
        final_response = response['answer']
        '''
        full_response = response['answer']
        start = full_response.find("Answer:") + len("Answer:")
        end = full_response.find("\\end{lstlisting}")

        final_response = full_response[start:end].strip() 
        '''

    elif llmname=='Gemini':

        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=google_api_key)  # type: ignore

        new_db = FAISS.load_local(directory_path, embeddings)
        docsearch = new_db.similarity_search(query)

        print("I am in Gemini query 1.1")
        prompt_template = """
            Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
            provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
            Context:\n {context}?\n
            Question: \n{question}\n

            Answer:
            """
        print("I am in Gemini query 1")
        model = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest",
                                   client=genai,
                                   temperature=0.3,
                                   google_api_key=google_api_key,
                                   )
        print("I am in Gemini query 2") 

        prompt = PromptTemplate(template=prompt_template,
                        input_variables=["context", "question"])  

        print(prompt)    
        chain = load_qa_chain(llm=model, chain_type="stuff", prompt=prompt)
        response = chain(
            {"input_documents": docsearch, "question": query}, return_only_outputs=True, )
        print(response)
        final_response = response['output_text']

    elif llmname=='Mistral':
       
       print("I am in Mistral 1")
       embeddings = HuggingFaceEmbeddings(model_name = 'sentence-transformers/all-mpnet-base-v2', model_kwargs = {'device':'cpu'})
       print("I am in Mistral query 1.1")
       docsearch = FAISS.load_local(directory_path, embeddings)
       print("I am in Mistral query 1.2")

       llm = HuggingFaceHub(
            repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
            model_kwargs={"temperature": 0.5, "max_length": 1048},
        )
       print("I am in Mistral query 1.3")
       memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
       print("I am in Mistral query 1.4")
       
       chain = ConversationalRetrievalChain.from_llm(
                llm=llm, retriever=docsearch.as_retriever(), memory=memory
            )
       print("I am in Mistral query 1.51")
    
       response = chain({"question": query})["answer"]

       # Extract text after "Helpful Answer"
       helpful_answer_index = response.rfind("Helpful Answer")
       
       if helpful_answer_index != -1:
            helpful_answer_text = response[helpful_answer_index + len("Helpful Answer"):].strip()
            final_response = helpful_answer_text
       else:
            final_response = response

       print("I am in Mistral query 1.52")
       print(final_response)

    delete_folder_and_files(directory_path)
    return final_response


def generate_matplotlib_code(data, user_query):

    messages = [{"role": "system", "content": "You are a helpful assistant capable of generating Python code."}]
    messages += [{"role": "user", "content": line} for line in data if line.strip()]


    messages.append({
        "role": "user",
        "content": f"Generate a plain Python Matplotlib code snippet for a {user_query}, based on the above conversations. The code should be compiled with no error start directly with 'import matplotlib.pyplot as plt' and end with 'plt.show()'. Also save the save the image locally as 'chart.png'. Provide a text based analysis of the chart. Ensure the code does not include any Markdown code block indicators like triple backticks."
    })

    try:
        openai.api_key = openai_api_key
        response = openai.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=messages,
            max_tokens=1000
        )
        print(response)
        return response
    except Exception as e:
        return f"An error occurred: {str(e)}"

def analyse_response(interview, user_query):

    messages = [{"role": "system", "content": "You are a helpful assistant capable of analyzing user interviews."}]
    messages += [{"role": "user", "content": line} for line in interview if line.strip()]


    messages.append({
        "role": "user",
        "content": f"{user_query}, based on the above conversations."
    })

    try:
        openai.api_key = openai_api_key
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,            
            max_tokens=1000
        )
        print(response)

        print("I am successful")

        first_choice = response.choices[0].message.content

        print(first_choice)       

        return first_choice


    except Exception as e:
        return f"An error occurred: {str(e)}"
    
def create_embeddings(docs,llmname,user_id,assistant_name):
      
    if llmname == 'Llama' or llmname == 'Mistral':
        print("I am here in Llama-6.1")
        embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2')
      
    elif llmname == 'OpenAI':
        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

    elif llmname == 'Gemini':
        print("I am in Gemini-1")
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=google_api_key)  # type: ignore
        
    else:
        return "LLM not supported currently"
    
    vectorstore = FAISS.from_documents(docs, embedding=embeddings)
    
    directory_path = f"/vidurusers/{user_id}/{assistant_name}/output"
    
    # Create directory only if it does not exist
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    # Save vectorstore locally as a folder
    vectorstore.save_local(directory_path)
    print("I am in Gemini-3")

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_name = f"vidurusers/{user_id}/{assistant_name}/output/"
    container_client = blob_service_client.get_container_client(container_name)

    for root, dirs, files in os.walk(directory_path):
        for file in files:
            local_file_path = os.path.join(root, file)

            with open(local_file_path, "rb") as data_file:
                blob_path = os.path.relpath(local_file_path, directory_path)
                blob_path = blob_path.replace(os.path.sep, '/')
                blob_name = f"vidurusers/{user_id}/{assistant_name}/output/{blob_path}"

                blob_client = container_client.get_blob_client(blob=blob_name)
                blob_client.upload_blob(data_file, overwrite=True)