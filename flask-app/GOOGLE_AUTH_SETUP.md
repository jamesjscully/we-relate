# Google Authentication Setup for We-Relate

## Overview
The We-Relate Flask app now supports Google Sign-In authentication in addition to traditional email/password registration.

## Current Implementation Status
✅ **Completed:**
- Consolidated registration at root route (`/`) - no more separate landing page
- Email used as username (simplified user model)
- Google Sign-In buttons integrated into main registration page
- Frontend JavaScript for Google Sign-In integration
- Backend route `/auth/google-signin` to handle Google authentication
- User model updated with `get_by_email` method
- Password confirmation validation
- Login system updated to accept email as username

## Setup Required for Production

### 1. Google Cloud Console Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Enable the Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Configure the OAuth consent screen
6. Add your domain to authorized domains
7. Add redirect URIs:
   - `http://localhost:5000` (for development)
   - `https://yourdomain.com` (for production)

### 2. Update Client ID
Replace `YOUR_GOOGLE_CLIENT_ID` in the following files:
- `templates/register.html` (line ~190)

### 3. Security Considerations
⚠️ **Important:** The current implementation uses JWT decoding without signature verification for demo purposes. For production, you should:

1. Install Google Auth libraries:
   ```bash
   poetry add google-auth google-auth-oauthlib google-auth-httplib2
   ```

2. Update the `google_signin` route in `auth/auth.py` to properly verify tokens:
   ```python
   from google.auth.transport import requests as google_requests
   from google.oauth2 import id_token
   
   # Replace the current JWT decoding with:
   try:
       idinfo = id_token.verify_oauth2_token(
           credential, google_requests.Request(), GOOGLE_CLIENT_ID
       )
       # Use idinfo instead of decoded_token
   except ValueError:
       return jsonify({'success': False, 'error': 'Invalid token'}), 400
   ```

### 4. Environment Variables
Add to your `.env` file:
```
GOOGLE_CLIENT_ID=your_actual_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

## Features Implemented

### Main Registration Page (`/`)
- Google Sign-In button with official Google branding
- Email/password form with confirm password field
- Client-side password validation
- Responsive design with We-Relate branding
- Pricing information ($12/month)
- Trust badges and security messaging

### Backend Registration (`/`)
- Uses email as username (simplified model)
- Password confirmation validation
- Proper error messages for validation failures
- Redirects to login after successful registration

### Login System (`/auth/login`)
- Accepts email as username
- Backward compatibility with existing users
- Updated UI to reflect email-based login

### Google Sign-In Route (`/auth/google-signin`)
- Accepts Google ID tokens
- Creates new users automatically for first-time Google users
- Logs users in and creates sessions
- Handles duplicate usernames gracefully

## Testing
Run the test script to verify functionality:
```bash
python test_registration.py
```

## Next Steps for Production
1. Set up Google Cloud Console project
2. Get real Google Client ID and Secret
3. Update security implementation for token verification
4. Add environment variable configuration
5. Test with real Google accounts
6. Consider adding user profile pictures from Google
7. Add option to link/unlink Google accounts 