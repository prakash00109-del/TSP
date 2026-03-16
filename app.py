import logging
import io
import tempfile
import csv
import os
from flask import Flask, request, jsonify, render_template, send_file, Response
from database import *
from pdf_utils import create_image_cell
from database import cleanup_expired_tokens, get_token_stats

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from datetime import datetime
import io


# --------------------------------------------------
# FILE VALIDATION UTILITIES
# --------------------------------------------------

ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/jpg', 'image/png', 'image/gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def validate_uploaded_file(file, allowed_types=None, max_size=None):
    """Validate uploaded file for type and size"""
    if not file or file.filename == '':
        return None, "No file selected"
    
    if allowed_types is None:
        allowed_types = ALLOWED_IMAGE_TYPES
    if max_size is None:
        max_size = MAX_FILE_SIZE
    
    # Check file extension
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
        return None, "Invalid file type. Only JPG, PNG, and GIF images are allowed"
    
    # Check MIME type
    if file.content_type not in allowed_types:
        return None, f"Invalid file type: {file.content_type}"
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    if file_size > max_size:
        return None, f"File too large. Maximum size is {max_size // (1024*1024)}MB"
    
    return file, None

def safe_read_file(file):
    """Safely read file data with size limit"""
    try:
        file.seek(0)
        data = file.read(MAX_FILE_SIZE)
        return data
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return None


# --------------------------------------------------
# LOGGING CONFIG
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger("PG_SYSTEM")


# --------------------------------------------------
# APP INIT
# --------------------------------------------------

app = Flask(__name__)

init_db()

# Clean up expired form tokens on startup
try:
    cleanup_expired_tokens()
    logger.info("Automatic token cleanup completed on startup")
except Exception as e:
    logger.error(f"Automatic token cleanup failed: {e}")


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.route("/")
def home():

    logger.info("Dashboard opened")

    return render_template("index.html")


# --------------------------------------------------
# ADD FLOOR
# --------------------------------------------------

@app.route("/add_floor", methods=["POST"])
def add_floor_api():

    try:

        data = request.get_json()

        floor = data.get("floor")

        if not floor:
            return jsonify({"success": False, "error": "Floor missing"})

        success = add_floor(floor)

        return jsonify({"success": success})

    except Exception as e:

        logger.error(f"add_floor error: {e}")

        return jsonify({"success": False})


# --------------------------------------------------
# DELETE FLOOR
# --------------------------------------------------

@app.route("/delete_floor", methods=["POST"])
def delete_floor_api():

    try:

        data = request.get_json()

        floor = data.get("floor")

        success = delete_floor(floor)

        return jsonify({"success": success})

    except Exception as e:

        logger.error(f"delete_floor error: {e}")

        return jsonify({"success": False})


# --------------------------------------------------
# ADD ROOM
# --------------------------------------------------

@app.route("/add_room", methods=["POST"])
def add_room_api():

    try:

        data = request.get_json()

        floor = data.get("floor")
        room = data.get("room")

        success = create_room(floor, room)

        return jsonify({"success": success})

    except Exception as e:

        logger.error(f"add_room error: {e}")

        return jsonify({"success": False})


# --------------------------------------------------
# DELETE ROOM
# --------------------------------------------------

@app.route("/delete_room", methods=["POST"])
def delete_room_api():

    try:

        data = request.get_json()

        floor = data.get("floor")
        room = data.get("room")

        success = delete_room(floor, room)

        return jsonify({"success": success})

    except Exception as e:

        logger.error(f"delete_room error: {e}")

        return jsonify({"success": False})


# --------------------------------------------------
# ADD BEDS
# --------------------------------------------------

@app.route("/add_beds", methods=["POST"])
def add_beds_api():

    try:

        data = request.get_json()

        floor = data.get("floor")
        room = data.get("room")
        beds = int(data.get("beds"))

        success = add_beds(floor, room, beds)

        return jsonify({"success": success})

    except Exception as e:

        logger.error(f"add_beds error: {e}")

        return jsonify({"success": False})


# --------------------------------------------------
# DELETE BED
# --------------------------------------------------

@app.route("/delete_bed", methods=["POST"])
def delete_bed_api():

    try:

        data = request.get_json()

        floor = data.get("floor")
        room = data.get("room")
        bed = data.get("bed")

        logger.info(f"Delete bed request: floor={floor}, room={room}, bed={bed}")

        success, message = delete_bed(floor, room, bed)

        if success:
            logger.info(f"Bed deleted successfully: {floor}-{room}-{bed}")
            return jsonify({"success": True, "message": message})
        else:
            logger.warning(f"Failed to delete bed: {floor}-{room}-{bed} - {message}")
            return jsonify({"success": False, "error": message})

    except Exception as e:

        logger.error(f"delete_bed API error: {e}")
        return jsonify({"success": False, "error": "Server error"})


# --------------------------------------------------
# GET ALL BEDS
# --------------------------------------------------

@app.route("/beds")
def get_all_beds():

    try:

        rows = get_beds()

        result = []

        for row in rows:

            result.append({

                "id": row["id"],
                "floor": row["floor"],
                "room": row["room"],
                "bed": row["bed"],

                "tenant": row["tenant_name"],
                "phone": row["phone"],
                "join_date": row["checkin_date"]

            })

        return jsonify(result)

    except Exception as e:

        logger.error(f"get_beds error: {e}")

        return jsonify([])


# --------------------------------------------------
# GET TENANT PROFILE
# --------------------------------------------------

