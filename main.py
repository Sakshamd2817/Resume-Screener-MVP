from fastapi import FastAPI, UploadFile, File, Depends
from pydantic import BaseModel
import os
import shutil
import fitz
import json
from sentence_transformers import SentenceTransformer, util
import torch
from fastapi import Form
# ------------------------
# Job Description Input
# ------------------------
class JobInput(BaseModel):
    description: str
    education: str
    min_exp: int
    skills: str

# ------------------------
# Folder Setup
# ------------------------
os.makedirs("code", exist_ok=True)
os.makedirs("jsons", exist_ok=True)

# ------------------------
# FastAPI App Init
# ------------------------
app = FastAPI()

# ------------------------
# Helper: Text Chunking
# ------------------------
def chunk_text(text, max_words=250):
    words = text.split()
    return [' '.join(words[i:i + max_words]) for i in range(0, len(words), max_words)]

# ------------------------
# Upload Endpoint
# ------------------------
@app.post("/resume/")
async def upload_file(
    files: list[UploadFile] = File(...),
    description: str = Form(...),
    education: str = Form(...),
    min_exp: int = Form(...),
    skills: str = Form(...)
):
    query_text = f"{description}, Education: {education}, Min Exp: {min_exp}, Skills: {skills}"
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Convert job description to embedding
    query_text = f"{description}, Education: {education}, Min Exp: {min_exp}, Skills: {skills}"
    job_embedding = model.encode(query_text, convert_to_tensor=True, normalize_embeddings=True)

    results = []

    for file in files:
        file_location = f"code/{file.filename}"
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Extract PDF text
        text = ""
        doc = fitz.open(file_location)
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text += page.get_text()
        doc.close()

        # Save extracted text
        json_path = f"jsons/{file.filename}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"filename": file.filename, "content": text}, f, indent=4)

        # Chunk + Embed
        chunks = chunk_text(text, max_words=250)
        chunk_embeddings = [model.encode(chunk, convert_to_tensor=True, normalize_embeddings=True) for chunk in chunks]
        resume_embedding = torch.stack(chunk_embeddings).mean(dim=0)

        # Cosine similarity
        similarity_score = util.pytorch_cos_sim(resume_embedding, job_embedding).item()
        eligibility = "✅ Candidate is eligible" if similarity_score > 0.65 else "❌ Candidate is not eligible"

        results.append({
            "filename": file.filename,
            "similarity": round(similarity_score, 4),
            "eligibility": eligibility
        })

    return {
        "message": "Resumes processed successfully.",
        "results": results
    }
