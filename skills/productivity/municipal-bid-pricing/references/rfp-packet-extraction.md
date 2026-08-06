---
title: RFP Packet Extraction — Chunked Gmail Attachments
type: reference
tags: [email, imap, rfp, attachment-extraction, boss-herman]
updated: 2026-07-18
---

# Extracting Chunked RFP Packets from Gmail

Boss Herman sends large RFP packets (>25MB) split across 3 Gmail messages because
Gmail caps message size at 25MB. Each email carries one `lb_chunk_0N` (or similar)
binary attachment plus a rejoin recipe and SHA-256 hashes in the body.

## The pattern

- 3 emails, same subject prefix, "chunk N of 3"
- Each has one octet-stream attachment: `lb_chunk_00`, `lb_chunk_01`, `lb_chunk_02`
- Email body contains the rejoin command, expected final SHA-256, and per-chunk hashes
- Rejoin with `cat`, verify before extracting

## Verified extraction recipe (2026-07-17, Long Beach PW25-648)

```python
import imaplib, email, os, hashlib

with open('/opt/data/.secrets/gmail-app.txt') as f:
    pwd = f.read().strip()

mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login('MuniBot.gsts@gmail.com', pwd)
mail.select('INBOX')

# Search by sender + subject keyword
typ, data = mail.uid('search', None, '(FROM "jwade@gstsinc.com" SUBJECT "Long Beach")')
uids = data[0].split()

outdir = '/opt/data/long_beach_rfp'
os.makedirs(outdir, exist_ok=True)
extracted = {}

for uid in uids:
    # USE UID FETCH with BODY.PEEK[] — not sequence-number fetch
    typ, msg_data = mail.uid('fetch', uid, '(BODY.PEEK[])')
    raw = None
    for rp in msg_data:
        if isinstance(rp, tuple) and len(rp) >= 2:
            raw = rp[1]  # bytes are at index [0][1], not the trailing b')'
            break
    if not raw:
        continue
    # DO NOT pass policy=policy — triggers AttributeError on some Python builds
    msg = email.message_from_bytes(raw)
    for part in msg.walk():
        fn = part.get_filename()
        if fn:
            payload = part.get_payload(decode=True)
            if payload:
                with open(os.path.join(outdir, fn), 'wb') as f:
                    f.write(payload)
                extracted[fn] = hashlib.sha256(payload).hexdigest()

mail.logout()
```

Then rejoin and verify:

```bash
cd /opt/data/long_beach_rfp
cat lb_chunk_00 lb_chunk_01 lb_chunk_02 > Long_Beach_RFP_PW25-648_Brent_Packet.tar.gz
sha256sum Long_Beach_RFP_PW25-648_Brent_Packet.tar.gz
# Compare against the hash in the email body
mkdir -p packet && tar -xzf Long_Beach_RFP_PW25-648_Brent_Packet.tar.gz -C packet
```

## Gotchas encountered

1. **`email.policy` AttributeError.** `email.message_from_bytes(raw, policy=policy)` throws
   `AttributeError: module 'email.policy' has no attribute 'message_factory'` on this host.
   Fix: omit the `policy` kwarg entirely — `email.message_from_bytes(raw)` works.

2. **Sequence-number fetch silently returns None for large messages.** `mail.fetch(b'13', '(RFC822)')`
   returns `[None]` for the 21MB emails but works for the 9MB one. **Use UID fetch instead:**
   `mail.uid('fetch', uid, '(BODY.PEEK[])')` — it reliably returns the full payload regardless
   of size. The `BODY.PEEK` variant also avoids marking the message as read.

3. **Tuple structure varies.** Large messages come back as `[(b'12 (RFC822 {21536002}', <bytes>), b')']`
   — the payload is at `msg_data[0][1]`, not the last element. Iterate and grab the first
   tuple with `len >= 2`.

4. **Himalaya `message read` only shows text, not attachments.** For attachment extraction,
   go straight to Python IMAP — himalaya's CLI doesn't expose a clean "save all attachments
   from message N" path for binary octet-stream parts. (`himalaya attachment download` exists
   but is finicky with chunked binary parts.)

5. **Prompt file may be a separate attachment.** Boss Herman's "chunk 1 of 3" email also
   carried `MuniBot_Long_Beach_PROMPT.txt` — a plain-text copy of the task instructions.
   Extract and read it; it's the authoritative spec for what the bid deliverable must contain.

## When this applies

Any forwarded packet where the email body mentions "chunk," "split," `cat`, or SHA-256
verification. The same recipe works for non-RFP large attachments (inventory exports,
GIS shapefile bundles, photo sets) — anything that exceeds Gmail's 25MB cap.
