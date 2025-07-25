# 🤖 Discord AI Selfbot - 2025 Edition

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-Educational-red.svg)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Selfbot-purple.svg)](https://discord.com)
[![AI](https://img.shields.io/badge/AI-Groq%20%7C%20OpenAI-green.svg)](https://groq.com)

A powerful, modern Discord selfbot with AI capabilities. Features the latest AI models, enhanced security measures, and cloud deployment support.

> ⚠️ **IMPORTANT DISCLAIMER**: This project violates Discord's Terms of Service and is for educational purposes only. Use at your own risk.

---

## ⭐ Key Features

| Feature | Description |
|---------|-------------|
| 🧠 **Latest AI Models** | Groq llama-3.3-70b-versatile + OpenAI GPT-4o |
| 🖼️ **Image Analysis** | AI vision for image recognition and analysis |
| 🔒 **Anti-Detection** | Advanced security with realistic human behavior |
| 💬 **Smart Conversations** | Context-aware responses with conversation memory |
| ☁️ **Cloud Ready** | Deploy to Render, Replit, or run locally |
| 🛡️ **Rate Limiting** | Built-in spam protection and cooldowns |
| 🎯 **Channel Control** | Selective activation per server/channel |
| 📊 **Health Monitoring** | Real-time status and error tracking |

---

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)

**Windows:**
```batch
# Download and run
run.bat
```

**Linux/macOS:**
```bash
chmod +x run.sh
./run.sh
```

### Option 2: Manual Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/Discord-AI-Selfbot.git
   cd Discord-AI-Selfbot
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements-render.txt
   ```

3. **Get Your API Keys**
   - **Discord Token**: [See guide](DISCORD_TOKEN_GUIDE.md)
   - **Groq API**: Free at [console.groq.com](https://console.groq.com)
   - **OpenAI API**: Optional at [platform.openai.com](https://platform.openai.com)

4. **Configure Environment**
   ```bash
   # Copy example configuration
   cp config/example.env config/.env
   
   # Edit with your tokens
   nano config/.env
   ```

5. **Run the Bot**
   ```bash
   python main.py
   ```

---

## ☁️ Cloud Deployment

### Deploy to Render (Free Hosting)

1. **Fork this repository** to your GitHub account

2. **Create a Render service**:
   - Go to [render.com](https://render.com) and connect your GitHub
   - Select your forked repository
   - Choose "Web Service"

3. **Configure deployment**:
   - **Build Command**: `pip install -r requirements-render.txt`
   - **Start Command**: `python start.py`

4. **Set environment variables**:
   ```
   DISCORD_TOKEN=your_discord_token_here
   GROQ_API_KEY=your_groq_api_key_here
   OPENAI_API_KEY=your_openai_key_here  # Optional
   ```

5. **Deploy** and monitor the logs

📖 **Full Guide**: See [RENDER_DEPLOY.md](RENDER_DEPLOY.md) for detailed instructions

---

## 🔧 Configuration

### Environment Variables

Create `config/.env` with your tokens:

```env
# Required
DISCORD_TOKEN=your_discord_token_here
GROQ_API_KEY=your_groq_api_key_here

# Optional
OPENAI_API_KEY=your_openai_key_here
ERROR_WEBHOOK_URL=your_discord_webhook_url
```

### Bot Settings

Edit `config/config.yaml` to customize:

```yaml
bot:
  prefix: "!"                    # Command prefix
  owner_id: 123456789012345678   # Your Discord user ID
  trigger: "ai, bot, hey"        # Words that trigger responses
  allow_dm: true                 # Respond to DMs
  realistic_typing: true         # Human-like typing simulation
  
ai:
  groq_model: "llama-3.3-70b-versatile"
  openai_model: "gpt-4o"
  max_tokens: 300
  temperature: 0.7
```

---

## 🎮 Commands

| Command | Description | Usage |
|---------|-------------|--------|
| `!help` | Show all commands | `!help` |
| `!toggleactive` | Toggle AI in current channel | `!toggleactive` |
| `!personality` | Analyze user personality | `!personality @user` |
| `!stats` | Show bot statistics | `!stats` |
| `!reload` | Reload bot configuration | `!reload` |
| `!system` | Show system information | `!system` |
| `!cleanup` | Clean old database entries | `!cleanup` |

**Admin Commands** (Owner only):
- `!adduser <id>` - Add authorized user
- `!removeuser <id>` - Remove authorized user  
- `!maintenance` - Toggle maintenance mode
- `!prompt view/set/clear` - Manage AI instructions

---

## 🔒 Security Features

### Anti-Detection Measures
- **Realistic Typing**: Variable delays that mimic human typing
- **Message Batching**: Groups responses to avoid rapid-fire messages
- **Rate Limiting**: Smart cooldowns based on user and channel activity
- **Startup Delays**: Random delays on bot initialization
- **Human Patterns**: Response timing that matches natural conversation

### Privacy & Safety
- **Local Database**: All data stored locally in SQLite
- **No Data Collection**: No telemetry or user data harvesting
- **Secure Token Storage**: Environment variables for sensitive data
- **Error Logging**: Comprehensive logs without exposing tokens

---

## 🤖 AI Capabilities

### Groq Integration
- **Model**: llama-3.3-70b-versatile (latest)
- **Speed**: Ultra-fast responses (~0.5s average)
- **Cost**: Free tier with generous limits
- **Reliability**: 99.9% uptime with automatic failover

### OpenAI Fallback
- **Model**: GPT-4o (latest)
- **Quality**: Highest quality responses
- **Features**: Advanced reasoning and creativity
- **Usage**: Automatic fallback when Groq is unavailable

### Smart Features
- **Context Memory**: Remembers previous messages in conversation
- **Image Analysis**: Can analyze and respond to uploaded images
- **Emotion Detection**: Understands sentiment and responds appropriately
- **Multi-language**: Responds in the language used by the user

---

## 📊 Monitoring & Health

### Built-in Health Checks
- **Status Endpoint**: `/health` - Bot status and uptime
- **Activity Monitor**: `/activity` - Real-time activity simulation
- **Statistics**: `/stats` - Detailed bot statistics

### Error Reporting
- **Discord Webhooks**: Real-time error notifications
- **Log Files**: Comprehensive logging to `selfbot.log`
- **Database Tracking**: Error patterns and statistics

### Performance Monitoring
- **Response Times**: AI response latency tracking
- **Rate Limiting**: Request frequency monitoring
- **Resource Usage**: CPU, memory, and network tracking

---

## ⚠️ Important Notes

### Legal Disclaimer
- **Educational Purpose**: This project is for learning and experimentation
- **Terms of Service**: Using selfbots violates Discord's ToS
- **Account Risk**: Your Discord account may be suspended or banned
- **Responsibility**: Use only on accounts you don't mind losing

### Best Practices
- **Test Environment**: Use a separate Discord account for testing
- **Rate Limits**: Don't spam messages or commands
- **Server Rules**: Respect server rules and moderation
- **Privacy**: Don't share your bot token with others

### Troubleshooting
- **Token Issues**: Ensure your Discord token is valid and not expired
- **API Errors**: Check your Groq/OpenAI API keys and quotas
- **Rate Limits**: If responses are slow, you may have hit rate limits
- **Channel Access**: Make sure the bot account can see and send messages

---

## 🤝 Contributing

We welcome contributions! Please:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Contributors

Special thanks to those who helped make this project possible:
- **_imjay** - Core development and AI integration
- **.joshua** - Enhanced features and cloud deployment support

### Development Setup
```bash
# Clone your fork
git clone https://github.com/yourusername/Discord-AI-Selfbot.git

# Install development dependencies
pip install -r requirements-render.txt

# Run tests
python deploy-test.py

# Start development server
python main.py
```

---

## 📝 License

This project is licensed for **Educational Use Only**. See the [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- **Documentation**: [Full project docs](replit.md)
- **Deployment Guide**: [Render deployment](RENDER_DEPLOY.md)
- **Token Guide**: [Getting Discord tokens](DISCORD_TOKEN_GUIDE.md)
- **Support**: [Discord Server](https://discord.gg/yUWmzQBV4P)

---

<div align="center">

**⭐ Star this repository if you found it helpful!**

Made with ❤️ for the Discord community

</div>
