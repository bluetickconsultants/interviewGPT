from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_cors import CORS
from openai import OpenAI
import re
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///response_cache.db'
db = SQLAlchemy(app)
load_dotenv()
CORS(app)


client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
)


# Define the ResponseCache model
class ResponseCache(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    skills = db.Column(db.JSON, nullable=False)
    soft_skills = db.Column(db.JSON, nullable=False)
    technical_skills = db.Column(db.JSON, nullable=False)

    def __init__(self, name, skills, soft_skills, technical_skills):
        self.name = name
        self.skills = skills
        self.soft_skills = soft_skills
        self.technical_skills = technical_skills


# Create the database tables
with app.app_context():
    db.create_all()


def extract_question_and_answer(text):
    """
    Extracts and returns question, answer, and type from a given text.
    Returns None for each if no match is found.
    """

    result = {}
    keywords = ["Question", "Answer", "Keywords", "Type"]

    for keyword in keywords:
        pattern = re.compile(
            rf'{keyword}:(.*?)(?=\b(?:{"|".join(keywords)})|$)', re.DOTALL | re.IGNORECASE)
        match = pattern.search(text)

        if match:
            result[keyword] = match.group(1).strip()
        else:
            result[keyword] = None

    return result["Question"], result["Answer"], result["Keywords"], result["Type"]


def ask_question(skill, work_experience, num_basic=0, num_intermediate=0, num_advanced=0, is_soft_skill=False):
    """
    Generates questions based on skill and work experience.
    Generates the specified number of questions based on number of num_basic, num_intermediate, and num_advanced for each level of difficulty.
    Adjusts prompt for soft skills if is_soft_skill is True.
    """

    def llm_output(prompt):
        # print("Generating questions with prompt:", prompt)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Skill is {skill} and years of experience {work_experience}"}
            ],
            temperature=0,
            max_tokens=1000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        response = dict(response)
        response_data = dict(dict(response['choices'][0])['message'])[
            'content'].replace("\n", " ")

        data = []
        if "------" in response_data:
            data = response_data.split("------")
        else:
            data = response_data.split("Question")
            data = [item for item in data if item not in ('', "", None)]
            data = ["Question" + x for x in data if x]

        questions = []
        for qa in data:
            q, a, k, l = extract_question_and_answer(qa)
            if q and a:
                questions.append(
                    {"question": q, "answer": a, "keywords": k, "type": l})

        return questions
    questions = []

    # Generate prompt dynamically based on the number of questions for each level
    prompt = f"""You will be provided with skill and year of experience.
        Based on years of experience Your task is to generate the following number of technical questions for the given core skill set based on the difficult level below ie(basic,intermediate and advanced):
        
        Basic: {num_basic} questions
        Intermediate: {num_intermediate} questions
        Advanced: {num_advanced} questions
        If any of the {num_basic} or {num_intermediate} or {num_advanced} is 0 then dont find technical question for that respective difficulty level.

        Questions should be specifically related to the mentioned skill and should not be repeated.
        Also, generate a one-line answer for each question, along with mandatory keywords to be used while answering.
        Display keywords to be present in the answer by prefixing with keyword: "Keywords:"
        for each difficult level of question , give corresponding Type ie for Basic questions give Type as "Basic" below, in the same passion for intermediate question give Type as "Intermediate" below and for advance question give Type as "Advanced" 
        Generate output in the form of 
        Question:
        Answer:
        Keywords:
        Type: Basic/Intermediate/Advanced
        ------
        """
    if is_soft_skill:
        # Adjust prompt for soft skills
        prompt = """You will be provided with a set of soft skills. Generate four 4 different relevant questions to evaluate the soft skills. 
        Add 1 compuslaory question which will be "tell me about yourself"
      Also, generate a one-line answer for the question, along with mandatory keywords to be used in the while answering that question. 
      tell me about yourself should be first question
      Order the questions in the sequence that we need to ask. display keywords to be present in the answer by prefixing with keyword: "Keywords:"
      
      Generate output in the form of 
      Question:
      Answer:
      Keywords:
      Type: Basic, Intermediate or Advance
      ------
      Question:
      Answer:
      Keywords:
      Type: Basic, Intermediate or Advance
      ------
      """

    # Add for basic, intermediate, and advanced questions
    questions.extend(llm_output(prompt))

    return questions


