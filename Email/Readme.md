# Gmail Email Cleaner

`email-deleter.py` opens a Tkinter dialog, authenticates with Gmail through OAuth, and deletes batches of unread promotional emails older than ~45 days. It is designed for light inbox maintenance when promotions start stacking up.

## Features

- Handles OAuth flows via `google-auth-oauthlib`; the first run will open the browser to authorize and write `token.pickle` for future runs.
- Provides a small GUI to confirm the deletion session, pick a batch size, and show progress while it calls `users.messages().delete`.
- Automatically skips emails that are marked as read or do not belong to the `promotions` category.

## Requirements

1. Download `credentials.json` from the Google Cloud console (Gmail API enabled) and place it beside the script.
2. Install dependencies: `pip install google-auth google-auth-oauthlib google-api-python-client pytz`.
3. Keep `token.pickle` in the folder after the first OAuth handshake so subsequent runs skip the browser prompt.

## How to Run

1. Start from the repository root and run `python Email/email-deleter.py`.
2. Confirm the GUI prompt, choose how many unread promotional emails to delete per batch, and let the script iterate until you stop it.

## Usage Example

```
$ python Email/email-deleter.py
Do you want to connect to Gmail and delete emails? (GUI prompt)
Found 423 messages to delete. Deletion process starting...
Deleted 250 of 423 messages...
```

If you need to re-authenticate (credentials rotated or `token.pickle` removed), the script will open a browser tab and refresh the tokens automatically.
