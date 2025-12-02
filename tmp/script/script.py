from dotenv import load_dotenv

load_dotenv("../.env")
import os
from typing import TypedDict

from IPython.display import Image, display
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph

os.getenv("LANGSMITH_API_KEY")
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_PROJECT"] = "agent"
os.getenv("GROQ_API_KEY")


class State(TypedDict):
    """Simple state schema for the Q&A graph.

    Keys:
        question: the user's question string
        answer: the model's answer string
    """

    user_input: str
    answer: str


def ayurved(query: str) -> str:
    """answer questions as per ayurved"""
    return "ayurved answer"


def allopathy(query: str) -> str:
    """answer questions as per allopathy"""
    return "allopathy answer"


def not_medical(query: str) -> str:
    """answer questions as per general knowledge"""
    return "general knowledge answer"


tool = [ayurved, allopathy, not_medical]
llm = ChatGroq(
    model="llama-3.3-70b-versatile", api_key=os.environ.get("GROQ_API_KEY"), temperature=0.0
)
llm_with_tools = llm.bind_tools(tool)


def langchain(llm=llm_with_tools):
    input_text = input("Enter your question: ")
    response = llm_with_tools.invoke(f"answer the following question: {input_text}")
    return response

    # Define simple node functions that operate on the shared state.


def medical_query_prompt():
    return """You are a helpful AI assistant that helps people find information is medical queries or not. If the question is medical, output ONLY 'YES'. Otherwise, output ONLY 'NO'."

    Question: {question}
    
    Answer:"""


def input_node(state: State) -> str:
    question = state.get("question")
    if not question:
        return "output"
    # Determine if the question is medical or not
    prompt = medical_query_prompt().format(question=question)
    response = llm.invoke(prompt)
    is_medical = "yes" in response.content.lower()
    print(
        f"[CLASSIFIER]: Question classified as {'MEDICAL' if is_medical else 'NON-MEDICAL'} ({response.content.strip()})"
    )
    if is_medical:
        return "tool"
    else:
        return "output"


def tool_node(state: State) -> dict:
    # Use both ayurved and allopathy tools to answer the medical question in state
    question = state.get("question", "")
    if not question:
        return {"answer": "No question provided."}

    ayurved_prompt = f"Answer the following medical question in the style of Ayurveda, keeping the answer brief but informative: {question}"
    ayurved_answer = llm.invoke(ayurved_prompt).content

    allopathy_prompt = f"Answer the following medical question in the style of Allopathy, keeping the answer brief but informative: {question}"
    allopathy_answer = llm.invoke(allopathy_prompt).content
    combined_answer = (
        f"**Dual Perspective for: '{question}'**\n\n"
        f"----------------------------------------\n"
        f"**Ayurveda:** {ayurved_answer}\n\n"
        f"**Allopathy:** {allopathy_answer}\n"
        f"----------------------------------------"
    )

    # resp = llm_with_tools.invoke(f"answer the following question: {combined_question}")
    return {"answer": combined_answer}


def output_node(state: State) -> dict:
    # Use the model to generate an answer from the question in state
    question = state.get("question")
    if not question:
        return {"answer": "No question provided."}
    # call the provided model's invoke method
    # pass a dict so the model/runtime receives a structured input
    resp = llm.invoke(f"answer the following question: {question}")
    return {"answer": resp.content}


def langgraph(model):
    # Provide a state_schema as required by StateGraph

    graph = StateGraph(State)

    # def start_node(state: State) -> None:
    #     return state

    # Add nodes to the graph. add_node accepts a node name and a callable.
    # graph.add_node("start_node", start_node)
    graph.add_node("tool", tool_node)
    graph.add_node("output", output_node)
    graph.add_conditional_edges(START, input_node, {"tool": "tool", "output": "output"})

    # Wire the nodes together
    # graph.add_edge(START, "start_node")
    # graph.add_conditional_edges(
    #     "start_node", input_node, {True: "tool", False: "output"}
    # )
    graph.add_edge("tool", END)
    graph.add_edge("output", END)

    # Run the graph with the provided question using the compiled graph API
    compiled_graph = graph.compile()
    try:
        image_data = compiled_graph.get_graph().draw_mermaid_png()
        display(Image(image_data))
        # open("graph.png", "wb").write(image_data) # File writing/system calls often fail in environments
        # __import__("os").system("open graph.png")
        print("Graph compiled and visualized successfully.")
    except Exception as e:
        print(f"Graph compiled successfully, but visualization failed: {e}")
    return compiled_graph


if __name__ == "__main__":
    # llm = ChatGroq(
    #     model="llama-3.3-70b-versatile",
    #     api_key=os.environ.get("GROQ_API_KEY"),
    #     temperature=0.0,
    # )
    # langchain_response = langchain()
    # print(langchain_response)
    # # langgraph returns the compiled graph object
    # compiled = langgraph(llm_with_tools)
    # question = input("Enter your question: ")
    # initial_state: SessionState = {"question": question, "answer": ""}
    # response = compiled.invoke(initial_state)
    # print("Final response from graph:", response)
    # 7.1. Run LangChain (optional comparison)
    print("\n--- Running LangChain Tool-Bound Model ---")
    try:
        langchain_response = langchain()
        print("LangChain Response:", langchain_response.content)
    except Exception as e:
        print(f"LangChain execution failed. Ensure GROQ_API_KEY is set. Error: {e}")

    # 7.2. Run LangGraph
    print("\n--- Running LangGraph Q&A System ---")
    compiled = langgraph(llm_with_tools)

    # Get user input for the graph
    question = input(
        "Enter your question for LangGraph (e.g., 'What is the capital of France?' or 'What is a symptom of flu?'): "
    )

    # CRITICAL: Invoke the graph with the initial state
    initial_state: State = {"question": question, "answer": ""}

    try:
        response = compiled.invoke(initial_state)

        # CRITICAL: Print the final answer from the state dictionary
        final_answer = response.get("answer", "No answer found in final state.")
        print("\n--- LangGraph Final Response ---")
        print(f"Question: {response.get('question')}")
        print(f"Answer: {final_answer}")

        # This final state dictionary 'response' is what LangSmith captures as the output,
        # ensuring the 'answer' field is now populated.

    except Exception as e:
        print(f"LangGraph execution failed. Error: {e}")
