import imaplib
import email
import os
from email.header import decode_header
from datetime import datetime, timedelta
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
                self.mail.login(self.email,self.app_password)
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
                    self.mail.login(self.email,self.app_password)
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

    def search_by_date_range_keywords_regex(self, from_date, to_date, keywords, subject_regex, require_all_keywords=False):
        
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

        # FIXED: Better IMAP OR query building
        def _build_keyword_criteria(keywords):
            if not keywords:
                return []
            
            if len(keywords) == 1:
                return ["SUBJECT", keywords[0]]
            
            # Build proper OR chain: OR (SUBJECT kw1) (SUBJECT kw2) for 2 keywords
            # For more keywords: OR (OR (SUBJECT kw1) (SUBJECT kw2)) (SUBJECT kw3)
            result = ["OR", ["SUBJECT", keywords[0]], ["SUBJECT", keywords[1]]]
            for kw in keywords[2:]:
                result = ["OR", result, ["SUBJECT", kw]]
            return result

        # Add keyword criteria if provided
        if keywords:
            keyword_criteria = _build_keyword_criteria(keywords)
            if keyword_criteria:
                criteria.extend(keyword_criteria)

        print(f"IMAP Search Criteria: {criteria}")

        # --- Search in IMAP ---
        try:
            # Convert nested lists to flat command for IMAP
            flat_criteria = self._flatten_criteria(criteria)
            print(f"Flat IMAP criteria: {flat_criteria}")
            
            status, data = self.mail.search(None, *flat_criteria)
        except Exception as e:
            print(f"IMAP search error: {e}")
            # Fallback: search with just date range
            try:
                status, data = self.mail.search(None, "SINCE", from_str, "BEFORE", before_str)
                print("Fallback: Using date range only")
            except Exception as e2:
                print(f"Fallback search also failed: {e2}")
                return []

        if status != "OK" or not data or not data[0]:
            print("No emails found by IMAP search")
            return []

        ids = data[0].split()
        print(f"IMAP found {len(ids)} emails")

        # --- Local filtering ---
        if subject_regex:
            pattern = re.compile(subject_regex, re.IGNORECASE)
        else:
            pattern = None

        results = []

        for mid in ids:
            try:
                status, msg_data = self.mail.fetch(mid, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])')
                if status != "OK" or not msg_data or not msg_data[0]:
                    continue

                msg = email.message_from_bytes(msg_data[0][1])
                subject_parts = decode_header(msg.get("Subject", ""))
                subject = "".join(
                    s.decode(enc or "utf-8", errors="ignore") if isinstance(s, bytes) else s
                    for s, enc in subject_parts
                ).strip()

                from_field = msg.get("From", "").strip()
                
                # IMPROVED: Better keyword filtering
                subj_lc = subject.lower()
                if keywords:
                    if require_all_keywords:
                        if not all(k.lower() in subj_lc for k in keywords):
                            continue
                    else:
                        if not any(k.lower() in subj_lc for k in keywords):
                            continue

                # IMPROVED: Only apply regex if provided
                if pattern and not pattern.search(subject):
                    continue

                # Get full email text
                def get_text(eid):
                    try:
                        result, msg_data = self.mail.fetch(eid, "(RFC822)")
                        raw_email = msg_data[0][1]
                        msg = email.message_from_bytes(raw_email)
                        
                        text_content = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    payload = part.get_payload(decode=True)
                                    if payload:
                                        text_content = payload.decode(errors="ignore")
                                        break
                                elif part.get_content_type() == "text/html" and not text_content:
                                    payload = part.get_payload(decode=True)
                                    if payload:
                                        text_content = payload.decode(errors="ignore")
                        else:
                            payload = msg.get_payload(decode=True)
                            if payload:
                                text_content = payload.decode(errors="ignore")
                        
                        return text_content
                    except Exception as e:
                        print(f"Error getting text for email {eid}: {e}")
                        return ""

                id_str = mid.decode() if isinstance(mid, bytes) else str(mid)
                email_text = get_text(id_str)
                
                results.append({
                    "id": id_str,
                    "subject": subject,
                    "from": from_field,
                    "date": msg.get("Date", "").strip(),
                    "text": email_text
                })
                
                print(f"✓ Added: {subject} | From: {from_field}")
                
            except Exception as e:
                print(f"Error processing email {mid}: {e}")
                continue

        print(f"Final results: {len(results)} emails after filtering")
        return results

    def _flatten_criteria(self, criteria):
        """Convert nested criteria list to flat list for IMAP"""
        result = []
        for item in criteria:
            if isinstance(item, list):
                result.extend(self._flatten_criteria(item))
            else:
                result.append(item)
        return result

    # NEW: Additional search methods for debugging
    def search_simple_date_range(self, from_date, to_date):
        """Simple date range search without keywords or regex"""
        def _to_imap_date(d):
            if isinstance(d, str):
                d = datetime.fromisoformat(d)
            if isinstance(d, datetime):
                d = d.date()
            return d.strftime("%d-%b-%Y")

        from_str = _to_imap_date(from_date)
        if isinstance(to_date, str):
            to_date = datetime.fromisoformat(to_date)
        elif not isinstance(to_date, datetime):
            to_date = datetime.combine(to_date, datetime.min.time())
        before_str = _to_imap_date(to_date + timedelta(days=1))

        status, data = self.mail.search(None, "SINCE", from_str, "BEFORE", before_str)
        if status != "OK" or not data or not data[0]:
            return []

        ids = data[0].split()
        results = []
        
        for mid in ids[:50]:  # Limit for debugging
            try:
                status, msg_data = self.mail.fetch(mid, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])')
                if status != "OK":
                    continue

                msg = email.message_from_bytes(msg_data[0][1])
                subject_parts = decode_header(msg.get("Subject", ""))
                subject = "".join(
                    s.decode(enc or "utf-8", errors="ignore") if isinstance(s, bytes) else s
                    for s, enc in subject_parts
                ).strip()

                results.append({
                    "id": mid.decode() if isinstance(mid, bytes) else str(mid),
                    "subject": subject,
                    "from": msg.get("From", "").strip(),
                    "date": msg.get("Date", "").strip(),
                    "text": ""  # Don't fetch text for debugging
                })
            except Exception as e:
                print(f"Error in simple search for {mid}: {e}")
                continue

        return results