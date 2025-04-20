# Stock_analysis
Complete automated system: Just upload a stock report file to your Google Drive folder and relax — you'll receive a detailed analysis report directly in your email.

# 📊 AI-Powered Stock Market Document Analyzer

This project is an end-to-end automation system that reads financial PDFs uploaded to a **Google Drive folder**, analyzes them using **GPT-40** (via Azure OpenAI), and sends a detailed report to your email.

---

## 🚀 Features

- 🔄 Automatically detects new PDF uploads to a connected Google Drive folder
- 📑 Uses OCR and LLMs to extract & interpret market insights
- 📈 Performs **fundamental** and **technical** analysis (Buffett, Lynch, Minervini, Darvas style)
- 📬 Sends you a **full analysis report via email**
- 🔐 Uses secure API keys and email authentication

---

## 🗂 Project Structure
```env

auto stock-analysizer/
│
├── agent_pipeline.py
├── gdrive_watcher       👈 monitored folder
├── credentials.json 
├── token.json
```



## 🔑 Configuration
### Azure OpenAI API Keys (in agent_pipeline.py)
```env
os.environ["AZURE_OPENAI_API_KEY"] = "your-azure-api-key"
os.environ["AZURE_OPENAI_ENDPOINT"] = "your-endpoint-url"
os.environ["OPENAI_API_VERSION"] = "your app version"
```

## Gmail SMTP Settings 
EMAIL_ADDRESS = "youremail@gmail.com"
EMAIL_PASSWORD = "your-app-password"
## 🔐 Enable 2-Step Verification in Gmail, then generate an App Password:
https://myaccount.google.com/apppasswords

## ☁️ Google Drive Setup
```env
- Go to Google Cloud Console
- Create a new project
- Enable Google Drive API
- Create OAuth 2.0 Client ID
- Download both:
- credentials.json
-token.json (will be created on first auth run)
```

## In gdrive_watcher.py, update your folder ID:
FOLDER_ID = "your-google-drive-folder-id"
## 📌 To get the folder ID:
Open your Google Drive folder → Copy the ID from the URL:
https://drive.google.com/drive/folders/1A2B3C4D5E6F7G8H9I ← This is the folder ID.
## Start the Google Drive Watcher
python gdrive_watcher.py