@app.route("/tenant/<int:bed_id>")
def tenant_profile(bed_id):

    try:

        tenant = get_tenant(bed_id)

        if not tenant:
            return jsonify({})

        return jsonify({

            "tenant_name": tenant["tenant_name"],
            "phone": tenant["phone"],
            "email": tenant["email"],
            "father_name": tenant["father_name"],
            "mother_name": tenant["mother_name"],
            "address": tenant["address"],
            "street": tenant["street"],
            "area": tenant["area"],
            "pincode": tenant["pincode"],
            "dob": tenant["dob"],
            "aadhar_number": tenant["aadhar_number"],
            "office_name": tenant["office_name"],
            "office_address": tenant["office_address"],
            "deposit": tenant["deposit"],
            "rent": tenant["rent"],
            "room": tenant["room"],
            "bed": tenant["bed"],
            "room_type": tenant["room_type"],
            "checkin_date": tenant["checkin_date"],
            "emergency_name": tenant["emergency_name"],
            "emergency_phone": tenant["emergency_phone"],
            "emergency_relation": tenant["emergency_relation"]

        })

    except Exception as e:

        logger.error(f"tenant profile error: {e}")

        return jsonify({})


# --------------------------------------------------
# ADD TENANT
# --------------------------------------------------

@app.route("/add_tenant", methods=["POST"])
def add_pg_tenant():

    try:

        data = {

            "name": request.form.get("name"),
            "father": request.form.get("father"),
            "mother": request.form.get("mother"),

            "address": request.form.get("address"),
            "street": request.form.get("street"),
            "area": request.form.get("area"),
            "pincode": request.form.get("pincode"),

            "aadhar_number": request.form.get("aadhar_number"),
            "dob": request.form.get("dob"),
            "email": request.form.get("email"),
            "phone": request.form.get("phone"),

            "office_name": request.form.get("office_name"),
            "office_address": request.form.get("office_address"),

            "deposit": request.form.get("deposit"),
            "rent": request.form.get("rent"),

            "room_type": request.form.get("room_type"),
            "checkin": request.form.get("checkin"),

            "emergency_name": request.form.get("emergency_name"),
            "emergency_phone": request.form.get("emergency_phone"),
            "emergency_relation": request.form.get("emergency_relation"),

            "floor": request.form.get("floor"),
            "room": request.form.get("room"),
            "bed": request.form.get("bed")

        }

        photo = request.files.get("photo")
        aadhar = request.files.get("aadhar")

        # Validate photo file
        photo_data = None
        if photo and photo.filename:
            validated_photo, error = validate_uploaded_file(photo)
            if error:
                return jsonify({"success": False, "error": f"Photo validation failed: {error}"})
            photo_data = safe_read_file(validated_photo)

        # Validate aadhar file  
        aadhar_data = None
        if aadhar and aadhar.filename:
            validated_aadhar, error = validate_uploaded_file(aadhar)
            if error:
                return jsonify({"success": False, "error": f"Aadhar validation failed: {error}"})
            aadhar_data = safe_read_file(validated_aadhar)

        logger.info(f"Photo data size: {len(photo_data) if photo_data else 0} bytes")
        logger.info(f"Aadhar data size: {len(aadhar_data) if aadhar_data else 0} bytes")

        success = add_tenant(data, photo_data, aadhar_data)

        return jsonify({"success": success})

    except Exception as e:

        logger.error(f"add_tenant error: {e}")

        return jsonify({"success": False})
    
@app.route("/update_tenant", methods=["POST"])
def update_tenant():

    try:

        data = request.form

        photo = request.files.get("photo")
        aadhar = request.files.get("aadhar")

        # Validate photo file
        photo_data = None
        if photo and photo.filename:
            validated_photo, error = validate_uploaded_file(photo)
            if error:
                return jsonify({"success": False, "error": f"Photo validation failed: {error}"})
            photo_data = safe_read_file(validated_photo)

        # Validate aadhar file  
        aadhar_data = None
        if aadhar and aadhar.filename:
            validated_aadhar, error = validate_uploaded_file(aadhar)
            if error:
                return jsonify({"success": False, "error": f"Aadhar validation failed: {error}"})
            aadhar_data = safe_read_file(validated_aadhar)

        logger.info(f"Update - Photo data size: {len(photo_data) if photo_data else 0} bytes")
        logger.info(f"Update - Aadhar data size: {len(aadhar_data) if aadhar_data else 0} bytes")

        floor = data.get("floor")
        room = data.get("room")
        bed = data.get("bed")

        conn = connect()
        cur = conn.cursor()

        # Build update query dynamically based on whether files are provided
        if photo_data or aadhar_data:
            cur.execute("""

            UPDATE rooms SET

            tenant_name=%s,
            father_name=%s,
            mother_name=%s,
            address=%s,
            street=%s,
            area=%s,
            pincode=%s,
            aadhar_number=%s,
            dob=%s,
            email=%s,
            phone=%s,
            office_name=%s,
            office_address=%s,
            deposit=%s,
            rent=%s,
            room_type=%s,
            checkin_date=%s,
            emergency_name=%s,
            emergency_phone=%s,
            emergency_relation=%s,
            photo=%s,
            aadhar=%s

            WHERE floor=%s AND room=%s AND bed=%s

            """,(
            data.get("name"),
            data.get("father"),
            data.get("mother"),
            data.get("address"),
            data.get("street"),
            data.get("area"),
            data.get("pincode"),
            data.get("aadhar_number"),
            data.get("dob"),
            data.get("email"),
            data.get("phone"),
            data.get("office_name"),
            data.get("office_address"),
            data.get("deposit"),
            data.get("rent"),
            data.get("room_type"),
            data.get("checkin"),
            data.get("emergency_name"),
            data.get("emergency_phone"),
            data.get("emergency_relation"),
            psycopg2.Binary(photo_data) if photo_data else None,
            psycopg2.Binary(aadhar_data) if aadhar_data else None,
            floor,
            room,
            bed

            ))
        else:
            cur.execute("""

            UPDATE rooms SET

            tenant_name=%s,
            father_name=%s,
            mother_name=%s,
            address=%s,
            street=%s,
            area=%s,
            pincode=%s,
            aadhar_number=%s,
            dob=%s,
            email=%s,
            phone=%s,
            office_name=%s,
            office_address=%s,
            deposit=%s,
            rent=%s,
            room_type=%s,
            checkin_date=%s,
            emergency_name=%s,
            emergency_phone=%s,
            emergency_relation=%s

            WHERE floor=%s AND room=%s AND bed=%s

            """,(
            data.get("name"),
            data.get("father"),
            data.get("mother"),
            data.get("address"),
            data.get("street"),
            data.get("area"),
            data.get("pincode"),
            data.get("aadhar_number"),
            data.get("dob"),
            data.get("email"),
            data.get("phone"),
            data.get("office_name"),
            data.get("office_address"),
            data.get("deposit"),
            data.get("rent"),
            data.get("room_type"),
            data.get("checkin"),
            data.get("emergency_name"),
            data.get("emergency_phone"),
            data.get("emergency_relation"),
            floor,
            room,
            bed

            ))

        conn.commit()

        return jsonify({"success":True})

    except Exception as e:

        logger.error(f"update_tenant error: {e}")
        print(e)

        return jsonify({"success":False})


