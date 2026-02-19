"""
Email sending utilities
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Domain configuration
DOMAIN = os.getenv("DOMAIN", "http://localhost:8000")

# Email configuration (use environment variables in production)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp-relay.brevo.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "your-email@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your-brevo-api-key")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@manuals.com")
FROM_NAME = os.getenv("FROM_NAME", "Manual Donkey")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")  # xkeysib-... key

# Use Brevo API instead of SMTP (Railway blocks SMTP ports)
USE_BREVO_API = bool(BREVO_API_KEY)
print(f"📧 Email configured: Brevo API={'Yes' if USE_BREVO_API else 'No'}, SMTP={SMTP_SERVER}:{SMTP_PORT}, FROM={FROM_EMAIL}")


def send_email_brevo_api(to_email: str, subject: str, html_content: str):
    """Send email using Brevo API (bypasses SMTP port blocking)"""
    print(f"🚀 Attempting to send email via Brevo API to {to_email}")
    try:
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": BREVO_API_KEY,
            "content-type": "application/json"
        }
        payload = {
            "sender": {
                "name": FROM_NAME,
                "email": FROM_EMAIL
            },
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_content
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        print(f"✅ Email sent successfully to {to_email} via Brevo API. Message ID: {response.json().get('messageId')}")
        return True
    except Exception as e:
        print(f"❌ Brevo API error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    """Send email using Resend API"""
    print(f"🚀 Attempting to send email via Resend to {to_email}")
    try:
        result = resend.Emails.send({
            "from": f"{FROM_NAME} <onboarding@resend.dev>",
            "to": to_email,
            "subject": subject,
            "html": html_content
        })
        print(f"✅ Email sent successfully to {to_email} via Resend. Result: {result}")
        return True
    except Exception as e:
        print(f"❌ Resend API error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def send_email_smtp(to_email: str, subject: str, html_content: str):
    """Send email using SMTP (fallback)"""
    print(f"📧 Attempting to send email via SMTP to {to_email}")
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = Header(subject, 'utf-8')
        
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=5) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email sent successfully to {to_email} via SMTP")
        return True
    except Exception as e:
        print(f"❌ SMTP error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def send_verification_email(to_email: str, code: str):
    """Send email verification code"""
    subject = "Verify Your Email - Manual Donkey"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .code {{ font-size: 32px; font-weight: bold; color: #667eea; text-align: center; letter-spacing: 5px; padding: 20px; background: #f7f7f7; border-radius: 10px; margin: 30px 0; }}
            .footer {{ text-align: center; color: #666; font-size: 14px; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="color: #667eea;">Email Verification</h1>
            </div>
            <p>Thank you for registering at Manual Donkey!</p>
            <p>Please use the following code to verify your email address:</p>
            <div class="code">{code}</div>
            <p>This code will expire in 15 minutes.</p>
            <p>If you didn't request this code, please ignore this email.</p>
            <div class="footer">
                <p>&copy; 2026 Manuals Store. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Try Brevo API first, fallback to SMTP
    print(f"📨 send_verification_email called for {to_email}")
    print(f"USE_BREVO_API: {USE_BREVO_API}")
    
    if USE_BREVO_API:
        if send_email_brevo_api(to_email, subject, html_content):
            return True
        else:
            print("⚠️ Brevo API failed, trying SMTP fallback...")
    
    # Fallback to SMTP (won't work on Railway but works locally)
    return send_email_smtp(to_email, subject, html_content)


def send_order_confirmation_email(to_email: str, order_id: int, product_title: str, price: float):
    """Send order confirmation email"""
    subject = f"Order Confirmation #{order_id} - Manual Donkey"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .success {{ color: #10b981; font-size: 48px; text-align: center; margin-bottom: 20px; }}
            .order-info {{ background: #f7f7f7; padding: 20px; border-radius: 10px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success">✓</div>
            <div class="header">
                <h1 style="color: #667eea;">Thank You for Your Purchase!</h1>
            </div>
            <p>Your order has been confirmed.</p>
            <div class="order-info">
                <p><strong>Order ID:</strong> {order_id}</p>
                <p><strong>Product:</strong> {product_title}</p>
                <p><strong>Email:</strong> {to_email}</p>
                <p><strong>Amount:</strong> ${price:.2f} USD</p>
            </div>
            <p>Your manual will be delivered to your email within 1-5 minutes.</p>
            <p>Please check your inbox and spam folder.</p>
            <div style="text-align: center; margin-top: 30px; color: #666; font-size: 14px;">
                <p>&copy; 2026 Manual Donkey. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Try Resend first, fallback to SMTP
    if USE_BREVO_API:
        if send_email_brevo_api(to_email, subject, html_content):
            return True
    
    return send_email_smtp(to_email, subject, html_content)


def send_manual_ready_email(to_email: str, order_id: int, product_title: str, download_link: str):
    """Send email notification when manual is ready to download"""
    subject = "Your Manual is Ready to Download!"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                       color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                      color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold; }}
            .order-details {{ background: white; padding: 15px; border-left: 4px solid #667eea; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 30px; color: #777; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Your Manual is Ready!</h1>
            </div>
            <div class="content">
                <p>Great news! Your manual is now available for download.</p>
                
                <div class="order-details">
                    <strong>Order #{order_id}</strong><br>
                    <strong>Product:</strong> {product_title}
                </div>
                
                <p>Click the button below to download your manual:</p>
                
                <div style="text-align: center;">
                    <a href="{download_link}" class="button">Download Manual</a>
                </div>
                
                <p>You can also copy this link directly:</p>
                <p style="background: white; padding: 10px; border-radius: 5px; word-break: break-all;">
                    {download_link}
                </p>
                
                <p>If you have any questions, please don't hesitate to contact us.</p>
                
                <p>Thank you for your purchase!</p>
            </div>
            <div class="footer">
                <p>This is an automated message from your Manual Store</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Try Resend first, fallback to SMTP
    if USE_BREVO_API:
        if send_email_brevo_api(to_email, subject, html_content):
            return True
    
    return send_email_smtp(to_email, subject, html_content)


def send_password_reset_email(to_email: str, reset_token: str, domain: str):
    """Send password reset email with reset link"""
    subject = "Reset Your Password 🔐"
    
    reset_link = f"{domain}/reset-password?token={reset_token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                       color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                      color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold; }}
            .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 30px; color: #777; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Reset Your Password</h1>
            </div>
            <div class="content">
                <p>You requested to reset your password. Click the button below to create a new password:</p>
                
                <div style="text-align: center;">
                    <a href="{reset_link}" class="button">Reset Password</a>
                </div>
                
                <p>Or copy this link directly:</p>
                <p style="background: white; padding: 10px; border-radius: 5px; word-break: break-all;">
                    {reset_link}
                </p>
                
                <div class="warning">
                    <strong>Important:</strong> This link will expire in 5 minutes. If you didn't request this password reset, please ignore this email.
                </div>
                
                <p>If you have any questions, please don't hesitate to contact us.</p>
            </div>
            <div class="footer">
                <p>This is an automated message from your Manual Store</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Try Resend first, fallback to SMTP
    if USE_BREVO_API:
        if send_email_brevo_api(to_email, subject, html_content):
            return True
    
    return send_email_smtp(to_email, subject, html_content)


def send_welcome_newsletter_email(to_email: str, discount_code: str):
    """Send welcome email with discount code"""
    subject = "Welcome! Here's Your 10% Discount Code 🎉"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%); padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #1f2937; border-radius: 15px; padding: 40px; box-shadow: 0 20px 60px rgba(0,0,0,0.4); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .icon {{ font-size: 64px; text-align: center; margin-bottom: 20px; }}
            h1 {{ color: #06b6d4; margin: 0; }}
            .code-box {{ background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%); border-radius: 12px; padding: 30px; text-align: center; margin: 30px 0; border: 2px solid #06b6d4; }}
            .code {{ font-size: 36px; font-weight: bold; color: white; letter-spacing: 3px; font-family: 'Courier New', monospace; }}
            .info {{ color: #d1d5db; font-size: 16px; line-height: 1.6; }}
            .cta {{ display: inline-block; background: linear-gradient(135deg, #06b6d4 0%, #0ea5e9 100%); color: white; padding: 15px 40px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 20px; }}
            .footer {{ text-align: center; color: #9ca3af; font-size: 14px; margin-top: 40px; border-top: 1px solid #374151; padding-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">✉️</div>
            <div class="header">
                <h1>Welcome to Manual Donkey!</h1>
            </div>
            
            <p class="info">Thank you for subscribing to our newsletter! 🎉</p>
            <p class="info">As promised, here's your exclusive <strong>10% discount code</strong>:</p>
            
            <div class="code-box">
                <div class="code">{discount_code}</div>
            </div>
            
            <p class="info">📌 <strong>How to use:</strong></p>
            <ul class="info">
                <li>Add products to your cart</li>
                <li>Go to checkout</li>
                <li>Enter the code above</li>
                <li>Enjoy 10% off your purchase!</li>
            </ul>
            
            <div style="text-align: center;">
                <a href="{DOMAIN}" class="cta">Start Shopping Now</a>
            </div>
            
            <div class="footer">
                <p>💡 This code is valid for your next purchase</p>
                <p style="margin-top: 10px;">&copy; 2026 Manual Donkey. All rights reserved.</p>
                <p style="font-size: 12px; color: #6b7280; margin-top: 10px;">
                    You received this email because you subscribed to our newsletter.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Try Resend first, fallback to SMTP
    if USE_BREVO_API:
        if send_email_brevo_api(to_email, subject, html_content):
            return True
    
    return send_email_smtp(to_email, subject, html_content)


def send_marketing_campaign_email(to_email: str, subject: str, html_content: str, tracking_token: str = None):
    """Send marketing campaign email with optional tracking"""
    
    # Add tracking pixel if token provided
    if tracking_token:
        tracking_pixel = f'<img src="{DOMAIN}/api/email/track/{tracking_token}" width="1" height="1" style="display:none;" />'
        html_content = html_content.replace('</body>', f'{tracking_pixel}</body>')
    
    # Try Resend first, fallback to SMTP
    if USE_BREVO_API:
        if send_email_brevo_api(to_email, subject, html_content):
            return True
    
    return send_email_smtp(to_email, subject, html_content)


def send_abandoned_cart_email(to_email: str, products: list, total_value: float):
    """Send abandoned cart reminder email"""
    subject = "Don't Forget Your Manuals! 🛒 Special Offer Inside"
    
    # Build product list HTML
    product_items = ""
    for product in products:
        product_items += f"""
            <div style="background: #374151; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                <h3 style="color: #60a5fa; margin: 0 0 5px 0;">{product['title']}</h3>
                <p style="color: #d1d5db; margin: 0; font-size: 18px; font-weight: bold;">${product['price']:.2f}</p>
            </div>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: #111827; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #1f2937; border-radius: 12px; overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%); padding: 40px 20px; text-align: center; }}
            .content {{ padding: 30px; color: #e5e7eb; }}
            .button {{ display: inline-block; background: linear-gradient(135deg, #3b82f6, #06b6d4); color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
            .footer {{ padding: 20px; text-align: center; color: #9ca3af; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="color: white; margin: 0;">Your Cart is Waiting! 🛒</h1>
            </div>
            
            <div class="content">
                <p style="font-size: 18px; margin-bottom: 20px;">You left these manuals in your cart:</p>
                
                {product_items}
                
                <div style="background: #059669; padding: 20px; border-radius: 8px; margin: 30px 0; text-align: center;">
                    <h2 style="color: white; margin: 0 0 10px 0;">Special Offer!</h2>
                    <p style="color: white; margin: 0; font-size: 16px;">Complete your purchase now and get an extra 5% OFF!</p>
                    <p style="color: #d1fae5; margin: 10px 0 0 0; font-size: 24px; font-weight: bold;">Total: ${total_value * 0.95:.2f} USD</p>
                    <p style="color: #d1fae5; margin: 0; font-size: 14px;">(Was: ${total_value:.2f})</p>
                </div>
                
                <div style="text-align: center;">
                    <a href="{DOMAIN}/cart" class="button">Complete Purchase Now</a>
                </div>
                
                <p style="margin-top: 30px; font-size: 14px; color: #9ca3af;">
                    This offer is valid for 48 hours. Don't miss out!
                </p>
            </div>
            
            <div class="footer">
                <p>&copy; 2026 Manual Donkey. All rights reserved.</p>
                <p style="margin-top: 10px;">You received this email because you added items to your cart.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Try Resend first, fallback to SMTP
    if USE_BREVO_API:
        if send_email_brevo_api(to_email, subject, html_content):
            return True
    
    return send_email_smtp(to_email, subject, html_content)


def send_discount_reminder_email(to_email: str, discount_code: str):
    """Send reminder about unused discount code"""
    subject = "Don't Forget Your 10% Discount Code! 🎁"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: #111827; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #1f2937; border-radius: 12px; overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%); padding: 40px 20px; text-align: center; }}
            .content {{ padding: 30px; color: #e5e7eb; }}
            .code-box {{ background: linear-gradient(135deg, #3b82f6, #06b6d4); padding: 30px; border-radius: 12px; text-align: center; margin: 30px 0; }}
            .code {{ font-size: 32px; font-weight: bold; color: white; letter-spacing: 3px; }}
            .button {{ display: inline-block; background: linear-gradient(135deg, #3b82f6, #06b6d4); color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
            .footer {{ padding: 20px; text-align: center; color: #9ca3af; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="color: white; margin: 0;">Your Discount is Still Waiting! 🎁</h1>
            </div>
            
            <div class="content">
                <p style="font-size: 18px;">Hi there!</p>
                <p>We noticed you haven't used your exclusive 10% discount code yet.</p>
                
                <div class="code-box">
                    <p style="color: white; margin: 0 0 10px 0; font-size: 14px;">YOUR DISCOUNT CODE:</p>
                    <div class="code">{discount_code}</div>
                    <p style="color: #dbeafe; margin: 10px 0 0 0; font-size: 14px;">10% OFF your entire purchase!</p>
                </div>
                
                <p style="font-size: 16px;">Browse our collection of professional vehicle manuals:</p>
                
                <ul style="color: #d1d5db; line-height: 1.8;">
                    <li>Repair Manuals</li>
                    <li>Workshop Manuals</li>
                    <li>Service Manuals</li>
                    <li>Parts Catalogs</li>
                </ul>
                
                <div style="text-align: center;">
                    <a href="{DOMAIN}/" class="button">Start Shopping Now</a>
                </div>
                
                <p style="margin-top: 30px; font-size: 14px; color: #9ca3af;">
                    💡 Save this code for when you're ready to purchase!
                </p>
            </div>
            
            <div class="footer">
                <p>&copy; 2026 Manual Donkey. All rights reserved.</p>
                <p style="margin-top: 10px;">You received this email because you subscribed to our newsletter.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Try Resend first, fallback to SMTP
    if USE_BREVO_API:
        if send_email_brevo_api(to_email, subject, html_content):
            return True
    
    return send_email_smtp(to_email, subject, html_content)


def send_admin_order_notification(order_id: int, customer_email: str, product_title: str, price: float, link_sent: bool = True):
    """Send notification to admin when a new order is placed"""
    admin_email = "wiktoriatopajew@gmail.com"
    subject = f"🛍 New Order #{order_id} - Manual Donkey"
    
    # Determine action message based on whether link was sent
    if link_sent:
        action_box = '''
                <div style="background: #d1fae5; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #10b981;">
                    <p style="margin: 0; font-size: 16px; color: #059669;">
                        ✅ <strong>Link wysłany automatycznie!</strong><br>
                        <span style="font-size: 14px;">Nie musisz nic robić - klient otrzymał link do pobrania.</span>
                    </p>
                </div>
        '''
    else:
        action_box = '''
                <div style="background: #fef3c7; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #f59e0b;">
                    <p style="margin: 0; font-size: 16px; color: #d97706;">
                        ⚠️ <strong>Wymagana akcja!</strong><br>
                        <span style="font-size: 14px;">Musisz dodać link do Google Drive w panelu admina i ręcznie wysłać do klienta.</span>
                    </p>
                </div>
        '''
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                       color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px 10px; }}
            .order-details {{ background: white; padding: 20px; border-left: 4px solid #10b981; margin: 20px 0; }}
            .highlight {{ background: #d1fae5; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: center; }}
            .footer {{ text-align: center; margin-top: 30px; color: #777; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 New Order Received!</h1>
            </div>
            <div class="content">
                <p>Great news! You have a new order on Manual Donkey.</p>
                
                <div class="order-details">
                    <p style="margin: 5px 0;"><strong>Order ID:</strong> #{order_id}</p>
                    <p style="margin: 5px 0;"><strong>Product:</strong> {product_title}</p>
                    <p style="margin: 5px 0;"><strong>Customer Email:</strong> {customer_email}</p>
                    <p style="margin: 5px 0;"><strong>Amount Paid:</strong> ${price:.2f} USD</p>
                </div>
                
                <div class="highlight">
                    <p style="margin: 0; font-size: 18px; font-weight: bold; color: #059669;">
                        💰 Payment: ${price:.2f} USD
                    </p>
                </div>
                
                {action_box}
                
                <p style="margin-top: 30px; color: #666; font-size: 14px;">
                    This is an automated notification from your Manual Donkey store.
                </p>
            </div>
            <div class="footer">
                <p>&copy; 2026 Manual Donkey. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    print(f"📧 Sending admin notification to {admin_email} for order #{order_id}")
    
    # Try Brevo API first, fallback to SMTP
    if USE_BREVO_API:
        if send_email_brevo_api(admin_email, subject, html_content):
            print(f"✅ Admin notification sent successfully for order #{order_id}")
            return True
        else:
            print(f"⚠️ Brevo API failed for admin notification, trying SMTP fallback...")
    
    # Fallback to SMTP
    result = send_email_smtp(admin_email, subject, html_content)
    if result:
        print(f"✅ Admin notification sent via SMTP for order #{order_id}")
    else:
        print(f"❌ Failed to send admin notification for order #{order_id}")
    return result

