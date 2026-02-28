from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import re
from typing import List, Optional
import os
import io
import httpx
from agents import run_agentic_generation
from database import (
    init_db, save_curriculum, get_curriculum, list_curricula, close_pool,
    create_user, authenticate_user, create_session, get_user_by_token, delete_session
)
from pdf_generator import generate_curriculum_pdf

# Get the absolute path to the directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(title="CurricuForge API")

# Setup static files and templates
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATE_DIR)


# ── Disable browser cache for static files (dev) ─────────────────────
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class NoCacheStaticMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheStaticMiddleware)


# ── Lifecycle events ─────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    await init_db()

@app.on_event("shutdown")
async def shutdown():
    await close_pool()


# ── Request model ────────────────────────────────────────────────────
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


# ── Page routes ──────────────────────────────────────────────────────
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

@app.get("/analysis", response_class=HTMLResponse)
async def analysis_page(request: Request):
    return templates.TemplateResponse("analysis.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/signin", response_class=HTMLResponse)
async def signin_page(request: Request):
    return templates.TemplateResponse("signin.html", {"request": request})


# ── Auth API endpoints ─────────────────────────────────────────────────
class SignUpRequest(BaseModel):
    full_name: str
    email: str
    password: str

class SignInRequest(BaseModel):
    email: str
    password: str

@app.post("/api/auth/signup")
async def api_signup(data: SignUpRequest):
    if not data.full_name.strip() or not data.email.strip() or not data.password.strip():
        raise HTTPException(status_code=400, detail="All fields are required.")
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    user_id = await create_user(data.full_name.strip(), data.email.strip(), data.password)
    if not user_id:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    # Auto sign-in after signup
    token = await create_session(user_id)
    response = JSONResponse({
        "status": "success",
        "user": {"id": user_id, "full_name": data.full_name.strip(), "email": data.email.strip()}
    })
    response.set_cookie(
        key="cf_session", value=token, httponly=True,
        max_age=7*24*3600, samesite="lax"
    )
    return response

