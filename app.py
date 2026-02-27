from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import os
import httpx

# Get the absolute path to the directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(title="CurricuForge API")

# Setup static files and templates
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

class CurriculumRequest(BaseModel):
    skill: str
    level: str = "undergraduate"
    semesters: int = 4
    hours: int = 15
    goals: Optional[str] = ""
    style: Optional[str] = "balanced"
    industry: Optional[str] = ""
    selectedTopics: List[str] = []
    notes: Optional[str] = ""

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/generate", response_class=HTMLResponse)
async def generate_page(request: Request):
    return templates.TemplateResponse("generate.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

def build_prompt(skill, level, semesters, hours, industry, goals, style, selected_topics, notes):
    prompt = f"""
    You are an expert curriculum designer. Create a comprehensive {semesters}-semester curriculum for '{skill}' at a {level} level.
    
    Parameters:
    - Weekly Commitment: {hours} hours
    - Industry Focus: {industry}
    - Learning Goals: {goals}
    - Instructional Style: {style}
    - Key Topics to Include: {', '.join(selected_topics) if selected_topics else 'General core topics'}
    - Additional Context: {notes}

    Format the response as a professional summary followed by a clear breakdown of topics for each of the {semesters} semesters. 
    Keep the tone educational and encouraging.
    """
    return prompt

@app.post("/generate")
async def generate_curriculum(data: CurriculumRequest):
    """
    Curriculum generation endpoint.
    Receives educational parameters and calls the Ollama Granite model.
    """
    prompt = build_prompt(
        data.skill, data.level, data.semesters, data.hours, 
        data.industry, data.goals, data.style, data.selectedTopics, data.notes
    )
    
    async with httpx.AsyncClient() as client:
        try:
            # Calling local Ollama instance with the granite3.3:3b model
            response = await client.post(
                'http://localhost:11434/api/generate', 
                json={
                    "model": "granite3.3:2b",
                    "prompt": prompt,
                    "stream": False
                }, 
                timeout=120.0
            )
            
            response.raise_for_status()
            ai_output = response.json().get('response', 'No response from model.')

            return {
                "status": "success",
                "skill": data.skill,
                "level": data.level,
                "semesters": data.semesters,
                "message": ai_output
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ollama Error: {str(e)}")
