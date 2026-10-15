from fastapi.testclient import TestClient

from app.engine import ChatEngine
from app.main import app

# Held-out phrasings (NOT in intents.json) with expected intent. None = must fall back.
CASES = [
    ("hey", "greeting"), ("good morning bot", "greeting"),
    ("ok bye", "goodbye"), ("see ya later", "goodbye"),
    ("thank you so much", "thanks"), ("thanks for the help", "thanks"),
    ("tell me about codealpha", "about"), ("what does your company do", "about"),
    ("which services do you provide", "services"), ("do you build mobile apps", "services"),
    ("what is the price", "pricing"), ("how much will a website cost", "pricing"),
    ("how do i apply for the internship", "internship"), ("will i get an internship certificate", "internship"),
    ("what is your phone number", "contact"), ("how do i contact codealpha", "contact"),
    ("what time do you open", "hours"), ("working hours please", "hours"),
    ("i am facing a problem", "support"), ("my app is not working", "support"),
    ("what is your refund policy", "refund"), ("i want to cancel my order", "refund"),
    ("track my order please", "tracking"), ("what is the status of my order", "tracking"),
    ("i want to talk to a real person", "human"), ("connect me with an agent", "human"),
    ("what is the weather in paris", None), ("asdfgh qwerty", None), ("who won the cricket match", None),
]

engine = ChatEngine()


def test_accuracy_at_least_85_percent():
    ok = sum(engine.predict(q)[0] == exp for q, exp in CASES)
    acc = ok / len(CASES)
    wrong = [(q, exp, engine.predict(q)) for q, exp in CASES if engine.predict(q)[0] != exp]
    print(f"\naccuracy={acc:.1%} ({ok}/{len(CASES)}) wrong={wrong}")
    assert acc >= 0.85


def test_api_chat_and_health():
    c = TestClient(app)
    assert c.get("/api/health").json()["status"] == "ok"
    r = c.post("/api/chat", json={"message": "what are your prices"})
    assert r.status_code == 200 and r.json()["intent"] == "pricing"


def test_api_rejects_empty():
    assert TestClient(app).post("/api/chat", json={"message": ""}).status_code == 422