# --------------------------------------------------
# REMOVE TENANT
# --------------------------------------------------

@app.route("/remove_tenant", methods=["POST"])
def remove_pg_tenant():

    try:

        data = request.get_json()

        floor = data.get("floor")
        room = data.get("room")
        bed = data.get("bed")

        success = remove_tenant(floor, room, bed)

        return jsonify({"success": success})

    except Exception as e:

        logger.error(f"remove_tenant error: {e}")

        return jsonify({"success": False})


# --------------------------------------------------
# GET PHOTO
# --------------------------------------------------

@app.route("/photo/<int:bed_id>")
def get_photo(bed_id):

    try:

        tenant = get_tenant(bed_id)

        if tenant and tenant["photo"]:

            return send_file(
                io.BytesIO(tenant["photo"]),
                mimetype="image/jpeg"
            )

        return "", 404

    except Exception as e:

        logger.error(f"photo error: {e}")

        return "", 500


# --------------------------------------------------
# GET AADHAAR
# --------------------------------------------------

@app.route("/aadhar/<int:bed_id>")
def get_aadhar(bed_id):

    try:

        tenant = get_tenant(bed_id)

        if tenant and tenant["aadhar"]:

            return send_file(
                io.BytesIO(tenant["aadhar"]),
                mimetype="image/jpeg"
            )

        return "", 404

    except Exception as e:

        logger.error(f"aadhar error: {e}")

        return "", 500


# --------------------------------------------------
# GET FORMER TENANT PHOTO
# --------------------------------------------------

@app.route("/former/photo/<int:former_id>")
def get_former_photo(former_id):

    try:

        tenant = get_former_tenant(former_id)

        if tenant and tenant["photo"]:

            return send_file(
                io.BytesIO(tenant["photo"]),
                mimetype="image/jpeg"
            )

        return "", 404

    except Exception as e:

        logger.error(f"former photo error: {e}")

        return "", 500


# --------------------------------------------------
# GET FORMER TENANT AADHAR
# --------------------------------------------------

@app.route("/former/aadhar/<int:former_id>")
def get_former_aadhar(former_id):

    try:

        tenant = get_former_tenant(former_id)

        if tenant and tenant["aadhar"]:

            return send_file(
                io.BytesIO(tenant["aadhar"]),
                mimetype="image/jpeg"
            )

        return "", 404

    except Exception as e:

        logger.error(f"former aadhar error: {e}")

        return "", 500


# --------------------------------------------------
# DOWNLOAD TENANT PDF
# --------------------------------------------------

