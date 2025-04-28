import os
import json
import logging
import requests
from datetime import datetime, timedelta
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions


# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class Translate:
    def __init__(self):
        self.AZURE_BLOB_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.AZURE_BLOB_CONTAINER = os.getenv("AZURE_CONTAINER_NAME")
        self.AZURE_BLOB_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
        self.AZURE_FORM_RECOGNIZER_ENDPOINT = os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT")
        self.AZURE_FORM_RECOGNIZER_KEY = os.getenv("AZURE_DOC_INTELLIGENCE_KEY")
        self.AZURE_TRANSLATOR_REGION = os.getenv("AZURE_TRANSLATOR_REGION")
        self.AZURE_TRANSLATOR_KEY = os.getenv("AZURE_TRANSLATOR_KEY")

        self.blob_service_client = BlobServiceClient(
            account_url=f"https://{self.AZURE_BLOB_ACCOUNT}.blob.core.windows.net",
            credential=self.AZURE_BLOB_KEY
        )
        self.document_analysis_client = DocumentAnalysisClient(
            endpoint=self.AZURE_FORM_RECOGNIZER_ENDPOINT,
            credential=AzureKeyCredential(self.AZURE_FORM_RECOGNIZER_KEY)
        )

        self.GLOSSARY = self.load_glossary()

    def load_glossary(self, file_path="glossary.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                glossary = json.load(file)
                logging.info("Glossary loaded successfully.")
                return glossary
        except Exception as e:
            logging.error(f"Failed to load glossary: {e}")
            return {}


    def upload_document_to_blob(self, local_path):
        try:
            blob_name = os.path.basename(local_path)
            blob_client = self.blob_service_client.get_blob_client(container=self.AZURE_BLOB_CONTAINER, blob=blob_name)
            with open(local_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            logging.info(f"Uploaded document to blob storage: {blob_name}")
            return blob_name
        except Exception as e:
            logging.error(f"Upload failed: {e}")
            return None

    def generate_sas_url(self, blob_name):
        try:
            sas_token = generate_blob_sas(
                account_name=self.AZURE_BLOB_ACCOUNT,
                container_name=self.AZURE_BLOB_CONTAINER,
                blob_name=blob_name,
                account_key=self.AZURE_BLOB_KEY,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=1)
            )
            sas_url = f"https://{self.AZURE_BLOB_ACCOUNT}.blob.core.windows.net/{self.AZURE_BLOB_CONTAINER}/{blob_name}?{sas_token}"
            logging.info(f"SAS URL generated for: {blob_name}")
            return sas_url
        except Exception as e:
            logging.error(f"SAS URL generation failed: {e}")
            return None

    def extract_text_from_document(self, blob_name):
        sas_url = self.generate_sas_url(blob_name)
        if not sas_url:
            return None
        try:
            poller = self.document_analysis_client.begin_analyze_document_from_url("prebuilt-read", sas_url)
            result = poller.result()
            extracted = "\n".join([line.content for page in result.pages for line in page.lines])
            logging.info(f"Text extracted from document: {blob_name}")
            return extracted or None
        except Exception as e:
            logging.error(f"Text extraction failed: {e}")
            return None

    def detect_language(self, text):
        try:
            url = "https://api.cognitive.microsofttranslator.com/detect?api-version=3.0"
            headers = {
                "Ocp-Apim-Subscription-Key": self.AZURE_TRANSLATOR_KEY,
                "Ocp-Apim-Subscription-Region": self.AZURE_TRANSLATOR_REGION,
                "Content-Type": "application/json"
            }
            response = requests.post(url, headers=headers, json=[{"text": text}])
            if response.status_code == 200:
                lang = response.json()[0].get("language")
                logging.info(f"Detected language: {lang}")
                return lang
            logging.error(f"Language detection API error: {response.text}")
            return None
        except Exception as e:
            logging.error(f"Language detection failed: {e}")
            return None

    def apply_glossary_replacements(self, translated_text):
        for eng_term, hindi_term in self.GLOSSARY.items():
            translated_text = translated_text.replace(eng_term, hindi_term)
        return translated_text

    def translate_text(self, text, target_language):
        try:
            url = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0"
            headers = {
                "Ocp-Apim-Subscription-Key": self.AZURE_TRANSLATOR_KEY,
                "Ocp-Apim-Subscription-Region": self.AZURE_TRANSLATOR_REGION,
                "Content-Type": "application/json"
            }
            response = requests.post(url, headers=headers, json=[{"text": text}], params={"to": target_language})
            if response.status_code == 200:
                translated = response.json()[0]["translations"][0]["text"]
                translated = self.apply_glossary_replacements(translated)
                logging.info("Translation successful.")
                return translated
            logging.error(f"Translation API error: {response.text}")
            return None
        except Exception as e:
            logging.error(f"Translation failed: {e}")
            return None

    def process_uploaded_document(self, local_path, target_language):
        logging.info(f"Starting document translation: {local_path} -> {target_language}")
        blob_name = self.upload_document_to_blob(local_path)
        if not blob_name:
            return {"error": "Failed to upload document."}

        extracted_text = self.extract_text_from_document(blob_name)
        if not extracted_text:
            return {"error": "Failed to extract text from document."}

        detected_lang = self.detect_language(extracted_text)
        if not detected_lang:
            return {"error": "Failed to detect source language."}

        if detected_lang == target_language:
            logging.info("Document already in target language.")
            return {"message": "Document is already in the target language.", "translated_text": extracted_text}

        translated_text = self.translate_text(extracted_text, target_language)
        return {"source_language": detected_lang, "translated_text": translated_text} if translated_text else {"error": "Translation failed."}
