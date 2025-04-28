import os
import json
import logging
import re
import pinecone
from langchain_openai import AzureChatOpenAI
from llm import LLM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Verdict:

    def __init__(self):
        self.PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

        self.pc = pinecone.Pinecone(api_key=self.PINECONE_API_KEY)
        self.knowledge_index = self.pc.Index("law-kb")
        self.cases_index = self.pc.Index("past-cases")

        self.llm = LLM()
        self.gen_llm = self.llm.initialize_gen_llm()
        self.emb_llm = self.llm.initialize_emb_llm()


    def extract_case_details(self, case_input):
        prompt = f"""
        Extract key details from the following legal case text:
        - Case Description
        - Involved Parties
        - Jurisdiction
        - Alleged Violations

        Respond in this JSON format:
        {{
            "case_description": "...",
            "involved_parties": "...",
            "jurisdiction": "...",
            "alleged_violations": "..."
        }}

        Case: "{case_input}"
        """
        logger.info("Sending prompt to LLM...")
        try:
            response = self.gen_llm.invoke(prompt)
        except Exception as e:
            logger.exception("Error calling LLM")
            return {"error": "LLM call failed: " + str(e)}
        
        raw_text = response.content.strip()
        raw_text = re.sub(r"^```json\n|\n```$", "", raw_text).strip()

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as e:
            logging.error(f"JSON Decode Error: {e}")
            return {"error": "Invalid JSON format returned by GPT"}

    def generate_embeddings(self, text):
        try:
            response = self.emb_llm.embeddings.create(model="text-embedding-ada-002", input=text)
            return response.data[0].embedding
        except Exception as e:
            logging.error(f"Failed to generate embeddings: {e}")
            return None

    def search_pinecone(self, index, query_embedding, top_k=5):
        try:
            results = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
            return results.matches if results.matches else []
        except Exception as e:
            logging.error(f"Error querying Pinecone: {e}")
            return []

    def get_verdict(self, case_description, relevant_laws, similar_cases):
        prompt = f"""
        A legal case was submitted with the following details:
        Case Description: {case_description}
        Relevant Laws:
        {relevant_laws}
        Similar Past Cases:
        {similar_cases}
        
        Based on the above, predict the most likely verdict and explain why.
        """
        try:
            response = self.gen_llm.invoke(prompt)
            return response.content
        except Exception as e:
            logging.error(f"Verdict generation failed: {e}")
            return None

    def process_case(self, case_input):
        logging.info(f"Received case input")

        case_details = self.extract_case_details(case_input)
        if not case_details or "error" in case_details:
            logging.error("Failed to extract case details")
            return {"error": "Failed to extract case details"}

        case_description = case_details.get("case_description", "No description available")
        logging.info(f"Case Description: {case_description}")

        case_embedding = self.generate_embeddings(case_description)
        if case_embedding is None:
            return {"error": "Failed to generate embeddings"}

        relevant_laws = self.search_pinecone(self.knowledge_index, case_embedding)
        similar_cases = self.search_pinecone(self.cases_index, case_embedding)

        logging.info(f"Found {len(relevant_laws)} relevant laws")
        logging.info(f"Found {len(similar_cases)} similar cases")

        if not relevant_laws:
            return {"error": "No relevant laws found"}

        if not similar_cases:
            return {"error": "No similar cases found"}

        laws_text = "\n".join([f"Title: {law['metadata'].get('title', 'No Title')}" for law in relevant_laws])
        cases_text = "\n".join([f"Title: {case['metadata'].get('title', 'No Title')}\nSummary: {case['metadata'].get('summary_chunk', 'No Summary')}" for case in similar_cases])

        verdict = self.get_verdict(case_description, laws_text, cases_text)
        if verdict is None:
            return {"error": "Verdict generation failed"}

        result = {
            "case_description": case_description,
            "involved_parties": case_details.get("involved_parties", "Unknown parties"),
            "jurisdiction": case_details.get("jurisdiction", "Unknown jurisdiction"),
            "alleged_violations": case_details.get("alleged_violations", "Unknown violations"),
            "verdict": verdict,
            "relevant_laws": laws_text,
            "similar_cases": cases_text
        }

        logging.info("Case processed successfully")
        return result
