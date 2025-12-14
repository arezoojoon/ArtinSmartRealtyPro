from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import google.generativeai as genai
import os
from dotenv import load_dotenv
from database import crm
from auto_scraper import AutoScraper

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Artin Lead Scraper & Personalizer API",
    description="Backend API for generating personalized LinkedIn messages using Google Gemini (FREE) - by ArtinSmartAgent",
    version="2.0.0",
    contact={
        "name": "ArtinSmartAgent - Arezoo Mohammadzadegan",
        "url": "https://www.artinsmartagent.com",
        "email": "info@artinsmartagent.com"
    }
)

# CORS configuration - Allow extension to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*", "http://localhost:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Gemini API key from environment variable (FREE - no credit card needed)
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    print("⚠️  WARNING: GEMINI_API_KEY not found in environment variables!")
    print("🎉 Get your FREE API Key:")
    print("1. Go to: https://aistudio.google.com/app/apikey")
    print("2. Click 'Create API Key'")
    print("3. Copy and paste into .env file:")
    print("   GEMINI_API_KEY=your_key_here")
    print("")
    print("✅ 100% FREE! No credit card required!")

# Initialize Gemini client once (reuse for all requests)
gemini_model = None
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    gemini_model = genai.GenerativeModel('gemini-pro')


# Request/Response Models
class Experience(BaseModel):
    title: str = ""
    company: str = ""
    duration: str = ""


class RecentPost(BaseModel):
    text: str
    timestamp: str = ""


class ProfileData(BaseModel):
    name: str
    about: str = ""
    experience: List[Experience] = []
    recentPosts: List[RecentPost] = []
    profileUrl: str = ""


class MessageRequest(BaseModel):
    profileData: ProfileData
    productDescription: str


class MessageResponse(BaseModel):
    message: str
    tokensUsed: Optional[int] = None
    model: str = "gemini-pro"


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "AI Lead Scraper & Personalizer API",
        "version": "1.0.0"
    }


@app.post("/api/generate-message", response_model=MessageResponse)
async def generate_message(request: MessageRequest):
    """
    Generate personalized LinkedIn cold DM using Chain of Thought prompting
    with Pain-Agitate-Solution framework (Powered by FREE Google Gemini)
    """
    
    if not gemini_api_key:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key not configured. Get free key at: https://aistudio.google.com/app/apikey"
        )
    
    if not gemini_model:
        raise HTTPException(
            status_code=500,
            detail="Gemini client not initialized. Please check your API key."
        )
    
    profile = request.profileData
    product = request.productDescription
    
    # ✨ NEW: Check if profile has real posts or not
    has_real_posts = (profile.recentPosts and 
                     len(profile.recentPosts) > 0 and 
                     profile.recentPosts[0].text != '[NO_POSTS_FOUND_USE_ABOUT]')
    
    # If no posts, use About section instead
    if not has_real_posts:
        # Use auto_scraper to generate message without posts
        from auto_scraper import AutoScraper
        scraper = AutoScraper()
        
        current_position = ""
        if profile.experience and len(profile.experience) > 0:
            exp = profile.experience[0]
            current_position = f"{exp.title} at {exp.company}".strip()
        
        generated_message = scraper.generate_message_from_about(
            name=profile.name,
            about=profile.about or '',
            job_title=current_position,
            product_desc=product
        )
        
        return MessageResponse(
            message=generated_message,
            tokensUsed=None,
            model="gemini-pro (no-post-fallback)"
        )
    
    # Extract the most recent post
    recent_post = profile.recentPosts[0].text
    
    # Build context from profile data
    current_position = ""
    if profile.experience and len(profile.experience) > 0:
        exp = profile.experience[0]
        current_position = f"{exp.title} at {exp.company}".strip()
    
    # Construct the AI prompt using Chain of Thought and PAS Framework
    full_prompt = f"""You are an expert copywriter specializing in cold outreach using the 'Pain-Agitate-Solution' framework.

Your task is to write highly personalized LinkedIn cold DMs that feel genuine, not salesy.

CRITICAL RULES:
1. ALWAYS start by referencing their recent post - prove you actually read it
2. Keep the message under 75 words (this is strict)
3. Use casual, professional tone - no corporate jargon
4. End with a low-friction question, NOT a hard pitch
5. Never use phrases like "I noticed", "I came across", "reaching out"
6. Be specific about their post topic, don't be generic

FRAMEWORK:
- Hook: Mention their recent post genuinely
- Bridge: Connect it to a pain point your product solves
- Soft CTA: Ask a question worth responding to

---

Generate a personalized cold DM for this person:

NAME: {profile.name}
CURRENT ROLE: {current_position or 'Not specified'}
RECENT POST TOPIC: {recent_post[:300]}

MY PRODUCT/SERVICE: {product}

Write the cold DM now. Remember: Under 75 words, start with their post, end with a question.

OUTPUT ONLY THE MESSAGE - NO EXPLANATIONS OR EXTRA TEXT."""

    try:
        # Use Gemini Pro (FREE model)
        response = gemini_model.generate_content(full_prompt)
        
        generated_message = response.text.strip()
        
        # Gemini doesn't provide token count easily, set to None
        tokens_used = None
        
        return MessageResponse(
            message=generated_message,
            tokensUsed=tokens_used,
            model="gemini-pro"
        )
        
    except Exception as e:
        error_msg = str(e)
        
        # Check for common Gemini errors
        if "API_KEY_INVALID" in error_msg or "invalid api key" in error_msg.lower():
            raise HTTPException(
                status_code=401,
                detail="Invalid Gemini API key. Get free key at: https://aistudio.google.com/app/apikey"
            )
        elif "quota" in error_msg.lower() or "rate" in error_msg.lower():
            raise HTTPException(
                status_code=429,
                detail="Gemini rate limit exceeded. Please wait a minute and try again."
            )
        else:
            print(f"Error generating message: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate message: {error_msg}"
            )


