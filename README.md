# Athletic Trainer Scheduler

This is an AI-powered scheduling assistant designed for student-athletes to book, reschedule, and cancel appointments with athletic trainers. The scheduler integrates with Google Sheets to manage trainer availability and prevent overlapping bookings.

---

## 🚀 Features

- 📅 Athlete appointment booking
- 🔁 Prevents double bookings
- 🗓 Trainer availability dashboard
- 📂 File upload support for schedule templates

---

## 🛠 Tech Stack

- **Backend:** Python (Flask)
- **AI Integration:** GPT-4 API (OpenAI)
- **Data Storage:** Google Sheets API
- **Frontend:** HTML, CSS
- **Deployment:** Google Cloud Functions or Heroku

---

## 📁 Folder Structure

/static/
/css/
buttons.css
style.css
/images/
default-profile.png
shark-logo.png
default_schedule_template.xlsx

/templates/
availability.html
base.html
generate.html
index.html
login.html
register.html
success.html
trainer_availability.html
upload.html
upload_success.html

app.py
helpers.py
availability.json
Athletic Trainer Schedule.xlsx
requirements.txt

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/athletic-scheduler.git
cd athletic-scheduler

2. Create and Activate Virtual Environment
python -m venv venv
.\venv\Scripts\activate

3. Install Dependencies
pip install -r requirements.txt

4. Set up enviromental variables
OPENAI_API_KEY=your-openai-api-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
FLASK_SECRET_KEY=your-flask-secret-key

5. Run the application
python app.py and click the provided link
