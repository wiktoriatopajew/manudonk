"""
Test newsletter email sending
"""
from email_utils import send_welcome_newsletter_email

# Test sending newsletter email
email = input("Enter your email to test: ")
code = "WELCOMETEST123"

print(f"\nSending newsletter email to {email}...")
result = send_welcome_newsletter_email(email, code)

if result:
    print("✅ Email sent successfully! Check your inbox.")
else:
    print("❌ Failed to send email. Check the error above.")
