from langgraph.graph import Graph
from classifier import Classifier
from agents import case_search_agent, verdict_agent, document_generation, perform_action

classifier = Classifier()

workflow = Graph()

workflow.add_node("classifier", classifier.classify_query)
workflow.add_node("case_search_agent", case_search_agent)
workflow.add_node("verdict_agent", verdict_agent)
workflow.add_node("document_generation", document_generation)
workflow.add_node("perform_action", perform_action)

def route_decision(inputs):
    classification, data = inputs
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
