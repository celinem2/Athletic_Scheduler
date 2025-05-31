from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import google.oauth2.credentials
from googleapiclient.discovery import build
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re
import os
import json
import pytz
import pandas as pd

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_key')

# Google API setup
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
CLIENT_SECRETS_FILE = "client_secret_1.json"
SCOPES = ['https://www.googleapis.com/auth/calendar']

# OpenAI API setup
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OpenAI API key not found. Please check your .env file.")

client = OpenAI(api_key=openai_api_key)
ASSISTANT_ID = "asst_8KSsFHPv61i0Dh1zY6Lr4S7V"

def require_role(role):
    if session.get('role') != role:
        return redirect(url_for('logout'))

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    flow.redirect_uri = url_for('oauth2callback', _external=True)
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    flow.redirect_uri = url_for('oauth2callback', _external=True)
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    with open('credentials.json', 'w') as cred_file:
        json.dump(session['credentials'], cred_file)
    if session.get('role') == 'trainer':
        return redirect(url_for('upload'))
    else:
        return redirect(url_for('view_availability'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    res = require_role('trainer')
    if res:
        return res

    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file.filename.endswith('.xlsx'):
            try:
                import pandas as pd
                from datetime import datetime, timedelta
                import json

                df = pd.read_excel(uploaded_file)
                required_columns = {'trainer_email', 'date', 'start_time', 'end_time', 'sport'}
                if not required_columns.issubset(df.columns):
                    return "Missing columns", 400

                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                df['start_time'] = df['start_time'].astype(str)
                df['end_time'] = df['end_time'].astype(str)

                grouped = {}

                for _, row in df.iterrows():
                    trainer = row['trainer_email']
                    date = row['date']
                    start_time = row['start_time']
                    end_time = row['end_time']
                    sport = str(row['sport']).strip().lower()

                    start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M:%S")
                    end_dt = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M:%S")

                    options = []
                    current = start_dt
                    while current + timedelta(minutes=30) <= end_dt:
                        options.append(current.strftime("%H:%M"))
                        current += timedelta(minutes=30)

                    block = {
                        "start_time": start_time[:5],
                        "end_time": end_time[:5],
                        "start_options": options,
                        "sport": sport
                    }

                    grouped.setdefault(trainer, {}).setdefault(date, []).append(block)

                with open("availability.json", "w") as f:
                    json.dump(grouped, f, indent=4)

                return render_template('upload_success.html')

            except Exception as e:
                return f"Error: {e}", 500

        return "Unsupported file format", 400

    return render_template('upload.html')

@app.route('/availability/view')
def view_availability():
    res = require_role('athlete')
    if res: return res
    if os.path.exists("availability.json"):
        with open("availability.json") as f:
            availability = json.load(f)
    else:
        availability = {}
    return render_template('availability.html', availability=availability)

@app.route('/trainer/<trainer_email>')
def trainer_availability(trainer_email):
    res = require_role('athlete')
    if res: return res
    if not os.path.exists("availability.json"):
        return "No availability found.", 404
    with open("availability.json") as f:
        data = json.load(f)
    trainer_schedule = data.get(trainer_email)
    if not trainer_schedule:
        return "Trainer not found.", 404
    return render_template('trainer_availability.html', trainer_email=trainer_email, schedule=trainer_schedule)

def parse_time_flexibly(date_str, time_str):
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    
@app.route('/book-slot', methods=['POST'])
def book_slot():
    res = require_role('athlete')
    if res: return res

    trainer_email = request.form['trainer_email']
    date = request.form['date']
    start = request.form['start_time']
    duration_minutes = int(request.form['duration'])

    try:
        tz = "America/New_York"
        start_dt = parse_time_flexibly(date, start)
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        start_iso = pytz.timezone(tz).localize(start_dt).isoformat()
        end_iso = pytz.timezone(tz).localize(end_dt).isoformat()
    except Exception as e:
        return f"Failed to format date/time: {str(e)}", 400

    event = {
        "title": f"Training Session with {trainer_email.split('@')[0]}",
        "start": start_iso,
        "end": end_iso,
        "location": "LIU Athletic Training Room",
        "description": "",
        "timeZone": tz,
        "trainer": trainer_email
    }

    session['events'] = [event]

    # Update availability to remove booked slot
    try:
        with open("availability.json", "r") as f:
            availability = json.load(f)
    except:
        availability = {}

    for trainer, dates in availability.items():
        if trainer != trainer_email:
            continue
        for slot_date, blocks in dates.items():
            if slot_date != date:
                continue
            for block in blocks:
                remaining = []
                for option in block['start_options']:
                    option_dt = parse_time_flexibly(date, option)
                    option_end = option_dt + timedelta(minutes=30)
                    if option_end <= start_dt or option_dt >= end_dt:
                        remaining.append(option)
                block['start_options'] = remaining
            availability[trainer][slot_date] = [b for b in blocks if b['start_options']]
        availability[trainer] = {d: b for d, b in availability[trainer].items() if b}
    availability = {t: d for t, d in availability.items() if d}

    with open("availability.json", "w") as f:
        json.dump(availability, f, indent=4)

    return render_template('success.html', start=start_dt.strftime("%H:%M"), end=end_dt.strftime("%H:%M"), date=date, trainer=trainer_email.split("@")[0].replace(".", " ").title())


@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/set-role/<role>')
def set_role(role):
    session['role'] = role
    return redirect(url_for('login'))

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes,
    }

if __name__ == '__main__':
    app.run(debug=True)
