import imaplib
import email
import os
import datetime
from email.header import decode_header
import re
class Email(): 
    def __init__(self, email, app_password, imap):
        self.email = email 
        self.app_password = app_password
        self.imap = imap
        self.mail = ''

    def login(self):
        # First time login
        if self.mail == '':
            try : 
                self.mail = imaplib.IMAP4_SSL(self.imap)
                self.mail.login(self.email,self.password)
            except Exception as e: 
                print(f"Error encountered while loggining in {e}")
            else : 
                self.mail.select("inbox")

            return self.mail 
        else: 
            # Login called on an already existing mail object
            try: 
                self.mail.select("inbox")
            except Exception as e:
                try:  
                    self.mail.login(self.email,self.password)
                except Exception as e : 
                    print(f'We request you to consider and resolve the following error {e}')
            else : 
                return self.mail
    def logout(self):
        try:
            self.mail.logout()
        except Exception as e: 
            print(f"Error encountered while logging out  {e}")

        else :
            
            print(f'Successfully logged out of {self.email}')

            # for data security purchases, clear the mail object to wipe out any information about the most recent interaction
            del self.mail
    
    def search_by_date_range_keywords_regex( self  , mail,
    from_date,             # datetime/date or "YYYY-MM-DD"
    to_date,               # datetime/date or "YYYY-MM-DD"
    keywords,              # list[str]
    subject_regex,         # regex pattern string
    require_all_keywords=False):
        
    # --- Convert to IMAP date strings ---
        def _to_imap_date(d):
            if isinstance(d, str):
                d = datetime.fromisoformat(d)
            if isinstance(d, datetime):
                d = d.date()
            return d.strftime("%d-%b-%Y")

        from_str = _to_imap_date(from_date)



        # Add 1 day to to_date for BEFORE clause
        if isinstance(to_date, str):
            to_date = datetime.fromisoformat(to_date)
        elif not isinstance(to_date, datetime):
            to_date = datetime.combine(to_date, datetime.min.time())
        before_str = _to_imap_date(to_date + timedelta(days=1))

        # --- Build IMAP criteria ---
        criteria = ["SINCE", from_str, "BEFORE", before_str]

        def _imap_or_subjects(keywords):
            if not keywords:
                return []
            tree = ["SUBJECT", f'"{keywords[0]}"']
            for kw in keywords[1:]:
                tree = ["OR"] + tree + ["SUBJECT", f'"{kw}"']
            return tree

        criteria += _imap_or_subjects(keywords or [""])

        # --- Search in IMAP ---
        status, data = mail.search(None, *criteria)
        if status != "OK" or not data or not data[0]:
            return []

        ids = data[0].split()

        # --- Local filtering ---
        pattern = re.compile(subject_regex, re.IGNORECASE)
        results = []

        for mid in ids:
            status, msg_data = mail.fetch(mid, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])')
            if status != "OK" or not msg_data or not msg_data[0]:
                continue

            msg = email.message_from_bytes(msg_data[0][1])
            subject_parts = decode_header(msg.get("Subject", ""))
            subject = "".join(
                s.decode(enc or "utf-8", errors="ignore") if isinstance(s, bytes) else s
                for s, enc in subject_parts
            ).strip()

            subj_lc = subject.lower()

            if keywords:
                if require_all_keywords:
                    if not all(k.lower() in subj_lc for k in keywords):
                        continue
                else:
                    if not any(k.lower() in subj_lc for k in keywords):
                        continue

            if not pattern.search(subject):
                continue



            def get_text(eid):
                result, msg_data = self.mail.fetch(eid, "(RFC822)")
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/html":
                            html = part.get_payload(decode=True).decode(errors="ignore")
                        elif part.get_content_type() == "text/plain":
                            text = part.get_payload(decode=True).decode(errors="ignore")
                    
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")
                splitted_text = text.split('\n')
                for i in range(len(splitted_text)):
                    print(f"{i} -- {splitted_text[i]}")
                if splitted_text[29].split() == []:
                    print('')
                else :
                    print(splitted_text[29].split()[4])
                    
                return text
            id = mid.decode() if isinstance(mid, bytes) else str(mid)
            results.append({
                "id": id,
                "subject": subject,
                "from": msg.get("From", "").strip(),
                "date": msg.get("Date", "").strip(),
                "text": get_text(id)
            })

        return results



    



            