@app.route("/download_tenant/<int:bed_id>")
def download_tenant_pdf(bed_id):
    try:
        tenant = get_tenant(bed_id)
        
        if not tenant:
            return "Tenant not found", 404
            
        buffer = io.BytesIO()
        
        # Create PDF with tenant details
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            leftMargin=0.5*inch, 
            rightMargin=0.5*inch,
            topMargin=1.0*inch, 
            bottomMargin=0.8*inch
        )
        
        styles = getSampleStyleSheet()
        elements = []
        
        # Professional title styles
        from professional_pdf import create_professional_title_style, create_professional_table_style, create_summary_box, create_professional_footer
        
        title_style, subtitle_style, section_style = create_professional_title_style()
        
        # Header
        elements.append(Paragraph("PG MANAGEMENT SYSTEM", title_style))
        elements.append(Paragraph("TENANT DETAILS", title_style))
        elements.append(Paragraph(f"Tenant Profile - {tenant['tenant_name'] or 'N/A'}", subtitle_style))
        elements.append(Spacer(1, 20))
        
        # Personal Information Section
        elements.append(Paragraph("👤 Personal Information", section_style))
        
        personal_data = [
            ['Field', 'Value'],
            ['Name', tenant['tenant_name'] or 'N/A'],
            ['Father Name', tenant['father_name'] or 'N/A'],
            ['Mother Name', tenant['mother_name'] or 'N/A'],
            ['Date of Birth', tenant['dob'] or 'N/A'],
            ['Phone', tenant['phone'] or 'N/A'],
            ['Email', tenant['email'] or 'N/A'],
            ['Aadhar Number', tenant['aadhar_number'] or 'N/A']
        ]
        
        personal_table = Table(personal_data, colWidths=[2*inch, 4*inch])
        personal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(personal_table)
        elements.append(Spacer(1, 20))
        
        # Photo & Documents Section
        elements.append(Paragraph("📷 Photo & Documents", section_style))
        
        # Create images section
        images_data = []
        
        # Add photo if available
        if tenant.get('photo'):
            try:
                # Add tenant photo
                photo_buffer = io.BytesIO(tenant['photo'])
                photo_image = Image(photo_buffer, width=2*inch, height=2.5*inch)
                photo_data = [
                    [Paragraph("Tenant Photo:", getSampleStyleSheet()['Heading6'])],
                    [photo_image]
                ]
                photo_table = Table(photo_data, colWidths=[2*inch])
                photo_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ]))
                images_data.append([photo_table])
            except Exception as e:
                logger.error(f"Error adding photo to PDF: {e}")
                images_data.append([Paragraph("Photo: Unable to display", getSampleStyleSheet()['Normal'])])
        else:
            images_data.append([Paragraph("Photo: Not available", getSampleStyleSheet()['Normal'])])
        
        # Add Aadhar card if available
        if tenant.get('aadhar'):
            try:
                # Add Aadhar card image
                aadhar_buffer = io.BytesIO(tenant['aadhar'])
                aadhar_image = Image(aadhar_buffer, width=2*inch, height=2.5*inch)
                aadhar_data = [
                    [Paragraph("Aadhar Card:", getSampleStyleSheet()['Heading6'])],
                    [aadhar_image]
                ]
                aadhar_table = Table(aadhar_data, colWidths=[2*inch])
                aadhar_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ]))
                images_data.append([aadhar_table])
            except Exception as e:
                logger.error(f"Error adding Aadhar to PDF: {e}")
                images_data.append([Paragraph("Aadhar Card: Unable to display", getSampleStyleSheet()['Normal'])])
        else:
            images_data.append([Paragraph("Aadhar Card: Not available", getSampleStyleSheet()['Normal'])])
        
        # Create images table side by side
        if len(images_data) > 0:
            images_table = Table(images_data, colWidths=[2.5*inch, 2.5*inch])
            images_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(images_table)
        
        elements.append(Spacer(1, 20))
        
        # Address Information Section
        elements.append(Paragraph("🏠 Address Information", section_style))
        
        address_data = [
            ['Field', 'Value'],
            ['Address', tenant['address'] or 'N/A'],
            ['Street', tenant['street'] or 'N/A'],
            ['Area', tenant['area'] or 'N/A'],
            ['Pincode', tenant['pincode'] or 'N/A']
        ]
        
        address_table = Table(address_data, colWidths=[2*inch, 4*inch])
        address_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(address_table)
        elements.append(Spacer(1, 20))
        
        # PG Information Section
        elements.append(Paragraph("🏢 PG Information", section_style))
        
        pg_data = [
            ['Field', 'Value'],
            ['Floor', tenant['floor'] or 'N/A'],
            ['Room', tenant['room'] or 'N/A'],
            ['Bed', tenant['bed'] or 'N/A'],
            ['Room Type', tenant['room_type'] or 'N/A'],
            ['Check-in Date', tenant['checkin_date'] or 'N/A'],
            ['Deposit', f"Rs.{tenant['deposit']}" if tenant['deposit'] else 'N/A'],
            ['Rent', f"Rs.{tenant['rent']}" if tenant['rent'] else 'N/A']
        ]
        
        pg_table = Table(pg_data, colWidths=[2*inch, 4*inch])
        pg_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(pg_table)
        elements.append(Spacer(1, 20))
        
        # Office Information Section
        elements.append(Paragraph("💼 Office Information", section_style))
        
        office_data = [
            ['Field', 'Value'],
            ['Office Name', tenant['office_name'] or 'N/A'],
            ['Office Address', tenant['office_address'] or 'N/A']
        ]
        
        office_table = Table(office_data, colWidths=[2*inch, 4*inch])
        office_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(office_table)
        elements.append(Spacer(1, 20))
        
        # Emergency Contact Section
        elements.append(Paragraph("🚨 Emergency Contact", section_style))
        
        emergency_data = [
            ['Field', 'Value'],
            ['Contact Name', tenant['emergency_name'] or 'N/A'],
            ['Contact Phone', tenant['emergency_phone'] or 'N/A'],
            ['Relation', tenant['emergency_relation'] or 'N/A']
        ]
        
        emergency_table = Table(emergency_data, colWidths=[2*inch, 4*inch])
        emergency_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(emergency_table)
        elements.append(Spacer(1, 25))
        
        # Footer
        elements.append(create_professional_footer())
        
        # Build PDF
        doc.build(elements, onFirstPage=on_first_page, onLaterPages=on_later_pages)
        
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'tenant_{tenant["tenant_name"] or "unknown"}_{bed_id}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Download tenant PDF error: {e}")
        return "Error generating PDF", 500


