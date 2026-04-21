from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/oauth", tags=["oauth"])

# OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:9000/oauth/callback")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class TokenRequest(BaseModel):
    """Token exchange request."""
    code: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    email: str


@router.get("/authorize")
async def get_auth_url():
    """Get Google OAuth authorization URL."""
    try:
        # Create the OAuth flow
        flow = Flow.from_client_secrets_file(
            filename=None,  # We'll use explicit config instead
            scopes=SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI,
        ) if False else Flow.from_client_config(
            client_config={
                "installed": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI,
        )
        
        # Get authorization URL
        auth_url, state = flow.authorization_url(access_type="offline", prompt="consent")
        
        return {
            "auth_url": auth_url,
            "state": state,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating auth URL: {str(e)}")


@router.post("/token", response_model=TokenResponse)
async def exchange_token(request: TokenRequest):
    """Exchange authorization code for access token."""
    try:
        # Validate that we have a code
        if not request.code:
            raise ValueError("Authorization code is missing")
        
        print(f"[TOKEN] Received code: {request.code[:30]}...")
        
        # Create the OAuth flow
        flow = Flow.from_client_config(
            client_config={
                "installed": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI,
        )
        
        # Exchange code for token
        print(f"[TOKEN] Fetching token with redirect_uri: {GOOGLE_REDIRECT_URI}")
        flow.fetch_token(code=request.code)
        
        credentials = flow.credentials
        print(f"[TOKEN] Credentials object: {credentials}")
        print(f"[TOKEN] Has token: {credentials.token is not None}")
        print(f"[TOKEN] Token value: {credentials.token[:30] if credentials.token else 'None'}...")
        
        if not credentials or not credentials.token:
            raise ValueError("Failed to obtain access token from Google")
        
        # Refresh token if needed to ensure it's valid
        if credentials.expired and credentials.refresh_token:
            print("[TOKEN] Token expired, refreshing...")
            request_obj = Request()
            credentials.refresh(request_obj)
        
        # Get user email via Gmail API (covered by gmail.readonly scope)
        from googleapiclient.discovery import build

        print(f"[TOKEN] Building gmail service...")
        gmail = build("gmail", "v1", credentials=credentials)
        profile = gmail.users().getProfile(userId="me").execute()
        user_email = profile.get("emailAddress")

        if not user_email:
            raise ValueError("Failed to retrieve user email from Gmail profile")
        
        print(f"[TOKEN] Successfully authenticated user: {user_email}")
        
        return TokenResponse(
            access_token=credentials.token,
            email=user_email,
        )
    
    except Exception as e:
        import traceback
        print(f"[TOKEN] Error: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Error exchanging token: {str(e)}")


@router.get("/callback")
async def oauth_callback(code: str = None, error: str = None, state: str = None):
    """Google OAuth callback - returns an HTML page that sends the code back to the frontend."""
    if error:
        return HTMLResponse(f"""
        <html>
        <head><title>Authentication Error</title></head>
        <body>
            <h1>Authentication Error</h1>
            <p>{error}</p>
            <p><a href="http://localhost:3000">Back to app</a></p>
        </body>
        </html>
        """)
    
    if not code:
        return HTMLResponse("""
        <html>
        <head><title>Authentication Error</title></head>
        <body>
            <h1>No authorization code received</h1>
            <p><a href="http://localhost:3000">Back to app</a></p>
        </body>
        </html>
        """)
    
    # Return HTML that sends the code back to the parent window
    # Use JSON.stringify to properly escape the code
    html = f"""
    <html>
    <head>
        <title>Authenticating...</title>
        <script>
            // Authorization code from Google
            const authCode = {json.dumps(code)};
            
            // Send the authorization code to the parent window
            if (window.opener) {{
                window.opener.postMessage({{
                    type: 'oauth-complete',
                    code: authCode
                }}, 'http://localhost:3000');
                window.close();
            }} else {{
                // Fallback: redirect to the app with the code
                window.location.href = 'http://localhost:3000?code=' + encodeURIComponent(authCode);
            }}
        </script>
    </head>
    <body>
        <p>Processing authentication...</p>
    </body>
    </html>
    """
    return HTMLResponse(html)
