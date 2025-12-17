"""
AI-Powered Property Information Extractor
Extracts property details from PDFs and images automatically
Agents just upload files - system does the rest!
"""

import re
import io
import base64
from typing import Dict, Optional, List
from pathlib import Path
import logging

# PDF Processing
try:
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False
    print("⚠️ PyPDF2 not installed. Run: pip install PyPDF2")

# Image Processing
try:
    from PIL import Image
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("⚠️ Pillow/pytesseract not installed. Run: pip install Pillow pytesseract")

# AI Vision (Gemini Vision for complex extraction)
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("⚠️ google-generativeai not installed. Run: pip install google-generativeai")

logger = logging.getLogger(__name__)


class PropertyExtractor:
    """Extract property information from PDFs and images automatically"""
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_model = None
        if HAS_GEMINI and gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def extract_from_pdf(self, pdf_path: str) -> Dict:
        """
        Extract property information from PDF brochure
        
        Returns:
            {
                'name': str,
                'price': float (AED),
                'area_sqft': float,
                'bedrooms': int,
                'bathrooms': int,
                'location': str,
                'description': str,
                'roi_percentage': float,
                'is_golden_visa_eligible': bool,
                'payment_plan': str,
                'completion_date': str,
                'raw_text': str
            }
        """
        if not HAS_PDF:
            raise ImportError("PyPDF2 not installed")
        
        try:
            # Read PDF text
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            logger.info(f"📄 Extracted {len(text)} characters from PDF")
            
            # Parse property details from text
            property_data = self._parse_property_text(text)
            property_data['raw_text'] = text[:1000]  # Store first 1000 chars
            
            return property_data
            
        except Exception as e:
            logger.error(f"❌ PDF extraction failed: {e}")
            return {'error': str(e)}
    
    async def extract_from_image(self, image_path: str, use_ai: bool = True) -> Dict:
        """
        Extract property information from image (flyer, screenshot, photo)
        
        Args:
            image_path: Path to image file
            use_ai: If True, use Gemini Vision for better extraction
        
        Returns: Same as extract_from_pdf
        """
        try:
            # Method 1: Gemini Vision (Best quality, FREE!)
            if use_ai and self.gemini_model:
                return await self._extract_with_gemini_vision(image_path)
            
            # Method 2: Tesseract OCR (Free, lower quality)
            elif HAS_OCR:
                return await self._extract_with_ocr(image_path)
            
            else:
                raise ImportError("No OCR method available. Install google-generativeai or pytesseract")
                
        except Exception as e:
            logger.error(f"❌ Image extraction failed: {e}")
            return {'error': str(e)}
    
    async def _extract_with_gemini_vision(self, image_path: str) -> Dict:
        """Use Gemini Vision to extract property details from image"""
        
        # Read image
        from PIL import Image as PILImage
        image = PILImage.open(image_path)
        
        prompt = """
        You are a Dubai real estate property analyzer. Extract all property information from this image.
        
        Return a JSON object with these fields (use null if not found):
        {
            "name": "Property name",
            "price": 1500000 (price in AED as number),
            "area_sqft": 1200 (area in square feet as number),
            "bedrooms": 2 (number of bedrooms),
            "bathrooms": 2 (number of bathrooms),
            "location": "Dubai Marina",
            "description": "Brief description",
            "roi_percentage": 8.5 (ROI % as number),
            "is_golden_visa_eligible": true/false,
            "payment_plan": "60/40" or "100% on handover",
            "completion_date": "Q4 2025",
            "property_type": "apartment/villa/townhouse/penthouse",
            "transaction_type": "buy/rent",
            "is_off_plan": true/false,
            "amenities": ["Pool", "Gym", "Parking"]
        }
        
        Extract numbers carefully:
        - Price: Look for "AED", "Dirhams", "Price", numbers with commas
        - Area: Look for "sqft", "sq ft", "square feet", "m²" (convert to sqft if m²)
        - Bedrooms: "BR", "Bed", "Bedroom", "Studio" = 0
        - ROI: "ROI", "Return", "Yield", "%" 
        
        If area is in m², convert to sqft (multiply by 10.764).
        Return ONLY the JSON object, no markdown.
        """
        
        try:
            response = self.gemini_model.generate_content([prompt, image])
            result_text = response.text.strip()
            
            # Remove markdown code blocks if present
            result_text = re.sub(r'^```json\s*', '', result_text)
            result_text = re.sub(r'\s*```$', '', result_text)
            
            # Parse JSON
            import json
            property_data = json.loads(result_text)
            
            logger.info(f"✅ Gemini Vision extracted: {property_data.get('name', 'Unknown')}")
            return property_data
            
        except Exception as e:
            logger.error(f"❌ Gemini Vision failed: {e}")
            return {'error': str(e)}
    
    async def _extract_with_ocr(self, image_path: str) -> Dict:
        """Use Tesseract OCR to extract text from image"""
        
        if not HAS_OCR:
            raise ImportError("pytesseract not installed")
        
        try:
            # Open image
            image = Image.open(image_path)
            
            # Extract text
            text = pytesseract.image_to_string(image)
            
            logger.info(f"🔍 OCR extracted {len(text)} characters")
            
            # Parse property details
            property_data = self._parse_property_text(text)
            property_data['raw_text'] = text[:1000]
            
            return property_data
            
        except Exception as e:
            logger.error(f"❌ OCR extraction failed: {e}")
            return {'error': str(e)}
    
    def _parse_property_text(self, text: str) -> Dict:
        """
        Parse property information from raw text using regex patterns
        Works for both PDF text and OCR results
        """
        
        data = {
            'name': None,
            'price': None,
            'area_sqft': None,
            'bedrooms': None,
            'bathrooms': None,
            'location': None,
            'description': None,
            'roi_percentage': None,
            'is_golden_visa_eligible': False,
            'payment_plan': None,
            'completion_date': None,
            'property_type': None,
            'transaction_type': 'buy',
            'is_off_plan': False,
            'amenities': []
        }
        
        text_lower = text.lower()
        
        # Extract PRICE (AED)
        price_patterns = [
            r'aed\s*([\d,]+(?:\.\d+)?)\s*(?:million|m)?',
            r'price[:\s]*([\d,]+(?:\.\d+)?)\s*(?:aed|million|m)?',
            r'([\d,]+(?:\.\d+)?)\s*(?:aed|million|m)',
            r'starting from\s*([\d,]+)'
        ]
        for pattern in price_patterns:
            match = re.search(pattern, text_lower)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    price = float(price_str)
                    # If it says "million" or is a small number, multiply
                    if 'million' in text_lower[max(0, match.start()-20):match.end()+10] or price < 100:
                        price *= 1_000_000
                    data['price'] = price
                    break
                except:
                    pass
        
        # Extract AREA (sqft)
        area_patterns = [
            r'([\d,]+(?:\.\d+)?)\s*(?:sq\.?\s*ft|sqft|square feet)',
            r'area[:\s]*([\d,]+(?:\.\d+)?)\s*(?:sq\.?\s*ft|sqft)?',
            r'([\d,]+(?:\.\d+)?)\s*m²'  # Convert from m² to sqft
        ]
        for pattern in area_patterns:
            match = re.search(pattern, text_lower)
            if match:
                area_str = match.group(1).replace(',', '')
                try:
                    area = float(area_str)
                    # If in m², convert to sqft
                    if 'm²' in pattern or 'm2' in text_lower[match.start():match.end()+5]:
                        area *= 10.764
                    data['area_sqft'] = area
                    break
                except:
                    pass
        
        # Extract BEDROOMS
        bedroom_patterns = [
            r'(\d+)\s*(?:br|bed|bedroom)',
            r'studio',  # Studio = 0 bedrooms
            r'(\d+)b(?:\s|$)'  # 2B, 3B format
        ]
        for pattern in bedroom_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if 'studio' in pattern:
                    data['bedrooms'] = 0
                else:
                    try:
                        data['bedrooms'] = int(match.group(1))
                    except:
                        pass
                break
        
        # Extract BATHROOMS
        bathroom_patterns = [
            r'(\d+)\s*(?:bath|bathroom)',
            r'(\d+)\s*ba(?:\s|$)'
        ]
        for pattern in bathroom_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    data['bathrooms'] = int(match.group(1))
                    break
                except:
                    pass
        
        # Extract LOCATION (Dubai areas)
        dubai_areas = [
            'dubai marina', 'downtown dubai', 'business bay', 'jbr', 'jumeirah beach residence',
            'palm jumeirah', 'arabian ranches', 'dubai hills', 'city walk', 'bluewaters',
            'dubai creek harbour', 'meydan', 'sports city', 'motor city', 'jvc',
            'jumeirah village circle', 'dubai south', 'international city', 'discovery gardens',
            'silicon oasis', 'tecom', 'barsha', 'jlt', 'jumeirah lakes towers', 'difc',
            'damac hills', 'akoya oxygen', 'tilal al ghaf', 'sobha hartland'
        ]
        for area in dubai_areas:
            if area in text_lower:
                data['location'] = area.title()
                break
        
        # Extract ROI
        roi_patterns = [
            r'roi[:\s]*([\d.]+)\s*%',
            r'return[:\s]*([\d.]+)\s*%',
            r'yield[:\s]*([\d.]+)\s*%',
            r'([\d.]+)\s*%\s*roi'
        ]
        for pattern in roi_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    data['roi_percentage'] = float(match.group(1))
                    break
                except:
                    pass
        
        # Detect GOLDEN VISA
        if any(word in text_lower for word in ['golden visa', 'golden-visa', 'uae residence']):
            data['is_golden_visa_eligible'] = True
        
        # Extract PAYMENT PLAN
        payment_patterns = [
            r'(\d+/\d+)\s*(?:payment|plan)',
            r'payment plan[:\s]*(\d+/\d+)',
            r'(\d+%)\s*on handover'
        ]
        for pattern in payment_patterns:
            match = re.search(pattern, text_lower)
            if match:
                data['payment_plan'] = match.group(1)
                break
        
        # Detect OFF-PLAN
        if any(word in text_lower for word in ['off-plan', 'off plan', 'under construction', 'completion']):
            data['is_off_plan'] = True
        
        # Extract COMPLETION DATE
        completion_patterns = [
            r'completion[:\s]*(q\d\s*\d{4})',
            r'handover[:\s]*(q\d\s*\d{4})',
            r'ready[:\s]*(\d{4})'
        ]
        for pattern in completion_patterns:
            match = re.search(pattern, text_lower)
            if match:
                data['completion_date'] = match.group(1).upper()
                break
        
        # Detect PROPERTY TYPE
        if 'villa' in text_lower:
            data['property_type'] = 'villa'
        elif 'townhouse' in text_lower:
            data['property_type'] = 'townhouse'
        elif 'penthouse' in text_lower:
            data['property_type'] = 'penthouse'
        elif 'studio' in text_lower:
            data['property_type'] = 'studio'
        else:
            data['property_type'] = 'apartment'
        
        # Extract AMENITIES
        amenity_keywords = {
            'pool': 'Swimming Pool',
            'gym': 'Gym',
            'parking': 'Parking',
            'beach': 'Beach Access',
            'garden': 'Private Garden',
            'balcony': 'Balcony',
            'maid room': "Maid's Room",
            'security': '24/7 Security',
            'concierge': 'Concierge',
            'spa': 'Spa',
            'kids play': "Kids Play Area",
            'bbq': 'BBQ Area'
        }
        for keyword, amenity in amenity_keywords.items():
            if keyword in text_lower:
                data['amenities'].append(amenity)
        
        # Extract NAME (first line or title)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            # Take first meaningful line as name
            for line in lines[:5]:
                if len(line) > 10 and len(line) < 100:
                    data['name'] = line
                    break
        
        # Create DESCRIPTION (first 200 chars)
        clean_text = ' '.join(text.split()[:50])
        if len(clean_text) > 200:
            data['description'] = clean_text[:200] + '...'
        else:
            data['description'] = clean_text
        
        return data
    
    async def extract_from_url(self, url: str) -> Dict:
        """
        Extract property information from URL (Bayut, Property Finder, etc.)
        
        Future enhancement: Web scraping
        """
        # TODO: Implement web scraping for property portals
        return {'error': 'URL extraction not yet implemented'}
    
    def validate_extraction(self, data: Dict) -> tuple[bool, List[str]]:
        """
        Validate extracted property data
        
        Returns:
            (is_valid, list_of_missing_fields)
        """
        required_fields = ['price', 'location']
        recommended_fields = ['name', 'area_sqft', 'bedrooms', 'property_type']
        
        missing_required = [f for f in required_fields if not data.get(f)]
        missing_recommended = [f for f in recommended_fields if not data.get(f)]
        
        is_valid = len(missing_required) == 0
        
        return is_valid, missing_required + missing_recommended


# Quick test function
async def test_extraction():
    """Test the property extractor"""
    import os
    
    extractor = PropertyExtractor(gemini_api_key=os.getenv('GEMINI_API_KEY'))
    
    print("🧪 Testing Property Extractor\n")
    
    # Test with sample text
    sample_text = """
    Marina Heights Luxury Tower
    2 Bedroom Apartment in Dubai Marina
    
    Price: AED 2,500,000
    Area: 1,450 sq.ft
    2 Bedrooms | 3 Bathrooms
    
    ROI: 8.5% per annum
    Golden Visa Eligible
    Sea View | Fully Furnished
    
    Amenities: Swimming Pool, Gym, Parking, 24/7 Security
    """
    
    result = extractor._parse_property_text(sample_text)
    
    print("📋 Extracted Data:")
    for key, value in result.items():
        if value:
            print(f"  {key}: {value}")
    
    is_valid, missing = extractor.validate_extraction(result)
    print(f"\n✅ Valid: {is_valid}")
    if missing:
        print(f"⚠️ Missing: {', '.join(missing)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_extraction())