@app.post("/api/auth/signin")
async def api_signin(data: SignInRequest):
    user = await authenticate_user(data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = await create_session(user['id'])
    response = JSONResponse({
        "status": "success",
        "user": user
    })
    response.set_cookie(
        key="cf_session", value=token, httponly=True,
        max_age=7*24*3600, samesite="lax"
    )
    return response

@app.post("/api/auth/signout")
async def api_signout(request: Request):
    token = request.cookies.get("cf_session")
    if token:
        await delete_session(token)
    response = JSONResponse({"status": "signed_out"})
    response.delete_cookie("cf_session")
    return response

@app.get("/api/auth/me")
async def api_current_user(request: Request):
    token = request.cookies.get("cf_session")
    if not token:
        return {"user": None}
    user = await get_user_by_token(token)
    return {"user": user}


# ── Chat endpoint for curriculum Q&A ─────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    curriculum_context: str
    chat_history: List[dict] = []

@app.post("/api/chat")
async def chat_with_curriculum(data: ChatRequest):
    """Chat with the AI about the generated curriculum."""
    try:
        from langchain_ollama import ChatOllama
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatOllama(model="granite3.3:2b", temperature=0.4)

        system_prompt = f"""You are a helpful academic advisor for the CurricuForge platform.
You have full knowledge of the following curriculum that was generated for a student:

{data.curriculum_context}

Your job:
- Answer questions about the curriculum clearly and helpfully
- Explain courses, topics, and learning paths in detail
- Suggest modifications if asked (explain what to change and why)
- Be encouraging, professional, and specific
- If the user asks to modify the curriculum, describe the changes in detail

Keep responses concise but informative (2-4 paragraphs max)."""

        # Build message history
        messages = [SystemMessage(content=system_prompt)]
        for msg in data.chat_history[-6:]:  # Keep last 6 messages for context
            if msg.get('role') == 'user':
                messages.append(HumanMessage(content=msg['content']))
            else:
                from langchain_core.messages import AIMessage
                messages.append(AIMessage(content=msg['content']))

        messages.append(HumanMessage(content=data.message))

        response = await llm.ainvoke(messages)

        return {"reply": response.content}
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

# ══════════════════════════════════════════════════════════════════════
#  PROMPT BUILDER
# ══════════════════════════════════════════════════════════════════════
def build_prompt(skill, level, semesters, hours, industry, goals, style, selected_topics, notes):
    # Start with core instructions
    prompt_parts = [
        f"You are an expert curriculum designer. Create a comprehensive {semesters}-semester curriculum for '{skill}' at a {level} level.",
        f"First, identify ALL individual courses needed to master '{skill}', then distribute them evenly across {semesters} semesters (3-4 courses per semester)."
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
        parameters.append("Key Topics to Include: General core topics")
    if notes:
        parameters.append(f"Additional Context: {notes}")

    if parameters:
        prompt_parts.append("\nParameters:")
        for param in parameters:
            prompt_parts.append(f"- {param}")

    # Strict formatting instructions
    prompt_parts.append("\nYour response MUST follow this EXACT structure for automated parsing. DO NOT include any conversational text or extra information outside these tags:")

    prompt_parts.append("\n<<OVERVIEW>>")
    prompt_parts.append("A professional, encouraging summary of the entire curriculum (max 3 sentences).")

    for i in range(1, semesters + 1):
        prompt_parts.append(f"\n<<SEMESTER {i}>>")
        prompt_parts.append(f"TITLE: (Descriptive theme for semester {i})")
        prompt_parts.append("")
        prompt_parts.append("COURSE: (Course name)")
        prompt_parts.append("CREDITS: (Number of credits)")
        prompt_parts.append("DURATION: (Number of weeks)")
        prompt_parts.append("TOPICS: (At least 5 specific topics, comma separated)")
        prompt_parts.append("DESCRIPTION: (2-3 sentences explaining what students learn)")
        prompt_parts.append("")
        prompt_parts.append("COURSE: (Next course name)")
        prompt_parts.append("CREDITS: (Number of credits)")
        prompt_parts.append("DURATION: (Number of weeks)")
        prompt_parts.append("TOPICS: (At least 5 specific topics, comma separated)")
        prompt_parts.append("DESCRIPTION: (2-3 sentences explaining what students learn)")
        prompt_parts.append("")
        prompt_parts.append("COURSE: (Third course name)")
        prompt_parts.append("CREDITS: (Number of credits)")
        prompt_parts.append("DURATION: (Number of weeks)")
        prompt_parts.append("TOPICS: (At least 5 specific topics, comma separated)")
        prompt_parts.append("DESCRIPTION: (2-3 sentences explaining what students learn)")

    prompt_parts.append("\nRules:")
    prompt_parts.append("- Each semester MUST have 3-4 courses")
    prompt_parts.append("- Each course MUST have at least 5 specific topics")
    prompt_parts.append("- Include credits and duration for every course")
    prompt_parts.append("- Maintain logical progression from foundational to advanced")
    prompt_parts.append("- Keep the tone educational, professional, and industry-aligned.")

    return "\n".join(prompt_parts)


# ══════════════════════════════════════════════════════════════════════
#  PARSER — Robust parser that handles multiple AI output formats
# ══════════════════════════════════════════════════════════════════════
def parse_curriculum_output(ai_output: str) -> dict:
    """
    Robust parser that handles various AI output formats:
    - <<OVERVIEW>> / <<SEMESTER N>> with COURSE: blocks
    - <<SEMESTER_N>> with COURSE: blocks
    - Fallback TOPICS/DETAILS format
    """
    parsed = {
        "summary": "Curriculum successfully generated.",
        "semesters": []
    }

    # Clean markdown artifacts
    cleaned = re.sub(r'\*\*', '', ai_output)
    cleaned = re.sub(r'#{1,3}\s*', '', cleaned)  # Remove markdown headers

    print(f"[PARSER] Raw output length: {len(ai_output)} chars")

    # ── Try to find OVERVIEW ─────────────────────────────────────
    # Try multiple overview formats
    for pattern in [
        r'<<\s*OVERVIEW\s*>>(.*?)(?=<<|$)',
        r'<<\s*PROGRAM_OVERVIEW\s*>>(.*?)(?=<<|$)',
        r'Overview[:\s]*(.*?)(?=<<|Semester|\n\n)',
    ]:
        overview_m = re.search(pattern, cleaned, re.DOTALL | re.IGNORECASE)
        if overview_m and overview_m.group(1).strip():
            parsed["summary"] = overview_m.group(1).strip()
            break

    # ── Try to find SEMESTERS ────────────────────────────────────
    # Pattern 1: <<SEMESTER N>> (with space)
    # Pattern 2: <<SEMESTER_N>> (with underscore)
    semester_pattern = r'<<\s*SEMESTER[\s_]+(\d+)\s*>>'
    semester_blocks = re.split(r'(?=' + semester_pattern + r')', cleaned, flags=re.IGNORECASE)

    semester_data = {}

    for block in semester_blocks:
        sem_match = re.search(semester_pattern, block, re.IGNORECASE)
        if not sem_match:
            continue

        num = int(sem_match.group(1))
        # Remove the semester tag
        content = re.sub(semester_pattern, '', block, count=1, flags=re.IGNORECASE).strip()
        # Remove closing tags
        content = re.sub(r'<<\s*/?\s*SEMESTER[\s_]*\d*\s*>>', '', content, flags=re.IGNORECASE).strip()

        # Extract title - try multiple patterns
        title = f"Semester {num}"
        for title_pat in [
            r'(?:SEMESTER_)?TITLE\s*:\s*(.*?)(?=\n)',
            r'^([A-Z][^\n]{5,60})(?=\n)',  # First line if it looks like a title
        ]:
            title_m = re.search(title_pat, content, re.IGNORECASE | re.MULTILINE)
            if title_m and title_m.group(1).strip():
                title = title_m.group(1).strip()
                break

        # ── Extract COURSE blocks ────────────────────────────────
        courses = []

        # Try Pattern 1: COURSE: blocks (our preferred format)
        course_splits = re.split(r'(?=(?:^|\n)\s*COURSE\s*:)', content, flags=re.IGNORECASE)

        for cb in course_splits:
            course_name_m = re.search(r'COURSE\s*:\s*(.*?)(?=\n|$)', cb, re.IGNORECASE)
            if not course_name_m:
                continue

            course_name = course_name_m.group(1).strip()
            if not course_name or len(course_name) < 3:
                continue

            # Credits
            credits_m = re.search(r'CREDITS?\s*:\s*(\d+)', cb, re.IGNORECASE)
            credits = int(credits_m.group(1)) if credits_m else 3

            # Duration
            duration_m = re.search(r'DURATION\s*:\s*(\d+)', cb, re.IGNORECASE)
            duration = int(duration_m.group(1)) if duration_m else 15

            # Topics
            topics = []
            topics_m = re.search(r'TOPICS?\s*:\s*(.*?)(?=\n\s*(?:DESCRIPTION|COURSE|OUTCOME|ASSESS|<<)|$)', cb, re.DOTALL | re.IGNORECASE)
            if topics_m:
                topics_raw = topics_m.group(1).strip()
                for t in re.split(r'[,;\n]', topics_raw):
                    cleaned_t = re.sub(r'^\s*[\d.\-•*]+\s*', '', t).strip()
                    if cleaned_t and len(cleaned_t) > 2 and len(cleaned_t) < 150:
                        topics.append(cleaned_t)

            # Description
            desc = ""
            desc_m = re.search(r'DESCRIPTION\s*:\s*(.*?)(?=\n\s*(?:COURSE|<<)|$)', cb, re.DOTALL | re.IGNORECASE)
            if desc_m:
                desc = desc_m.group(1).strip()

            courses.append({
                "name": course_name,
                "credits": credits,
                "duration": duration,
                "topics": topics,
                "description": desc
            })

        # Try Pattern 2: <<COURSE_N>> blocks
        if not courses:
            course_tag_splits = re.split(r'(?=<<\s*COURSE_\d+\s*>>)', content, flags=re.IGNORECASE)
            for cb in course_tag_splits:
                tag_m = re.search(r'<<\s*COURSE_\d+\s*>>', cb, re.IGNORECASE)
                if not tag_m:
                    continue
                cb_clean = re.sub(r'<<\s*/?COURSE_\d+\s*>>', '', cb, flags=re.IGNORECASE).strip()

                c_title_m = re.search(r'TITLE\s*:\s*(.*?)(?=\n)', cb_clean, re.IGNORECASE)
                c_credits_m = re.search(r'CREDITS?\s*:\s*(\d+)', cb_clean, re.IGNORECASE)
                c_duration_m = re.search(r'DURATION\s*:\s*(\d+)', cb_clean, re.IGNORECASE)

                topics = []
                topics_section = re.search(r'TOPICS?\s*:\s*(.*?)(?=\n\s*(?:OUTCOME|ASSESS|DESCRIPTION|<<)|$)', cb_clean, re.DOTALL | re.IGNORECASE)
                if topics_section:
                    for line in re.split(r'[,;\n]', topics_section.group(1)):
                        cleaned_t = re.sub(r'^\s*[\d.\-•*]+\s*', '', line).strip()
                        if cleaned_t and len(cleaned_t) > 2:
                            topics.append(cleaned_t)

                desc_m = re.search(r'(?:DESCRIPTION|OUTCOMES?)\s*:\s*(.*?)(?=\n\s*(?:ASSESS|<<|COURSE)|$)', cb_clean, re.DOTALL | re.IGNORECASE)

                courses.append({
                    "name": c_title_m.group(1).strip() if c_title_m else "Untitled Course",
                    "credits": int(c_credits_m.group(1)) if c_credits_m else 3,
                    "duration": int(c_duration_m.group(1)) if c_duration_m else 15,
                    "topics": topics,
                    "description": desc_m.group(1).strip() if desc_m else ""
                })

        # Fallback Pattern 3: Old TOPICS/DETAILS format (no courses)
        if not courses:
            topics_m = re.search(r'TOPICS?\s*:\s*(.*?)(?=\nDETAILS|\nDESCRIPTION|\n<<|$)', content, re.DOTALL | re.IGNORECASE)
            details_m = re.search(r'(?:DETAILS|DESCRIPTION)\s*:\s*([\s\S]*?)(?=\n<<|$)', content, re.IGNORECASE)
            topics_str = topics_m.group(1).strip() if topics_m else ""
            details = details_m.group(1).strip() if details_m else ""
            topics = [t.strip() for t in re.split(r'[,\n;]', topics_str) if t.strip() and len(t.strip()) > 2]
            courses.append({
                "name": title,
                "credits": 3,
                "duration": 15,
                "topics": topics,
                "description": details
            })

        semester_data[num] = {
            "number": num,
            "title": title,
            "courses": courses
        }

    # Sort and add semesters
    for i in sorted(semester_data.keys()):
        parsed["semesters"].append(semester_data[i])

    print(f"[PARSER] Found {len(parsed['semesters'])} semesters, summary length: {len(parsed['summary'])}")
    for sem in parsed["semesters"]:
        print(f"[PARSER]   Semester {sem['number']}: {sem['title']} — {len(sem['courses'])} courses")

    return parsed


# ── Generation endpoint ──────────────────────────────────────────────
@app.post("/generate")
async def generate_curriculum(data: CurriculumRequest, request: Request):
    """
    Agentic Curriculum generation endpoint.
    Uses a multi-agent LangGraph workflow (Planner -> Detailer -> Reviewer).
    Saves to SQLite.
    """
    try:
        input_payload = data.dict()

        # Build the prompt
        full_prompt = build_prompt(
            data.skill, data.level, data.semesters, data.hours,
            data.industry, data.goals, data.style, data.selectedTopics, data.notes
        )

        # Pass the prompt along with the input data
        input_payload['full_prompt'] = full_prompt

        # Execute the multi-agent graph
        result = await run_agentic_generation(input_payload)

        # Extract outputs
        ai_output = result['details']['raw_text']
        plan = result.get('plan', '')
        review_result = result.get('review_result', 'No review available')

        print(f"--- AGENT PLAN ---\n{plan}")
        print(f"--- AGENT REVIEW ---\n{review_result}")
        print(f"--- DETAILED OUTPUT (first 2000 chars) ---\n{ai_output[:2000]}")

        # Parse the structured text
        structured_curriculum = parse_curriculum_output(ai_output)

        # Save to SQLite (with user_id if logged in)
        db_id = None
        user_id = None
        token = request.cookies.get("cf_session")
        if token:
            user = await get_user_by_token(token)
            if user:
                user_id = user['id']
        try:
            db_id = await save_curriculum(input_payload, structured_curriculum, plan, review_result, ai_output, user_id=user_id)
        except Exception as db_err:
            print(f"[DB] Save failed (non-critical): {db_err}")

        return {
            "status": "success",
            "skill": data.skill,
            "level": data.level,
            "semesters": data.semesters,
            "curriculum": structured_curriculum,
            "agent_review": review_result,
            "db_id": db_id
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Agent Workflow Error: {str(e)}")


# ── History page & endpoints ────────────────────────────────────────
@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})

@app.get("/api/curricula")
async def api_list_curricula(request: Request):
    """Get recent generated curricula for the logged-in user."""
    user_id = None
    token = request.cookies.get("cf_session")
    if token:
        user = await get_user_by_token(token)
        if user:
            user_id = user['id']
    items = await list_curricula(limit=50, user_id=user_id)
    return {"curricula": items}

@app.get("/api/curricula/{curriculum_id}")
async def api_get_curriculum(curriculum_id: int):
    """Get a specific stored curriculum."""
    result = await get_curriculum(curriculum_id)
    if not result:
        raise HTTPException(status_code=404, detail="Curriculum not found")
    return result


# ── PDF Export endpoint ──────────────────────────────────────────────
class PDFExportRequest(BaseModel):
    curriculum: dict
    params: dict

@app.post("/export-pdf")
async def export_pdf(data: PDFExportRequest):
    """Generate and return a PDF of the curriculum."""
    try:
        pdf_bytes = generate_curriculum_pdf(data.curriculum, data.params)
        skill_name = data.params.get('skill', 'curriculum').replace(' ', '_')
        filename = f"CurricuForge_{skill_name}.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")
