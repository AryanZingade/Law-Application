import os
import re
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from langgraph.graph import Graph
from langchain_openai import AzureChatOpenAI
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, ContentSettings
import datetime
import requests

from casesearch import search_cases
from verdict import process_case
from formatter import (
    classify_document_type,
    fetch_template_from_blob,
    extract_placeholders,
    extract_json_from_response,
    fill_document_with_gpt,
    generate_extraction_prompt
)
from summarisation import extract_summary
from translate import process_uploaded_document

# Env variables
OPENAI_API_KEY = os.getenv("OPENAI_GPT_API_KEY")
AZURE_ENDPOINT = os.getenv("OPENAI_GPT_ENDPOINT")
AZURE_BLOB_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
AZURE_BLOB_CONTAINER = os.getenv("AZURE_CONTAINER_NAME")
AZURE_BLOB_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")

app = Flask(__name__)
CORS(app)

# Initialize LLM
llm = AzureChatOpenAI(
    azure_deployment="gpt-4o-mini",
    azure_endpoint=AZURE_ENDPOINT,
    api_key=OPENAI_API_KEY,
    api_version="2024-10-21",
    temperature=0.2
)

def generate_sas_url(blob_name):
    sas_token = generate_blob_sas(
        account_name=AZURE_BLOB_ACCOUNT,
        container_name=AZURE_BLOB_CONTAINER,
        blob_name=blob_name,
        account_key=AZURE_BLOB_KEY,
        permission=BlobSasPermissions(read=True),  # Ensure the correct permission
        expiry=datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Ensure token expiry is reasonable
    )
    return f"https://{AZURE_BLOB_ACCOUNT}.blob.core.windows.net/{AZURE_BLOB_CONTAINER}/{blob_name}?{sas_token}"


def upload_pdf_to_blob(file_path, file_name):
    blob_service_client = BlobServiceClient(
        account_url=f"https://{AZURE_BLOB_ACCOUNT}.blob.core.windows.net",
        credential=AZURE_BLOB_KEY
    )
    blob_client = blob_service_client.get_blob_client(
        container=AZURE_BLOB_CONTAINER,
        blob=file_name
    )
    with open(file_path, "rb") as data:
        blob_client.upload_blob(
            data,
            overwrite=True,
            content_settings=ContentSettings(content_type="application/pdf")
        )
    return f"File {file_name} uploaded successfully."

def get_most_recent_blob():
    blob_service_client = BlobServiceClient(
        account_url=f"https://{AZURE_BLOB_ACCOUNT}.blob.core.windows.net",
        credential=AZURE_BLOB_KEY
    )
    container_client = blob_service_client.get_container_client(AZURE_BLOB_CONTAINER)
    blobs = container_client.list_blobs()
    most_recent_blob = max(blobs, key=lambda b: b['last_modified'])
    return most_recent_blob['name']

@app.route("/upload-pdf", methods=["POST"])
def upload_pdf():
    print("Handling PDF upload route...")
    if "file" not in request.files:
        print("No file part in the request")
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        print("No file selected")
        return jsonify({"error": "No file selected"}), 400

    filename = file.filename
    temp_path = os.path.join("/tmp", filename)
    file.save(temp_path)

    try:
        message = upload_pdf_to_blob(temp_path, filename)
        os.remove(temp_path)
        print(f"PDF uploaded successfully: {filename}")
        return jsonify({"message": message, "filename": filename}), 200
    except Exception as e:
        print(f"Error uploading PDF: {e}")
        return jsonify({"error": str(e)}), 500

def classify_query(data):
    print("Classifying user input...")
    user_input = data.get("user_input", "").strip() if isinstance(data, dict) else str(data).strip()
    if not user_input:
        print("No user input provided, classifying as unknown")
        return "unknown", data

    prompt = f"""
    Classify the following user query:
    - "case_search" if searching for similar legal cases.
    - "verdict_prediction" if seeking a verdict prediction.
    - "document_generation" if query is regarding any kind of drafting or creation of a document.
    - "perform_action" if the query is regarding summarising a document or translating a document.
    
    Query: \"{user_input}\"
    Output (case_search or verdict_prediction or document_generation or perform_action):
    """
    response = llm.invoke(prompt)
    classification = response.content.strip().lower()
    print(f"Query classified as: {classification}")
    return (classification if classification in ["case_search", "verdict_prediction", "document_generation", "perform_action"] else "unknown", data)

def case_search_agent(data):
    print("Routing to case_search_agent...")
    query = data.get("user_input", "") if isinstance(data, dict) else str(data)
    if not query:
        print("No query provided for case search")
        return {"error": "No query provided."}
    return {"result": search_cases(query)}

def verdict_agent(data):
    print("Routing to verdict_agent...")
    case_input = data.get("user_input", "") if isinstance(data, dict) else str(data)
    if not case_input:
        print("No case input provided for verdict prediction")
        return {"error": "No case input provided."}
    return process_case(case_input)

