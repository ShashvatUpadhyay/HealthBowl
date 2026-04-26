# 🥗 HealthBowl - AI-Powered Nutrition & Health Marketplace

**HealthBowl** is a multimodal Django-based web application designed to bridge the gap between users and healthy lifestyle products. It features an intelligent AI Chatbot powered by **Groq (LLaMA 3)** that provides personalized health advice, diet plans, and product recommendations from the integrated store.

## 🚀 Key Features

* **AI Health Assistant:** Integrated chatbot using RAG (Retrieval-Augmented Generation) to answer health-related queries and recommend products from the store.
* **Product Marketplace:** Browse and purchase health-focused products like protein powders, vitamins, and organic snacks.
* **Admin Dashboard:** Full control over inventory management, orders, and user queries.
* **Modern UI:** Built with Django templates, tailored for a clean and responsive user experience.
* **Secure Config:** Environment variables management for API keys and sensitive data.

## 🛠️ Tech Stack

* **Backend:** Django (Python)
* **AI Engine:** Groq API (LLaMA-3-8b)
* **Database:** SQLite (Development) / PostgreSQL (Production)
* **Frontend:** HTML5, CSS3, JavaScript
* **Deployment:** GitHub & PythonAnywhere

## 📦 Installation & Setup

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/ShashvatUpadhyay/HealthBowl.git](https://github.com/ShashvatUpadhyay/HealthBowl.git)
    cd HealthBowl
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    # Activate it:
    # Windows: venv\Scripts\activate
    # Mac/Linux: source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Environment Variables:**
    Create a `.env` file in the root directory and add your Groq API Key:
    ```env
    GROQ_API_KEY=your_groq_api_key_here
    ```

5.  **Run Migrations & Start Server:**
    ```bash
    python manage.py migrate
    python manage.py runserver
    ```
    Access the app at `http://127.0.0.1:8000/`

## 📂 Project Structure

```text
├── HLIFE/              # Main Project Configuration
├── store/              # Product Marketplace & Cart Logic
├── static/             # CSS, Images, and JS files
├── bot.py              # AI Chatbot Logic (Groq Integration)
├── manage.py           # Django CLI
├── .env.example        # Template for environment variables
└── requirements.txt    # Project dependencies
