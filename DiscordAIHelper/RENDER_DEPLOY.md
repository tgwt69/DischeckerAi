# Discord AI Selfbot - Render Deployment Guide

This guide will help you deploy your Discord AI Selfbot to Render.com for 24/7 hosting.

## Prerequisites

1. A Discord user token (your personal account token)
2. A Groq API key (free at console.groq.com)
3. An OpenAI API key (optional, for fallback)
4. A Render.com account

## Deployment Steps

### 1. Fork or Clone the Repository

1. Fork this repository to your GitHub account
2. Or clone it to your local machine and push to your own GitHub repo

### 2. Create a Render Web Service

1. Go to [Render.com](https://render.com) and sign in
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `discord-ai-selfbot` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements-render.txt`
   - **Start Command**: `python start.py`

### 3. Set Environment Variables

In your Render dashboard, add these environment variables:

**Required:**
- `DISCORD_TOKEN`: Your Discord user token
- `GROQ_API_KEY`: Your Groq API key from console.groq.com

**Optional:**
- `OPENAI_API_KEY`: Your OpenAI API key (recommended for fallback)
- `ERROR_WEBHOOK_URL`: Discord webhook URL for error notifications

### 4. How to Get Your Discord Token

⚠️ **Warning**: Using selfbots violates Discord's Terms of Service. Use at your own risk.

1. Open Discord in your web browser (not the app)
2. Press F12 to open Developer Tools
3. Go to the Network tab
4. Send a message or refresh Discord
5. Look for API requests and find the 'Authorization' header
6. Copy the token value (starts with 'MTA', 'MTU', 'Nz', 'OD', etc.)

### 5. Deploy

1. Click "Create Web Service" in Render
2. Render will automatically build and deploy your bot
3. Monitor the logs to ensure successful deployment

## Important Notes

### Free Tier Limitations
- Render's free tier spins down after 15 minutes of inactivity
- The bot includes keep-alive mechanisms to stay active
- For true 24/7 operation, consider upgrading to a paid plan

### Configuration
- The bot automatically detects cloud environments
- Configuration files are created automatically
- Database is stored in the `/data` directory

### Health Monitoring
- Health check endpoint available at `https://your-app.onrender.com/health`
- Multiple monitoring endpoints for uptime services
- Built-in error logging and reporting

### Security
- Never commit your Discord token to version control
- Use Render's environment variables for all sensitive data
- The bot includes anti-detection measures for Discord

## Troubleshooting

### Bot Not Responding
1. Check the Render logs for errors
2. Verify your Discord token is valid
3. Ensure the bot is active in the correct channels

### Build Failures
1. Check that all dependencies are in `requirements-render.txt`
2. Verify Python version compatibility
3. Review build logs for specific errors

### Token Issues
1. Make sure the token starts with the correct prefix
2. Test the token locally first
3. Regenerate the token if needed

## Support

For issues with:
- **Deployment**: Check Render's documentation
- **Bot functionality**: Review the project logs
- **Discord API**: Ensure compliance with rate limits

Remember: This is an educational project. Selfbots violate Discord's ToS.