# --------------------------------------------------
# EXPORT ALL TENANTS CSV
# --------------------------------------------------

@app.route("/export/all_tenants/csv")
def export_all_tenants_csv():
    try:
        conn = connect()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT tenant_name, father_name, mother_name, address, street, area, pincode,
                   aadhar_number, dob, email, phone, office_name, office_address,
                   deposit, rent, floor, room, bed, room_type, checkin_date,
                   emergency_name, emergency_phone, emergency_relation, photo, aadhar
            FROM rooms 
            WHERE tenant_name IS NOT NULL AND tenant_name != ''
            ORDER BY floor, room, bed
        """)
        
        tenants = cur.fetchall()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Tenant Name', 'Father Name', 'Mother Name', 'Address', 'Street', 'Area', 'Pincode',
                        'Aadhar Number', 'DOB', 'Email', 'Phone', 'Office Name', 'Office Address',
                        'Deposit', 'Rent', 'Floor', 'Room', 'Bed', 'Room Type', 'Checkin Date',
                        'Emergency Name', 'Emergency Phone', 'Emergency Relation'])
        
        # Data
        for tenant in tenants:
            writer.writerow(tenant)
        
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=all_tenants.csv'}
        )
        
    except Exception as e:
        logger.error(f"Export all tenants CSV error: {e}")
        return "Error exporting data", 500


# --------------------------------------------------
# EXPORT ALL TENANTS PDF
# --------------------------------------------------

def on_first_page(canvas, doc):
    # Professional header
    canvas.saveState()
    canvas.setFont('Helvetica-Bold', 12)
    canvas.setFillColor(colors.darkblue)
    canvas.drawString(0.5*inch, 10.5*inch, "PG MANAGEMENT SYSTEM")
    canvas.line(0.5*inch, 10.3*inch, 7.5*inch, 10.3*inch)
    canvas.restoreState()

def on_later_pages(canvas, doc):
    # Header for subsequent pages
    canvas.saveState()
    canvas.setFont('Helvetica-Bold', 10)
    canvas.setFillColor(colors.darkblue)
    canvas.drawString(0.5*inch, 10.5*inch, "PG MANAGEMENT SYSTEM - TENANTS REPORT")
    canvas.line(0.5*inch, 10.3*inch, 7.5*inch, 10.3*inch)
    
    # Footer with page number
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(7.5*inch, 0.5*inch, f"Page {doc.page}")
    canvas.drawString(0.5*inch, 0.5*inch, f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    canvas.restoreState()

@app.route("/export/all_tenants/pdf")
def export_all_tenants_pdf():
    try:
        conn = connect()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT tenant_name, father_name, mother_name, address, street, area, pincode,
                   aadhar_number, dob, email, phone, office_name, office_address,
                   deposit, rent, floor, room, bed, room_type, checkin_date,
                   emergency_name, emergency_phone, emergency_relation, photo, aadhar
            FROM rooms 
            WHERE tenant_name IS NOT NULL AND tenant_name != ''
            ORDER BY floor, room, bed
        """)
        
        tenants = cur.fetchall()
        
        buffer = io.BytesIO()
        
        # Full page utilization with minimal margins to prevent title cutoff
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            leftMargin=0.2*inch, 
            rightMargin=0.2*inch,
            topMargin=1.0*inch, 
            bottomMargin=0.8*inch
        )
        
        styles = getSampleStyleSheet()
        elements = []
        
        # Professional title styles
        from professional_pdf import create_professional_title_style, create_professional_table_style, create_summary_box, create_professional_footer, create_instructions_note
        
        title_style, subtitle_style, section_style = create_professional_title_style()
        elements = []
        
        # Professional header with proper spacing
        elements.append(Paragraph("PG MANAGEMENT SYSTEM", title_style))
        elements.append(Paragraph("ALL TENANTS REPORT", title_style))
        elements.append(Paragraph(f"Comprehensive Tenant Listing as of {datetime.now().strftime('%d %B %Y')}", subtitle_style))
        elements.append(Spacer(1, 20))
        
        # Instructions for clickable buttons
        elements.append(create_instructions_note())
        elements.append(Spacer(1, 15))
        
        # Professional summary section
        elements.append(Paragraph("📊 Report Summary", section_style))
        elements.append(create_summary_box(len(tenants)))
        elements.append(Spacer(1, 25))
        
        # Enhanced table data with both clickable links and visible URLs
        headers = ['S.No', 'Tenant Name', 'Photo', 'Aadhar', 'Floor', 'Room Type', 'Bed', 'Phone', 'Email', 'Checkin Date', 'Rent']
        data = [headers]
        
        for idx, tenant in enumerate(tenants, 1):
            # Extract image data (last two columns)
            photo_data = tenant[23] if len(tenant) > 23 and tenant[23] else None
            aadhar_data = tenant[24] if len(tenant) > 24 and tenant[24] else None
            
            # Create clickable links with visible URLs
            styles = getSampleStyleSheet()
            link_style = ParagraphStyle(
                'LinkStyle',
                parent=styles['Normal'],
                fontSize=6,
                alignment=TA_CENTER,
                textColor=colors.blue,
                fontName='Helvetica-Bold'
            )
            url_style = ParagraphStyle(
                'UrlStyle', 
                parent=styles['Normal'],
                fontSize=5,
                alignment=TA_CENTER,
                textColor=colors.darkgrey,
                fontName='Helvetica'
            )
            normal_style = ParagraphStyle(
                'NormalCell',
                parent=styles['Normal'],
                fontSize=8,
                alignment=TA_CENTER,
                textColor=colors.black
            )
            
            # Get bed_id for creating links
            cur.execute("""
                SELECT id FROM rooms 
                WHERE floor = %s AND room = %s AND bed = %s AND tenant_name = %s
                LIMIT 1
            """, (tenant[15], tenant[16], tenant[17], tenant[0]))
            
            bed_result = cur.fetchone()
            bed_id = bed_result[0] if bed_result else None
            base_url = request.host_url.rstrip('/')
            
            # Create photo cell with clickable link and visible URL
            if photo_data and bed_id:
                photo_url = f"{base_url}/photo/{bed_id}"
                # Shorten URL for display
                short_url = photo_url.replace(base_url, "")
                photo_cell = [[
                    Paragraph(f'<a href="{photo_url}" color="blue"><u>VIEW</u></a>', link_style),
                    Paragraph(f'<font size="1">{short_url}</font>', url_style)
                ]]
            else:
                photo_cell = [[Paragraph("No Photo", normal_style)]]
                
            # Create Aadhar cell with clickable link and visible URL
            if aadhar_data and bed_id:
                aadhar_url = f"{base_url}/aadhar/{bed_id}"
                # Shorten URL for display
                short_url = aadhar_url.replace(base_url, "")
                aadhar_cell = [[
                    Paragraph(f'<a href="{aadhar_url}" color="blue"><u>VIEW</u></a>', link_style),
                    Paragraph(f'<font size="1">{short_url}</font>', url_style)
                ]]
            else:
                aadhar_cell = [[Paragraph("No Aadhar", normal_style)]]
            
            data.append([
                str(idx),  # Serial number
                tenant[0] if tenant[0] else '',  # tenant_name
                photo_cell,  # Photo
                aadhar_cell,  # Aadhar
                tenant[15] if tenant[15] else '',  # floor
                tenant[16] if tenant[16] else '',  # room (now labeled as Room Type)
                tenant[17] if tenant[17] else '',  # bed
                tenant[10] if tenant[10] else '',  # phone
                tenant[9] if tenant[9] else '',    # email
                tenant[18] if tenant[18] else '',  # checkin_date
                f"Rs.{tenant[14]}" if tenant[14] else ''  # rent
            ])
        
        # Calculate optimal column widths to prevent text overlap
        col_widths = [
            0.4*inch,   # S.No
            1.0*inch,   # Tenant Name
            0.6*inch,   # Photo (with links and URLs)
            0.6*inch,   # Aadhar (with links and URLs)
            0.7*inch,   # Floor (wider for "GROUND FLOOR")
            1.3*inch,   # Room Type (much wider for "4 SHARING AC ROOM")
            0.4*inch,   # Bed
            0.7*inch,   # Phone
            1.0*inch,   # Email
            0.9*inch,   # Checkin Date (wider for dates)
            0.5*inch    # Rent
        ]
        
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(create_professional_table_style())
        
        elements.append(table)
        elements.append(Spacer(1, 25))
        
        # Professional footer
        elements.append(create_professional_footer())
        
        # Build PDF with professional page templates
        doc.build(elements, onFirstPage=on_first_page, onLaterPages=on_later_pages)
        
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name='all_tenants.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Export all tenants PDF error: {e}")
        return "Error exporting data", 500


