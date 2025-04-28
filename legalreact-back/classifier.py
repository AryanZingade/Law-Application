from llm import LLM

class Classifier:

    def __init__(self):
        self.llm = LLM()
        self.gen_llm = self.llm.initialize_gen_llm()
        
    def classify_query(self, data):
        user_input = data.get("user_input", "").strip()
        if not user_input:
            return "unknown", data

        prompt = f"""
        Classify the following user query:
        - "case_search" if searching for similar legal cases.
        - "verdict_prediction" if seeking a verdict prediction.
        - "document_generation" if query is regarding any kind of drafting or creation of a document.
        - "perform_action" if the query is regarding summarizing or translating a document.
        
        Query: \"{user_input}\"
        Output (case_search or verdict_prediction or document_generation or perform_action):
        """
        
        response = self.gen_llm.invoke(prompt) 
        classification = response.content.strip().lower()
        return classification if classification in ["case_search", "verdict_prediction", "document_generation", "perform_action"] else "unknown", data

    def extract_language_code(self, user_query):
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
        response = self.gen_llm.invoke(prompt)
        return response.content.strip().lower()
