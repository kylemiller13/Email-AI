from fastapi import APIRouter

router = APIRouter(prefix="/compare", tags=["compare"])

# Curated pairs drawn from real dataset examples (Enron legitimate, Nazario phishing).
# Each pair shares the same theme so the two emails look plausibly similar.
PAIRS = [
    {
        "id": 1,
        "theme": "IT password reset notice",
        "legitimate": {
            "subject": "Password Reset Notification",
            "sender": "it-helpdesk@enron.com",
            "body": (
                "This is an automated email — please do not reply.\n\n"
                "If you need further assistance, contact the ISC Help Desk at 713-345-4727.\n\n"
                "The password for your account (PO0507544) has been reset to: 14031399\n\n"
                "Please log in and change your password at your earliest convenience."
            ),
        },
        "phishing": {
            "subject": "Help Desk: Password Expiry Notice",
            "sender": "helpdesk@mail-server-secure.com",
            "body": (
                "Your password will expire in 3 days.\n\n"
                "Click Here To Validate Your E-mail Password.\n\n"
                "Thank you,\n"
                "IT-Service Help Desk\n\n"
                "Your password will expire in 3 days. "
                "Click Here To Validate E-mail Password. "
                "Thank you, IT-Service Help Desk."
            ),
        },
        "red_flags": [
            "Sender domain is 'mail-server-secure.com' — not from any real company",
            "No account name, system, or specific details mentioned",
            "Vague 'Click Here' link — no actual URL shown",
            "Body is copy-pasted twice, a sign of an automated spam template",
            "No phone number or named contact provided",
        ],
        "explanation": (
            "The phishing email uses urgency ('will expire in 3 days') and a vague 'Click Here' "
            "link to steal your password. The sender domain is fake. "
            "The legitimate email gives a specific account ID, a real phone number to call, "
            "and resets your password directly — it doesn't ask you to click anything."
        ),
    },
    {
        "id": 2,
        "theme": "New system access credentials",
        "legitimate": {
            "subject": "Your Guest Access to EOL is Ready",
            "sender": "carrie.kelly@enron.com",
            "body": (
                "Hi,\n\n"
                "Your guest access to EOL has been established.\n\n"
                "At www.enrononline.com, use:\n"
                "  User ID:  EOL76371\n"
                "  Password: welcome!\n\n"
                "If you have any questions please contact Tara Sweitzer.\n\n"
                "Thank you,\n"
                "Carrie  (Ext: 3-5472)"
            ),
        },
        "phishing": {
            "subject": "Verify Your Account — Action Required",
            "sender": "noreply@cpanel-support.net",
            "body": (
                "Dear Client,\n\n"
                "Our Technical Services Department is carrying out a planned software upgrade. "
                "Please login to re-confirm your account details.\n\n"
                "To login, please click the link below.\n\n"
                "Failure to verify your account within 48 hours will result in permanent suspension."
            ),
        },
        "red_flags": [
            "'Dear Client' — no name used, applies to anyone",
            "Sender domain is 'cpanel-support.net', not an official cPanel domain",
            "Threat of 'permanent suspension' to create panic",
            "No specific upgrade details, date, or reason given",
            "'Click the link below' — no actual URL is shown",
        ],
        "explanation": (
            "The phishing email impersonates a hosting provider but uses a suspicious domain. "
            "It relies on a generic greeting, vague technical language, and a suspension threat "
            "to pressure you into clicking. "
            "The legitimate email gives specific credentials, a real URL, and a named colleague "
            "you can call to verify."
        ),
    },
    {
        "id": 3,
        "theme": "Account expiry / update required",
        "legitimate": {
            "subject": "System Migration: Passwords Will Be Reset",
            "sender": "chris.germany@enron.com",
            "body": (
                "All,\n\n"
                "When we convert Unify to Sybase 12.0, all passwords will be reset to 'houston'. "
                "Once you log in to Unify you will need to change your password.\n\n"
                "This is an unavoidable side effect of the Sybase 12.0 migration.\n\n"
                "Thanks,\n"
                "Chris"
            ),
        },
        "phishing": {
            "subject": "Your ADP Account Will Expire Soon!",
            "sender": "adp-noreply@adp-payroll-service.com",
            "body": (
                "Dear User,\n\n"
                "Your ADP account will expire soon. "
                "We recommend that you update your account now to avoid suspension.\n\n"
                "Click here to update your account.\n\n"
                "Sincerely,\n"
                "ADP Payroll Services"
            ),
        },
        "red_flags": [
            "'Dear User' — not addressed to you by name",
            "Sender domain is 'adp-payroll-service.com', not ADP's real domain (adp.com)",
            "Vague 'Click here' with no URL shown",
            "No expiry date, account ID, or specific details provided",
            "Urgency without specifics: 'will expire soon'",
        ],
        "explanation": (
            "The phishing email pretends to be from ADP (a real payroll company) but uses a fake domain. "
            "It keeps everything vague — no expiry date, no account ID — because it targets anyone, "
            "not a real ADP customer. "
            "The legitimate email names a specific system, explains exactly what will happen, "
            "and comes from a named colleague."
        ),
    },
    {
        "id": 4,
        "theme": "Email account security notice",
        "legitimate": {
            "subject": "Access Request: Your Approval Needed",
            "sender": "it-systems@enron.com",
            "body": (
                "You have received this email because you are listed as a data approver.\n\n"
                "Please visit the following link to review and approve or reject this request:\n"
                "http://itcapps.corp.enron.com/srrs/auth/emaillink.asp?id=49773&page=approval\n\n"
                "Request ID:    49773\n"
                "Requested by:  L. Newton"
            ),
        },
        "phishing": {
            "subject": "Microsoft Account Verification Required",
            "sender": "verify@microsoft-accounts.com",
            "body": (
                "Your two (2) outgoing emails have been placed on hold due to a recent upgrade "
                "in our database.\n\n"
                "You are required to immediately validate and re-set your email account.\n\n"
                "Kindly click HERE to update your Outlook account.\n\n"
                "© 2013 Microsoft Corporation. All rights reserved."
            ),
        },
        "red_flags": [
            "Sender is 'microsoft-accounts.com' — Microsoft's real domain is microsoft.com",
            "'Kindly click HERE' — no visible destination URL",
            "Vague reason: 'placed on hold due to an upgrade'",
            "Outdated copyright (© 2013) copied to appear official",
            "No account name, ID, or specific details — targets anyone",
        ],
        "explanation": (
            "This email impersonates Microsoft but uses 'microsoft-accounts.com' instead of 'microsoft.com'. "
            "The vague reason and generic 'click HERE' link are classic phishing tactics. "
            "Microsoft never asks you to verify your account by clicking a link in an email. "
            "The legitimate email shows the exact URL, a request ID, and the requester's name."
        ),
    },
    {
        "id": 5,
        "theme": "Payment or transaction confirmation",
        "legitimate": {
            "subject": "75th Anniversary Dinner — Registration Confirmed",
            "sender": "meetingstop@aol.com",
            "body": (
                "Thank you!\n\n"
                "We've received your registration for the 75th Anniversary Dinner. "
                "Mark your calendar and plan to have an enjoyable evening.\n\n"
                "Sincerely,\n"
                "The Conference Team"
            ),
        },
        "phishing": {
            "subject": "Your Recent PayPal Payment — Please Verify",
            "sender": "service@paypal-secure-center.com",
            "body": (
                "Dear Customer,\n\n"
                "You have received this email due to account configuration problems. "
                "We ask that you confirm your information to regain access to your account.\n\n"
                "Please click here to confirm now.\n\n"
                "If this message arrived as junk mail, please disregard."
            ),
        },
        "red_flags": [
            "'Dear Customer' — PayPal always uses your full name",
            "Sender domain is 'paypal-secure-center.com', not paypal.com",
            "'Account configuration problems' — vague and designed to worry you",
            "'Click here to confirm now' — no visible URL",
            "Junk mail disclaimer is a common tactic to appear legitimate",
        ],
        "explanation": (
            "This email impersonates PayPal using a fake domain. "
            "PayPal always addresses you by name and never uses vague terms like 'configuration problems'. "
            "The junk mail disclaimer at the bottom is a manipulation tactic to lower your guard. "
            "The legitimate email is simple, event-specific, and asks nothing of you."
        ),
    },
]


@router.get("/pair")
async def get_pair(round: int = 0):
    """Return an email pair for the given round (cycles through all pairs)."""
    pair = PAIRS[round % len(PAIRS)]
    return {
        "id": pair["id"],
        "round": round,
        "total_rounds": len(PAIRS),
        "theme": pair["theme"],
        "legitimate": pair["legitimate"],
        "phishing": pair["phishing"],
        "red_flags": pair["red_flags"],
        "explanation": pair["explanation"],
    }
