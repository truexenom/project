import asyncio
import imghdr
import smtplib
from email.message import EmailMessage

import aiosmtplib

from shot import screen

msg = EmailMessage()
msg['Subject'] = 'Test'

msg.add_attachment(screen, maintype='image', subtype=imghdr.what(None, screen))

from configmgr import config

FROM = config.get('email', 'from')
TO = config.get('email', 'to')
SERVER = config.get('email', 'server')
PORT = config.get('email', 'port')
LOGIN = config.get('email', 'login')
PASSWORD = config.get('email', 'passwd')

msg['From'] = FROM
msg['To'] = TO

async def send_hello_world():
    smtp_client = aiosmtplib.SMTP(hostname=SERVER, port=PORT, use_tls=False)
    await smtp_client.connect()
    await smtp_client.ehlo()
    await smtp_client.starttls()
    await smtp_client.ehlo()
    await smtp_client.login(username=LOGIN, password=PASSWORD)
    await smtp_client.send_message(msg)
    await smtp_client.quit()


event_loop = asyncio.get_event_loop()
event_loop.run_until_complete(send_hello_world())