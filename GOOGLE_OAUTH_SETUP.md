# Google OAuth Setup Guide

This guide will help you set up Google OAuth authentication for We Relate.

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google+ API" and enable it
   - Also enable "Google OAuth2 API"

## Step 2: Create OAuth Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Configure the OAuth consent screen first if prompted:
   - Choose "External" for user type
   - Fill in the required fields:
     - App name: "We Relate"
     - User support email: your email
     - Developer contact information: your email
   - Add scopes: `openid`, `email`, `profile`
   - Add test users if needed
4. Create OAuth client ID:
   - Application type: "Web application"
   - Name: "We Relate"
   - Authorized redirect URIs:
     - For local development: `http://localhost:5000/login/google/authorized`
     - For production: `https://yourdomain.com/login/google/authorized`

## Step 3: Configure Environment Variables

1. Copy your Client ID and Client Secret from the Google Cloud Console
2. Update your `.env` file:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key
SECRET_KEY=your_secret_key
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
```

## Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 5: Initialize Database

The app will automatically create the necessary database tables when you first run it.

```bash
python run.py
```

## Step 6: Test the Setup

1. Navigate to `http://localhost:5000`
2. Click "Continue with Google"
3. Complete the OAuth flow
4. You should be redirected back to the app and logged in

## Troubleshooting

### Common Issues

1. **redirect_uri_mismatch error**
   - Make sure the redirect URI in Google Cloud Console exactly matches your app URL
   - For local development: `http://localhost:5000/login/google/authorized`

2. **OAuth consent screen not configured**
   - Complete the OAuth consent screen configuration in Google Cloud Console
   - Add your email as a test user during development

3. **Invalid client_id**
   - Double-check your `GOOGLE_OAUTH_CLIENT_ID` in the `.env` file
   - Make sure there are no extra spaces or characters

### Production Deployment

For production deployment:

1. Update the authorized redirect URI in Google Cloud Console to your production domain
2. Set up proper environment variables on your production server
3. Use HTTPS for your production domain (required by Google OAuth)

## Security Notes

- Never commit your `.env` file to version control
- Use different OAuth credentials for development and production
- Regularly rotate your client secrets
- Review and limit the OAuth scopes to only what you need