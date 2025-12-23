
import os
import time
import random
import logging
import asyncio
from typing import Optional, List, Any
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Safety settings to prevent API key ban
GEMINI_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]

def get_gemini_api_keys() -> List[str]:
    """Get all available Gemini API keys from environment"""
    keys = [
        os.getenv("GEMINI_KEY_1"),
        os.getenv("GEMINI_KEY_2"),
        os.getenv("GEMINI_KEY_3"),
        os.getenv("GEMINI_API_KEY"),
        os.getenv("GOOGLE_API_KEY"),
    ]
    # Filter out None and placeholder values
    valid_keys = [k for k in keys if k and k != "your_gemini_api_key" and k.startswith("AIza")]
    
    if not valid_keys:
        logger.error("❌ No valid Gemini API keys found! Please check .env file.")
    
    return valid_keys


def get_random_api_key() -> Optional[str]:
    """Get a random API key from available keys (Key Rotation)"""
    keys = get_gemini_api_keys()
    if not keys:
        return None
    selected = random.choice(keys)
    logger.debug(f"🔑 Using Gemini key ending in ...{selected[-6:]}")
    return selected


class GeminiClient:
    """
    Wrapper for Gemini API with robust features:
    - Key Rotation
    - Retry Logic (Exponential Backoff)
    - Error Handling
    - Safety Settings
    """
    
    def __init__(self, model_name: str = 'gemini-1.5-flash'):
        self.model_name = model_name
        self.api_keys = get_gemini_api_keys()
        self.current_key = get_random_api_key()
        self.model = None
        
        if self.current_key:
            self._init_model(self.current_key)
        else:
            logger.warning("⚠️ GeminiClient initialized without valid keys - calls will fail")
            
    def _init_model(self, api_key: str):
        """Initialize Gemini model with specific key"""
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                safety_settings=GEMINI_SAFETY_SETTINGS
            )
            self.current_key = api_key
            logger.info(f"✅ Gemini model {self.model_name} initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini model: {e}")
            self.model = None
            
    def _rotate_key(self) -> bool:
        """Rotate to a different API key. Returns True if successful."""
        if len(self.api_keys) <= 1:
            logger.warning("⚠️ Cannot rotate key - only 1 key available")
            return False
        
        other_keys = [k for k in self.api_keys if k != self.current_key]
        if other_keys:
            new_key = random.choice(other_keys)
            logger.info(f"🔄 Rotating Gemini API key...")
            self._init_model(new_key)
            return True
        return False
        
    async def generate_content_async(self, contents: List[Any], max_retries: int = 3, **kwargs):
        """
        Generate content asynchronously with retry logic and key rotation
        """
        wait_time = 2
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if not self.model:
                    if not self._init_if_possible():
                         raise Exception("Gemini model not initialized and no valid keys")

                # Run in executor because genai library is synchronous
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: self.model.generate_content(contents, **kwargs)
                )
                
                return response
                
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # Check for quota/rate limit errors
                if any(x in error_str for x in ['quota', 'resource exhausted', '429']):
                    logger.warning(f"⚠️ Rate limit hit (attempt {attempt + 1}/{max_retries}). Waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    wait_time *= 2
                    self._rotate_key()
                    continue
                
                # Check for invalid key
                if any(x in error_str for x in ['invalid', 'api key', '400']):
                    logger.error(f"❌ Invalid API key detected (attempt {attempt + 1}). Rotating...")
                    if not self._rotate_key():
                        logger.error("❌ No alternative keys available to rotate to")
                        raise e
                    continue
                    
                # Other errors
                logger.error(f"❌ Gemini error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                
        logger.error(f"❌ All {max_retries} retry attempts failed. Last error: {last_error}")
        raise last_error

    def generate_content(self, contents: List[Any], max_retries: int = 3, **kwargs):
        """Synchronous version of generate_content"""
        # Simple wrapper for sync usage if needed
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.generate_content_async(contents, max_retries, **kwargs))

    def _init_if_possible(self):
        """Try to initialize if keys exist but model is None"""
        if self.api_keys:
            self.current_key = get_random_api_key()
            self._init_model(self.current_key)
            return True
        return False
        
    def upload_file(self, file_path: str, mime_type: str = None):
        """Upload file wrapper"""
        if not self.current_key:
             self._rotate_key()
             
        # Configure genai with current key before upload
        genai.configure(api_key=self.current_key)
        return genai.upload_file(file_path, mime_type=mime_type)
