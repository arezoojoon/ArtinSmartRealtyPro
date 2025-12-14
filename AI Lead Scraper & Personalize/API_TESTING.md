# API Testing Guide

This guide helps you test the backend API independently before integrating with the Chrome extension.

## Prerequisites

- Backend server running on `http://localhost:8000`
- OpenAI API key configured in `.env`

## Test 1: Health Check

**PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get
```

**Expected Response:**
```json
{
  "status": "ok",
  "service": "AI Lead Scraper & Personalizer API",
  "version": "1.0.0"
}
```

## Test 2: API Health (Check OpenAI Config)

**PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method Get
```

**Expected Response:**
```json
{
  "status": "healthy",
  "openai_configured": true,
  "model": "gpt-4o-mini"
}
```

## Test 3: Generate Message

**PowerShell:**
```powershell
$body = @{
    profileData = @{
        name = "John Doe"
        about = "Senior Sales Manager passionate about B2B growth"
        experience = @(
            @{
                title = "VP of Sales"
                company = "TechCorp Inc"
                duration = "2020 - Present"
            }
        )
        recentPosts = @(
            @{
                text = "Just closed our biggest deal of the year! But managing all these leads manually is becoming overwhelming. Our team needs better automation tools."
                timestamp = "2024-01-15"
            }
        )
        profileUrl = "https://linkedin.com/in/johndoe"
    }
    productDescription = "I sell AI-powered sales automation software that helps B2B companies increase conversions by 40%"
} | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/generate-message" -Method Post -Body $body -ContentType "application/json"

Write-Host "Generated Message:"
Write-Host $response.message
Write-Host "`nTokens Used: $($response.tokensUsed)"
Write-Host "Model: $($response.model)"
```

**Expected Response:**
A personalized message under 75 words that:
- References John's post about closing a big deal
- Connects to the pain point (manual lead management)
- Suggests your product as a solution
- Ends with a low-friction question

## Test 4: Interactive API Documentation

Open your browser to:
```
http://localhost:8000/docs
```

This opens the **Swagger UI** where you can:
- See all API endpoints
- Test requests interactively
- View request/response schemas
- Try different inputs

## Example Test Scenarios

### Scenario 1: Tech Founder
```json
{
  "profileData": {
    "name": "Sarah Chen",
    "recentPosts": [
      {
        "text": "Scaling our startup is exciting but hiring engineers takes forever. Spending 50% of my time on recruitment instead of product."
      }
    ]
  },
  "productDescription": "I run a technical recruiting agency that finds vetted engineers in 48 hours"
}
```

### Scenario 2: Marketing Leader
```json
{
  "profileData": {
    "name": "Mike Johnson",
    "recentPosts": [
      {
        "text": "Our LinkedIn content gets great engagement, but we struggle to track which posts actually drive pipeline. Need better analytics."
      }
    ]
  },
  "productDescription": "I sell LinkedIn analytics software that connects social engagement to revenue"
}
```

### Scenario 3: Sales Executive
```json
{
  "profileData": {
    "name": "Emily Rodriguez",
    "recentPosts": [
      {
        "text": "Cold calling is dead but personalized outreach takes too much time. How do you scale 1:1 messaging?"
      }
    ]
  },
  "productDescription": "I provide AI-powered personalization for cold outreach at scale"
}
```

## Troubleshooting

### Error: "OpenAI API key not configured"

**Fix:**
```powershell
cd backend
notepad .env
# Add: OPENAI_API_KEY=sk-your-key-here
```
Then restart the server.

### Error: "Connection refused"

**Fix:**
1. Check if backend is running: `http://localhost:8000`
2. Restart the server: `python main.py`
3. Check firewall settings

### Error: "Invalid API key"

**Fix:**
1. Verify your OpenAI key at: https://platform.openai.com/api-keys
2. Make sure you have credits on your account
3. Check for typos in `.env` file

### Error: "Rate limit exceeded"

**Fix:**
- You've hit OpenAI's rate limit
- Wait a few minutes
- Upgrade your OpenAI plan if needed

## Cost Monitoring

Each API call costs approximately **$0.00015** (GPT-4o-mini).

To monitor costs:
1. Visit: https://platform.openai.com/usage
2. Check your usage dashboard
3. Set up billing alerts

## Performance Benchmarks

Expected response times:
- Health check: < 50ms
- Message generation: 2-5 seconds
- Token usage: 100-300 tokens per message

## Next Steps

Once API testing is successful:
1. Load the Chrome extension
2. Configure extension settings
3. Test on real LinkedIn profiles
4. Monitor API usage and costs

---

**Happy Testing! 🚀**
