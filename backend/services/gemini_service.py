import requests
import json
import re
import base64
import time


class GeminiService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        self.transcription_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

    def transcribe_audio(self, audio_base64, mime_type="audio/webm"):

        url = f"{self.transcription_url}?key={self.api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": audio_base64
                        }
                    },
                    {
                        "text": "Transcribe the spoken words in this audio clip exactly as said. Return ONLY the raw transcription text. If there is no speech or the audio is silent, return exactly: [SILENT]. Do not add any commentary, labels, or formatting."
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 2048,
            }
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=payload, timeout=30)
                if response.status_code == 429:
                    wait_time = (2 ** attempt) + 1
                    print(f"Transcription rate limited, retrying in {wait_time}s (attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                response.raise_for_status()
                result = response.json()
                text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                if text == '[SILENT]' or text.lower() == '[silent]':
                    return ""
                return text
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429 and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 1
                    print(f"Transcription rate limited, retrying in {wait_time}s (attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                print(f"Gemini Transcription Error: {e}")
                return ""
            except Exception as e:
                print(f"Gemini Transcription Error: {e}")
                return ""
        return ""

    COMPANY_PROMPTS = {
        "Google": {
            "dsa": "Focus on graph traversal, tree problems, dynamic programming, and complex algorithmic challenges. Google values elegant, optimal solutions with clean code. Prefer problems involving BFS/DFS, shortest path, or tree manipulation.",
            "interview": "Include 'Googlyness' behavioral questions about collaboration, intellectual humility, and innovation. Ask about system design for massive scale. Include questions about how they handle ambiguity and drive impact."
        },
        "Amazon": {
            "dsa": "Include practical coding problems testing data structure knowledge, efficiency, and scalability. Problems that simulate real-world scenarios are preferred.",
            "interview": "Prioritize Amazon Leadership Principles: Customer Obsession, Ownership, Invent and Simplify, Learn and Be Curious, Hire and Develop the Best, Insist on the Highest Standards, Think Big, Bias for Action, Frugality, Earn Trust, Dive Deep, Have Backbone, Deliver Results. Frame ALL behavioral questions around these principles explicitly."
        },
        "Meta": {
            "dsa": "Focus on array manipulation, string processing, graph problems, and problems involving social network modeling. Meta values clean, efficient code that can handle billions of users.",
            "interview": "Ask about building products at scale, moving fast and breaking things, being bold. Include system design questions about social networking features, news feeds, and real-time messaging."
        },
        "Apple": {
            "dsa": "Focus on optimization problems, memory-efficient solutions, clean code architecture, and problems involving data compression or efficient storage.",
            "interview": "Ask about attention to detail, user experience, design thinking, privacy-conscious development, and building premium-quality products. Focus on craftsmanship."
        },
        "Netflix": {
            "dsa": "Focus on distributed systems concepts, caching strategies, streaming-related problems, and content recommendation algorithms.",
            "interview": "Ask about Netflix culture: freedom and responsibility, high performance, context not control, highly aligned and loosely coupled. Focus on independent decision-making and innovation."
        },
        "Microsoft": {
            "dsa": "Cover a broad range of DSA topics including trees, graphs, dynamic programming, design patterns, and problems involving cloud/distributed systems.",
            "interview": "Ask about growth mindset, collaboration, inclusive design, and building accessible technology. Include questions about empowering every person and organization."
        },
        "Startup": {
            "dsa": "Focus on practical, full-stack coding problems that test versatility, quick thinking, and ability to build MVPs. Problems should be realistic and product-oriented.",
            "interview": "Ask about wearing multiple hats, adaptability, ownership mentality, rapid prototyping, scrappiness, and startup culture fit. Focus on practical problem-solving and resourcefulness."
        }
    }

    def _call_gemini(self, prompt):

        url = f"{self.base_url}?key={self.api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.95,
                "topK": 40,
                "maxOutputTokens": 8192,
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            text = result['candidates'][0]['content']['parts'][0]['text']
            return text
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return None

    def _parse_json_response(self, text):

        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        for pattern in [r'\{[\s\S]*\}', r'\[[\s\S]*\]']:
            json_match = re.search(pattern, text)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    continue
        return None

    def extract_interview_info(self, resume_text):
        prompt = """You are an AI assistant helping to set up a mock interview.
Based on the candidate's professional experience in their resume, extract the most suitable tech domain, interview difficulty level, and target company type.

Available Domains: "Frontend Development", "Backend Development", "Full Stack Development", "Data Science", "Machine Learning / AI", "Mobile App Development", "Cloud Computing & DevOps", "Cybersecurity", "Blockchain & Web3", "Database & System Design"
Available Difficulties: "Easy", "Medium", "Hard" (Base this on years of experience: <2 years = Easy, 2-5 = Medium, 5+ = Hard)
Available Companies: "Google", "Amazon", "Meta", "Apple", "Netflix", "Microsoft", "Startup" (If not explicitly targeting FAANG/Big Tech, choose "Startup" or the best fit).

Candidate Resume Extract:
{resume_extract}

Return the response in this EXACT JSON format (no other text):
{{
    "domain": "<One of the exact domain strings above>",
    "difficulty": "<One of the exact difficulty strings above>",
    "company": "<One of the exact company strings above>"
}}"""
        text = self._call_gemini(prompt.format(resume_extract=resume_text[:3000]))
        result = self._parse_json_response(text)
        
        if result:
            return result
            
        return {"domain": "Full Stack Development", "difficulty": "Medium", "company": "Startup"}

    def parse_pdf_and_extract_info(self, pdf_bytes):
        url = f"{self.base_url}?key={self.api_key}"
        prompt = """You are an AI assistant helping to set up a mock interview based on a resume document.
Read the attached PDF candidate resume carefully.
First, extract all the professional text content from the resume.
Then, based on their experience, extract the most suitable tech domain, interview difficulty level, and target company type.

Available Domains: "Frontend Development", "Backend Development", "Full Stack Development", "Data Science", "Machine Learning / AI", "Mobile App Development", "Cloud Computing & DevOps", "Cybersecurity", "Blockchain & Web3", "Database & System Design"
Available Difficulties: "Easy", "Medium", "Hard" (Base this on years of experience: <2 years = Easy, 2-5 = Medium, 5+ = Hard)
Available Companies: "Google", "Amazon", "Meta", "Apple", "Netflix", "Microsoft", "Startup" (If not explicitly targeting FAANG/Big Tech, choose "Startup" or the best fit).

Return the response in this EXACT JSON format (no other text):
{
    "text": "<The full extracted text of the resume>",
    "info": {
        "domain": "<One of the exact domain strings above>",
        "difficulty": "<One of the exact difficulty strings above>",
        "company": "<One of the exact company strings above>"
    }
}"""
        payload = {
            "contents": [{
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": "application/pdf",
                            "data": base64.b64encode(pdf_bytes).decode('utf-8')
                        }
                    },
                    {
                        "text": prompt
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 4096,
                "responseMimeType": "application/json"
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            text = result['candidates'][0]['content']['parts'][0]['text']
            parsed = json.loads(text)
            return parsed
        except Exception as e:
            print(f"Gemini PDF Parse Error: {e}")
            return None

    def generate_dsa_question(self, domain, difficulty, company_mode, resume_text=""):

        company_info = self.COMPANY_PROMPTS.get(company_mode, self.COMPANY_PROMPTS["Startup"])

        resume_context = ""
        if resume_text:
            resume_context = f"""
The candidate has submitted their resume. Here are their details:
---
{resume_text[:3000]}
---
Generate a question that relates to their experience and skills mentioned in the resume, but is still a proper DSA/coding challenge.
"""

        prompt = f"""You are a senior technical interviewer at {company_mode}. 
Generate exactly ONE {difficulty}-level Data Structures and Algorithms coding question for a candidate specializing in {domain}.

{company_info['dsa']}

{resume_context}

The question should be clear, well-defined, and solvable within 30-45 minutes.

Return the response in this EXACT JSON format (no other text):
{{
    "title": "Question Title",
    "description": "Detailed description of the problem including what the function should do",
    "examples": [
        {{"input": "example input", "output": "expected output", "explanation": "brief explanation"}},
        {{"input": "example input 2", "output": "expected output 2", "explanation": "brief explanation"}},
        {{"input": "example input 3", "output": "expected output 3", "explanation": "brief explanation"}}
    ],
    "constraints": ["constraint 1", "constraint 2", "constraint 3"],
    "difficulty": "{difficulty}",
    "topic": "Primary DSA topic (e.g., Arrays, Trees, Graphs, DP, etc.)"
}}"""

        text = self._call_gemini(prompt)
        result = self._parse_json_response(text)

        if result:
            return result


        return {
            "title": "Two Sum",
            "description": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target. You may assume that each input would have exactly one solution, and you may not use the same element twice.",
            "examples": [
                {"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]", "explanation": "Because nums[0] + nums[1] == 9"},
                {"input": "nums = [3,2,4], target = 6", "output": "[1,2]", "explanation": "Because nums[1] + nums[2] == 6"},
                {"input": "nums = [3,3], target = 6", "output": "[0,1]", "explanation": "Because nums[0] + nums[1] == 6"}
            ],
            "constraints": ["2 <= nums.length <= 10^4", "-10^9 <= nums[i] <= 10^9", "Only one valid answer exists"],
            "difficulty": difficulty,
            "topic": "Arrays & Hash Maps"
        }

    def evaluate_code(self, question, code, language):

        prompt = f"""You are a senior technical interviewer evaluating a coding solution.

QUESTION:
{json.dumps(question) if isinstance(question, dict) else question}

CANDIDATE'S SOLUTION ({language}):
```
{code}
```

Evaluate the solution thoroughly on these criteria:
1. Correctness - Does it solve the problem correctly?
2. Time Complexity - What is the time complexity? Is it optimal?
3. Space Complexity - What is the space complexity?
4. Code Quality - Is the code clean, readable, well-structured?
5. Edge Cases - Does it handle edge cases?

Return the response in this EXACT JSON format (no other text):
{{
    "score": <number from 0 to 10>,
    "remarks": "Detailed overall feedback (2-3 sentences)",
    "correctness": "Assessment of correctness",
    "time_complexity": "O(?) - explanation",
    "space_complexity": "O(?) - explanation",
    "code_quality": "Assessment of code quality",
    "edge_cases": "Assessment of edge case handling",
    "suggestions": "What could be improved"
}}"""

        text = self._call_gemini(prompt)
        result = self._parse_json_response(text)

        if result:
            result['score'] = max(0, min(10, int(result.get('score', 5))))
            return result

        return {
            "score": 5,
            "remarks": "Unable to fully evaluate the solution. Please try again.",
            "correctness": "Could not verify",
            "time_complexity": "Unknown",
            "space_complexity": "Unknown",
            "code_quality": "Not evaluated",
            "edge_cases": "Not evaluated",
            "suggestions": "Please resubmit your solution"
        }

    def generate_interview_questions(self, domain, difficulty, company_mode, resume_text=""):

        company_info = self.COMPANY_PROMPTS.get(company_mode, self.COMPANY_PROMPTS["Startup"])

        resume_context = ""
        if resume_text:
            resume_context = f"""
The candidate's resume details:
---
{resume_text[:3000]}
---
Generate 2-3 questions specifically about the projects and skills mentioned in their resume (like a real interviewer would reference their CV). The remaining questions should be general technical/behavioral.
"""

        prompt = f"""You are a senior interviewer at {company_mode} conducting a {difficulty}-level interview for a {domain} role.

{company_info['interview']}

{resume_context}

Generate exactly 5 interview questions. Include a good mix:
- 2-3 Technical questions (domain-specific concepts, system design, problem-solving)
- 2-3 Behavioral questions (company-culture fit, past experience, leadership)

Each question should be conversational and natural, as if spoken by a real interviewer.

Return the response in this EXACT JSON format (no other text):
{{
    "questions": [
        {{"id": 1, "question": "Full question text here", "type": "technical", "topic": "Brief topic"}},
        {{"id": 2, "question": "Full question text here", "type": "behavioral", "topic": "Brief topic"}},
        {{"id": 3, "question": "Full question text here", "type": "technical", "topic": "Brief topic"}},
        {{"id": 4, "question": "Full question text here", "type": "behavioral", "topic": "Brief topic"}},
        {{"id": 5, "question": "Full question text here", "type": "technical", "topic": "Brief topic"}}
    ]
}}"""

        text = self._call_gemini(prompt)
        result = self._parse_json_response(text)

        if result and 'questions' in result:
            return result


        return {
            "questions": [
                {"id": 1, "question": f"Tell me about a challenging {domain} project you worked on recently. What was your approach?", "type": "behavioral", "topic": "Experience"},
                {"id": 2, "question": f"How would you design a scalable system for a {domain} application that handles millions of users?", "type": "technical", "topic": "System Design"},
                {"id": 3, "question": "Describe a time when you had to disagree with a team member. How did you resolve it?", "type": "behavioral", "topic": "Teamwork"},
                {"id": 4, "question": f"What are the most important security considerations in {domain}?", "type": "technical", "topic": "Security"},
                {"id": 5, "question": "Where do you see yourself in 5 years and how does this role fit into your career goals?", "type": "behavioral", "topic": "Career Goals"}
            ]
        }

    def evaluate_interview(self, questions_answers, domain):

        qa_text = ""
        for i, qa in enumerate(questions_answers, 1):
            qa_text += f"\nQuestion {i}: {qa['question']}\nCandidate's Answer: {qa['answer']}\n"

        prompt = f"""You are a senior interviewer evaluating a {domain} candidate's interview performance.

Here are the questions and the candidate's responses:
{qa_text}

Evaluate each answer on:
1. Relevance - Did they answer the question asked?
2. Depth - Was the answer thorough and detailed?
3. Communication - Was the answer clear and well-structured?
4. Technical Accuracy - For technical questions, was the answer correct?
5. Behavioral Quality - For behavioral questions, did they use STAR method or give concrete examples?

Return the response in this EXACT JSON format (no other text):
{{
    "per_question": [
        {{"question_id": 1, "score": <0-10>, "remarks": "Specific feedback for this answer"}},
        {{"question_id": 2, "score": <0-10>, "remarks": "Specific feedback for this answer"}},
        {{"question_id": 3, "score": <0-10>, "remarks": "Specific feedback for this answer"}},
        {{"question_id": 4, "score": <0-10>, "remarks": "Specific feedback for this answer"}},
        {{"question_id": 5, "score": <0-10>, "remarks": "Specific feedback for this answer"}}
    ],
    "overall_score": <0-10>,
    "overall_remarks": "Comprehensive overall assessment of the interview performance (3-4 sentences)",
    "strengths": "Key strengths demonstrated",
    "improvements": "Areas for improvement"
}}"""

        text = self._call_gemini(prompt)
        result = self._parse_json_response(text)

        if result:
            if 'per_question' in result:
                for pq in result['per_question']:
                    pq['score'] = max(0, min(10, int(pq.get('score', 5))))
            result['overall_score'] = max(0, min(10, int(result.get('overall_score', 5))))
            return result

        return {
            "per_question": [
                {"question_id": i, "score": 5, "remarks": "Unable to evaluate. Please try again."}
                for i in range(1, 6)
            ],
            "overall_score": 5,
            "overall_remarks": "Unable to fully evaluate the interview. Please try again.",
            "strengths": "Not evaluated",
            "improvements": "Not evaluated"
        }
