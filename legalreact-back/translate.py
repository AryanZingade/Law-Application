import os
import json
import logging
import requests
from datetime import datetime, timedelta
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

# --- Load environment variables ---
AZURE_BLOB_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
AZURE_BLOB_CONTAINER = os.getenv("AZURE_CONTAINER_NAME")
AZURE_BLOB_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
AZURE_FORM_RECOGNIZER_ENDPOINT = os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT")
AZURE_FORM_RECOGNIZER_KEY = os.getenv("AZURE_DOC_INTELLIGENCE_KEY")
AZURE_TRANSLATOR_REGION = os.getenv("AZURE_TRANSLATOR_REGION")
AZURE_TRANSLATOR_KEY = os.getenv("AZURE_TRANSLATOR_KEY")

# --- Logging ---
logging.basicConfig(level=logging.INFO)

# --- Azure Clients ---
blob_service_client = BlobServiceClient(
    account_url=f"https://{AZURE_BLOB_ACCOUNT}.blob.core.windows.net",
    credential=AZURE_BLOB_KEY
)

document_analysis_client = DocumentAnalysisClient(
    endpoint=AZURE_FORM_RECOGNIZER_ENDPOINT,
    credential=AzureKeyCredential(AZURE_FORM_RECOGNIZER_KEY)
)

# --- Load glossary ---
def load_glossary(file_path="glossary.json"):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Failed to load glossary: {str(e)}")
        return {}

GLOSSARY = load_glossary()

# --- Upload file to blob storage ---
def upload_document_to_blob(local_path):
    try:
        blob_name = os.path.basename(local_path)
        blob_client = blob_service_client.get_blob_client(container=AZURE_BLOB_CONTAINER, blob=blob_name)

        with open(local_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
            logging.info(f"Uploaded file to blob: {blob_name}")
        return blob_name
    except Exception as e:
        logging.error(f"Failed to upload document: {str(e)}")
        return None

# --- Generate SAS URL for Form Recognizer ---
def generate_sas_url(blob_name):
    try:
        sas_token = generate_blob_sas(
            account_name=AZURE_BLOB_ACCOUNT,
            container_name=AZURE_BLOB_CONTAINER,
            blob_name=blob_name,
            account_key=AZURE_BLOB_KEY,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1)
        )
        sas_url = f"https://{AZURE_BLOB_ACCOUNT}.blob.core.windows.net/{AZURE_BLOB_CONTAINER}/{blob_name}?{sas_token}"
        logging.info(f"SAS URL generated for blob: {blob_name}")
        return sas_url
    except Exception as e:
        logging.error(f"Failed to generate SAS URL: {str(e)}")
        return None

# --- Extract text using Form Recognizer ---
def extract_text_from_document(blob_name):
    sas_url = generate_sas_url(blob_name)
    if not sas_url:
        return None

    logging.info(f"Extracting text from blob: {blob_name}")
    try:
        poller = document_analysis_client.begin_analyze_document_from_url("prebuilt-read", sas_url)
        result = poller.result()
        extracted = "\n".join([line.content for page in result.pages for line in page.lines])
        return extracted or None
    except Exception as e:
        logging.error(f"Failed to extract text: {str(e)}")
        return None

# --- Detect document language ---
def detect_language(text):
    url = "https://api.cognitive.microsofttranslator.com/detect?api-version=3.0"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": AZURE_TRANSLATOR_REGION,
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, headers=headers, json=[{"text": text}])
        return response.json()[0].get("language") if response.status_code == 200 else None
    except Exception as e:
        logging.error(f"Language detection failed: {str(e)}")
        return None

# --- Apply glossary replacements ---
def apply_glossary_replacements(translated_text):
    for eng_term, hindi_term in GLOSSARY.items():
        translated_text = translated_text.replace(eng_term, hindi_term)
    return translated_text

# --- Translate text using Azure Translator ---
def translate_text(text, target_language):
    url = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": AZURE_TRANSLATOR_REGION,
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, headers=headers, json=[{"text": text}], params={"to": target_language})
        if response.status_code == 200:
            translated = response.json()[0]["translations"][0]["text"]
            return apply_glossary_replacements(translated)
        else:
            logging.error(f"Translation failed: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Translation failed: {str(e)}")
        return None

# --- Complete document processing pipeline ---
def process_uploaded_document(local_path, target_language):
    logging.info(f"Processing uploaded document: {local_path} -> {target_language}")
    
    blob_name = upload_document_to_blob(local_path)
    if not blob_name:
        return {"error": "Failed to upload document."}

    extracted_text = extract_text_from_document(blob_name)
    if not extracted_text:
        return {"error": "Failed to extract text from document."}

    detected_lang = detect_language(extracted_text)
    if not detected_lang:
        return {"error": "Failed to detect source language."}

    if detected_lang == target_language:
        return {"message": "Document is already in the target language.", "translated_text": extracted_text}

    translated_text = translate_text(extracted_text, target_language)
    return {"source_language": detected_lang, "translated_text": translated_text} if translated_text else {"error": "Translation failed."}
