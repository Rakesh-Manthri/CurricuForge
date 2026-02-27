from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['GET'])
def generate_page():
    return render_template('generate.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/generate', methods=['POST'])
def generate_curriculum():
    """
    Curriculum generation endpoint.
    Receives educational parameters and calls the Ollama Granite model.
    """
    data = request.json

    skill = data.get('skill', '')
    level = data.get('level', 'undergraduate')
    semesters = data.get('semesters', 4)
    hours = data.get('hours', 15)
    goals = data.get('goals', '')
    style = data.get('style', 'balanced')
    industry = data.get('industry', '')
    selected_topics = data.get('selectedTopics', [])
    notes = data.get('notes', '')

    # ------------------------------------------------------------------
    # TODO: Connect to Ollama Granite 3.3 2B
    # Replace this block with actual Ollama API call:
    #
    # import requests as req
    # prompt = build_prompt(skill, level, semesters, hours, industry)
    # response = req.post('http://localhost:11434/api/generate', json={
    #     "model": "granite3.3:2b",
    #     "prompt": prompt,
    #     "stream": False
    # })
    # ai_output = response.json().get('response', '')
    # ------------------------------------------------------------------

    return jsonify({
        "status": "success",
        "skill": skill,
        "level": level,
        "semesters": semesters,
        "hours": hours,
        "industry": industry,
        "selected_topics": selected_topics,
        "message": f"Granite 3.3 2B is ready to generate a {semesters}-semester {level} curriculum for '{skill}'. Connect Ollama to activate AI generation."
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
