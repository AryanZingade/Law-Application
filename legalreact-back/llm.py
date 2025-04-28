from langchain_openai import AzureChatOpenAI
import os
import openai

class LLM:

    def __init__(self):
        self.AZURE_ENDPOINT = os.getenv("OPENAI_GPT_ENDPOINT")
        self.OPENAI_API_KEY = os.getenv("OPENAI_GPT_API_KEY")

        self.AZURE_OPENAI_ENDPOINT = os.getenv("EMBEDDING_API_ENDPOINT")
        self.AZURE_OPENAI_KEY = os.getenv("EMBEDDING_API_KEY")
        self.AZURE_OPENAI_MODEL = "text-embedding-ada-002"
        self.AZURE_OPENAI_VERSION = os.getenv("EMBEDDING_API_VERSION")

    def initialize_emb_llm(self):
        return openai.AzureOpenAI(
        api_key=self.AZURE_OPENAI_KEY,
        api_version=self.AZURE_OPENAI_VERSION,
        azure_endpoint=self.AZURE_OPENAI_ENDPOINT
    )

    def initialize_gen_llm(self):
        return AzureChatOpenAI(
        azure_deployment="gpt-4o-mini",
        azure_endpoint=self.AZURE_ENDPOINT,
        api_key=self.OPENAI_API_KEY,
        api_version="2024-10-21",
        temperature=0.2
    )