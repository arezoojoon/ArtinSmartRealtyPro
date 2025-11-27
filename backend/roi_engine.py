"""
ArtinSmartRealty V2 - ROI Engine
Generates professional PDF reports with Agent branding
"""

import os
import io
from datetime import datetime
from typing import Optional, Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart

from database import Tenant, Lead, Language


# ==================== CONSTANTS ====================

# Color scheme matching the dashboard
NAVY_BLUE = colors.HexColor('#0f1729')
GOLD = colors.HexColor('#D4AF37')
WHITE = colors.Color(1, 1, 1)
LIGHT_GRAY = colors.HexColor('#f5f5f5')
DARK_GRAY = colors.HexColor('#333333')


# ROI assumptions for Dubai Real Estate
DEFAULT_ASSUMPTIONS = {
    "rental_yield": 0.07,  # 7% average rental yield
    "appreciation": 0.05,  # 5% annual appreciation
    "maintenance_rate": 0.02,  # 2% maintenance costs
    "service_charge_rate": 0.015,  # 1.5% service charges
    "dld_fee": 0.04,  # 4% Dubai Land Department fee
    "agency_fee": 0.02,  # 2% agency commission
    "mortgage_rate": 0.045,  # 4.5% mortgage rate
    "mortgage_ltv": 0.75,  # 75% Loan-to-Value
    # FOMO/Price Shock parameters
    "price_growth_6m": 0.05,  # 5% expected growth in 6 months
    "limited_units_threshold": 20,  # "Limited units" messaging threshold
}

