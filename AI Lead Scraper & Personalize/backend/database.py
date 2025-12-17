# CRM Database Module for Artin Lead Scraper
# Stores leads in SQLite and exports to Excel

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import json

# Database file path
DB_PATH = Path(__file__).parent / "leads_database.db"

class LeadsCRM:
    """
    CRM Database Manager for storing and exporting LinkedIn leads
    """
    
    def __init__(self):
        self.db_path = DB_PATH
        self._initialize_database()
    
    def _initialize_database(self):
        """Create database and tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                job_title TEXT,
                company TEXT,
                linkedin_url TEXT UNIQUE,
                about TEXT,
                location TEXT,
                experience_json TEXT,
                recent_posts_json TEXT,
                generated_message TEXT,
                message_sent BOOLEAN DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on linkedin_url for fast duplicate detection
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_linkedin_url 
            ON leads(linkedin_url)
        """)
        
        # Create index on created_at for sorting
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at 
            ON leads(created_at DESC)
        """)
        
        conn.commit()
        conn.close()
    
    def add_lead(self, lead_data: Dict) -> Dict:
        """
        Add a new lead to database
        Returns: {'success': bool, 'message': str, 'lead_id': int}
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if lead already exists
            linkedin_url = lead_data.get('profileUrl', '')
            if linkedin_url:
                cursor.execute(
                    "SELECT id, name FROM leads WHERE linkedin_url = ?",
                    (linkedin_url,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    return {
                        'success': False,
                        'message': f'Lead already exists: {existing[1]}',
                        'lead_id': existing[0],
                        'duplicate': True
                    }
            
            # Extract contact info from about section
            email = self._extract_email(lead_data.get('about', ''))
            phone = self._extract_phone(lead_data.get('about', ''))
            
            # Get job title and company from first experience
            job_title = ''
            company = ''
            experiences = lead_data.get('experience', [])
            if experiences and len(experiences) > 0:
                job_title = experiences[0].get('title', '')
                company = experiences[0].get('company', '')
            
            # Insert new lead
            cursor.execute("""
                INSERT INTO leads (
                    name, email, phone, job_title, company, linkedin_url,
                    about, experience_json, recent_posts_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lead_data.get('name', 'Unknown'),
                email,
                phone,
                job_title,
                company,
                linkedin_url,
                lead_data.get('about', ''),
                json.dumps(lead_data.get('experience', [])),
                json.dumps(lead_data.get('recentPosts', []))
            ))
            
            lead_id = cursor.lastrowid
            conn.commit()
            
            return {
                'success': True,
                'message': 'Lead added successfully',
                'lead_id': lead_id,
                'duplicate': False
            }
            
        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'message': f'Error adding lead: {str(e)}',
                'lead_id': None
            }
        finally:
            conn.close()
    
    def update_generated_message(self, linkedin_url: str, message: str) -> bool:
        """Update the generated message for a lead"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE leads 
                SET generated_message = ?, updated_at = CURRENT_TIMESTAMP
                WHERE linkedin_url = ?
            """, (message, linkedin_url))
            
            conn.commit()
            return cursor.rowcount > 0
        except:
            return False
        finally:
            conn.close()
    
    def mark_message_sent(self, linkedin_url: str) -> bool:
        """Mark a lead as message sent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE leads 
                SET message_sent = 1, updated_at = CURRENT_TIMESTAMP
                WHERE linkedin_url = ?
            """, (linkedin_url,))
            
            conn.commit()
            return cursor.rowcount > 0
        except:
            return False
        finally:
            conn.close()
    
    def get_all_leads(self, limit: int = 1000) -> List[Dict]:
        """Get all leads from database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM leads 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        leads = []
        for row in rows:
            lead = dict(row)
            # Parse JSON fields
            if lead['experience_json']:
                lead['experience'] = json.loads(lead['experience_json'])
            if lead['recent_posts_json']:
                lead['recent_posts'] = json.loads(lead['recent_posts_json'])
            leads.append(lead)
        
        return leads
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM leads")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM leads WHERE message_sent = 1")
        sent = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM leads WHERE email IS NOT NULL AND email != ''")
        with_email = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM leads WHERE phone IS NOT NULL AND phone != ''")
        with_phone = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_leads': total,
            'messages_sent': sent,
            'with_email': with_email,
            'with_phone': with_phone
        }
    
    def export_to_excel(self, output_path: Optional[str] = None) -> str:
        """
        Export all leads to Excel file
        Returns: path to exported file
        """
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"leads_export_{timestamp}.xlsx"
        
        # Get all leads
        leads = self.get_all_leads()
        
        # Prepare data for Excel
        excel_data = []
        for lead in leads:
            excel_data.append({
                'Name': lead['name'],
                'Email': lead['email'] or '',
                'Phone': lead['phone'] or '',
                'Job Title': lead['job_title'] or '',
                'Company': lead['company'] or '',
                'LinkedIn URL': lead['linkedin_url'] or '',
                'About': (lead['about'] or '')[:500],  # Limit to 500 chars
                'Generated Message': (lead['generated_message'] or '')[:1000],
                'Message Sent': 'Yes' if lead['message_sent'] else 'No',
                'Notes': lead['notes'] or '',
                'Added Date': lead['created_at'],
                'Last Updated': lead['updated_at']
            })
        
        # Create DataFrame
        df = pd.DataFrame(excel_data)
        
        # Write to Excel with formatting
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Leads', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Leads']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                )
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
        
        return output_path
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email from text using simple pattern matching"""
        import re
        if not text:
            return None
        
        # Simple email regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        
        return matches[0] if matches else None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text"""
        import re
        if not text:
            return None
        
        # Phone number patterns (various formats)
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        
        return None


# Singleton instance
crm = LeadsCRM()
