import smtplib
from email.message import EmailMessage

class Email:
	"""
	Class so that one SMTP connection is maintained for all emails
  """
	def __init__(self, host, port, username, password, *, smtp_tls=False, smtp_ssl=False):
		self.username = username

		smtp_server = smtplib.SMTP(host, port=port) if not smtp_ssl else smtplib.SMTP_SSL(host, port=port)
		if smtp_tls:
			smtp_server.starttls()
		smtp_server.login(username, password)
		self.smtp = smtp_server

	def send_notification(self, email_addresses, subject, message):
		msg = EmailMessage()
		msg['Subject'] = subject
		msg['From'] = self.username
		msg['To'] = ', '.join(email_addresses)
		msg.set_content(message)	

		print("Email: Sent notification to email addresses")
		self.smtp.send_message(msg)

class FakeEmail:
	"""
	Class to make it so coding won't be difficult in main.py
	If it acts like a duck, quacks like a duck, it IS a duck
	Unless you are talking about the initializer
	Then it's not a duck. Think of a chicken in a duck skin
	"""
	def __init__(self):
		pass

	def send_notification(self, email_addresses, subject, message):
		print("Mock email")
		print("To: ", email_addresses)
		print("Subject: ", subject)
		print("=======================")
		print(message)
