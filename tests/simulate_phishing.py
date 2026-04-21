#!/usr/bin/env python3
"""
Simulate phishing email scanning without Gmail authentication.
Useful for testing when Gmail API credentials are not available.
"""

import requests
import json
from datetime import datetime

API_BASE_URL = "http://localhost:9000"

# Sample phishing emails
PHISHING_SAMPLES = [
    {
        "gmail_id": "test_phishing_1",
        "sender": "support@paypa-secure.com",
        "subject": "URGENT: Verify Your Account - Action Required!",
        "body": """Dear Valued Customer,

We have detected suspicious activity on your PayPal account. 
To protect your account, we require you to verify your information immediately.

Click here to verify your account now: http://paypal-secure.verify.com/login?verify=true

If you don't verify within 24 hours, your account will be SUSPENDED!

Your account security is our priority.

Best regards,
PayPal Security Team""",
        "received_at": datetime.now().isoformat(),
        "user_email": "testuser@gmail.com",
    },
    {
        "gmail_id": "test_phishing_2",
        "sender": "no-reply@amaz0n-accounts.com",
        "subject": "Confirm Your Amazon Account Now",
        "body": """Amazon Alert!

Your account has been locked for security reasons.

Please click below to confirm your identity and unlock your account:
https://amaz0n-accounts.com/verify?user=testuser

Do not ignore this email! Your account may be permanently suspended.

Amazon Account Team""",
        "received_at": datetime.now().isoformat(),
        "user_email": "testuser@gmail.com",
    },
    {
        "gmail_id": "test_phishing_3",
        "sender": "admin@banksecurity-verify.net",
        "subject": "Immediate Action Required - Update Your Banking Information",
        "body": """Dear Customer,

We need to update your banking information due to new security regulations.

Please click here and enter your credentials: http://banksecurity-verify.net/update

Required information:
- Username
- Password
- Social Security Number
- Credit Card Number

Failure to comply within 48 hours will result in account closure.

Your Bank Security Team""",
        "received_at": datetime.now().isoformat(),
        "user_email": "testuser@gmail.com",
    },
]

# Sample legitimate emails
LEGITIMATE_SAMPLES = [
    {
        "gmail_id": "test_legitimate_1",
        "sender": "no-reply@paypal.com",
        "subject": "Your PayPal Receipt - Transaction #987654321",
        "body": """Hello,

Thank you for your purchase. Here's your receipt:

Item: Monthly Subscription
Amount: $9.99 USD
Date: January 15, 2026
Transaction ID: 987654321

Your payment was successful. You can access your receipt anytime by logging into your PayPal account.

For questions about your purchase, visit the Help Center at paypal.com/help

Best regards,
PayPal Customer Service
https://www.paypal.com""",
        "received_at": datetime.now().isoformat(),
        "user_email": "testuser@gmail.com",
    },
    {
        "gmail_id": "test_legitimate_2",
        "sender": "noreply@github.com",
        "subject": "You have a new notification on GitHub",
        "body": """Hi testuser,

You received a new notification.

Repository: example/project
Event: Someone commented on your pull request #42

View the comment: https://github.com/example/project/pull/42#comment-123456

You're receiving this because you subscribed to notifications in this repository.

Manage your notification settings: https://github.com/settings/notifications

Thanks,
GitHub""",
        "received_at": datetime.now().isoformat(),
        "user_email": "testuser@gmail.com",
    },
]


def scan_email(email_data):
    """Send email to FastAPI for scanning."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/emails/scan",
            json=email_data,
            timeout=30,
        )
        return response.status_code == 200, response.json()
    except requests.exceptions.RequestException as e:
        return False, {"error": str(e)}


def print_result(email_data, result, success):
    """Print scanning result in a readable format."""
    print("\n" + "="*70)
    print(f"From: {email_data['sender']}")
    print(f"Subject: {email_data['subject']}")
    print("="*70)
    
    if success:
        print(f"Classification: {result['classification'].upper()}")
        print(f"Confidence: {result['confidence_score']:.0%}")
        print(f"Risk Level: {result['risk_level'].upper()}")
        print(f"Explanation: {result['explanation']}")
        
        if result["warning_signs"]:
            print("\nWarning Signs:")
            for sign in result["warning_signs"]:
                print(f"  • {sign}")
    else:
        print(f"ERROR: {result.get('error', 'Unknown error')}")


def main():
    """Run the simulation."""
    print("\n" + "🛡️ " + "="*65 + " 🛡️")
    print("EMAIL RISK AI - PHISHING SIMULATION TEST")
    print("="*70)
    print(f"\nTesting API at {API_BASE_URL}")
    
    # Test health endpoint first
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ API is running and accessible")
        else:
            print("✗ API returned an error")
            return
    except requests.exceptions.RequestException:
        print("✗ Cannot connect to API")
        print("  Make sure FastAPI is running: uvicorn api.main:app --reload --port 9000")
        return
    
    all_results = []
    
    # Scan phishing samples
    print("\n" + "-"*70)
    print("PHISHING SAMPLES (should be classified as 'phishing')")
    print("-"*70)
    
    for i, email in enumerate(PHISHING_SAMPLES, 1):
        print(f"\n[{i}/{len(PHISHING_SAMPLES) + len(LEGITIMATE_SAMPLES)}]")
        success, result = scan_email(email)
        print_result(email, result, success)
        all_results.append((email, result, success))
    
    # Scan legitimate samples
    print("\n" + "-"*70)
    print("LEGITIMATE SAMPLES (should be classified as 'legitimate')")
    print("-"*70)
    
    for i, email in enumerate(LEGITIMATE_SAMPLES, 1):
        print(f"\n[{len(PHISHING_SAMPLES) + i}/{len(PHISHING_SAMPLES) + len(LEGITIMATE_SAMPLES)}]")
        success, result = scan_email(email)
        print_result(email, result, success)
        all_results.append((email, result, success))
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    successful = sum(1 for _, _, success in all_results if success)
    phishing_correct = sum(
        1 for email, result, success in all_results 
        if success and email in PHISHING_SAMPLES and result["classification"] == "phishing"
    )
    legitimate_correct = sum(
        1 for email, result, success in all_results 
        if success and email in LEGITIMATE_SAMPLES and result["classification"] == "legitimate"
    )
    
    print(f"\nSuccessful scans: {successful}/{len(all_results)}")
    print(f"Phishing correctly identified: {phishing_correct}/{len(PHISHING_SAMPLES)}")
    print(f"Legitimate correctly identified: {legitimate_correct}/{len(LEGITIMATE_SAMPLES)}")
    
    if successful == len(all_results):
        accuracy = (phishing_correct + legitimate_correct) / len(all_results) * 100
        print(f"\n✓ Overall accuracy: {accuracy:.0f}%")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
