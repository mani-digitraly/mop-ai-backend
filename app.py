from flask import Flask, request, jsonify
from flask_cors import CORS
import os, math
from openai import OpenAI
import requests
from dotenv import load_dotenv
load_dotenv()



app = Flask(__name__)
CORS(app)

# init OpenAI client (reads from env)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# conversation memory (simple list for now)
memory = [
    {"role": "system", "content": "You are a helpful AI agent."}
]

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_msg = data.get("message", "").strip()

    # Tool: calculator
    if user_msg.startswith("/calc "):
        expr = user_msg.replace("/calc ", "")
        try:
            result = eval(expr, {"__builtins__": {}}, {"math": math})
            reply = f"Result: {result}"
            memory.append({"role": "user", "content": user_msg})
            memory.append({"role": "assistant", "content": reply})
            return jsonify({"reply": reply, "meta": "tool:calc"})
        except Exception as e:
            return jsonify({"reply": f"Error: {str(e)}", "meta": "tool:calc"})

    # Otherwise: use LLM
    memory.append({"role": "user", "content": user_msg})
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        # fallback (echo)
        reply = f"You said: {user_msg}"
        memory.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply, "meta": "echo"})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # cheaper but smart
            messages=memory,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        memory.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply, "meta": "llm"})
    except Exception as e:
        return jsonify({"reply": f"LLM error: {str(e)}", "meta": "error"})
def lookup_word(word):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        meaning = data[0]["meanings"][0]["definitions"][0]["definition"]
        return f"Definition of {word}: {meaning}"
    return f"Could not find definition for {word}."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
