import tkinter as tk
from tkinter import messagebox, simpledialog
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import os
import webbrowser

SCOPES = ["https://mail.google.com/"]


def authenticate_gmail():
    """Authenticate and create a service client for the Gmail API using OAuth."""
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return creds


def get_header(headers, name):
    for header in headers:
        if header.get("name") == name:
            return header.get("value")
    return "(unknown)"


def open_email(service, message_id, root):
    detail = (
        service.users()
        .messages()
        .get(
            userId="me",
            id=message_id,
            format="metadata",
            metadataHeaders=["Subject", "From", "Date"],
        )
        .execute()
    )
    headers = detail.get("payload", {}).get("headers", [])
    subject = get_header(headers, "Subject")
    sender = get_header(headers, "From")
    date = get_header(headers, "Date")
    snippet = detail.get("snippet", "")

    detail_text = (
        f"Subject: {subject}\n"
        f"From: {sender}\n"
        f"Date: {date}\n\n"
        f"Snippet:\n{snippet}"
    )
    messagebox.showinfo("Email Preview", detail_text)

    should_open = messagebox.askyesno(
        "Open in Browser?", "Open this email in Gmail (browser)?"
    )
    if should_open:
        webbrowser.open(f"https://mail.google.com/mail/u/0/#inbox/{message_id}")
        messagebox.showinfo("Opened", "Email opened in your default browser.")
    else:
        messagebox.showinfo("Complete", "Email preview shown only.")

    root.destroy()


def main():
    root = tk.Tk()
    root.title("Gmail Email Opener")
    root.geometry("400x200")

    proceed = messagebox.askyesno("Proceed?", "Connect to Gmail and open an email?")
    if not proceed:
        messagebox.showinfo("Terminated", "Process terminated by the user.")
        root.destroy()
        return

    message_id = simpledialog.askstring(
        "Email ID", "Enter the Gmail message ID to open:", parent=root
    )
    if not message_id:
        messagebox.showinfo("Cancelled", "No email ID provided.")
        root.destroy()
        return

    creds = authenticate_gmail()
    service = build("gmail", "v1", credentials=creds)

    try:
        open_email(service, message_id, root)
    except Exception as exc:
        messagebox.showerror("Error", f"Unable to open email: {exc}")
        root.destroy()


if __name__ == "__main__":
    main()
