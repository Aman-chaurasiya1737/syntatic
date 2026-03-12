import requests
import copy

API_KEY = "AIzaSyBV-vv02SgZoRzpp0my4niXX-2P-7QngOY"
PROJECT_ID = "syntatic-1"
BASE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"


def python_to_firestore(value):
    if isinstance(value, str):
        return {"stringValue": value}
    elif isinstance(value, bool):
        return {"booleanValue": value}
    elif isinstance(value, int):
        return {"integerValue": str(value)}
    elif isinstance(value, float):
        return {"doubleValue": value}
    elif isinstance(value, list):
        return {"arrayValue": {"values": [python_to_firestore(v) for v in value]}}
    elif isinstance(value, dict):
        return {"mapValue": {"fields": {k: python_to_firestore(v) for k, v in value.items()}}}
    elif value is None:
        return {"nullValue": None}
    else:
        return {"stringValue": str(value)}


def push_company_sessions(company, sessions):
    url = f"{BASE_URL}/interview_sessions/{company}?key={API_KEY}"

    doc_body = {
        "fields": {
            "company": python_to_firestore(company),
            "sessions": python_to_firestore(sessions),
            "count": python_to_firestore(len(sessions)),
        }
    }

    resp = requests.patch(url, json=doc_body, timeout=30)

    if resp.status_code == 200:
        print(f"  [OK] {company}: {len(sessions)} sessions pushed to Firebase")
        return True
    else:
        print(f"  [ERROR] {company}: {resp.status_code} - {resp.text[:200]}")
        return False


def q(id, question, type, topic):
    return {"id": id, "question": question, "type": type, "topic": topic}


# Common technical/behavioral combinations
TECH_TOPICS = [
    "System Design",
    "Data Structures",
    "Algorithms",
    "Database Architecture",
    "Scalability",
    "API Design",
    "Security",
    "Performance Optimization",
    "Testing & Quality",
    "Distributed Systems"
]

BEHAVIORAL_TOPICS = [
    "Past Experience",
    "Conflict Resolution",
    "Leadership",
    "Failure & Growth",
    "Time Management",
    "Cross-functional Collaboration",
    "Adaptability",
    "Mentorship",
    "Goal Setting",
    "Communication"
]

COMPANIES = [
    "GOOGLE",
    "AMAZON",
    "META",
    "APPLE",
    "NETFLIX",
    "MICROSOFT",
    "STARTUP"
]

# Generate 50 sessions for each company
print(f"\nGenerating 50 sessions (5 questions each) for {len(COMPANIES)} companies...")

for company in COMPANIES:
    company_sessions = []
    
    # Prefix some questions with company names to make them specific
    c_name = "your previous company" if company == "STARTUP" else company
    
    for session_idx in range(50):
        # Base questions, rotating through topics based on index
        t1 = TECH_TOPICS[(session_idx) % len(TECH_TOPICS)]
        t2 = TECH_TOPICS[(session_idx + 3) % len(TECH_TOPICS)]
        t3 = TECH_TOPICS[(session_idx + 7) % len(TECH_TOPICS)]
        
        b1 = BEHAVIORAL_TOPICS[(session_idx) % len(BEHAVIORAL_TOPICS)]
        b2 = BEHAVIORAL_TOPICS[(session_idx + 5) % len(BEHAVIORAL_TOPICS)]
        
        # Determine specific wording based on company
        if company == "GOOGLE":
            b_q1 = f"Tell me about a time you had to deal with ambiguity, which is common here at Google. How did you handle it?"
            t_q1 = f"How would you design a scalable system like Google Docs?"
        elif company == "AMAZON":
            b_q1 = f"Amazon's leadership principles emphasize 'Customer Obsession'. Tell me about a time you put the customer first."
            t_q1 = f"How would you optimize the checkout process for millions of concurrent users during Prime Day?"
        elif company == "META":
            b_q1 = f"At Meta we move fast. Tell me about a time you had to make a quick decision without having all the facts."
            t_q1 = f"How would you design the news feed architecture to handle billions of updates per day?"
        elif company == "APPLE":
            b_q1 = f"Apple values extreme attention to detail. Give an example of a project where your focus on details made a big difference."
            t_q1 = f"How do you approach building applications that are highly performant while minimizing battery drain?"
        elif company == "NETFLIX":
            b_q1 = f"Netflix culture values 'Freedom and Responsibility'. Tell me about a time you took ownership of a failure."
            t_q1 = f"How would you design a global content delivery network for streaming video?"
        elif company == "MICROSOFT":
            b_q1 = f"Microsoft serves enterprise customers. Tell me about a time you had to deliver on commitments to demanding stakeholders."
            t_q1 = f"How do you ensure enterprise-grade security and compliance when designing APIs?"
        else: # STARTUP
            b_q1 = f"In a startup environment, you often wear many hats. Tell me about a time you stepped outside your core responsibilities."
            t_q1 = f"How do you make pragmatic technical choices when you need to launch an MVP quickly?"

        session = {
            "session_id": session_idx + 1,
            "questions": [
                q(1, t_q1, "technical", t1),
                q(2, b_q1, "behavioral", b1),
                q(3, f"Can you explain a complex {t2} concept you've worked with recently to someone without a technical background?", "technical", t2),
                q(4, f"Tell me about a challenging situation involving {b2} and how you navigated it.", "behavioral", b2),
                q(5, f"What are the biggest tradeoffs you consider when dealing with {t3}?", "technical", t3)
            ]
        }
        
        # Add some variation so not all 50 sessions have the exact same templates
        if session_idx % 3 == 1:
            session["questions"][0] = q(1, f"Describe your approach to designing systems for {t1}.", "technical", t1)
            session["questions"][2] = q(3, t_q1, "technical", "System Design")
            
        if session_idx % 4 == 2:
            session["questions"][1] = q(2, f"Give me an example of how you handle {b1} in a fast-paced environment.", "behavioral", b1)
            session["questions"][3] = q(4, b_q1, "behavioral", "Company Culture")

        company_sessions.append(session)
        
    print(f"{company}: 50 sessions created")
    # Push to Firebase
    push_company_sessions(company, company_sessions)

print("\nDone! All interview sessions pushed successfully.")
