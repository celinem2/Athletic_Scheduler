# Import required libraries
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from datetime import datetime
import os

# Define the function to authenticate with Google Calendar API
def authenticate_google_calendar():
    """
    Authenticates the user with Google Calendar API using OAuth2.
    Returns the credentials object.
    """
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None

    # Check if token.json exists (stores user's access and refresh tokens)
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If no valid credentials are available, prompt user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for future use
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())

    return creds


# Define the function to convert date and time to ISO 8601 format
def convert_to_iso8601(date_str, time_str):
    """
    Converts a human-readable date and time string into ISO 8601 format.
    
    Args:
        date_str (str): The date in a human-readable format (e.g., "January 25 2025").
        time_str (str): The time in a human-readable format (e.g., "4:00pm").
    
    Returns:
        str: The ISO 8601 formatted datetime string.
    """
    try:
        # Clean up date string (remove ordinal suffixes like "th", "st", etc.)
        date_str = date_str.replace("st", "").replace("nd", "").replace("rd", "").replace("th", "")

        # Combine date and time and parse into a datetime object
        dt = datetime.strptime(f"{date_str} {time_str}", "%B %d %Y %I:%M%p")

        # Convert to ISO 8601 format with UTC timezone
        return dt.isoformat() + "Z"
    except ValueError as e:
        raise ValueError(f"Invalid date or time format: {e}")


# Define the function to insert an event into Google Calendar
def insert_event_to_calendar(event_data):
    """
    Inserts an event into Google Calendar using the provided event data.
    
    Args:
        event_data (dict): A dictionary containing event details (title, date, start, end, etc.).
    
    Returns:
        None
    """
    credentials = authenticate_google_calendar()
    service = build('calendar', 'v3', credentials=credentials)

    try:
        # Convert start and end times to ISO 8601 format
        start_iso = convert_to_iso8601(event_data['date'], event_data['start'])
        end_iso = convert_to_iso8601(event_data['date'], event_data['end'])

        # Construct Google Calendar API event object
        event = {
            'summary': event_data['title'],
            'location': event_data.get('location', ''),
            'description': event_data.get('description', ''),
            'start': {
                'dateTime': start_iso,
                'timeZone': event_data.get('timeZone', 'UTC')
            },
            'end': {
                'dateTime': end_iso,
                'timeZone': event_data.get('timeZone', 'UTC')
            }
        }

        # Submit the event to Google Calendar
        response = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {response.get('htmlLink')}")
    except Exception as e:
        print(f"An error occurred while inserting an event: {e}")
