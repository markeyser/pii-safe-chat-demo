# Importing necessary modules
import os
from dotenv import load_dotenv
import openai
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
import gradio as gr  # 3.32

# Load the environment variables from the local .env file
# NOTE: while using Jupyter Notebooks with VS Code, even when the .env
# is located in the root directory of the project, you must use ../.env
# instead of .env
load_dotenv()

# Check if the .env file exists in the Google Drive path
if os.path.exists("/content/drive/MyDrive/Projects/.env"):
    load_dotenv("/content/drive/MyDrive/Projects/.env")
    COLAB = True
    print("Note: using Google Colab")
else:
    COLAB = False
    print("Note: not using Google Colab")


# Retrieving API keys from the environment
openai.api_key = os.getenv("OPENAI_API_KEY")
username = os.getenv("PII_SAFE_CHAT_USERNAME")
password = os.getenv("PII_SAFE_CHAT_PASSWORD")

print(username)