# gdrive_watcher.py
import time
import os
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from agent_pipeline import app
from email.message import EmailMessage
import smtplib, ssl

# Settings
FOLDER_ID = "your gdrive folder_id"
PROCESSED_IDS = set()
EMAIL_SENDER = "give sender email id"
EMAIL_PASSWORD = "give your emaill app password"
EMAIL_RECEIVER = "dipanjan761@gmail.com"

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authenticate_drive():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def get_new_pdfs(service):
    results = service.files().list(
        q=f"'{FOLDER_ID}' in parents and mimeType='application/pdf'",
        spaces='drive',
        fields='files(id, name, modifiedTime)'
    ).execute()
    files = results.get('files', [])
    return [f for f in files if f['id'] not in PROCESSED_IDS]

def download_pdf(service, file_id, filename):
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(filename, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

def process_and_email(file_path):
    input_data = {"question": file_path}
    final_summary = None

    for output in app.stream(input_data):
        for key, value in output.items():
            final_summary = value.get("final_summary")

    if final_summary:
        summary_path = file_path + ".summary.txt"
        with open(summary_path, "w") as f:
            f.write(final_summary)
        send_email(summary_path)

def send_email(attachment_path):
    msg = EmailMessage()
    msg["Subject"] = "✅ Analysis is Ready..."
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg.set_content("The Stock Analysis is ready. Please find the attached analysis.")

    with open(attachment_path, "rb") as f:
        data = f.read()
        name = os.path.basename(attachment_path)
    msg.add_attachment(data, maintype="application", subtype="octet-stream", filename=name)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

    print(f"[📧] Email sent with attachment: {name}")

def main():
    service = authenticate_drive()
    print("📂 Watching Google Drive folder...")

    while True:
        new_files = get_new_pdfs(service)
        for file in new_files:
            file_id = file['id']
            filename = f"downloads/{file['name']}"
            os.makedirs("downloads", exist_ok=True)

            print(f"[+] New PDF: {file['name']}")
            download_pdf(service, file_id, filename)
            process_and_email(filename)
            PROCESSED_IDS.add(file_id)

        time.sleep(10)  # Check every 10 seconds

if __name__ == "__main__":
    main()
