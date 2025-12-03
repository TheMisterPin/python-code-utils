import tkinter as tk
from tkinter import messagebox, simpledialog
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import os
import datetime
import pytz

SCOPES = ["https://mail.google.com/"]  # Allows full access to modify emails

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

def delete_old_unopened_emails(service, root, batch_size):
    """Delete all unopened emails older than 2 months with no labels and dynamically update progress."""
    total_deleted = 0
    continue_deleting = True
    progress_label = tk.Label(root, font=("Helvetica", 10))
    progress_label.pack(pady=20)

    while continue_deleting:
        two_months_ago = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=45)
        query = f"is:unread category:promotions"
        response = service.users().messages().list(userId="me", q=query, maxResults=500).execute()
        messages = response.get("messages", [])
        next_page_token = response.get("nextPageToken")

        while next_page_token and len(messages) < batch_size:
            response = service.users().messages().list(userId="me", q=query, maxResults=500, pageToken=next_page_token).execute()
            messages.extend(response.get("messages", []))
            next_page_token = response.get("nextPageToken")

        if messages:
            num_messages = len(messages)
            progress_label.config(text=f"Found {num_messages} messages to delete. Deletion process starting...")
            root.update()

            for index, message in enumerate(messages[:batch_size], start=1):
                service.users().messages().delete(userId="me", id=message["id"]).execute()
                progress_label.config(text=f"Deleted {index} of {num_messages} messages...")
                root.update()
                total_deleted += 1

            progress_label.config(text=f"{num_messages} messages deleted in this batch.")
            root.update()
        else:
            progress_label.config(text="No messages found to delete.")
            root.update()
            break  # Exit while loop if no messages found

        continue_deleting = messagebox.askyesno("Continue?", "Do you want to search and delete more emails?")
        if not continue_deleting:
            progress_label.config(text=f"Total messages deleted: {total_deleted}")
            root.update()
            break

def get_batch_size(root):
    """Get the batch size from the user."""
    batch_size = simpledialog.askinteger("Batch Size", "How many unread emails should be deleted? (1 - 25000):", parent=root, minvalue=1, maxvalue=25000)
    if batch_size is None or batch_size < 1 or batch_size > 25000:
        messagebox.showerror("Error", "Invalid batch size entered. Please enter a number between 1 and 25000.")
        return get_batch_size(root)
    return batch_size

def main():
    root = tk.Tk()
    root.title("Gmail Email Deleter")
    root.geometry("400x200")  # Set the window size

    proceed = messagebox.askyesno("Proceed?", "Do you want to connect to Gmail and delete emails?")
    if not proceed:
        messagebox.showinfo("Terminated", "Process terminated by the user.")
        root.destroy()
        return

    creds = authenticate_gmail()
    service = build("gmail", "v1", credentials=creds)
    batch_size = get_batch_size(root)  # Get user-selected batch size
    delete_old_unopened_emails(service, root, batch_size)
    messagebox.showinfo("Complete", "Email deletion process is complete.")
    root.destroy()

if __name__ == "__main__":
    main()
