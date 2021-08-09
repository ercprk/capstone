#!/usr/bin/python3

import pickle
import os.path
import base64
import binascii
import html2text
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Function : GetMessageSenderAndTexts
# Does     : Get message details with the given ID
# Args:    : service : Authorized Gmail API service instance.
#            user_id : User's email address. The special value "me"
#                    can be used to indicate the authenticated user.
#            msg_id  : The ID of the Message required.
# Returns  : The sender of the message, and texts from the message
def GetMessageSenderAndTexts(service, user_id, msg_id):
    try:
        sender = ''
        texts = ''

        message = service.users().messages().get(userId=user_id, id=msg_id, format='full').execute()

        # Get sender
        for header in message['payload']['headers']:
            if header['name'] == 'From':
                sender = header['value']
                break

        # Get texts
        text_maker = html2text.HTML2Text()
        text_maker.ignore_emphasis = True
        text_maker.ignore_images = True
        text_maker.ignore_tables = True
        text_maker.ignore_links = True

        parts = list()
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if 'data' in part['body']:
                    parts.append(part)
        else:
            parts.append(message['payload'])

        for part in parts:
            mime_type = part['mimeType']
            data = part['body']['data']

            content_type = ''
            content_transfer_encoding = ''
            for header in part['headers']:
                if header['name'] == 'Content-Type':
                    content_type = header['value']
                elif header['name'] == 'Content-Transfer-Encoding':
                    content_transfer_encoding = header['value']

            # Always do base64 decoding, since Message returned by Gmail API is always base64 encoded:
            # https://stackoverflow.com/questions/56087503/gmail-returns-base64-encoded-but-lists-as-quotable-printable
            if mime_type == 'text/plain':
                if 'UTF-8' in content_type or 'utf-8' in content_type:
                    texts += str(base64.urlsafe_b64decode(data), encoding='utf-8', errors='ignore')
                elif 'iso-8859-1' in content_type:
                    texts += str(base64.urlsafe_b64decode(data), encoding='iso-8859-1', errors='ignore')
                elif 'us-ascii' in content_type:
                    texts += str(base64.urlsafe_b64decode(data), encoding='us-ascii', errors='ignore')
                elif 'windows-1252' in content_type:
                    texts += str(base64.urlsafe_b64decode(data), encoding='windows-1252', errors='ignore')
                else:
                    print('Unknown content type in text/plain:\n\t%s' % content_type)
            elif mime_type == 'text/html':
                if 'UTF-8' in content_type or 'utf-8' in content_type:
                    texts += text_maker.handle(str(base64.urlsafe_b64decode(data), encoding='utf-8', errors='ignore'))
                elif 'iso-8859-1' in content_type:
                    texts += text_maker.handle(str(base64.urlsafe_b64decode(data), encoding='iso-8859-1', errors='ignore'))
                elif 'us-ascii' in content_type:
                    texts += text_maker.handle(str(base64.urlsafe_b64decode(data), encoding='us-ascii', errors='ignore'))
                elif 'windows-1252' in content_type:
                    texts += text_maker.handle(str(base64.urlsafe_b64decode(data), encoding='windows-1252', errors='ignore'))
                else:
                    print('Unknown content type in text/html:\n\t%s' % content_type)
            else:
                print('Unknown MIME type:\n\t%s' % mime_type)

        texts += message['snippet']
    except HttpError as error:
        print('An HttpError occurred: %s' % error)
    except binascii.Error as error:
        print('A binascii.Error occurred: %s' % error)
    except KeyError as error:
        print('A KeyError occurred: %s' % error)
    finally:
        return sender, texts

# Function : ListMessageMatchingQuery
# Does     : List all Messages of the user's mailbox matching the query.
# Args     : service : Authorized Gmail API service instance.
#            user_id : User's email address. The special value "me"
#                     can be used to indicate the authenticated user.
#            query   : String used to filter messages returned.
#                      Eg.- 'from:user@some_domain.com' for Messages from a
#                      particular sender.
# Returns  : List of Messages that match the criteria of the query. Note that
#            the returned list contains Message IDs, you must use get with the
#            appropriate ID to get the details of a Message.
def ListMessagesMatchingQuery(service, user_id):

    query = "in:anywhere"

    response = service.users().messages().list(userId=user_id, q=query, maxResults=511).execute()

    messages = []
    if 'messages' in response:
        messages.extend(response['messages'])

    pageToken = None
    if 'nextPageToken' in response:
        pageToken = response['nextPageToken']

    while pageToken:
        response = service.users().messages().list(userId=user_id, q=query, maxResults=511, pageToken=pageToken).execute()
        messages.extend(response['messages'])
        if 'nextPageToken' in response:
            pageToken = response['nextPageToken']
        else:
            break

    return messages


def main():

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    mails = ListMessagesMatchingQuery(service, "me")
    num_mails = len(mails)
    print(f"There are {num_mails} mails.")

    fo_data = open(file="unsanitized_data.txt", mode="w", encoding="utf-8", errors="ignore")
    fo_senders = open(file="senders.txt", mode="w", encoding="utf-8", errors="ignore")
    print("Scraping...")
    counter = 0

    unique_senders = set()

    for mail in mails:
        id = mail['id']
        sender, texts = GetMessageSenderAndTexts(service, "me", id)
        fo_data.write(texts)
        fo_senders.write(sender + '\n')

        tokens = sender.split(' <')
        if len(tokens) > 1:
            name = tokens[0]
            unique_senders.add(name.strip('"'))

        counter = counter + 1
        if counter % 100 == 0 or counter == num_mails:
            print('%d emails scraped (%.2f%% complete)' % (counter, float(counter / num_mails) * 100))

    fo_data.close()
    fo_senders.close()

    fo_unique_senders = open(file="unique_senders.txt", mode="w", encoding="utf-8", errors="ignore")
    for unique_sender in unique_senders:
        fo_unique_senders.write(unique_sender + '\n')
    fo_unique_senders.close()

if __name__ == '__main__':
    main()
