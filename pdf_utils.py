import io
from reportlab.platypus import Image, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

def create_image_cell(image_data, max_width=1.0*inch, max_height=1.0*inch):
    """Create a table cell with embedded image from binary data"""
    if image_data:
        try:
            # Debug: Check if we have valid image data
            if len(image_data) < 50:
                # Too small to be a valid image
                styles = getSampleStyleSheet()
                placeholder = Paragraph("Invalid", styles['Normal'])
                return [[placeholder]]
            
            # Create image from binary data
            img = Image(io.BytesIO(image_data))
            
            # Maintain aspect ratio while fitting within constraints
            img.drawWidth = max_width
            img.drawHeight = max_height
            
            # Return image as a list for table cell
            return [[img]]
        except Exception as e:
            # If image fails to load, return placeholder with error info
            styles = getSampleStyleSheet()
            placeholder = Paragraph("Load Error", styles['Normal'])
            return [[placeholder]]
    else:
        # Return placeholder for missing images
        styles = getSampleStyleSheet()
        placeholder = Paragraph("No Image", styles['Normal'])
        return [[placeholder]]

def create_clickable_image_section(image_data, title, bed_id, image_type):
    """Create a section with image and clickable link info"""
    styles = getSampleStyleSheet()
    
    # Create title
    title_style = styles['Heading3']
    title_style.alignment = TA_CENTER
    title_style.fontSize = 8
    
    elements = []
    elements.append(Paragraph(title, title_style))
    
    if image_data:
        try:
            # Add image
            img = Image(io.BytesIO(image_data))
            img.drawWidth = 1.2*inch
            img.drawHeight = 1.2*inch
            elements.append(img)
            
            # Add clickable info
            info_style = styles['Normal']
            info_style.fontSize = 6
            info_style.alignment = TA_CENTER
            info_text = f"View Full Size: /{image_type}/{bed_id}"
            elements.append(Paragraph(info_text, info_style))
            
        except Exception as e:
            error_style = styles['Normal']
            error_style.fontSize = 6
            error_style.textColor = colors.red
            elements.append(Paragraph("Image Error", error_style))
    else:
        no_image_style = styles['Normal']
        no_image_style.fontSize = 6
        no_image_style.textColor = colors.grey
        elements.append(Paragraph("No Image Available", no_image_style))
    
    return elements