# --------------------------------------------------
# GET TENANT DOCUMENT URLS
# --------------------------------------------------

@app.route("/tenant/<int:bed_id>/document-urls")
def get_tenant_document_urls(bed_id):
    try:
        tenant = get_tenant(bed_id)
        
        if not tenant:
            return jsonify({"error": "Tenant not found"}), 404
        
        base_url = request.host_url.rstrip('/')
        urls = {
            "tenant_name": tenant.get("tenant_name", "Unknown"),
            "photo_url": f"{base_url}/photo/{bed_id}" if tenant.get("photo") else None,
            "aadhar_url": f"{base_url}/aadhar/{bed_id}" if tenant.get("aadhar") else None,
            "download_pdf_url": f"{base_url}/download_tenant/{bed_id}"
        }
        
        return jsonify(urls)
        
    except Exception as e:
        logger.error(f"get_tenant_document_urls error: {e}")
        return jsonify({"error": "Server error"}), 500


# --------------------------------------------------
# TOKEN CLEANUP ENDPOINT
# --------------------------------------------------

@app.route("/admin/cleanup-tokens", methods=["POST"])
def cleanup_tokens():
    try:
        cleanup_expired_tokens()
        stats = get_token_stats()
        return jsonify({
            "success": True, 
            "message": "Token cleanup completed",
            "stats": stats
        })
    except Exception as e:
        logger.error(f"cleanup_tokens error: {e}")
        return jsonify({"success": False, "error": "Cleanup failed"})


# --------------------------------------------------
# GENERATE FORM LINK FOR EMPTY BED
# --------------------------------------------------

@app.route("/generate-form-link/<int:bed_id>", methods=["POST"])
def generate_form_link(bed_id):
    try:
        token = generate_form_token(bed_id)
        if token:
            # Get the actual host from headers (works behind proxies/reverse proxies)
            host = request.headers.get('X-Forwarded-Host', request.host)
            scheme = request.headers.get('X-Forwarded-Proto', request.scheme)
            form_url = f"{scheme}://{host}/tenant-form/{token}"
            logger.info(f"Generated form URL: {form_url}")
            return jsonify({"success": True, "form_url": form_url})
        return jsonify({"success": False, "error": "Bed not available"})
    except Exception as e:
        logger.error(f"generate_form_link error: {e}")
        return jsonify({"success": False})

