from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
import os

# todo удалить можно
# def get_drive():
#     # путь к credentials.json рядом с кодом
#     creds_path = os.path.join(os.path.dirname(__file__), "..", "kimibot-471115-e680904a37bc.json")
#     creds_path = os.path.abspath(creds_path)
#
#     scopes = ["https://www.googleapis.com/auth/drive"]
#
#     gauth = GoogleAuth()
#     gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scopes)
#
#     return GoogleDrive(gauth)