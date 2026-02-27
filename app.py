from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import re # Added for regex parsing
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
    # Start with core instructions, emphasizing strict adherence to format and providing an example
    prompt_parts = [
        f"You are an expert curriculum designer. Create a comprehensive {semesters}-semester curriculum for '{skill}' at a {level} level."
    ]

    # Add parameters only if they have values
    parameters = []
    parameters.append(f"Weekly Commitment: {hours} hours")
    if industry:
        parameters.append(f"Industry Focus: {industry}")
    if goals:
        parameters.append(f"Learning Goals: {goals}")
    if style:
        parameters.append(f"Instructional Style: {style}")
    if selected_topics:
        parameters.append(f"Key Topics to Include: {', '.join(selected_topics)}")
    else:
        parameters.append("Key Topics to Include: General core topics") # Always include this line
    if notes:
        parameters.append(f"Additional Context: {notes}")

    if parameters:
        prompt_parts.append("\nParameters:")
        for param in parameters:
            prompt_parts.append(f"- {param}")

    # Add the strict formatting instructions
    #prompt_parts.append("\nFormat the response EXACTLY as follows for clarity and parsing. DO NOT deviate from this structure:")
    prompt_parts.append("\nYour response MUST follow this EXACT structure for automated parsing. DO NOT include any conversational text or extra information outside these tags:")
    prompt_parts.append("\n<<OVERVIEW>>")
    prompt_parts.append("A professional, encouraging summary of the entire curriculum (max 3 sentences).")


    for i in range(1, semesters + 1):
        prompt_parts.append(f"\n<<SEMESTER {i}>>")
        prompt_parts.append(f"TITLE: (Descriptive name for semester {i})")
        prompt_parts.append("TOPICS: (4-6 topics, comma separated)")
        prompt_parts.append("DETAILS: (2-3 sentences explaining learning outcomes)")

    prompt_parts.append("\nKeep the tone educational, professional, and industry-aligned.")

    return "\n".join(prompt_parts)

def parse_curriculum_output(ai_output: str) -> dict:
    """
    Parses the raw AI output string into a structured dictionary.
    Expected format:
    <<OVERVIEW>>
    [Summary Text]
    <<SEMESTER 1>>
    TITLE: [Semester Title]
    TOPICS: [Topic 1], [Topic 2]
    DETAILS: [Learning outcomes]
    ...
    """
    parsed_data = {
        "summary": "Could not parse summary.",
        "semesters": []
    }

    # Extract overview/summary
    # Adjusted regex to be more specific about the end of the overview, looking for the first semester tag
    overview_match = re.search(r'<<OVERVIEW>>\s*(.*?)(?=\n*<<SEMESTER 1>>|\Z)', ai_output, re.DOTALL | re.IGNORECASE) # Corrected from &lt;&lt;OVERVIEW&gt;&gt;
    if overview_match:
        parsed_data["summary"] = overview_match.group(1).strip()
        ai_output = ai_output[overview_match.end():].strip()

    # Extract semesters
    semester_pattern = r'<<SEMESTER (\d+)>>\s*TITLE:\s*(.*?)\s*TOPICS:\s*(.*?)\s*DETAILS:\s*(.*?)(?=\n*<<SEMESTER|\Z)' # Corrected from &lt;&lt;SEMESTER (\d+)&gt;&gt;
    semesters_matches = re.finditer(semester_pattern, ai_output, re.DOTALL | re.IGNORECASE)

    for match in semesters_matches:
        semester_number = int(match.group(1))
        semester_title = match.group(2).strip()
        topics_str = match.group(3).strip()
        details = match.group(4).strip()
        topics = [t.strip() for t in topics_str.split(',') if t.strip()]
        parsed_data["semesters"].append({"number": semester_number, "title": semester_title, "topics": topics, "details": details})

    return parsed_data

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

            print(f"Raw AI Output:\n{ai_output}") # Debugging: Print raw AI output

            # Parse the AI output into a structured format
            structured_curriculum = parse_curriculum_output(ai_output)

            return {
                "status": "success",
                "skill": data.skill,
                "level": data.level,
                "semesters": data.semesters,
                "curriculum": structured_curriculum # Send structured data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ollama Error: {str(e)}")