def fetch_skills(content):
    """
    Extracts soft skills, technical skills, and years of experience from job description content.
    """
    messages = [
        {
            "role": "system",
            "content": """
You are tasked with analyzing a job description to extract and categorize required skills into two categories: soft skills and technical skills. 
For soft skills, identify the top 3, with 'good communication skills' as a mandatory inclusion. 
For Technical Skills, pay special attention to specific technologies, programming languages, frameworks, tools, databases required, OOPS or Data Structure & algorithms skills,
Typescript or Redux, and methodologies mentioned. 
The technical skills section requires careful consolidation of related skills, particularly for programming languages and their frameworks.
If the Job Description contains above mentioned keyword, it should be noted as a Technical Skill.
Follow these guidelines:

1. Combine HTML and CSS into one point, labeled 'HTML and CSS'.
2. For JavaScript frameworks, create a single entry titled 'JavaScript Frameworks'.  Do not list each framework on a separate line or as a separate point.
3. Group all Python frameworks (like Django, Flask, FastAPI) into one entry, labeled 'Python Frameworks'.
4. Apart from 'HTML and CSS' and 'JavaScript Frameworks', the remaining four points in the technical skills section should pertain to other essential tools and skills for the job.
6. Add one point on methodologies mentioned like Agile or Waterfall or Scrum
7. Add a point if State management tooks like context or redux or Mobux or any other global state management tools are mentioned.
8. Add a point on debugging or containerization or orchestration is mentioned
9. Add a point on cloud services like AWS or GCP or Azure or any other cloud skills are mentioned
10. Add only one point combining all the CI CD points like github, jenkins, circeci or GitLab CI or GH Actions
5. Important point. From the skills you've identified,list only 4 technical skills randomly. Ensure that 4 points covers all the points listed in job description. It should not be just 1 word skill
11.Combine all mentioned versions of [SOFTWARE] (e.g., [VERSION_1], [VERSION_2], and [VERSION_3]) into a single skill entry labeled '[SOFTWARE] Versions'.".dont give as seperate version as individual skills.
If the job description does not specify the required years of experience, estimate this based on the role's level (internship, junior, senior, lead). Format your response as follows: 
Soft Skills: ["Skill 1", "Skill 2", "Good Communication Skills"]
Technical Skills: [ "Tool/Skill 1", "Tool/Skill 2". "Tool/Skill 3", "Tool/Skill 4"]
Years of Experience: <estimated range, e.g., 2-3 years>"

This revised version is more explicit about how to list the JavaScript frameworks, emphasizing that they should be included in one entry and not separated into individual lines or points.       """
        },
        {
            "role": "user",
            "content": content
        }
    ]

    # OpenAI API call
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0,
        max_tokens=1000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    response = dict(response)
    skills_text = dict(dict(response['choices'][0])['message'])[
        'content'].replace("\n", "")
    soft_skills_part, technical_skills_part = skills_text.split(
        "Technical Skills:")

    # Extract soft skills and technical skills
    soft_skills = soft_skills_part.replace("Soft Skills:", "").replace(
        "[", "").replace("]", "").split(",")
    technical_skills, expr = technical_skills_part.split("Years of Experience")
    technical_skills = technical_skills.replace(
        "[", "").replace("]", "").split(",")

    return soft_skills, technical_skills[:6], expr.strip()


