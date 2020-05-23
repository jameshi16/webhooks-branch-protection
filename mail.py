import smtplib
from smtplib import SMTPSenderRefused
from email.message import EmailMessage

class Email:
	"""
	Class so that one SMTP connection is maintained for all emails
	"""
	def __init__(self, host, port, username, password, *, smtp_tls=False, smtp_ssl=False):
		self.__host = host
		self.__port = port
		self.__username = username
		self.__password = password
		self.__smtp_tls = smtp_tls
		self.__smtp_ssl = smtp_ssl

		self.connect()

	def connect(self):
		smtp_server = smtplib.SMTP(self.__host, port=self.__port) if not self.__smtp_ssl else smtplib.SMTP_SSL(self.__host, port=self.__port)
		if self.__smtp_tls:
			smtp_server.starttls()
		smtp_server.login(self.__username, self.__password)
		self.smtp = smtp_server	

	def send_notification(self, email_addresses, subject, message):
		msg = EmailMessage()
		msg['Subject'] = subject
		msg['From'] = self.__username
		msg['To'] = ', '.join(email_addresses)
		msg.set_content(message)

		try:
			self.smtp.send_message(msg)
			print("Email: Sent notification to email addresses")
		except SMTPSenderRefused as e:
			if e.smtp_code == 451:
				print("Email: Disconnected from SMTP server. Reconnecting...")
				self.connect()
				self.send_notification(email_addresses, subject, message)
			else:
				raise e

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
