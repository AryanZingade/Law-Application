import os
import json
import logging
from datetime import datetime, timedelta
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from langchain.schema import SystemMessage, HumanMessage
from langchain_openai import AzureChatOpenAI
from llm import LLM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Summarisation:

    def __init__(self):
        self.AZURE_BLOB_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.AZURE_BLOB_CONTAINER = os.getenv("AZURE_CONTAINER_NAME")
        self.AZURE_BLOB_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
        self.AZURE_FORM_RECOGNIZER_ENDPOINT = os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT")
        self.AZURE_FORM_RECOGNIZER_KEY = os.getenv("AZURE_DOC_INTELLIGENCE_KEY")

        logger.info("Connecting to Azure Blob Storage...")
        self.blob_service_client = BlobServiceClient(
            account_url=f"https://{self.AZURE_BLOB_ACCOUNT}.blob.core.windows.net",
            credential=self.AZURE_BLOB_KEY
        )
        self.container_client = self.blob_service_client.get_container_client(self.AZURE_BLOB_CONTAINER)

        self.llm = LLM()
        self.gen_llm = self.llm.initialize_gen_llm()

    def get_latest_contract(self):
        try:
            logger.info("Fetching available blobs..")
            blobs = list(self.container_client.list_blobs())
            if not blobs:
                logger.warning("No blobs found in the container.")
                return None, "No contract files found in Azure Blob Storage."

            latest_blob = max(blobs, key=lambda x: x.last_modified)
            logger.info(f"Latest blob found: {latest_blob.name}")
            return latest_blob.name, None
        except Exception as e:
            logger.exception("Error fetching latest contract from Azure Blob Storage.")
            return None, str(e)

    def generate_sas_url(self, blob_name):
        try:
            logger.info(f"Generating SAS URL for blob: {blob_name}")
            sas_token = generate_blob_sas(
                account_name=self.AZURE_BLOB_ACCOUNT,
                container_name=self.AZURE_BLOB_CONTAINER,
                blob_name=blob_name,
                account_key=self.AZURE_BLOB_KEY,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=1)
            )
            sas_url = f"https://{self.AZURE_BLOB_ACCOUNT}.blob.core.windows.net/{self.AZURE_BLOB_CONTAINER}/{blob_name}?{sas_token}"
            logger.info("SAS URL generated successfully.")
            return sas_url
        except Exception as e:
            logger.exception("Failed to generate SAS URL.")
            raise e

    def extract_summary(self, file_path, file_name):
        try:
            logger.info(f"Extracting summary for file: {file_name}")
            blob_url = self.generate_sas_url(file_name)
            
            client = DocumentAnalysisClient(
                self.AZURE_FORM_RECOGNIZER_ENDPOINT,
                AzureKeyCredential(self.AZURE_FORM_RECOGNIZER_KEY)
            )
            poller = client.begin_analyze_document_from_url("prebuilt-layout", blob_url)
            result = poller.result()

            extracted_text = "\n".join([line.content for page in result.pages for line in page.lines])
            logger.info("Document text extracted successfully.")

            prompt = f"""
            Extract key legal details from the following contract text:
            
            **Contract Text:**
            {extracted_text}
            
            Return the result as a JSON object with keys: "parties", "dates", "financial_terms", "confidentiality", "termination", "governing_law".
            """
            messages = [
                SystemMessage(content="You are a legal document assistant."),
                HumanMessage(content=prompt)
            ]

            logger.info("Sending prompt to LLM...")
            try:
                response = self.gen_llm.invoke(messages)
            except Exception as e:
                logger.exception("Error calling LLM")
                return {"error": "LLM call failed: " + str(e)}

            raw_response = response.content.strip()

            if raw_response.startswith("```json"):
                raw_response = raw_response[7:]
            if raw_response.endswith("```"):
                raw_response = raw_response[:-3]

            try:
                parsed_response = json.loads(raw_response)
                logger.info("LLM response parsed successfully.")
                return parsed_response
            except json.JSONDecodeError:
                logger.error("Failed to parse LLM response as JSON.")
                return {"error": "Failed to parse response from GPT."}

        except Exception as e:
            logger.exception("Error occurred during document summary extraction.")
            return {"error": str(e)}