def remove_special_characters_from_list(skill_list):
    cleaned_list = []

    for skill in skill_list:
        # Define a regular expression pattern to match special characters
        pattern = r'[^a-zA-Z0-9\s]'

        # Use re.sub() to replace matches with an empty string
        cleaned_skill = re.sub(pattern, '', skill)

        cleaned_list.append(cleaned_skill.strip())

    return cleaned_list


@app.route('/fetch_skills', methods=['POST'])
def fetch_skills_endpoint():
    """
    Flask endpoint to generate questions based on job description.
    """
    data = request.get_json()
    content = data.get("job_description", "").strip()
    name = data.get("name", "").strip()

    existing_entry = ResponseCache.query.filter_by(name=name).first()

    if existing_entry:
        # If a record with the same name exists, return it
        return jsonify({'message': 'Data retrieved successfully', 'skills': existing_entry.skills}), 200
    soft_skills, technical_skills, expr = fetch_skills(content)
    soft_skills = remove_special_characters_from_list(soft_skills)
    technical_skills = remove_special_characters_from_list(technical_skills)

    response = {'soft_skills': soft_skills,
                "technical_skills": technical_skills,
                "experience": expr}

    if len(name):
        new_entry = ResponseCache(
            name=name, skills=response, soft_skills=None, technical_skills=None)
        db.session.add(new_entry)
        db.session.commit()

    return jsonify({'message': 'Data retrieved successfully', 'skills': response}), 200


@app.route('/generate_soft_skill_questions', methods=['POST'])
def generate_soft_skill_questions_endpoint():
    """
    Flask endpoint to generate soft skill related questions.
    """
    data = request.get_json()
    soft_skills = data.get("soft_skills", "").strip()
    name = data.get("name", "").strip()
    experience = data.get("experience", "").strip()

    existing_entry = ResponseCache.query.filter_by(name=name).first()

    if existing_entry and existing_entry.soft_skills != None:
        # If a record with the same name exists, return it
        return jsonify({'message': 'Data retrieved successfully', 'soft_skills': existing_entry.soft_skills}), 200

    soft_skills = remove_special_characters_from_list(soft_skills.split(","))

    output = {"soft_skills": []}

    # Process soft skills
    soft_skill_questions = ask_question(
        soft_skills, experience, 1, 1, 1, is_soft_skill=True)
    output["soft_skills"].append(
        {"name": "Soft Skills", "questions": soft_skill_questions})

    if len(name):
        existing_entry.soft_skills = output
        db.session.commit()

    return jsonify({'message': 'Data retrieved successfully', 'soft_skills': output}), 200


@app.route('/generate_technical_questions', methods=['POST'])
def generate_technical_questions_endpoint():
    """
    Flask endpoint to generate questions based on job description.
    """
    data = request.get_json()
    skills_info = data.get("technical_skills", [])  # List of skill information
    name = data.get("name", "").strip()
    output = {"technical_skills": []}

    existing_entry = ResponseCache.query.filter_by(name=name).first()

    if existing_entry and existing_entry.technical_skills != None:
        # If a record with the same name exists, return it
        return jsonify({'message': 'Data retrieved successfully', 'technical_skills': existing_entry.technical_skills}), 200

    for skill_info in skills_info:
        skill = skill_info.get("skill", "").strip()
        experience = skill_info.get("experience", "").strip()
        num_basic = skill_info.get("num_basic")
        num_intermediate = skill_info.get("num_intermediate")
        num_advanced = skill_info.get("num_advanced")

        if num_basic == num_intermediate == num_advanced == 0:
            continue  # Skip this skill if all difficulty levels are zero

        questions = ask_question(
            skill, experience, num_basic, num_intermediate, num_advanced)

        output["technical_skills"].append(
            {"name": skill, "questions": questions})

    if len(name):
        existing_entry.technical_skills = output
        db.session.commit()

    return jsonify({'message': 'Data retrieved successfully', 'technical_skills': output}), 200


@app.route('/')
def hello():
    return "hello"


if __name__ == '__main__':
    # Run Flask application
    app.run(debug=True)
