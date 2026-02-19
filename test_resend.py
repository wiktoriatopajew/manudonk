"""
Test Resend email sending
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Check if resend is installed
try:
    import resend
    print("✅ resend package is installed")
except ImportError:
    print("❌ resend package NOT installed - installing now...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'resend'])
    import resend
    print("✅ resend package installed successfully")

# Check API key
api_key = os.getenv("RESEND_API_KEY")
if api_key:
    print(f"✅ RESEND_API_KEY found: {api_key[:10]}...")
    resend.api_key = api_key
else:
    print("❌ RESEND_API_KEY not found in environment")
    exit(1)

# Try sending a test email
print("\n🚀 Attempting to send test email...")

# IMPORTANT: Change this to your actual email!
test_email = input("Enter your email to test: ")

try:
    result = resend.Emails.send({
        "from": "Your Manuals Store <onboarding@resend.dev>",
        "to": test_email,
        "subject": "Test Email from Manuals Store",
        "html": """
        <h1>✅ Test Email Success!</h1>
        <p>This is a test email from your Manuals Store to verify Resend integration.</p>
        <p><strong>If you received this, Resend is working perfectly! 🎉</strong></p>
        <p>This means your API key is valid and emails can be sent.</p>
        """
    })
    print(f"\n✅ Email sent successfully!")
    print(f"Result: {result}")
    print(f"\n📧 Check your inbox (and spam folder) at: {test_email}")
except Exception as e:
    print(f"\n❌ Error sending email: {str(e)}")
    import traceback
    traceback.print_exc()
