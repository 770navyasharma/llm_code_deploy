# LLM Code Deployment Automator

![Project Status](https://img.shields.io/badge/status-complete-success)
![Python Version](https://img.shields.io/badge/python-3.9+-blue)
![Framework](https://img.shields.io/badge/framework-Flask-black)
![Deployment](https://img.shields.io/badge/deployment-Vercel-black)

This project is an automated application that receives instructions via an API, uses the Google Gemini LLM to generate a complete web application, and then automatically creates a GitHub repository and deploys the new application to GitHub Pages. It is designed to handle multi-round tasks, including initial creation (Build) and subsequent updates (Revise).

---

## 🏛️ Project Architecture

The application follows a serverless architecture, receiving a request and orchestrating a series of API calls to build and deploy a new web application without manual intervention.

**Workflow:**
`Instructor POST Request` → `Vercel API Endpoint` → `(Gemini API + GitHub API)` → `Deployed GitHub Pages Site` → `Webhook Notification`

---

## ✨ Features

-   **API-Driven Automation:** Fully automated workflow triggered by a single JSON POST request.
-   **Intelligent Code Generation:** Utilizes the Gemini AI (`gemini-1.5-pro-latest`) to generate HTML, CSS, and JavaScript based on a natural language `brief`.
-   **Smart Prompt Engineering:** Enhances AI accuracy by passing `attachments` (like CSV/JSON data) and `checks` (evaluation criteria) directly into the prompt.
-   **Automated Git & Deployment:** Automatically creates a new public GitHub repository, pushes the generated code, adds an MIT License, and enables GitHub Pages.
-   **Multi-Round Capability:** Handles both initial `round: 1` build requests and `round: 2` revision requests to update existing code.
-   **Webhook Notifications:** Pings an `evaluation_url` upon successful completion to notify an external service.

---

## 🛠️ Technology Stack

-   **Backend:** Python 3.9+
-   **Framework:** Flask
-   **Deployment:** Vercel (Serverless Functions)
-   **AI Model:** Google Gemini API (`gemini-1.5-pro-latest`)
-   **VCS & Hosting:** GitHub API & GitHub Pages

---

## 🚀 Setup and Deployment

This guide covers setting up the project locally and deploying it to Vercel.

### 1. Local Setup

**Prerequisites:**
-   Python 3.9+
-   Node.js and npm (for installing the Vercel CLI)

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/770nayasharma/llm-code-deploy.git](https://github.com/770nayasharma/llm-code-deploy.git)
    cd llm-code-deploy
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create an environment file (`.env`):**
    Create a file named `.env` in the root of the project and add your secret keys.
    ```env
    # .env file
    GEMINI_API_KEY="your_google_gemini_api_key"
    GITHUB_TOKEN="your_github_personal_access_token"
    GITHUB_USERNAME="your_github_username"
    MY_APP_SECRET="your_strong_secret_password"
    ```

### 2. Deployment to Vercel

1.  **Install the Vercel CLI:**
    ```bash
    npm install -g vercel
    ```

2.  **Log in to your Vercel account:**
    ```bash
    vercel login
    ```

3.  **Link your local project to Vercel:**
    Run this command from the project's root directory. It will prompt you to link to a new or existing project.
    ```bash
    vercel
    ```

4.  **Add Environment Variables to Vercel:**
    The deployed application cannot read the local `.env` file. You must add the secrets to the Vercel project's settings:
    -   Go to your project on the Vercel dashboard.
    -   Navigate to `Settings` > `Environment Variables`.
    -   Add each of the four keys from your `.env` file (`GEMINI_API_KEY`, `GITHUB_TOKEN`, etc.) to the **Production** environment.

5.  **Turn Off Deployment Protection:**
    By default, Vercel protects new deployments. To allow your API to be publicly accessible:
    -   In your Vercel project dashboard, go to `Settings` > `Deployment Protection`.
    -   Disable "Vercel Authentication".

6.  **Deploy to Production:**
    Run the final command to push your code and environment variables live.
    ```bash
    vercel --prod
    ```
    Vercel will provide you with the final production URL.

---

## 💡 Usage

Interact with the deployed API by sending `POST` requests. The final API URL will be your Vercel production URL plus the `/api/build` route.

### Example: Round 1 (Build) Request

This example uses the "sum-of-sales" task, which includes `attachments` and `checks`.

```bash
curl [https://your-production-url.vercel.app/api/build](https://your-production-url.vercel.app/api/build) \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "your_strong_secret_password",
    "task": "sum-of-sales-test",
    "round": 1,
    "email": "your-email@example.com",
    "nonce": "sales-test-123",
    "evaluation_url": "[https://webhook.site/your-unique-id](https://webhook.site/your-unique-id)",
    "brief": "Create a single-page site that calculates the total sales from the attached data.csv file. The page title should be ''Sales Report''. Display the final sum inside an HTML element with the id ''total-sales''.",
    "checks": [
      "The page title is exactly ''Sales Report''",
      "The page contains an element with id ''total-sales''",
      "The text inside #total-sales is 350"
    ],
    "attachments": [{
      "name": "data.csv",
      "url": "data:text/csv;base64,cHJvZHVjdCxzYWxlcwpBcHBsZSwxNTUKQmFuYW5hLDc1Ck9yYW5nZSwxMjU="
    }]
  }'

```

### Example: Round 2 (Revise) Request

This command updates the repository created in the previous step.

```bash
  curl [https://your-production-url.vercel.app/api/build](https://your-production-url.vercel.app/api/build) \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "your_strong_secret_password",
    "task": "sum-of-sales-test",
    "round": 2,
    "email": "your-email@example.com",
    "nonce": "sales-revision-456",
    "evaluation_url": "[https://webhook.site/your-unique-id](https://webhook.site/your-unique-id)",
    "brief": "Update the ''Sales Report'' page. Add a Bootstrap table below the total to display each product and its individual sale amount from the original data.csv."
  }'

```

#📜 License

This project is licensed under the MIT License.

  
