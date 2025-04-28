import requests
import os
from casesearch import CaseSearch
from summarisation import Summarisation
from verdict import Verdict
from translate import Translate
from formatter import Formatter
from utils import Utils
from classifier import Classifier
from llm import LLM

def case_search_agent(data):
    if isinstance(data, tuple):
        data = data[0]
    if isinstance(data, str):
        data = {"user_input": data}

    query = data.get("user_input", "")

    case_search = CaseSearch()
    return case_search.search_cases(query)

def verdict_agent(data):
    if isinstance(data, dict):
        case_input = data.get("user_input", "")
    else:
        case_input = data 

    verdict_search = Verdict()
    return verdict_search.process_case(case_input)

def document_generation(inputs):

    data = inputs[1] if isinstance(inputs, tuple) else inputs
    user_query = data.get("user_input", "").strip()

    formatter = Formatter()
    llm = LLM()
    gen_llm = llm.initialize_gen_llm()
    document_type = formatter.classify_document_type(user_query)
    template_path = formatter.fetch_template_from_blob(document_type)
    placeholders = formatter.extract_placeholders(template_path)
    extraction_prompt = formatter.generate_extraction_prompt(user_query, document_type, placeholders)
    response = gen_llm.invoke([{"role": "user", "content": extraction_prompt}])
    extracted_data =formatter. extract_json_from_response(response.content.strip())
    final_doc_path = formatter.fill_document_with_gpt(template_path, extracted_data)
    return {"document_path": final_doc_path}

def perform_action(inputs):

    utils = Utils()
    data = inputs[1] if isinstance(inputs, tuple) else inputs
    user_query = data.get("user_input", "").strip()
    file_name = utils.get_most_recent_blob()
    sas_url = utils.generate_sas_url(file_name)
    response = requests.get(sas_url)

    if response.status_code != 200:
        return {"error": "Failed to download blob using SAS URL."}

    file_path = os.path.join("/tmp", file_name)
    with open(file_path, "wb") as f:
        f.write(response.content)

    try:
        summarisation = Summarisation()
        translate = Translate()
        classifier = Classifier()
        if "summarize" in user_query.lower() or "summarise" in user_query.lower():
            return summarisation.extract_summary(file_path, file_name)
        elif "translate" in user_query.lower():
            target_lang = classifier.extract_language_code(user_query)
            return translate.process_uploaded_document(local_path=file_path, target_language=target_lang)
        else:
            return {"error": "Invalid query. Please include 'summarize' or 'translate to <language>'."}
    finally:
        os.remove(file_path)
