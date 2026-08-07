from flask import Flask, request, jsonify
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import operator

load_dotenv()

app = Flask(__name__)

# -------------------------
# LLM
# -------------------------

llm_model = ChatGroq(
    model="llama-3.3-70b-versatile"
)

# -------------------------
# STRUCTURED OUTPUT
# -------------------------

class EvaluationSchema(BaseModel):
    feedback: str = Field(description="Feedback")
    score: int = Field(description="Score", ge=0, le=10)

structured_model = llm_model.with_structured_output(EvaluationSchema)

# -------------------------
# STATE
# -------------------------

class ContentState(TypedDict, total=False):
    content: str
    language_feedback: str
    examples_feedback: str
    advantages_feedback: str
    overall_feedback: str
    individual_score: Annotated[list[int], operator.add]
    avg_score: float

# -------------------------
# COMMON EVALUATION
# -------------------------

def run_evaluation(criteria, content):

    prompt = f"""
    Evaluate this content based on:
    {criteria}

    Return:
    1. Feedback
    2. Score out of 10

    Content:
    {content}
    """

    return structured_model.invoke(prompt)

# -------------------------
# NODES
# -------------------------

def evaluate_language(state):

    output = run_evaluation(
        "Language quality, grammar, readability",
        state["content"]
    )

    return {
        "language_feedback": output.feedback,
        "individual_score": [output.score]
    }

def evaluate_examples(state):

    output = run_evaluation(
        "Examples and use cases",
        state["content"]
    )

    return {
        "examples_feedback": output.feedback,
        "individual_score": [output.score]
    }

def evaluate_advantages(state):

    output = run_evaluation(
        "Advantages and limitations",
        state["content"]
    )

    return {
        "advantages_feedback": output.feedback,
        "individual_score": [output.score]
    }

def final_evaluation(state):

    prompt = f"""
    Summarize these feedbacks:

    Language:
    {state["language_feedback"]}

    Examples:
    {state["examples_feedback"]}

    Advantages:
    {state["advantages_feedback"]}
    """

    overall_feedback = llm_model.invoke(prompt).content

    avg_score = (
        sum(state["individual_score"])
        / len(state["individual_score"])
    )

    return {
        "overall_feedback": overall_feedback,
        "avg_score": avg_score
    }

# -------------------------
# LANGGRAPH
# -------------------------

graph = StateGraph(ContentState)

graph.add_node("evaluate language", evaluate_language)
graph.add_node("evaluate examples", evaluate_examples)
graph.add_node("evaluate advantages", evaluate_advantages)
graph.add_node("final evaluation", final_evaluation)

graph.add_edge(START, "evaluate language")
graph.add_edge(START, "evaluate examples")
graph.add_edge(START, "evaluate advantages")

graph.add_edge("evaluate language", "final evaluation")
graph.add_edge("evaluate examples", "final evaluation")
graph.add_edge("evaluate advantages", "final evaluation")

graph.add_edge("final evaluation", END)

workflow = graph.compile()

# -------------------------
# API ROUTE
# -------------------------

@app.route("/generate", methods=["POST"])
def generate():

    data = request.json

    topic = data.get("topic")

    prompt = f"""
    Generate content on {topic}
    with examples, advantages and limitations.
    """

    # Generate content
    content_generated = llm_model.invoke(prompt).content

    # Workflow execution
    initial_state = {
        "content": content_generated,
        "individual_score": []
    }

    final_state = workflow.invoke(initial_state)

    return jsonify({
        "content": content_generated,
        "feedback": final_state["overall_feedback"],
        "score": final_state["avg_score"]
    })

# -------------------------
# RUN
# -------------------------

if __name__ == "__main__":
    app.run(debug=True)

    