@app.post("/api/save-lead")
async def save_lead(request: MessageRequest):
    """
    Save scraped lead to CRM database
    """
    try:
        result = crm.add_lead({
            'name': request.profileData.name,
            'about': request.profileData.about,
            'experience': [exp.dict() for exp in request.profileData.experience],
            'recentPosts': [post.dict() for post in request.profileData.recentPosts],
            'profileUrl': request.profileData.profileUrl
        })
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save lead: {str(e)}"
        )


@app.post("/api/update-message")
async def update_message(data: Dict):
    """Update generated message for a lead"""
    linkedin_url = data.get('linkedin_url')
    message = data.get('message')
    
    if not linkedin_url or not message:
        raise HTTPException(status_code=400, detail="Missing linkedin_url or message")
    
    success = crm.update_generated_message(linkedin_url, message)
    
    return {"success": success}


@app.post("/api/mark-sent")
async def mark_sent(data: Dict):
    """Mark lead as message sent"""
    linkedin_url = data.get('linkedin_url')
    
    if not linkedin_url:
        raise HTTPException(status_code=400, detail="Missing linkedin_url")
    
    success = crm.mark_message_sent(linkedin_url)
    
    return {"success": success}


@app.get("/api/leads")
async def get_leads(limit: int = 1000):
    """Get all leads from database"""
    leads = crm.get_all_leads(limit=limit)
    return {"leads": leads}


@app.get("/api/stats")
async def get_stats():
    """Get CRM statistics"""
    stats = crm.get_stats()
    return stats


@app.get("/api/export-excel")
async def export_excel():
    """
    Export all leads to Excel file and download
    """
    try:
        # Generate Excel file
        file_path = crm.export_to_excel()
        
        # Return file for download
        return FileResponse(
            path=file_path,
            filename=file_path,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                "Content-Disposition": f"attachment; filename={file_path}"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export Excel: {str(e)}"
        )


@app.get("/api/health")
async def health_check():
    """Detailed health check with API key status"""
    stats = crm.get_stats()
    return {
        "status": "healthy",
        "gemini_configured": bool(gemini_api_key),
        "model": "gemini-pro (FREE)",
        "database": {
            "total_leads": stats['total_leads'],
            "messages_sent": stats['messages_sent']
        }
    }


# ============================================================================
# 🤖 AUTO-SCRAPER ENDPOINTS - Fully Automated
# ============================================================================

auto_scraper = AutoScraper()

@app.post("/api/auto/send-daily-linkedin")
async def auto_send_daily_linkedin(data: Dict):
    """
    Automatically send 10 LinkedIn messages daily
    """
    product_desc = data.get('product_description', '')
    
    if not product_desc:
        raise HTTPException(status_code=400, detail="Product description required")
    
    result = auto_scraper.send_daily_linkedin_messages(product_desc)
    return result


@app.get("/api/auto/prepare-email-campaign")
async def auto_prepare_email_campaign(product_desc: str):
    """
    Prepare email list with personalized messages
    """
    email_list = auto_scraper.prepare_email_campaign(product_desc)
    return {
        'count': len(email_list),
        'emails': email_list
    }


@app.get("/api/auto/prepare-whatsapp-campaign")
async def auto_prepare_whatsapp_campaign(product_desc: str):
    """
    Prepare WhatsApp list with ready-to-use links
    """
    whatsapp_list = auto_scraper.prepare_whatsapp_campaign(product_desc)
    return {
        'count': len(whatsapp_list),
        'contacts': whatsapp_list
    }


@app.get("/api/auto/campaign-stats")
async def auto_campaign_stats():
    """
    Complete campaign statistics
    """
    return auto_scraper.get_campaign_stats()


@app.post("/api/auto/generate-without-post")
async def auto_generate_without_post(data: Dict):
    """
    Generate message without needing posts (uses About section only)
    """
    name = data.get('name', '')
    about = data.get('about', '')
    job_title = data.get('job_title', '')
    product_desc = data.get('product_description', '')
    
    message = auto_scraper.generate_message_from_about(
        name=name,
        about=about,
        job_title=job_title,
        product_desc=product_desc
    )
    
    return {'message': message}


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Artin Lead Scraper & Personalizer API...")
    print("   by ArtinSmartAgent - Arezoo Mohammadzadegan")
    print("   Website: www.artinsmartagent.com")
    print("")
    print("🎉 Powered by Google Gemini (100% FREE!)")
    print("")
    print("✨ AUTO-SCRAPER Features:")
    print("   • Auto-scrape 500 leads")
    print("   • Auto-send 10 LinkedIn messages/day")
    print("   • Auto-generate email campaigns")
    print("   • Auto-generate WhatsApp campaigns")
    print("   • Works WITHOUT posts (uses About section)")
    print("")
    print("📝 To get your FREE API Key:")
    print("   1. Go to: https://aistudio.google.com/app/apikey")
    print("   2. Click 'Create API Key'")
    print("   3. Copy and paste in .env: GEMINI_API_KEY=your_key")
    print("")
    print("🌐 API running at: http://localhost:8000")
    print("📚 API docs at: http://localhost:8000/docs")
    print("")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

