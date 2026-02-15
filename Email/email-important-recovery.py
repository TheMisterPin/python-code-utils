import tkinter as tk
from tkinter import messagebox, simpledialog
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import os

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


def fetch_important_messages(service, max_results):
    query = "is:important (in:trash OR in:spam)"
    messages = []
    page_token = None

    while len(messages) < max_results:
        batch_size = min(500, max_results - len(messages))
        response = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=batch_size, pageToken=page_token)
            .execute()
        )
        messages.extend(response.get("messages", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return messages


def recover_messages(service, messages, status_label):
    recovered = 0
    for index, message in enumerate(messages, start=1):
        service.users().messages().modify(
            userId="me",
            id=message["id"],
            body={"removeLabelIds": ["TRASH", "SPAM"], "addLabelIds": ["INBOX"]},
        ).execute()
        recovered += 1
        status_label.config(text=f"Recovered {index} of {len(messages)} messages...")
        status_label.update()
    return recovered


def populate_message_list(service, messages, text_widget):
    text_widget.delete("1.0", tk.END)
    for message in messages:
        detail = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=message["id"],
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
        text_widget.insert(
            tk.END,
            f"ID: {message['id']}\nSubject: {subject}\nFrom: {sender}\nDate: {date}\nSnippet: {snippet}\n\n",
        )
    text_widget.update()


def get_max_results(root):
    max_results = simpledialog.askinteger(
        "Recovery Size",
        "How many important emails should be recovered? (1 - 1000):",
        parent=root,
        minvalue=1,
        maxvalue=1000,
    )
    if max_results is None:
        return None
    if max_results < 1 or max_results > 1000:
        messagebox.showerror("Error", "Please enter a number between 1 and 1000.")
        return get_max_results(root)
    return max_results


def main():
    root = tk.Tk()
    root.title("Gmail Important Email Recovery")
    root.geometry("700x500")

    proceed = messagebox.askyesno(
        "Proceed?", "Connect to Gmail and recover important emails?"
    )
    if not proceed:
        messagebox.showinfo("Terminated", "Process terminated by the user.")
        root.destroy()
        return

    max_results = get_max_results(root)
    if max_results is None:
        messagebox.showinfo("Cancelled", "No recovery size provided.")
        root.destroy()
        return

    creds = authenticate_gmail()
    service = build("gmail", "v1", credentials=creds)

    status_label = tk.Label(root, font=("Helvetica", 10))
    status_label.pack(pady=10)

    text_frame = tk.Frame(root)
    text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=text_widget.yview)

    status_label.config(text="Searching for important emails in Trash/Spam...")
    root.update()

    messages = fetch_important_messages(service, max_results)

    if not messages:
        status_label.config(text="No important emails found to recover.")
        messagebox.showinfo("Complete", "No important emails found in Trash/Spam.")
        root.update()
        root.destroy()
        return

    populate_message_list(service, messages, text_widget)
    status_label.config(text=f"Found {len(messages)} important emails.")
    root.update()

    should_recover = messagebox.askyesno(
        "Recover?", f"Recover {len(messages)} important emails back to Inbox?"
    )
    if not should_recover:
        status_label.config(text="Recovery cancelled. Messages listed only.")
        root.update()
        root.mainloop()
        return

    recovered = recover_messages(service, messages, status_label)
    status_label.config(text=f"Recovered {recovered} important emails.")
    root.update()
    messagebox.showinfo("Complete", "Important email recovery is complete.")

    root.mainloop()


if __name__ == "__main__":
    main()
