import { useEffect } from 'react';

const OAuthCallback = () => {
  useEffect(() => {
    // Extract the authorization code from the URL
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const error = params.get('error');

    if (error) {
      console.error('OAuth error:', error);
      if (window.opener) {
        window.opener.postMessage(
          { type: 'oauth-error', error },
          window.location.origin
        );
      }
      window.close();
    } else if (code) {
      // Send the code back to the parent window
      if (window.opener) {
        window.opener.postMessage(
          { type: 'oauth-complete', code },
          window.location.origin
        );
        // Close this popup after a short delay to ensure message is received
        setTimeout(() => {
          window.close();
        }, 500);
      }
    }
  }, []);

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      backgroundColor: '#f7fafc',
      fontFamily: 'Inter, sans-serif',
    }}>
      <div style={{ textAlign: 'center' }}>
        <p style={{ fontSize: '16px', color: '#718096' }}>
          Processing authentication...
        </p>
        <p style={{ fontSize: '12px', color: '#a0aec0', marginTop: '8px' }}>
          This window will close automatically.
        </p>
      </div>
    </div>
  );
};

export default OAuthCallback;