# Translations for the PDF
PDF_TRANSLATIONS = {
    "title": {
        Language.EN: "Dubai Real Estate\nROI Analysis Report",
        Language.FA: "گزارش تحلیل بازگشت سرمایه\nاملاک دبی",
        Language.AR: "تقرير تحليل العائد على الاستثمار\nعقارات دبي",
        Language.RU: "Анализ ROI\nНедвижимость Дубая"
    },
    "prepared_for": {
        Language.EN: "Prepared for",
        Language.FA: "تهیه شده برای",
        Language.AR: "أُعدّ لـ",
        Language.RU: "Подготовлено для"
    },
    "prepared_by": {
        Language.EN: "Prepared by",
        Language.FA: "تهیه شده توسط",
        Language.AR: "أعده",
        Language.RU: "Подготовил"
    },
    "investment_summary": {
        Language.EN: "Investment Summary",
        Language.FA: "خلاصه سرمایه‌گذاری",
        Language.AR: "ملخص الاستثمار",
        Language.RU: "Обзор инвестиций"
    },
    "property_value": {
        Language.EN: "Property Value",
        Language.FA: "ارزش ملک",
        Language.AR: "قيمة العقار",
        Language.RU: "Стоимость недвижимости"
    },
    "down_payment": {
        Language.EN: "Down Payment (25%)",
        Language.FA: "پیش پرداخت (25%)",
        Language.AR: "الدفعة الأولى (25%)",
        Language.RU: "Первоначальный взнос (25%)"
    },
    "total_investment": {
        Language.EN: "Total Initial Investment",
        Language.FA: "کل سرمایه‌گذاری اولیه",
        Language.AR: "إجمالي الاستثمار الأولي",
        Language.RU: "Общая сумма инвестиций"
    },
    "annual_income": {
        Language.EN: "Annual Rental Income",
        Language.FA: "درآمد سالانه اجاره",
        Language.AR: "الدخل السنوي من الإيجار",
        Language.RU: "Годовой доход от аренды"
    },
    "roi_projection": {
        Language.EN: "5-Year ROI Projection",
        Language.FA: "پیش‌بینی ROI 5 ساله",
        Language.AR: "توقعات العائد على الاستثمار لـ 5 سنوات",
        Language.RU: "Прогноз ROI на 5 лет"
    },
    "year": {
        Language.EN: "Year",
        Language.FA: "سال",
        Language.AR: "السنة",
        Language.RU: "Год"
    },
    "rental_income": {
        Language.EN: "Rental Income",
        Language.FA: "درآمد اجاره",
        Language.AR: "دخل الإيجار",
        Language.RU: "Доход от аренды"
    },
    "property_appreciation": {
        Language.EN: "Property Appreciation",
        Language.FA: "افزایش ارزش ملک",
        Language.AR: "ارتفاع قيمة العقار",
        Language.RU: "Рост стоимости"
    },
    "cumulative_roi": {
        Language.EN: "Cumulative ROI",
        Language.FA: "ROI تجمعی",
        Language.AR: "العائد التراكمي",
        Language.RU: "Совокупный ROI"
    },
    "golden_visa": {
        Language.EN: "🛂 Golden Visa Eligibility",
        Language.FA: "🛂 واجد شرایط ویزای طلایی",
        Language.AR: "🛂 الأهلية للتأشيرة الذهبية",
        Language.RU: "🛂 Право на Золотую Визу"
    },
    "golden_visa_text": {
        Language.EN: "Investments of AED 2,000,000 or more qualify for UAE Golden Visa residency (10 years)!",
        Language.FA: "سرمایه‌گذاری 2,000,000 درهم یا بیشتر واجد شرایط ویزای طلایی امارات (10 سال) است!",
        Language.AR: "الاستثمارات بقيمة 2,000,000 درهم أو أكثر مؤهلة للحصول على تأشيرة الإقامة الذهبية (10 سنوات)!",
        Language.RU: "Инвестиции от 2 000 000 AED дают право на Золотую Визу ОАЭ (10 лет)!"
    },
    "disclaimer": {
        Language.EN: "Disclaimer: This analysis is for informational purposes only. Actual returns may vary based on market conditions.",
        Language.FA: "توجه: این تحلیل صرفاً جنبه اطلاعاتی دارد. بازده واقعی ممکن است بر اساس شرایط بازار متفاوت باشد.",
        Language.AR: "إخلاء المسؤولية: هذا التحليل لأغراض إعلامية فقط. قد تختلف العوائد الفعلية بناءً على ظروف السوق.",
        Language.RU: "Отказ от ответственности: Этот анализ носит исключительно информационный характер. Фактическая доходность может варьироваться."
    },
    # FOMO/Price Shock section
    "price_alert": {
        Language.EN: "⚠️ PRICE ALERT",
        Language.FA: "⚠️ هشدار قیمت",
        Language.AR: "⚠️ تنبيه السعر",
        Language.RU: "⚠️ ПРЕДУПРЕЖДЕНИЕ О ЦЕНЕ"
    },
    "price_growth_text": {
        Language.EN: "Based on current market trends, this property type is expected to appreciate ~5% in the next 6 months.\n\nBuying NOW could save you: AED {savings:,.0f}",
        Language.FA: "بر اساس روند فعلی بازار، انتظار می‌رود این نوع ملک ~۵٪ در ۶ ماه آینده رشد کند.\n\nخرید الان می‌تواند {savings:,.0f} درهم صرفه‌جویی کند!",
        Language.AR: "بناءً على اتجاهات السوق الحالية، من المتوقع أن يرتفع هذا النوع من العقارات ~5% في الأشهر الستة القادمة.\n\nالشراء الآن قد يوفر لك: {savings:,.0f} درهم",
        Language.RU: "Исходя из текущих рыночных тенденций, этот тип недвижимости ожидаемо вырастет ~5% за 6 месяцев.\n\nПокупка СЕЙЧАС сэкономит вам: {savings:,.0f} AED"
    },
    "act_now": {
        Language.EN: "⏰ Don't wait - secure your investment today!",
        Language.FA: "⏰ صبر نکنید - سرمایه‌گذاری خود را امروز تضمین کنید!",
        Language.AR: "⏰ لا تنتظر - أمّن استثمارك اليوم!",
        Language.RU: "⏰ Не ждите - обеспечьте свои инвестиции сегодня!"
    }
}


