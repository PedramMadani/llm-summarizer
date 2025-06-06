from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

from data.text_cleaner import clean_text
from llm.lsa_summarizer import generate_lsa_summary
from llm.ollama_client import generate_llm_summary
from vectorization.vectorizers import vectorize_tfidf, vectorize_bert
from llm.summarize_and_vectorize import summarize_and_vectorize
from xai.lime_explainer import explain_prediction_lime
from xai.shap_explainer import explain_prediction_shap
from models.trainers import load_saved_model

app = FastAPI(
    title="Text Summarization & Vectorization API",
    description="Exposes endpoints for preprocessing, summarization, embedding, and explainability (LIME/SHAP).",
    version="1.0.0"
)


class TextRequest(BaseModel):
    text: str


@app.get("/")
def root():
    return {"message": "Text Processing API is running 🚀"}


# --- Preprocessing ---
@app.post("/preprocess")
def preprocess_text(request: TextRequest):
    cleaned = clean_text(request.text)
    return {"cleaned_text": cleaned}


# --- Summarization ---
@app.post("/summarize/lsa")
def summarize_lsa(request: TextRequest):
    summary = generate_lsa_summary(request.text)
    if not summary:
        raise HTTPException(
            status_code=400, detail="LSA summarization failed.")
    return {"lsa_summary": summary}


@app.post("/summarize/llm")
def summarize_llm(request: TextRequest):
    summary = generate_llm_summary(request.text)
    if not summary:
        raise HTTPException(
            status_code=400, detail="LLM summarization failed.")
    return {"llm_summary": summary}


# --- Vectorization ---
@app.post("/vectorize/tfidf")
def vectorize_tfidf_endpoint(request: TextRequest):
    vectors, _ = vectorize_tfidf([request.text])
    return {"tfidf_vector": vectors.toarray()[0].tolist()}


@app.post("/vectorize/bert")
def vectorize_bert_endpoint(request: TextRequest):
    vectors, _ = vectorize_bert([request.text])
    return {"bert_vector": vectors[0]}


# --- Combined pipeline ---
@app.post("/summarize-and-vectorize")
def summarize_and_vectorize_endpoint(request: TextRequest):
    result = summarize_and_vectorize(request.text)
    return result


# --- Explainability ---
@app.post("/xai/lime")
def explain_with_lime(request: TextRequest):
    model, vectorizer, class_names = load_saved_model()
    explanation = explain_prediction_lime(
        request.text, model, vectorizer, class_names)
    return {"lime_explanation": explanation}


@app.post("/xai/shap")
def explain_with_shap(request: TextRequest):
    model, vectorizer, _ = load_saved_model()
    shap_values = explain_prediction_shap([request.text], model, vectorizer)
    if shap_values is None:
        raise HTTPException(status_code=500, detail="SHAP explanation failed.")
    return {
        "shap_values": shap_values.values.tolist(),
        "base_values": shap_values.base_values.tolist(),
        "data": shap_values.data.tolist()
    }
