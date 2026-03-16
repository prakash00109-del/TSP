from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime

def create_professional_title_style():
    """Create professional title styles"""
    styles = getSampleStyleSheet()
    
    # Main title style
    title_style = ParagraphStyle(
        'ProfessionalTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        spaceBefore=20,
        alignment=TA_CENTER,
        textColor=colors.darkblue,
        borderWidth=0,
        borderColor=colors.white,
        fontName='Helvetica-Bold'
    )
    
    # Subtitle style
    subtitle_style = ParagraphStyle(
        'ProfessionalSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=25,
        spaceBefore=5,
        alignment=TA_CENTER,
        textColor=colors.darkgrey,
        fontName='Helvetica',
        leading=16
    )
    
    # Section header style
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=15,
        spaceBefore=20,
        alignment=TA_LEFT,
        textColor=colors.darkblue,
        borderWidth=0,
        fontName='Helvetica-Bold'
    )
    
    return title_style, subtitle_style, section_style

def create_professional_table_style():
    """Create professional table styling with text wrapping"""
    return TableStyle([
        # Header styling - professional gradient effect
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        
        # Data row styling - clean and professional
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # S.No center
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),   # Tenant Name left
        ('ALIGN', (2, 1), (3, -1), 'CENTER'), # Photo, Aadhar center
        ('ALIGN', (4, 1), (6, -1), 'CENTER'), # Floor, Room, Bed center
        ('ALIGN', (7, 1), (7, -1), 'CENTER'), # Phone center
        ('ALIGN', (8, 1), (8, -1), 'LEFT'),   # Email left
        ('ALIGN', (9, 1), (-1, -1), 'CENTER'), # Date, Rent center
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        
        # Professional grid styling
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2C3E50')),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#2C3E50')),
        
        # Professional alternating row colors - subtle
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        
        # Make VIEW buttons look clickable
        ('TEXTCOLOR', (2, 1), (3, -1), colors.HexColor('#3498DB')),
        ('FONTNAME', (2, 1), (3, -1), 'Helvetica-Bold'),
        
        # Better padding for readability
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        
        # Enable text wrapping for long content
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])

def create_summary_box(total_tenants):
    """Create professional summary statistics box"""
    styles = getSampleStyleSheet()
    
    # Summary data
    summary_data = [
        ['Total Tenants', str(total_tenants)],
        ['Report Generated', datetime.now().strftime('%d-%m-%Y %H:%M:%S')],
        ['Report Type', 'Comprehensive Tenant Listing']
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#3498DB')),
        ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#2ECC71')),
        ('BACKGROUND', (0, 2), (0, 2), colors.HexColor('#9B59B6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    return summary_table

def create_professional_footer():
    """Create professional footer"""
    styles = getSampleStyleSheet()
    
    footer_style = ParagraphStyle(
        'ProfessionalFooter',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#7F8C8D'),
        borderWidth=0,
        spaceBefore=20,
        fontName='Helvetica'
    )
    
    footer_text = "This is a computer-generated document. For any queries, please contact the PG Management."
    return Paragraph(footer_text, footer_style)

def create_instructions_note():
    """Create instructions for clickable links with URLs"""
    styles = getSampleStyleSheet()
    
    instruction_style = ParagraphStyle(
        'Instructions',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=15,
        spaceBefore=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#27AE60'),
        borderWidth=0,
        fontName='Helvetica-Oblique'
    )
    
    instruction_text = "📸 Click 'VIEW' buttons to see tenant photos and documents.<br/>💡 URLs are shown below each button for manual access if clicking doesn't work."
    return Paragraph(instruction_text, instruction_style)