def document_generation(inputs):
    print("Routing to document_generation...")
    if isinstance(inputs, tuple):
        _, data = inputs
    else:
        data = inputs

    user_query = data.get("user_input", "").strip()
    if not user_query:
        print("No user input provided for document generation")
        return {"error": "User input is missing or empty."}

    document_type = classify_document_type(user_query)
    if not document_type:
        print(f"Could not classify document type from user input: {user_query}")
        return {"error": "Could not determine document type."}

    template_path = fetch_template_from_blob(document_type)
    if not template_path:
        print(f"Template fetching failed for document type: {document_type}")
        return {"error": "Template fetching failed."}

    placeholders = extract_placeholders(template_path)
    if not placeholders:
        print(f"No placeholders found in template: {template_path}")
        return {"error": "No placeholders found in the template."}

    extraction_prompt = generate_extraction_prompt(user_query, document_type, placeholders)
    response = llm.invoke([{ "role": "user", "content": extraction_prompt }])
    extracted_data = extract_json_from_response(response.content.strip())
    if not extracted_data:
        print(f"GPT response format incorrect for user input: {user_query}")
        return {"error": "GPT response format is incorrect."}

    final_doc_path = fill_document_with_gpt(template_path, extracted_data)
    if not final_doc_path:
        print("Failed to generate document")
        return {"error": "Failed to generate document."}

    print(f"Document generated successfully: {final_doc_path}")
    return {"document_path": final_doc_path}

def extract_language_code(user_query):
    prompt = f"""
You are a helpful assistant that extracts the target language from a user's translation request.

Example queries and expected output:
- "translate this to Hindi" → hi
- "I want my document translated into French" → fr
- "please translate my PDF to Arabic" → ar
- "can you convert this into Japanese?" → ja

If no language is mentioned, return "en" for English.

Now extract the language code from this query:
\"{user_query}\"

Respond only with the 2-letter ISO 639-1 language code.
    """
    response = llm.invoke(prompt)
    return response.content.strip().lower()


def perform_action(inputs):
    print("Routing to perform_action...")
    if isinstance(inputs, tuple):
        _, data = inputs
    else:
        data = inputs

    user_query = data.get("user_input", "").strip()
    if not user_query:
        print("No user input provided for action (summarize/translate)")
        return {"error": "User input is missing or empty."}

    file_name = get_most_recent_blob()
    if not file_name:
        print("No file found in blob storage.")
        return {"error": "No file found in blob storage."}

    sas_url = generate_sas_url(file_name)
    response = requests.get(sas_url)

    if response.status_code != 200:
        print(f"Failed to download blob using SAS URL: {sas_url}")
        return {"error": "Failed to download blob using SAS URL."}

    file_path = os.path.join("/tmp", file_name)
    with open(file_path, "wb") as f:
        f.write(response.content)

    try:
        if "summarize" in user_query.lower() or "summarise" in user_query.lower():
            print("Summarizing the document...")
            result = extract_summary(file_path, file_name)
        elif "translate" in user_query.lower():
            target_lang = extract_language_code(user_query)
            print(f"Translating the document to {target_lang}...")
            result = process_uploaded_document(local_path=file_path, target_language=target_lang)
        else:
            print(f"Invalid query: {user_query}.")
            return {"error": "Invalid query. Please include 'summarize' or 'translate to <language>'."}
        return result
    finally:
        os.remove(file_path)


# Workflow Setup
workflow = Graph()
workflow.add_node("classifier", classify_query)
workflow.add_node("case_search_agent", case_search_agent)
workflow.add_node("verdict_agent", verdict_agent)
workflow.add_node("document_generation", document_generation)
workflow.add_node("perform_action", perform_action)

def route_decision(inputs):
    classification, data = inputs
    print(f"Routing decision: {classification}")
    if not isinstance(data, dict):
        return None
    data["classification"] = classification
    if classification == "case_search":
        return "case_search_agent"
    elif classification == "verdict_prediction":
        return "verdict_agent"
    elif classification == "document_generation":
        return "document_generation"
    elif classification == "perform_action":
        return "perform_action"
    else:
        return None

workflow.add_conditional_edges("classifier", route_decision)
workflow.set_finish_point("case_search_agent")
workflow.set_finish_point("verdict_agent")
workflow.set_finish_point("document_generation")
workflow.set_finish_point("perform_action")
workflow.set_entry_point("classifier")
app_workflow = workflow.compile()

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/invoke", methods=["POST"])
def invoke_workflow():
    print("Invoking workflow...")
    data = request.json

    if not data:
        print("No JSON data provided in request")
        return jsonify({"error": "JSON data is required"}), 400

    if "user_input" not in data:
        print("user_input not provided in request")
        return jsonify({"error": "user_input is required"}), 400

    target_lang = data.get("targetLanguage")  # Default to English if not provided
    print(f"Target language selected: {target_lang}")

    # You can use target_lang here if you need it for preprocessing or logging
    result = app_workflow.invoke(data)  # Make sure your workflow handles targetLanguage

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
