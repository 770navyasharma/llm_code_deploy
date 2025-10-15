# app.py

import os
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai
import re
import requests
import base64
import time

# --- 1. SETUP AND CONFIGURATION ---
load_dotenv()

MY_APP_SECRET = os.getenv("MY_APP_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_API_URL = "https://api.github.com"

required_keys = ["MY_APP_SECRET", "GEMINI_API_KEY", "GITHUB_TOKEN", "GITHUB_USERNAME"]
for key in required_keys:
    if not os.getenv(key):
        raise ValueError(f"Error: Missing required environment variable '{key}'")

genai.configure(api_key=GEMINI_API_KEY)
app = Flask(__name__)

# --- NEW HELPER FUNCTION TO PROCESS ATTACHMENTS ---
def process_attachments(attachments):
    """Decodes data URIs from attachments and returns their formatted content."""
    if not attachments:
        return ""
    
    content_list = []
    for attachment in attachments:
        try:
            # Format is "data:<media_type>;base64,<data>"
            header, encoded = attachment['url'].split(',', 1)
            decoded_content = base64.b64decode(encoded).decode('utf-8')
            content_list.append(f"--- Attachment File: {attachment['name']} ---\n{decoded_content}\n--- End of {attachment['name']} ---")
        except Exception as e:
            print(f"⚠️  Could not decode attachment {attachment.get('name', 'N/A')}: {e}")
            content_list.append(f"--- Attachment File: {attachment['name']} (DECODING FAILED) ---")

    return "\n\n".join(content_list)

# --- 2. LLM (GEMINI) HELPER FUNCTIONS (UPGRADED PROMPTS) ---

def generate_code_with_gemini(brief, checks, attachments_content):
    """Generates application code from scratch using an enhanced prompt."""
    print("🧠 Calling Gemini API to generate initial code...")
    
    # --- PROMPT ENHANCEMENT: Added checks and attachments ---
    prompt = f"""
    You are an expert full-stack web developer. Your task is to build a single-page web application based on the following brief.
    You must generate a single index.html file that includes all necessary HTML, CSS, and JavaScript.
    Use CDN links for any external libraries like Bootstrap or jQuery if needed.
    The generated code must be correct and directly usable.

    BRIEF:
    {brief}

    EVALUATION CHECKS:
    The code will be evaluated against these checks. Ensure the generated code can pass them:
    - {'- '.join(checks)}

    ATTACHED FILE CONTENTS:
    The user has provided the following file contents. Use them to complete the brief.
    {attachments_content if attachments_content else "None"}

    Respond ONLY with the complete HTML code inside a single markdown code block. Do not add any explanatory comments.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    try:
        code = re.search(r'```html(.*)```', response.text, re.DOTALL).group(1).strip()
        print("✅ Successfully generated initial code.")
        return code
    except AttributeError:
        print("❌ Error: Could not extract code from Gemini's response. Using raw response.")
        return response.text

def revise_code_with_gemini(brief, checks, attachments_content, original_code):
    """Revises existing code based on a new brief and checks."""
    print("🧠 Calling Gemini API to revise code...")
    
    # --- PROMPT ENHANCEMENT: Added checks and attachments for revision ---
    prompt = f"""
    You are an expert full-stack web developer. Your task is to revise an existing HTML file based on a new brief.
    Do not add any explanatory comments, just provide the final, complete, updated code.

    NEW REVISION BRIEF:
    {brief}

    NEW EVALUATION CHECKS:
    The updated code must pass these new checks:
    - {'- '.join(checks)}
    
    NEW ATTACHED FILE CONTENTS:
    {attachments_content if attachments_content else "None"}

    ORIGINAL `index.html` CODE TO BE REVISED:
    ```html
    {original_code}
    ```

    Respond ONLY with the complete and updated HTML code inside a single markdown code block.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    try:
        code = re.search(r'```html(.*)```', response.text, re.DOTALL).group(1).strip()
        print("✅ Successfully revised code.")
        return code
    except AttributeError:
        print("❌ Error: Could not extract revised code from Gemini's response. Using raw response.")
        return response.text

def generate_readme_with_gemini(brief):
    """Generates a README.md file with a new 'Code Explanation' section."""
    print("🧠 Calling Gemini API to generate README...")

    # --- PROMPT ENHANCEMENT: Added 'Code Explanation' section ---
    prompt = f"""
    You are a professional technical writer. Based on the following application brief, write a professional README.md file.
    The README must include the following sections:
    - A suitable title for the project.
    - Summary: A brief summary of what the project does.
    - Setup: Explain that it's a static site and no local setup is needed to run it.
    - Usage: Explain how to view and use the live deployed page.
    - Code Explanation: Briefly explain how the HTML, CSS, and JavaScript work together to achieve the goal.
    - License: State that the project is under the MIT License.

    APPLICATION BRIEF:
    "{brief}"

    Respond ONLY with the complete markdown content for the README.md file.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    print("✅ README generated.")
    return response.text

def revise_readme_with_gemini(brief, original_readme):
    """Revises an existing README file, including the code explanation."""
    print("🧠 Calling Gemini API to revise README...")
    prompt = f"""
    You are a technical writer. Your task is to update an existing README.md file based on a new brief describing changes to the application.
    Ensure the summary, usage, and code explanation sections are updated to reflect the new functionality.
    NEW BRIEF FOR CHANGES: "{brief}"
    ORIGINAL README.md CONTENT:
    {original_readme}
    Respond ONLY with the complete and updated markdown content for the README.md file.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    print("✅ README revised.")
    return response.text

# --- 3. GITHUB & OTHER HELPER FUNCTIONS (UNCHANGED BUT ROBUST) ---

def get_mit_license():
    year = time.strftime("%Y")
    # Using a multiline string for cleaner formatting
    return f"""Copyright (c) {year} {GITHUB_USERNAME}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

def create_github_repo(repo_name):
    print(f"Creating GitHub repo: {repo_name}...")
    url = f"{GITHUB_API_URL}/user/repos"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    payload = {"name": repo_name, "private": False, "description": f"AI-generated app for task: {repo_name}"}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        print("✅ Repo created successfully.")
        return response.json()
    elif response.status_code == 422:
        print("⚠️ Repo already exists. Will proceed.")
        return {"html_url": f"https://github.com/{GITHUB_USERNAME}/{repo_name}"}
    else:
        raise Exception(f"GitHub repo creation failed with status {response.status_code}: {response.text}")

def create_or_update_files_in_repo(repo_name, files_with_content, commit_message):
    print(f"Pushing {len(files_with_content)} files to {repo_name}...")
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    latest_commit_sha = ""
    for file_path, data in files_with_content.items():
        url = f"{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/{repo_name}/contents/{file_path}"
        content_encoded = base64.b64encode(data["content"].encode('utf-8')).decode('utf-8')
        payload = {"message": commit_message, "content": content_encoded, "committer": {"name": "LLM Code Bot", "email": "bot@example.com"}}
        if data.get("sha"): payload["sha"] = data["sha"]
        response = requests.put(url, headers=headers, json=payload)
        if response.status_code in [200, 201]:
            latest_commit_sha = response.json()["commit"]["sha"]
            print(f"  - ✅ Pushed {file_path}")
        else:
            raise Exception(f"GitHub push failed for {file_path} with status {response.status_code}: {response.text}")
    print(f"✅ All files pushed. Latest commit SHA: {latest_commit_sha}")
    return latest_commit_sha

def get_file_from_repo(repo_name, file_path):
    print(f"Fetching '{file_path}' from '{repo_name}'...")
    url = f"{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/{repo_name}/contents/{file_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        content = base64.b64decode(data['content']).decode('utf-8')
        print(f"✅ Fetched '{file_path}' (sha: {data['sha']})")
        return {"content": content, "sha": data['sha']}
    else:
        raise Exception(f"Failed to fetch {file_path} with status {response.status_code}: {response.text}")

def enable_github_pages(repo_name):
    print(f"Enabling GitHub Pages for {repo_name}...")
    url = f"{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/{repo_name}/pages"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    payload = {"source": {"branch": "main", "path": "/"}}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        pages_url = response.json()["html_url"]
        print(f"✅ GitHub Pages enabled. It may take a minute to go live at: {pages_url}")
        return pages_url
    else:
        get_response = requests.get(url, headers=headers)
        if get_response.status_code == 200:
            pages_url = get_response.json()["html_url"]
            print(f"✅ GitHub Pages was already enabled at: {pages_url}")
            return pages_url
        else:
            raise Exception(f"GitHub Pages enabling failed with status {response.status_code}: {response.text}")

def notify_evaluation_api(payload):
    url = payload.pop("evaluation_url")
    print(f"📢 Notifying evaluation server at {url}...")
    headers = {"Content-Type": "application/json"}
    for i, delay in enumerate([1, 2, 4, 8]):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                print("✅ Successfully notified evaluation server.")
                return
            else:
                print(f"⚠️ Notification failed with status {response.status_code}. Retrying in {delay}s...")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Notification request failed: {e}. Retrying in {delay}s...")
        if i < 3: time.sleep(delay)
    raise Exception("Could not notify the evaluation server after multiple retries.")

# --- 4. CORE PROCESSING LOGIC (UPDATED) ---

def process_request(data):
    """Handles a round 1 'build' request using all available data."""
    repo_name = data["task"]
    print(f"🚀 Starting BUILD process for task: {repo_name}, round: 1")

    # --- ENHANCEMENT: Process attachments and use checks ---
    attachments_content = process_attachments(data.get("attachments"))
    checks = data.get("checks", [])
    
    html_content = generate_code_with_gemini(data["brief"], checks, attachments_content)
    readme_content = generate_readme_with_gemini(data["brief"])
    license_content = get_mit_license()

    repo_info = create_github_repo(repo_name)

    files_to_push = {
        "index.html": {"content": html_content},
        "README.md": {"content": readme_content},
        "LICENSE": {"content": license_content}
    }
    commit_sha = create_or_update_files_in_repo(repo_name, files_to_push, "feat: Initial commit")
    pages_url = enable_github_pages(repo_name)
    
    # --- ENHANCEMENT: Shortened wait time for robustness ---
    print("Waiting 30 seconds for GitHub Pages to deploy...")
    time.sleep(30)

    notification_payload = {
        "email": data["email"], "task": data["task"], "round": 1, "nonce": data["nonce"],
        "repo_url": repo_info["html_url"], "commit_sha": commit_sha, "pages_url": pages_url,
        "evaluation_url": data["evaluation_url"]
    }
    notify_evaluation_api(notification_payload)
    print(f"🎉 Successfully completed BUILD task: {repo_name}")

def process_revision_request(data):
    """Handles a round 2 'revise' request using all available data."""
    repo_name = data["task"]
    print(f"🚀 Starting REVISE process for task: {repo_name}, round: 2")

    # --- ENHANCEMENT: Process attachments and use checks for revision ---
    attachments_content = process_attachments(data.get("attachments"))
    checks = data.get("checks", [])
    
    original_html = get_file_from_repo(repo_name, "index.html")
    original_readme = get_file_from_repo(repo_name, "README.md")

    revised_html_content = revise_code_with_gemini(data["brief"], checks, attachments_content, original_html["content"])
    revised_readme_content = revise_readme_with_gemini(data["brief"], original_readme["content"])

    files_to_update = {
        "index.html": {"content": revised_html_content, "sha": original_html["sha"]},
        "README.md": {"content": revised_readme_content, "sha": original_readme["sha"]}
    }
    commit_sha = create_or_update_files_in_repo(repo_name, files_to_update, "feat: Apply revisions for round 2")
    pages_url = enable_github_pages(repo_name)
    
    # --- ENHANCEMENT: Shortened wait time for robustness ---
    print("Waiting 30 seconds for GitHub Pages to redeploy...")
    time.sleep(30)

    notification_payload = {
        "email": data["email"], "task": data["task"], "round": 2, "nonce": data["nonce"],
        "repo_url": f"https://github.com/{GITHUB_USERNAME}/{repo_name}", "commit_sha": commit_sha, "pages_url": pages_url,
        "evaluation_url": data["evaluation_url"]
    }
    notify_evaluation_api(notification_payload)
    print(f"🎉 Successfully completed REVISE task: {repo_name}")

# --- 5. FLASK API ENDPOINT (UNCHANGED) ---

@app.route('/api/build', methods=['POST'])
def handle_build_request():
    """Main webhook to receive requests from instructors."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    if "secret" not in data or data.get("secret") != MY_APP_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    print(f"✅ Secret verified for task: {data.get('task')}")

    try:
        if data.get("round") == 2:
            process_revision_request(data)
        else:
            process_request(data)
        return jsonify({"status": "Process completed successfully."}), 200
    except Exception as e:
        error_message = f"A critical error occurred: {str(e)}"
        print(f"❌ {error_message}")
        return jsonify({"error": error_message}), 500

# --- 6. LOCAL DEVELOPMENT SERVER (UNCHANGED) ---

if __name__ == '__main__':
    app.run(debug=True, port=5001)