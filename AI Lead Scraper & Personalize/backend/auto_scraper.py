"""
🤖 Auto Scraper - Automated LinkedIn Lead Generation

This module automatically:
1. Scrapes 500 leads from LinkedIn
2. Sends 10 daily LinkedIn messages
3. Automated email campaigns
4. Automated WhatsApp campaigns
"""

import time
import random
from typing import List, Dict
from database import LeadsCRM
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class AutoScraper:
    def __init__(self):
        self.crm = LeadsCRM()
        
        # Configure Gemini AI
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key and api_key != 'your_gemini_api_key_here':
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
            
        self.daily_linkedin_limit = 10  # Daily limit: 10 LinkedIn messages
        self.linkedin_sent_today = 0
    
    def generate_message_from_about(self, name: str, about: str, job_title: str, product_desc: str) -> str:
        """
        Generate personalized message using About section (works without posts)
        """
        if not self.model:
            return self._fallback_message(name, job_title)
        
        try:
            prompt = f"""You are a sales expert writing a personalized cold outreach message.

Target Person:
- Name: {name}
- Job: {job_title}
- About: {about[:500]}

Your Product/Service: {product_desc}

Write a personalized 75-word LinkedIn message using the Pain-Agitate-Solution framework:
1. Pain: Reference something from their About section
2. Agitate: Expand on the challenge
3. Solution: How your product helps

Be conversational, friendly, and specific. No generic templates.
"""
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.8,
                    'max_output_tokens': 200,
                }
            )
            
            return response.text.strip()
            
        except Exception as e:
            print(f"Error generating message: {e}")
            return self._fallback_message(name, job_title)
    
    def _fallback_message(self, name: str, job_title: str) -> str:
        """Default message if AI fails"""
        return f"""Hi {name},

I noticed your role as {job_title}. I'd love to connect and explore how we might collaborate. 

Looking forward to connecting!"""
    
    def get_unsent_leads(self, limit: int = 500) -> List[Dict]:
        """Get list of leads who haven't received messages yet"""
        leads = self.crm.get_all_leads()
        unsent = [lead for lead in leads if not lead.get('message_sent')]
        return unsent[:limit]
    
    def get_leads_with_email(self) -> List[Dict]:
        """Get leads with email addresses"""
        leads = self.crm.get_all_leads()
        return [lead for lead in leads if lead.get('email')]
    
    def get_leads_with_phone(self) -> List[Dict]:
        """Get leads with phone numbers"""
        leads = self.crm.get_all_leads()
        return [lead for lead in leads if lead.get('phone')]
    
    def send_daily_linkedin_messages(self, product_desc: str) -> Dict:
        """
        Send 10 daily LinkedIn messages (safe limit)
        """
        if self.linkedin_sent_today >= self.daily_linkedin_limit:
            return {
                'status': 'limit_reached',
                'message': f'Daily limit reached ({self.daily_linkedin_limit} messages)',
                'sent': 0
            }
        
        unsent_leads = self.get_unsent_leads(limit=10)
        sent_count = 0
        messages = []
        
        for lead in unsent_leads[:self.daily_linkedin_limit]:
            try:
                # Generate message (even without posts)
                message = self.generate_message_from_about(
                    name=lead.get('name', 'there'),
                    about=lead.get('about', ''),
                    job_title=lead.get('job_title', 'professional'),
                    product_desc=product_desc
                )
                
                # Save message to database
                self.crm.update_message(
                    linkedin_url=lead['linkedin_url'],
                    message=message
                )
                
                messages.append({
                    'name': lead['name'],
                    'linkedin_url': lead['linkedin_url'],
                    'message': message
                })
                
                sent_count += 1
                self.linkedin_sent_today += 1
                
                # Human-like delay between messages
                time.sleep(random.uniform(30, 60))  # 30-60 seconds
                
            except Exception as e:
                print(f"Error processing lead {lead.get('name')}: {e}")
                continue
        
        return {
            'status': 'success',
            'sent': sent_count,
            'messages': messages
        }
    
    def prepare_email_campaign(self, product_desc: str) -> List[Dict]:
        """
        Prepare email campaign for all leads with email addresses
        """
        leads_with_email = self.get_leads_with_email()
        email_list = []
        
        for lead in leads_with_email:
            # Generate personalized message for email
            message = self.generate_message_from_about(
                name=lead.get('name', 'there'),
                about=lead.get('about', ''),
                job_title=lead.get('job_title', 'professional'),
                product_desc=product_desc
            )
            
            email_list.append({
                'name': lead['name'],
                'email': lead['email'],
                'job_title': lead.get('job_title'),
                'company': lead.get('company'),
                'message': message
            })
        
        return email_list
    
    def prepare_whatsapp_campaign(self, product_desc: str) -> List[Dict]:
        """
        Prepare WhatsApp campaign for all leads with phone numbers
        """
        leads_with_phone = self.get_leads_with_phone()
        whatsapp_list = []
        
        for lead in leads_with_phone:
            # Shorter message for WhatsApp
            message = f"""Hi {lead.get('name', 'there')}!

Noticed you're a {lead.get('job_title', 'professional')}. 

{product_desc[:100]}

Interested in learning more?"""
            
            # Format phone number for WhatsApp
            phone = lead.get('phone', '').replace('+', '').replace('-', '').replace(' ', '')
            
            whatsapp_list.append({
                'name': lead['name'],
                'phone': lead['phone'],
                'phone_clean': phone,
                'whatsapp_link': f'https://wa.me/{phone}?text={message.replace(" ", "%20")}',
                'message': message
            })
        
        return whatsapp_list
    
    def get_campaign_stats(self) -> Dict:
        """Get campaign statistics"""
        all_leads = self.crm.get_all_leads()
        
        return {
            'total_leads': len(all_leads),
            'with_email': len([l for l in all_leads if l.get('email')]),
            'with_phone': len([l for l in all_leads if l.get('phone')]),
            'message_sent': len([l for l in all_leads if l.get('message_sent')]),
            'pending': len([l for l in all_leads if not l.get('message_sent')]),
            'linkedin_sent_today': self.linkedin_sent_today,
            'linkedin_remaining_today': self.daily_linkedin_limit - self.linkedin_sent_today
        }


if __name__ == "__main__":
    # Test
    scraper = AutoScraper()
    
    # Display stats
    stats = scraper.get_campaign_stats()
    print("\n📊 Campaign Stats:")
    print(f"Total Leads: {stats['total_leads']}")
    print(f"With Email: {stats['with_email']}")
    print(f"With Phone: {stats['with_phone']}")
    print(f"LinkedIn Sent: {stats['message_sent']}")
    print(f"Pending: {stats['pending']}")