# --------------------------------------------------
# TENANT FORM PAGE
# --------------------------------------------------

@app.route("/tenant-form/<token>")
def tenant_form_page(token):
    try:
        bed = get_bed_by_token(token)
        if not bed:
            return "Invalid or expired form link", 404
        
        return render_template("tenant_form.html", 
                             bed=bed, 
                             token=token)
    except Exception as e:
        logger.error(f"tenant_form_page error: {e}")
        return "Error loading form", 500

# --------------------------------------------------
# SUBMIT TENANT FORM
# --------------------------------------------------

@app.route("/submit-tenant-form/<token>", methods=["POST"])
def submit_tenant_form(token):
    try:
        bed = get_bed_by_token(token)
        if not bed:
            return jsonify({"success": False, "error": "Invalid token"})
        
        data = {
            "name": request.form.get("name"),
            "father": request.form.get("father"),
            "mother": request.form.get("mother"),
            "address": request.form.get("address"),
            "street": request.form.get("street"),
            "area": request.form.get("area"),
            "pincode": request.form.get("pincode"),
            "aadhar_number": request.form.get("aadhar_number"),
            "dob": request.form.get("dob"),
            "email": request.form.get("email"),
            "phone": request.form.get("phone"),
            "office_name": request.form.get("office_name"),
            "office_address": request.form.get("office_address"),
            "deposit": request.form.get("deposit"),
            "rent": request.form.get("rent"),
            "room_type": request.form.get("room_type"),
            "checkin": request.form.get("checkin"),
            "emergency_name": request.form.get("emergency_name"),
            "emergency_phone": request.form.get("emergency_phone"),
            "emergency_relation": request.form.get("emergency_relation")
        }
        
        photo = request.files.get("photo")
        aadhar = request.files.get("aadhar")
        
        # Validate photo file
        photo_data = None
        if photo and photo.filename:
            validated_photo, error = validate_uploaded_file(photo)
            if error:
                return jsonify({"success": False, "error": f"Photo validation failed: {error}"})
            photo_data = safe_read_file(validated_photo)

        # Validate aadhar file  
        aadhar_data = None
        if aadhar and aadhar.filename:
            validated_aadhar, error = validate_uploaded_file(aadhar)
            if error:
                return jsonify({"success": False, "error": f"Aadhar validation failed: {error}"})
            aadhar_data = safe_read_file(validated_aadhar)
        
        success = add_tenant_via_form(token, data, photo_data, aadhar_data)
        
        if success:
            return jsonify({"success": True, "message": "Registration successful!"})
        return jsonify({"success": False, "error": "Registration failed"})
        
    except Exception as e:
        logger.error(f"submit_tenant_form error: {e}")
        return jsonify({"success": False, "error": "Server error"})


# --------------------------------------------------
# EXPORT FORMER TENANTS CSV
# --------------------------------------------------