class ROIEngine:
    """
    ROI PDF Generator with Agent Branding
    """
    
    def __init__(self, tenant: Tenant, lead: Lead):
        self.tenant = tenant
        self.lead = lead
        # ALWAYS use English for PDF (better font support and readability)
        self.lang = Language.EN
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=28,
            textColor=NAVY_BLUE,
            alignment=TA_CENTER,
            spaceAfter=30,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=GOLD,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=NAVY_BLUE,
            spaceBefore=20,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=DARK_GRAY,
            alignment=TA_LEFT,
            spaceAfter=10
        ))
        
        # Golden visa highlight
        self.styles.add(ParagraphStyle(
            name='GoldenVisa',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=GOLD,
            alignment=TA_CENTER,
            spaceBefore=20,
            spaceAfter=10,
            fontName='Helvetica-Bold',
            borderColor=GOLD,
            borderWidth=1,
            borderPadding=10
        ))
    
    def _get_text(self, key: str) -> str:
        """Get translated text."""
        return PDF_TRANSLATIONS.get(key, {}).get(self.lang, PDF_TRANSLATIONS.get(key, {}).get(Language.EN, key))
    
    def _calculate_roi(self, property_value: float) -> Dict[str, Any]:
        """Calculate ROI projections."""
        results = {
            "property_value": property_value,
            "down_payment": property_value * (1 - DEFAULT_ASSUMPTIONS["mortgage_ltv"]),
            "dld_fee": property_value * DEFAULT_ASSUMPTIONS["dld_fee"],
            "agency_fee": property_value * DEFAULT_ASSUMPTIONS["agency_fee"],
            "yearly_projections": []
        }
        
        results["total_investment"] = (
            results["down_payment"] + 
            results["dld_fee"] + 
            results["agency_fee"]
        )
        
        current_value = property_value
        cumulative_rental = 0
        
        for year in range(1, 6):
            # Calculate yearly figures
            rental_income = current_value * DEFAULT_ASSUMPTIONS["rental_yield"]
            maintenance = current_value * DEFAULT_ASSUMPTIONS["maintenance_rate"]
            service_charges = current_value * DEFAULT_ASSUMPTIONS["service_charge_rate"]
            
            net_rental = rental_income - maintenance - service_charges
            cumulative_rental += net_rental
            
            # Property appreciation
            appreciation = current_value * DEFAULT_ASSUMPTIONS["appreciation"]
            current_value += appreciation
            
            # Total gains
            total_gain = cumulative_rental + (current_value - property_value)
            roi_percentage = (total_gain / results["total_investment"]) * 100
            
            results["yearly_projections"].append({
                "year": year,
                "rental_income": net_rental,
                "property_value": current_value,
                "appreciation": appreciation,
                "cumulative_roi": roi_percentage
            })
        
        return results
    
    def _create_header(self, canvas, doc):
        """Create page header with logo."""
        canvas.saveState()
        
        # Draw header background
        canvas.setFillColor(NAVY_BLUE)
        canvas.rect(0, A4[1] - 1.5*inch, A4[0], 1.5*inch, fill=1)
        
        # Draw gold accent line
        canvas.setStrokeColor(GOLD)
        canvas.setLineWidth(3)
        canvas.line(0, A4[1] - 1.5*inch, A4[0], A4[1] - 1.5*inch)
        
        # Add agent name
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 24)
        canvas.drawString(0.75*inch, A4[1] - 0.8*inch, self.tenant.name or "ArtinSmartRealty")
        
        # Add company name
        if self.tenant.company_name:
            canvas.setFont("Helvetica", 12)
            canvas.drawString(0.75*inch, A4[1] - 1.1*inch, self.tenant.company_name)
        
        # Try to add logo if URL exists
        if self.tenant.logo_url:
            try:
                logo = Image(self.tenant.logo_url, width=0.8*inch, height=0.8*inch)
                logo.drawOn(canvas, A4[0] - 1.5*inch, A4[1] - 1.2*inch)
            except Exception:
                pass  # Skip logo if can't load
        
        canvas.restoreState()
    
    def _create_footer(self, canvas, doc):
        """Create page footer."""
        canvas.saveState()
        
        # Draw footer line
        canvas.setStrokeColor(GOLD)
        canvas.setLineWidth(1)
        canvas.line(0.75*inch, 0.5*inch, A4[0] - 0.75*inch, 0.5*inch)
        
        # Add contact info
        canvas.setFillColor(DARK_GRAY)
        canvas.setFont("Helvetica", 9)
        
        contact_text = f"{self.tenant.name}"
        if self.tenant.phone:
            contact_text += f" | {self.tenant.phone}"
        
        canvas.drawString(0.75*inch, 0.3*inch, contact_text)
        
        # Add page number
        canvas.drawRightString(A4[0] - 0.75*inch, 0.3*inch, f"Page {doc.page}")
        
        canvas.restoreState()
    
    def _add_page_decorations(self, canvas, doc):
        """Add header and footer to page."""
        self._create_header(canvas, doc)
        self._create_footer(canvas, doc)
    
    def generate_pdf(self, property_value: Optional[float] = None) -> bytes:
        """
        Generate the ROI PDF report.
        Returns PDF as bytes.
        """
        # Use budget from lead if no value provided
        if property_value is None:
            if self.lead.budget_max:
                property_value = self.lead.budget_max
            elif self.lead.budget_min:
                property_value = self.lead.budget_min * 1.5
            else:
                property_value = 2000000  # Default 2M AED
        
        # Calculate ROI
        roi_data = self._calculate_roi(property_value)
        
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=2*inch,  # Leave space for header
            bottomMargin=1*inch,
            leftMargin=0.75*inch,
            rightMargin=0.75*inch
        )
        
        # Build content
        story = []
        
        # Title
        story.append(Paragraph(
            self._get_text("title"),
            self.styles['CustomTitle']
        ))
        
        # Date
        story.append(Paragraph(
            datetime.now().strftime("%B %d, %Y"),
            self.styles['CustomSubtitle']
        ))
        
        story.append(Spacer(1, 20))
        
        # Prepared for section
        if self.lead.name:
            story.append(Paragraph(
                f"{self._get_text('prepared_for')}: <b>{self.lead.name}</b>",
                self.styles['CustomBody']
            ))
        
        story.append(Paragraph(
            f"{self._get_text('prepared_by')}: <b>{self.tenant.name}</b>",
            self.styles['CustomBody']
        ))
        
        story.append(Spacer(1, 30))
        
        # Investment Summary Section
        story.append(Paragraph(
            self._get_text("investment_summary"),
            self.styles['SectionHeader']
        ))
        
        story.append(HRFlowable(width="100%", thickness=2, color=GOLD))
        story.append(Spacer(1, 10))
        
        # Investment summary table
        summary_data = [
            [self._get_text("property_value"), f"AED {property_value:,.0f}"],
            [self._get_text("down_payment"), f"AED {roi_data['down_payment']:,.0f}"],
            ["DLD Fee (4%)", f"AED {roi_data['dld_fee']:,.0f}"],
            ["Agency Fee (2%)", f"AED {roi_data['agency_fee']:,.0f}"],
            [self._get_text("total_investment"), f"AED {roi_data['total_investment']:,.0f}"],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -2), LIGHT_GRAY),
            ('BACKGROUND', (0, -1), (-1, -1), NAVY_BLUE),
            ('TEXTCOLOR', (0, -1), (-1, -1), WHITE),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, DARK_GRAY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(summary_table)
        
        story.append(Spacer(1, 30))
        
        # ROI Projection Section
        story.append(Paragraph(
            self._get_text("roi_projection"),
            self.styles['SectionHeader']
        ))
        
        story.append(HRFlowable(width="100%", thickness=2, color=GOLD))
        story.append(Spacer(1, 10))
        
        # ROI projection table
        projection_headers = [
            self._get_text("year"),
            self._get_text("rental_income"),
            self._get_text("property_appreciation"),
            self._get_text("cumulative_roi")
        ]
        
        projection_data = [projection_headers]
        for proj in roi_data["yearly_projections"]:
            projection_data.append([
                str(proj["year"]),
                f"AED {proj['rental_income']:,.0f}",
                f"AED {proj['appreciation']:,.0f}",
                f"{proj['cumulative_roi']:.1f}%"
            ])
        
        projection_table = Table(projection_data, colWidths=[0.8*inch, 1.8*inch, 1.8*inch, 1.5*inch])
        projection_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('BACKGROUND', (0, 1), (-1, -1), LIGHT_GRAY),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, DARK_GRAY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(projection_table)
        
        # Golden Visa notice (if applicable)
        if property_value >= 2000000:
            story.append(Spacer(1, 30))
            
            # Create golden visa box
            gv_data = [[self._get_text("golden_visa")], [self._get_text("golden_visa_text")]]
            gv_table = Table(gv_data, colWidths=[5.5*inch])
            gv_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef9e7')),
                ('TEXTCOLOR', (0, 0), (-1, 0), NAVY_BLUE),
                ('TEXTCOLOR', (0, 1), (-1, 1), DARK_GRAY),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('FONTSIZE', (0, 1), (-1, 1), 11),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 2, GOLD),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            story.append(gv_table)
        
        # PRICE SHOCK / FOMO Section - Show expected price growth
        story.append(Spacer(1, 20))
        
        # Calculate potential savings if buying now
        price_growth = DEFAULT_ASSUMPTIONS["price_growth_6m"]
        potential_savings = property_value * price_growth
        
        price_alert_text = self._get_text("price_growth_text").format(savings=potential_savings)
        
        price_data = [
            [self._get_text("price_alert")],
            [price_alert_text],
            [self._get_text("act_now")]
        ]
        price_table = Table(price_data, colWidths=[5.5*inch])
        price_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff3e0')),  # Orange tint for urgency
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#e65100')),  # Orange for alert
            ('TEXTCOLOR', (0, 1), (-1, 1), DARK_GRAY),
            ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#e65100')),  # Orange for CTA
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('FONTSIZE', (0, 1), (-1, 1), 10),
            ('FONTSIZE', (0, 2), (-1, 2), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#e65100')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(price_table)
        
        # Disclaimer
        story.append(Spacer(1, 40))
        story.append(Paragraph(
            self._get_text("disclaimer"),
            ParagraphStyle(
                'Disclaimer',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=colors.gray,
                alignment=TA_CENTER
            )
        ))
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_page_decorations, onLaterPages=self._add_page_decorations)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    async def generate_and_save(self, property_value: Optional[float] = None) -> str:
        """
        Generate PDF and save to file.
        Returns the file path.
        """
        pdf_bytes = self.generate_pdf(property_value)
        
        # Create output directory
        output_dir = os.getenv("PDF_OUTPUT_DIR", "/tmp/roi_reports")
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"roi_report_{self.lead.id}_{timestamp}.pdf"
        filepath = os.path.join(output_dir, filename)
        
        # Write file
        with open(filepath, "wb") as f:
            f.write(pdf_bytes)
        
        return filepath


# ==================== CONVENIENCE FUNCTION ====================

async def generate_roi_pdf(tenant: Tenant, lead: Lead, property_value: Optional[float] = None) -> bytes:
    """
    Convenience function to generate ROI PDF.
    """
    engine = ROIEngine(tenant, lead)
    return engine.generate_pdf(property_value)
