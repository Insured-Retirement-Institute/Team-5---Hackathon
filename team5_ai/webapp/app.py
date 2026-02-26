"""
webapp/app.py

Simple Flask chat app that proxies messages to the Bedrock Agent.
Run with: python webapp/app.py
"""

import io
import json
import os
import re
import uuid
import boto3
from flask import Flask, render_template, request, jsonify, session
from asgiref.wsgi import WsgiToAsgi
from mangum import Mangum

AGENT_ID = os.environ.get("AGENT_ID", "SZJMM4QTCE")
AGENT_ALIAS_ID = os.environ.get("AGENT_ALIAS_ID", "TSTALIASID")
REGION = os.environ.get("AWS_REGION", "us-east-1")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-prod")

bedrock = boto3.client("bedrock-agent-runtime", region_name=REGION)

DOC_MAX_CHARS = 20_000


@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files["file"]
    filename = f.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "docx":
        try:
            from docx import Document
            doc = Document(io.BytesIO(f.read()))
            text = "\n".join(para.text for para in doc.paragraphs if para.text.strip())
        except Exception as exc:
            return jsonify({"error": f"Could not read .docx: {exc}"}), 400
    elif ext == "txt":
        try:
            text = f.read().decode("utf-8", errors="replace")
        except Exception as exc:
            return jsonify({"error": f"Could not read .txt: {exc}"}), 400
    else:
        return jsonify({"error": "Unsupported file type. Upload .docx or .txt"}), 400

    truncated = len(text) > DOC_MAX_CHARS
    text = text[:DOC_MAX_CHARS]

    session["doc_text"] = text
    session["doc_name"] = filename

    return jsonify({"filename": filename, "chars": len(text), "truncated": truncated})


@app.route("/clear-doc", methods=["POST"])
def clear_doc():
    session.pop("doc_text", None)
    session.pop("doc_name", None)
    return jsonify({"ok": True})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = (data or {}).get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())

    # Prepend document context if one has been uploaded
    doc_context = session.get("doc_text", "")
    if doc_context:
        doc_name = session.get("doc_name", "document")
        input_text = (
            f"[Attached document: {doc_name}]\n{doc_context}\n\n"
            f"---\n\nUser message: {user_message}"
        )
    else:
        input_text = user_message

    try:
        response = bedrock.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session["session_id"],
            inputText=input_text,
        )

        # Collect streaming chunks
        reply = ""
        for event in response.get("completion", []):
            chunk = event.get("chunk")
            if chunk:
                reply += chunk.get("bytes", b"").decode()

        # Strip FORM_SPEC block if the agent appended one
        form_spec = None
        match = re.search(r'FORM_SPEC:\s*(\{.*\})\s*$', reply, re.DOTALL)
        if match:
            try:
                form_spec = json.loads(match.group(1))
                reply = reply[:match.start()].strip()
            except (json.JSONDecodeError, ValueError):
                pass

        result = {"reply": reply}
        if form_spec:
            result["form"] = form_spec
        return jsonify(result)

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# Lambda handler (used when deployed to AWS)
handler = Mangum(WsgiToAsgi(app), lifespan="off")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