@app.route("/export/former_tenants/csv")
def export_former_tenants_csv():
    try:
        conn = connect()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT tenant_name, father_name, mother_name, address, street, area, pincode,
                   aadhar_number, dob, email, phone, office_name, office_address,
                   deposit, rent, floor, room, bed, room_type, checkin_date, leaving_date,
                   emergency_name, emergency_phone, emergency_relation, photo, aadhar
            FROM former_tenants 
            ORDER BY leaving_date DESC, created_at DESC
        """)
        
        tenants = cur.fetchall()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Tenant Name', 'Father Name', 'Mother Name', 'Address', 'Street', 'Area', 'Pincode',
                        'Aadhar Number', 'DOB', 'Email', 'Phone', 'Office Name', 'Office Address',
                        'Deposit', 'Rent', 'Floor', 'Room', 'Bed', 'Room Type', 'Checkin Date', 'Leaving Date',
                        'Emergency Name', 'Emergency Phone', 'Emergency Relation'])
        
        # Data
        for tenant in tenants:
            writer.writerow(tenant)
        
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=former_tenants.csv'}
        )
        
    except Exception as e:
        logger.error(f"Export former tenants CSV error: {e}")
        return "Error exporting data", 500


# --------------------------------------------------
# EXPORT FORMER TENANTS PDF
# --------------------------------------------------

@app.route("/export/former_tenants/pdf")
def export_former_tenants_pdf():
    try:
        conn = connect()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT tenant_name, father_name, mother_name, address, street, area, pincode,
                   aadhar_number, dob, email, phone, office_name, office_address,
                   deposit, rent, floor, room, bed, room_type, checkin_date, leaving_date,
                   emergency_name, emergency_phone, emergency_relation, photo, aadhar
            FROM former_tenants 
            ORDER BY floor, room, bed
        """)
        
        tenants = cur.fetchall()
        
        buffer = io.BytesIO()
        
        # Full page utilization with minimal margins to prevent title cutoff
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            leftMargin=0.2*inch, 
            rightMargin=0.2*inch,
            topMargin=1.0*inch, 
            bottomMargin=0.8*inch
        )
        
        styles = getSampleStyleSheet()
        elements = []
        
        # Professional title styles
        from professional_pdf import create_professional_title_style, create_professional_table_style, create_summary_box, create_professional_footer, create_instructions_note
        
        title_style, subtitle_style, section_style = create_professional_title_style()
        elements = []
        
        # Professional header with proper spacing
        elements.append(Paragraph("PG MANAGEMENT SYSTEM", title_style))
        elements.append(Paragraph("FORMER TENANTS REPORT", title_style))
        elements.append(Paragraph(f"Comprehensive Former Tenant Listing as of {datetime.now().strftime('%d %B %Y')}", subtitle_style))
        elements.append(Spacer(1, 20))
        
        # Instructions for clickable buttons
        elements.append(create_instructions_note())
        elements.append(Spacer(1, 15))
        
        # Professional summary section
        elements.append(Paragraph("📊 Report Summary", section_style))
        elements.append(create_summary_box(len(tenants)))
        elements.append(Spacer(1, 25))
        
        # Enhanced table data with both clickable links and visible URLs
        headers = ['S.No', 'Tenant Name', 'Photo', 'Aadhar', 'Floor', 'Room Type', 'Bed', 'Phone', 'Email', 'Checkin Date', 'Leaving Date', 'Rent']
        data = [headers]
        
        for idx, tenant in enumerate(tenants, 1):
            # Extract image data (last two columns)
            photo_data = tenant[23] if len(tenant) > 23 and tenant[23] else None
            aadhar_data = tenant[24] if len(tenant) > 24 and tenant[24] else None
            
            # Create clickable links with visible URLs
            styles = getSampleStyleSheet()
            link_style = ParagraphStyle(
                'LinkStyle',
                parent=styles['Normal'],
                fontSize=6,
                alignment=TA_CENTER,
                textColor=colors.blue,
                fontName='Helvetica-Bold'
            )
            url_style = ParagraphStyle(
                'UrlStyle', 
                parent=styles['Normal'],
                fontSize=5,
                alignment=TA_CENTER,
                textColor=colors.darkgrey,
                fontName='Helvetica'
            )
            normal_style = ParagraphStyle(
                'NormalCell',
                parent=styles['Normal'],
                fontSize=8,
                alignment=TA_CENTER,
                textColor=colors.black
            )
            
            # Get bed_id for creating links (from former_tenants table)
            cur.execute("""
                SELECT id FROM former_tenants 
                WHERE floor = %s AND room = %s AND bed = %s AND tenant_name = %s
                LIMIT 1
            """, (tenant[15], tenant[16], tenant[17], tenant[0]))
            
            bed_result = cur.fetchone()
            bed_id = bed_result[0] if bed_result else None
            base_url = request.host_url.rstrip('/')
            
            # Create photo cell with clickable link and visible URL
            if photo_data and bed_id:
                photo_url = f"{base_url}/former/photo/{bed_id}"
                # Shorten URL for display
                short_url = photo_url.replace(base_url, "")
                photo_cell = [[
                    Paragraph(f'<a href="{photo_url}" color="blue"><u>VIEW</u></a>', link_style),
                    Paragraph(f'<font size="1">{short_url}</font>', url_style)
                ]]
            else:
                photo_cell = [[Paragraph("No Photo", normal_style)]]
                
            # Create Aadhar cell with clickable link and visible URL
            if aadhar_data and bed_id:
                aadhar_url = f"{base_url}/former/aadhar/{bed_id}"
                # Shorten URL for display
                short_url = aadhar_url.replace(base_url, "")
                aadhar_cell = [[
                    Paragraph(f'<a href="{aadhar_url}" color="blue"><u>VIEW</u></a>', link_style),
                    Paragraph(f'<font size="1">{short_url}</font>', url_style)
                ]]
            else:
                aadhar_cell = [[Paragraph("No Aadhar", normal_style)]]
            
            data.append([
                str(idx),  # Serial number
                tenant[0] if tenant[0] else '',  # tenant_name
                photo_cell,  # Photo
                aadhar_cell,  # Aadhar
                tenant[15] if tenant[15] else '',  # floor
                tenant[16] if tenant[16] else '',  # room (now labeled as Room Type)
                tenant[17] if tenant[17] else '',  # bed
                tenant[10] if tenant[10] else '',  # phone
                tenant[9] if tenant[9] else '',    # email
                tenant[18] if tenant[18] else '',  # checkin_date
                tenant[19] if tenant[19] else '',  # leaving_date
                f"Rs.{tenant[14]}" if tenant[14] else ''  # rent
            ])
        
        # Calculate optimal column widths to prevent text overlap
        col_widths = [
            0.4*inch,   # S.No
            1.0*inch,   # Tenant Name
            0.6*inch,   # Photo (with links and URLs)
            0.6*inch,   # Aadhar (with links and URLs)
            0.7*inch,   # Floor (wider for "GROUND FLOOR")
            1.3*inch,   # Room Type (much wider for "4 SHARING AC ROOM")
            0.4*inch,   # Bed
            0.7*inch,   # Phone
            1.0*inch,   # Email
            0.9*inch,   # Checkin Date (wider for dates)
            0.5*inch    # Rent
        ]
        
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(create_professional_table_style())
        
        elements.append(table)
        elements.append(Spacer(1, 25))
        
        # Professional footer
        elements.append(create_professional_footer())
        
        # Build PDF with professional page templates
        doc.build(elements, onFirstPage=on_first_page, onLaterPages=on_later_pages)
        
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name='former_tenants.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Export former tenants PDF error: {e}")
        return "Error exporting data", 500
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
