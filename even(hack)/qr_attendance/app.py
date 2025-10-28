from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, session, flash, Response,send_from_directory
import os
import json
import qrcode
import io
from fpdf import FPDF
from io import BytesIO
from datetime import datetime, time
import base64
import csv
import re
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
import threading
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
from flask_mail import Message
from flask import current_app as app
from flask_mail import Mail, Message
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email,Optional
from wtforms import StringField, SelectField, SubmitField, HiddenField, RadioField
from wtforms.validators import DataRequired, Email, Length, Regexp
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.platypus import Image
from pathlib import Path
from datetime import datetime, timedelta
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Lock
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import textwrap
from num2words import num2words
import math
import uuid

# Initialize Flask app first
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key


mail = Mail(app)

# Configuration - Use Port 587 with TLS
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'smartnlightinnovations@gmail.com'
app.config['MAIL_PASSWORD'] = 'raja rbot qghf ywig'  # This is an app password, not your regular password
app.config['MAIL_DEFAULT_SENDER'] = 'smartnlightinnovations@gmail.com'
app.config['MAIL_DEBUG'] = False  # Set to False for production
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Initialize mail with error handling
try:
    mail = Mail(app)
    print("✅ Mail initialized successfully")
except Exception as e:
    print(f"❌ Mail initialization failed: {e}")
    mail = None

# Credentials
RECEIPT_CREDENTIALS = {'username': 'MD2025', 'password': 'CCAD01'}
ADMIN_CREDENTIALS = {'username': 'AD2025', 'password': 'CCAD02'}
TEAMS_CREDENTIALS = {'username': 'TC2025', 'password': 'CCMA1'}

# File paths
DATABASE_FILE = 'data/database.json'
SCANNED_LOG_FILE = 'data/scanned_log.json'
EMAIL_LOGS_FILE = 'data/email_logs.json'
HOMEPAGE_CONFIG_FILE = 'data/homepage_config.json'
HACKATHON_CONFIG_FILE = 'data/hackathon_config.json'
STUDENT_MASTER_FILE = 'data/student_master_data.json'


# Constants
YEARS = ['1st', '2nd', '3rd', '4th']
BRANCHES = [
    'CSE', 'AIML', 'Cyber Security', 'Data Science', 
    'Mechanical', 'Civil', 'ECE', 'EEE', 'Freshman'
]

# Section mapping for each branch
SECTION_MAPPING = {
    'CSE': ['A', 'B', 'C', 'D', 'E'],
    'AIML': ['A', 'B', 'C', 'D', 'E'],
    'Cyber Security': ['A', 'B', 'C', 'D', 'E'],
    'Data Science': ['A', 'B', 'C', 'D', 'E'],
    'Mechanical': ['A', 'B', 'C', 'D', 'E'],
    'Civil': ['A', 'B', 'C', 'D', 'E'],
    'ECE': ['A', 'B', 'C', 'D', 'E'],
    'EEE': ['A', 'B', 'C', 'D', 'E'],
    'Freshman': ['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon', 
                'Zeta', 'Eta', 'Theta', 'Iota', 'Omega']
}

SCAN_TYPES = ['entry', 'food']
PHONEPE_QR_CODE = 'static/team_001_qr.png'

# File upload configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

# Global variables
active_breaks = {}  
team_id_lock = threading.Lock()
break_lock = threading.Lock()
IST = pytz.timezone('Asia/Kolkata')

class ReceiptForm(FlaskForm):
    viewer_name = StringField('Payer Name', validators=[DataRequired()], render_kw={'readonly': True})
    viewer_email = StringField('Payer Email', validators=[DataRequired()])
    year = SelectField('Year', 
                     choices=[('', 'Select year'), 
                             ('1st', '1st Year (₹500)'), 
                             ('2nd', '2nd Year (₹600)')],
                     validators=[DataRequired()],
                     render_kw={'readonly': True})  # Make year read-only
    contact_number = StringField('Contact Number', validators=[DataRequired()])
    receiver_name = SelectField('Receiver Name',
                              choices=[('', 'Select receiver'),
                                      
                                      ('Laxmi Nivas', 'Laxmi Nivas'),
                                        ('Sheshank', 'Sheshank'),
                                      ('Govardhini Reddy', 'Govardhini Reddy'),
                                      
                                      ('Raghava', 'Raghava')],
                              validators=[DataRequired()])
    amount = HiddenField('Amount', validators=[DataRequired()])
    receipt_no = HiddenField('Receipt Number')
    submit = SubmitField('Generate Receipt')
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def initialize_new_databases():
    """Initialize the new student master and registered users databases"""
    # Initialize student master data
    if not os.path.exists(STUDENT_MASTER_FILE):
        with open(STUDENT_MASTER_FILE, 'w') as f:
            json.dump({'students': []}, f)
    
 


def initialize_files():
    """Initialize all required data files with proper structure"""
    # Initialize database file
    if not os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'w') as f:
            json.dump({'teams': [], 'individuals': []}, f)
    
    if not os.path.exists(HACKATHON_CONFIG_FILE):
        with open(HACKATHON_CONFIG_FILE, 'w') as f:
            json.dump({
                'payment_required': True,
                'hackathon_name': 'Default Hackathon',
                'registration_fee': 500
            }, f)
    
    if not os.path.exists(SCANNED_LOG_FILE):
        with open(SCANNED_LOG_FILE, 'w') as f:
            json.dump({
                'entries': [],
                'food': []
            }, f)
    initialize_new_databases()
    if not os.path.exists(HOMEPAGE_CONFIG_FILE):
        default_homepage_config = {
            'hero_title': '36 Hours Hackathon Registration',
            'hero_subtitle': 'Register your team for the 36 Hours Hackathon event and showcase your skills',
            'event_date': 'July 21-23, 2025',
            'event_location': 'Sphoorthy Engineering College Campus',
            'registration_deadline': 'July 15, 2025',
            'about_event': 'Join us for an exciting competition where teams showcase their skills and compete for amazing prizes. The event will feature multiple challenges testing various aspects of technical and creative abilities.',
            'requirements': [
                'Teams must have 3-4 members',
                'Complete all required member information',
                'Payment must be completed for registration',
                'Members can be from any Institutions',
                'Registration deadline: July 15, 2025'
            ]
        }
        with open(HOMEPAGE_CONFIG_FILE, 'w') as f:
            json.dump(default_homepage_config, f, indent=4)

@app.route('/admin/payment-screenshots')
def view_payment_screenshots():
    """View all online payment screenshots"""
    if not session.get('admin_logged_in') and not session.get('receipt_logged_in'):
        return redirect(url_for('admin_login'))
    
    # Get all individuals with online payments
    online_payments = []
    
    try:
        with open(DATABASE_FILE, 'r') as f:
            data = json.load(f)
            
        for individual in data.get('individuals', []):
            if individual.get('payment_method') == 'online' and individual.get('payment_screenshot'):
                online_payments.append({
                    'individual_id': individual['individual_id'],
                    'name': individual['name'],
                    'email': individual['email'],
                    'payment_id': individual.get('payment_id', 'N/A'),
                    'payment_screenshot': individual['payment_screenshot'],
                    'payment_date': individual.get('payment_date', 'N/A'),
                    'amount': individual.get('registration_fee', 'N/A'),
                    'year': individual.get('year', 'N/A'),
                    'branch': individual.get('branch', 'N/A'),
                    'contact': individual.get('contact_number', 'N/A'),
                    'college': individual.get('college', 'N/A'),
                    'payment_verified': individual.get('payment_verified', False)
                })
                
        # Sort by payment date (newest first)
        online_payments.sort(key=lambda x: x['payment_date'], reverse=True)
        
        # Calculate stats
        stats = {
            'total_payments': len(online_payments),
            'verified_payments': len([p for p in online_payments if p['payment_verified']]),
            'pending_payments': len([p for p in online_payments if not p['payment_verified']]),
            'total_amount': sum([int(p['amount']) for p in online_payments if str(p['amount']).isdigit()]),
            'first_year_count': len([p for p in online_payments if p.get('year') == '1st']),
            'second_year_count': len([p for p in online_payments if p.get('year') == '2nd'])
        }
                
    except Exception as e:
        print(f"Error reading payment screenshots: {str(e)}")
        flash('Error loading payment screenshots', 'error')
        online_payments = []
        stats = {
            'total_payments': 0,
            'verified_payments': 0,
            'pending_payments': 0,
            'total_amount': 0,
            'first_year_count': 0,
            'second_year_count': 0
        }
    
    return render_template('view_payment_screenshots.html', 
                         payments=online_payments, 
                         stats=stats,
                         filter_type='all')

def get_payment_stats():
    """Calculate payment statistics"""
    try:
        with open(DATABASE_FILE, 'r') as f:
            data = json.load(f)
        
        online_payments = []
        for individual in data.get('individuals', []):
            if individual.get('payment_method') == 'online' and individual.get('payment_screenshot'):
                online_payments.append(individual)
        
        return {
            'total_payments': len(online_payments),
            'verified_payments': len([p for p in online_payments if p.get('payment_verified')]),
            'pending_payments': len([p for p in online_payments if not p.get('payment_verified')]),
            'total_amount': sum([int(p.get('registration_fee', 0)) for p in online_payments]),
            'first_year_count': len([p for p in online_payments if p.get('year') == '1st']),
            'second_year_count': len([p for p in online_payments if p.get('year') == '2nd'])
        }
    except Exception as e:
        print(f"Error calculating payment stats: {str(e)}")
        return {
            'total_payments': 0,
            'verified_payments': 0,
            'pending_payments': 0,
            'total_amount': 0,
            'first_year_count': 0,
            'second_year_count': 0
        }
@app.route('/admin/payment-screenshots/verified')
def view_verified_screenshots():
    """View only verified payment screenshots"""
    if not session.get('admin_logged_in') and not session.get('receipt_logged_in'):
        return redirect(url_for('admin_login'))
    
    verified_payments = []
    
    try:
        with open(DATABASE_FILE, 'r') as f:
            data = json.load(f)
            
        for individual in data.get('individuals', []):
            if (individual.get('payment_method') == 'online' and 
                individual.get('payment_screenshot') and 
                individual.get('payment_verified')):
                
                verified_payments.append({
                    'individual_id': individual['individual_id'],
                    'name': individual['name'],
                    'email': individual['email'],
                    'payment_id': individual.get('payment_id', 'N/A'),
                    'payment_screenshot': individual['payment_screenshot'],
                    'payment_date': individual.get('payment_date', 'N/A'),
                    'amount': individual.get('registration_fee', 'N/A'),
                    'year': individual.get('year', 'N/A'),
                    'branch': individual.get('branch', 'N/A'),
                    'contact': individual.get('contact_number', 'N/A'),
                    'college': individual.get('college', 'N/A')
                })
                
        verified_payments.sort(key=lambda x: x['payment_date'], reverse=True)
                
    except Exception as e:
        print(f"Error reading verified screenshots: {str(e)}")
        flash('Error loading verified screenshots', 'error')
    
    return render_template('view_payment_screenshots.html', payments=verified_payments, filter_type='verified')

@app.route('/admin/payment-screenshots/pending')
def view_pending_screenshots():
    """View only pending payment screenshots"""
    if not session.get('admin_logged_in') and not session.get('receipt_logged_in'):
        return redirect(url_for('admin_login'))
    
    pending_payments = []
    
    try:
        with open(DATABASE_FILE, 'r') as f:
            data = json.load(f)
            
        for individual in data.get('individuals', []):
            if (individual.get('payment_method') == 'online' and 
                individual.get('payment_screenshot') and 
                not individual.get('payment_verified')):
                
                pending_payments.append({
                    'individual_id': individual['individual_id'],
                    'name': individual['name'],
                    'email': individual['email'],
                    'payment_id': individual.get('payment_id', 'N/A'),
                    'payment_screenshot': individual['payment_screenshot'],
                    'payment_date': individual.get('payment_date', 'N/A'),
                    'amount': individual.get('registration_fee', 'N/A'),
                    'year': individual.get('year', 'N/A'),
                    'branch': individual.get('branch', 'N/A'),
                    'contact': individual.get('contact_number', 'N/A'),
                    'college': individual.get('college', 'N/A')
                })
                
        pending_payments.sort(key=lambda x: x['payment_date'], reverse=True)
                
    except Exception as e:
        print(f"Error reading pending screenshots: {str(e)}")
        flash('Error loading pending screenshots', 'error')
    
    return render_template('view_payment_screenshots.html', payments=pending_payments, filter_type='pending')

@app.route('/admin/receipts/verified')
def view_verified_receipts():
    """View only verified receipts"""
    if not session.get('admin_logged_in') and not session.get('receipt_logged_in'):
        return redirect(url_for('admin_login'))
    
    verified_receipts = []
    
    try:
        with open(DATABASE_FILE, 'r') as f:
            data = json.load(f)
            
        for individual in data.get('individuals', []):
            if (individual.get('payment_method') == 'cash' and 
                individual.get('cash_receipt_photo') and 
                individual.get('payment_verified')):
                
                # Build the correct file path for receipts
                receipt_filename = individual['cash_receipt_photo']
                
                # Check if file exists in any of the receipt locations
                file_found = False
                receipt_file_path = None
                
                # Check uploads folder first
                uploads_path = os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename)
                if os.path.exists(uploads_path):
                    file_found = True
                    receipt_file_path = receipt_filename
                else:
                    # Check receipts folder and subfolders
                    receipts_base_dir = os.path.join('static', 'receipts')
                    if os.path.exists(receipts_base_dir):
                        # Check root receipts folder
                        root_receipt_path = os.path.join(receipts_base_dir, receipt_filename)
                        if os.path.exists(root_receipt_path):
                            file_found = True
                            receipt_file_path = root_receipt_path
                        else:
                            # Check receiver subfolders
                            for receiver_folder in os.listdir(receipts_base_dir):
                                receiver_path = os.path.join(receipts_base_dir, receiver_folder, receipt_filename)
                                if os.path.exists(receiver_path):
                                    file_found = True
                                    receipt_file_path = receiver_path
                                    break
                
                if file_found and receipt_file_path:
                    verified_receipts.append({
                        'individual_id': individual['individual_id'],
                        'name': individual['name'],
                        'email': individual['email'],
                        'receipt_id': individual.get('receipt_number', 'N/A'),
                        'receipt_file': receipt_file_path,  # Use the correct path
                        'receipt_date': individual.get('payment_date', 'N/A'),
                        'amount': individual.get('registration_fee', 'N/A'),
                        'year': individual.get('year', 'N/A'),
                        'branch': individual.get('branch', 'N/A'),
                        'contact': individual.get('contact_number', 'N/A'),
                        'college': individual.get('college', 'N/A'),
                        'receiver_name': individual.get('cash_receiver_name', 'N/A'),
                        'receipt_verified': True  # Always True for verified receipts
                    })
                else:
                    print(f"⚠️ Receipt file not found: {receipt_filename}")
                
        # Sort by receiver name first, then by receipt date
        verified_receipts.sort(key=lambda x: (x['receiver_name'], x['receipt_date']), reverse=False)
                
    except Exception as e:
        print(f"Error reading verified receipts: {str(e)}")
        flash('Error loading verified receipts', 'error')
    
    return render_template('view_receipts.html', receipts=verified_receipts, filter_type='verified')

@app.route('/admin/receipts/pending')
def view_pending_receipts():
    """View only pending receipts"""
    if not session.get('admin_logged_in') and not session.get('receipt_logged_in'):
        return redirect(url_for('admin_login'))
    
    pending_receipts = []
    
    try:
        with open(DATABASE_FILE, 'r') as f:
            data = json.load(f)
            
        for individual in data.get('individuals', []):
            if (individual.get('payment_method') == 'cash' and 
                individual.get('cash_receipt_photo') and 
                not individual.get('payment_verified')):
                
                # Build the correct file path for receipts
                receipt_filename = individual['cash_receipt_photo']
                
                # Check if file exists in any of the receipt locations
                file_found = False
                receipt_file_path = None
                
                # Check uploads folder first
                uploads_path = os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename)
                if os.path.exists(uploads_path):
                    file_found = True
                    receipt_file_path = receipt_filename
                else:
                    # Check receipts folder and subfolders
                    receipts_base_dir = os.path.join('static', 'receipts')
                    if os.path.exists(receipts_base_dir):
                        # Check root receipts folder
                        root_receipt_path = os.path.join(receipts_base_dir, receipt_filename)
                        if os.path.exists(root_receipt_path):
                            file_found = True
                            receipt_file_path = root_receipt_path
                        else:
                            # Check receiver subfolders
                            for receiver_folder in os.listdir(receipts_base_dir):
                                receiver_path = os.path.join(receipts_base_dir, receiver_folder, receipt_filename)
                                if os.path.exists(receiver_path):
                                    file_found = True
                                    receipt_file_path = receiver_path
                                    break
                
                if file_found and receipt_file_path:
                    pending_receipts.append({
                        'individual_id': individual['individual_id'],
                        'name': individual['name'],
                        'email': individual['email'],
                        'receipt_id': individual.get('receipt_number', 'N/A'),
                        'receipt_file': receipt_file_path,  # Use the correct path
                        'receipt_date': individual.get('payment_date', 'N/A'),
                        'amount': individual.get('registration_fee', 'N/A'),
                        'year': individual.get('year', 'N/A'),
                        'branch': individual.get('branch', 'N/A'),
                        'contact': individual.get('contact_number', 'N/A'),
                        'college': individual.get('college', 'N/A'),
                        'receiver_name': individual.get('cash_receiver_name', 'N/A'),
                        'receipt_verified': individual.get('payment_verified', False)
                    })
                else:
                    print(f"⚠️ Receipt file not found: {receipt_filename}")
                
        # Sort by receiver name
        pending_receipts.sort(key=lambda x: x['receiver_name'])
                
    except Exception as e:
        print(f"Error reading pending receipts: {str(e)}")
        flash('Error loading pending receipts', 'error')
    
    return render_template('view_receipts.html', receipts=pending_receipts, filter_type='pending')

@app.route('/update_receipt_status/<individual_id>', methods=['POST'])
def update_receipt_status(individual_id):
    """Update receipt verification status"""
    print(f"DEBUG: update_receipt_status called with individual_id: {individual_id}")
    
    if not session.get('admin_logged_in') and not session.get('receipt_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        print(f"DEBUG: Request JSON data: {data}")
        
        if not data:
            return jsonify({'success': False, 'message': 'No JSON data received'}), 400
            
        action = data.get('action')
        print(f"DEBUG: Action received: {action}")
        
        if action not in ['approve', 'reject']:
            return jsonify({'success': False, 'message': 'Invalid action'}), 400
            
        # Load database
        with open(DATABASE_FILE, 'r+') as f:
            try:
                db_data = json.load(f)
                individual_found = False
                individual_data = None
                
                print(f"DEBUG: Looking for individual: {individual_id}")
                print(f"DEBUG: Total individuals: {len(db_data.get('individuals', []))}")
                
                # Find individual by individual_id
                for i, individual in enumerate(db_data.get('individuals', [])):
                    if individual.get('individual_id') == individual_id:
                        individual_found = True
                        individual_data = individual.copy()
                        print(f"DEBUG: Found individual at index {i}: {individual.get('individual_id')}")
                        
                        # Update payment verification status
                        db_data['individuals'][i]['payment_verified'] = (action == 'approve')
                        db_data['individuals'][i]['payment_status'] = 'approved' if action == 'approve' else 'rejected'
                        db_data['individuals'][i]['payment_review_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        db_data['individuals'][i]['payment_review_by'] = session.get('admin_id', 'unknown')
                        break
                
                if not individual_found:
                    print(f"DEBUG: Individual not found: {individual_id}")
                    return jsonify({
                        'success': False, 
                        'message': f'Individual not found: {individual_id}'
                    }), 404
                
                print(f"DEBUG: Successfully updated individual: {individual_id}")
                
                # Save changes
                f.seek(0)
                json.dump(db_data, f, indent=4)
                f.truncate()
                
                # Send verification email if payment was approved
                if action == 'approve' and individual_data and individual_data.get('email'):
                    try:
                        threading.Thread(
                            target=send_payment_verification_email_individual,
                            args=(individual_data['email'], individual_data)
                        ).start()
                        print(f"✅ Payment verification email queued for: {individual_data['email']}")
                    except Exception as email_error:
                        print(f"❌ Failed to queue verification email: {email_error}")
                
                return jsonify({
                    'success': True,
                    'message': f'Receipt {action}d successfully',
                    'new_status': action == 'approve'
                })
                
            except json.JSONDecodeError as e:
                print(f"DEBUG: JSON decode error: {e}")
                return jsonify({
                    'success': False,
                    'message': 'Database error',
                    'error': str(e)
                }), 500
                
    except Exception as e:
        print(f"DEBUG: General error: {e}")
        return jsonify({
            'success': False,
            'message': 'Server error',
            'error': str(e)
        }), 500
def send_payment_verification_email_individual(recipient_email, individual_data):
    """
    Send payment verification email to individual participant
    """
    def send_email():
        with app.app_context():
            try:
                # Load homepage config for event details
                try:
                    with open(HOMEPAGE_CONFIG_FILE, 'r') as f:
                        homepage_config = json.load(f)
                except:
                    homepage_config = {
                        'hero_title': 'Freshers Fiesta 2025',
                        'event_date': 'November 09, 2025',
                        'event_location': 'SPHN GROUNDS'
                    }

                subject = f"Payment Verified - {individual_data['name']}"
                
                # HTML email content
                html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body {{
            font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #444;
            max-width: 600px;
            margin: 0 auto;
            padding: 0;
            background-color: #f9f9f9;
        }}
        .email-container {{
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            margin: 20px auto;
        }}
        .email-header {{
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
            padding: 30px 20px;
            text-align: center;
            color: white;
        }}
        .email-title {{
            font-size: 28px;
            font-weight: 700;
            margin: 10px 0;
            color: white;
            letter-spacing: 1px;
        }}
        .email-subtitle {{
            font-size: 16px;
            opacity: 0.9;
        }}
        .email-body {{
            padding: 30px;
        }}
        .verification-badge {{
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin: 20px 0;
        }}
        .info-section {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #3498db;
        }}
        .payment-details {{
            background-color: #e8f5e8;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #27ae60;
        }}
        .developer-info {{
            background-color: #e8f4fd;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
        }}
        .email-footer {{
            background-color: #f5f7fa;
            padding: 25px;
            text-align: center;
            border-top: 1px solid #eaeaea;
        }}
        .contact-links {{
            margin: 20px 0;
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 15px;
        }}
        .contact-links a {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            color: #3498db;
            text-decoration: none;
            font-weight: 500;
            padding: 8px 12px;
            border-radius: 6px;
            background-color: rgba(52, 152, 219, 0.1);
        }}
        .copyright {{
            font-size: 13px;
            color: #7f8c8d;
            margin-top: 20px;
        }}
        @media only screen and (max-width: 600px) {{
            .email-title {{
                font-size: 24px;
            }}
            .email-body {{
                padding: 20px;
            }}
            .contact-links {{
                flex-direction: column;
                gap: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="email-header">
            <div class="email-title">PAYMENT VERIFIED ✅</div>
            <div class="email-subtitle">Your registration is now complete!</div>
        </div>
        
        <div class="email-body">
            <div class="verification-badge">
                <h3 style="margin: 0 0 10px 0;">🎉 Payment Successfully Verified!</h3>
                <p style="margin: 0; opacity: 0.9;">Your registration for Freshers Fiesta 2025 is now confirmed</p>
            </div>
            
            <div class="info-section">
                <h4 style="margin: 0 0 15px 0; color: #1e3c72;">Participant Information</h4>
                <p><strong>Name:</strong> {individual_data['name']}</p>
                <p><strong>Registration ID:</strong> {individual_data['individual_id']}</p>
                <p><strong>Email:</strong> {individual_data['email']}</p>
                <p><strong>College:</strong> {individual_data['college']}</p>
                <p><strong>Branch:</strong> {individual_data['branch']}</p>
                <p><strong>Year:</strong> {individual_data['year']}</p>
            </div>
            
            <div class="payment-details">
                <h4 style="margin: 0 0 15px 0; color: #27ae60;">Payment Details</h4>
                <p><strong>Payment Method:</strong> {individual_data.get('payment_method', 'N/A').title()}</p>
                <p><strong>Amount Paid:</strong> ₹{individual_data.get('registration_fee', 'N/A')}</p>
                <p><strong>Payment Date:</strong> {individual_data.get('payment_date', 'N/A')}</p>
                <p><strong>Verification Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Status:</strong> <span style="color: #27ae60; font-weight: bold;">VERIFIED ✅</span></p>
            </div>
            
            <div style="background-color: #e2f0fd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3498db;">
                <h4 style="margin: 0 0 10px 0; color: #0d6efd;">Next Steps</h4>
                <ul style="margin: 0; padding-left: 20px; color: #0d6efd;">
                    <li>Your registration is now complete and confirmed</li>
                    <li>You will receive event updates as the date approaches</li>
                    <li>Check your email for schedule information</li>
                    <li>Follow our social media for announcements</li>
                    <li>Save your registration ID for event check-in</li>
                </ul>
            </div>
            
            <div class="developer-info">
                <h4 style="margin: 0 0 10px 0; color: #1e3c72;">🛠️ Technical Support</h4>
                <p style="margin: 0; color: #1e3c72;">
                    <strong>Smart N Light Innovations</strong><br>
                    24/7 Technical Support Available
                </p>
                <div class="contact-links">
                    <a href="https://smartnlightinnovation.netlify.app" target="_blank">
                        <i class="fas fa-globe"></i> Visit Website
                    </a>
                    <a href="tel:+919059160424">
                        <i class="fas fa-phone"></i> +91 9059160424
                    </a>
                    <a href="mailto:smartnlightinnovations@gmail.com">
                        <i class="fas fa-envelope"></i> Email Support
                    </a>
                </div>
            </div>
        </div>
        
        <div class="email-footer">
            <h4 style="margin: 0 0 15px 0; color: #1e3c72;">Smart N Light Innovations</h4>
            
            <div class="contact-links">
                <a href="mailto:smartnlightinnovations@gmail.com">
                    <i class="fas fa-envelope"></i> Email Us
                </a>
                <a href="tel:+919059160424">
                    <i class="fas fa-phone"></i> Call Support
                </a>
                <a href="https://smartnlightinnovation.netlify.app" target="_blank">
                    <i class="fas fa-globe"></i> Our Website
                </a>
            </div>
            
            <div class="copyright">
                &copy; {datetime.now().year} Smart N Light Innovations. All rights reserved.
            </div>
        </div>
    </div>
</body>
</html>
                """
                
                # Plain text version
                text = f"""
PAYMENT VERIFIED - REGISTRATION CONFIRMED

Dear {individual_data['name']},

We are pleased to inform you that your payment has been verified and your registration for Freshers Fiesta 2025 is now complete!

PARTICIPANT INFORMATION:
Name: {individual_data['name']}
Registration ID: {individual_data['individual_id']}
Email: {individual_data['email']}
College: {individual_data['college']}
Branch: {individual_data['branch']}
Year: {individual_data['year']}

PAYMENT DETAILS:
Payment Method: {individual_data.get('payment_method', 'N/A').title()}
Amount Paid: ₹{individual_data.get('registration_fee', 'N/A')}
Payment Date: {individual_data.get('payment_date', 'N/A')}
Verification Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: VERIFIED ✅

NEXT STEPS:
- Your registration is now complete and confirmed
- You will receive event updates as the date approaches
- Check your email for schedule information
- Follow our social media for announcements
- Save your registration ID for event check-in

EVENT DETAILS:
Event: Freshers Fiesta 2025
Date: November 09, 2025
Location: SPHN GROUNDS

TECHNICAL SUPPORT:
Smart N Light Innovations
24/7 Technical Support Available
Website: https://smartnlightinnovation.netlify.app
Phone: +91 9059160424
Email: smartnlightinnovations@gmail.com

Thank you for completing your registration!

Best regards,
Smart N Light Innovations Team

© {datetime.now().year} Smart N Light Innovations. All rights reserved.
                """
                
                # Create message
                msg = Message(subject, recipients=[recipient_email])
                msg.body = text
                msg.html = html
                
                # Send email
                mail.send(msg)
                print(f"✅ Payment verification email sent successfully to: {recipient_email}")
                return True
                
            except Exception as e:
                print(f"❌ Failed to send payment verification email to {recipient_email}: {e}")
                return False
    
    # Start the email sending in a background thread
    threading.Thread(target=send_email).start()
    return True

# Add registration control route
@app.route('/admin/registration-control', methods=['GET', 'POST'])
def registration_control():
    """Admin page to control registration status"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    # Registration control file
    REGISTRATION_CONTROL_FILE = 'data/registration_control.json'
    
    # Default settings
    default_settings = {
        'registration_open': True,
        'registration_message': 'Registration is currently closed. Please check back later.',
        'closed_title': 'Registration Closed',
        'closed_subtitle': 'Thank you for your interest in Freshers Fiesta 2025',
        'show_countdown': True,
        'countdown_date': '2025-11-09 00:00:00'
    }
    
    if request.method == 'POST':
        try:
            # Get form data
            registration_open = request.form.get('registration_open') == 'on'
            registration_message = request.form.get('registration_message', '').strip()
            closed_title = request.form.get('closed_title', '').strip()
            closed_subtitle = request.form.get('closed_subtitle', '').strip()
            show_countdown = request.form.get('show_countdown') == 'on'
            countdown_date = request.form.get('countdown_date', '').strip()
            
            # Update settings
            settings = {
                'registration_open': registration_open,
                'registration_message': registration_message,
                'closed_title': closed_title,
                'closed_subtitle': closed_subtitle,
                'show_countdown': show_countdown,
                'countdown_date': countdown_date,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_by': session.get('admin_id', 'unknown')
            }
            
            # Save settings
            with open(REGISTRATION_CONTROL_FILE, 'w') as f:
                json.dump(settings, f, indent=4)
            
            flash('Registration settings updated successfully!', 'success')
            
        except Exception as e:
            flash(f'Error updating settings: {str(e)}', 'error')
    
    # Load current settings
    try:
        with open(REGISTRATION_CONTROL_FILE, 'r') as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = default_settings
        # Save default settings
        with open(REGISTRATION_CONTROL_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    
    return render_template('registration_control.html', settings=settings)

# Add this function to check registration status
def is_registration_open():
    """Check if registration is currently open"""
    REGISTRATION_CONTROL_FILE = 'data/registration_control.json'
    
    try:
        with open(REGISTRATION_CONTROL_FILE, 'r') as f:
            settings = json.load(f)
        return settings.get('registration_open', True)
    except FileNotFoundError:
        return True  # Default to open if no settings file


@app.route('/admin/receipts')
def view_receipts():
    """View receipts organized by receiver"""
    if not session.get('admin_logged_in') and not session.get('receipt_logged_in'):
        return redirect(url_for('admin_login'))
    
    receivers = {}
    
    try:
        # Define receiver information
        receiver_info = {
            
            'Laxmi_Nivas': {'display_name': 'Laxmi Nivas', 'folder_name': 'Laxmi_Nivas'},
            
            'Govardhini_Reddy': {'display_name': 'Govardhini Reddy', 'folder_name': 'Govardhini_Reddy'},
            'Sheshank': {'display_name': 'Sheshank', 'folder_name': 'Sheshank'},
            'Raghava': {'display_name': 'Raghava', 'folder_name': 'Raghava'}
        }
        
        # Scan receipts directory for each receiver
        receipts_base_dir = os.path.join(app.root_path, 'static', 'receipts')
        
        for receiver_key, info in receiver_info.items():
            receiver_folder = info['folder_name']
            receiver_dir = os.path.join(receipts_base_dir, receiver_folder)
            
            receipt_count = 0
            latest_receipt = None
            
            if os.path.exists(receiver_dir):
                # Count PDF files in the receiver's directory
                pdf_files = [f for f in os.listdir(receiver_dir) if f.endswith('.pdf')]
                receipt_count = len(pdf_files)
                
                # Get the latest receipt by modification time
                if pdf_files:
                    pdf_files_with_time = []
                    for pdf_file in pdf_files:
                        file_path = os.path.join(receiver_dir, pdf_file)
                        mod_time = os.path.getmtime(file_path)
                        pdf_files_with_time.append((pdf_file, mod_time))
                    
                    # Sort by modification time (newest first)
                    pdf_files_with_time.sort(key=lambda x: x[1], reverse=True)
                    latest_receipt = pdf_files_with_time[0][0] if pdf_files_with_time else None
            
            # Also count receipts from database for this receiver
            with open(DATABASE_FILE, 'r') as f:
                data = json.load(f)
                
            db_receipt_count = 0
            for individual in data.get('individuals', []):
                if (individual.get('payment_method') == 'cash' and 
                    individual.get('cash_receiver_name') == info['display_name'].split(' (')[0] and
                    individual.get('cash_receipt_photo')):
                    db_receipt_count += 1
            
            # Use the higher count between file system and database
            total_receipts = max(receipt_count, db_receipt_count)
            
            receivers[receiver_key] = {
                'display_name': info['display_name'],
                'folder_name': info['folder_name'],
                'receipt_count': total_receipts,
                'latest_receipt': latest_receipt
            }
        
        # Sort receivers by receipt count (highest first)
        receivers = dict(sorted(receivers.items(), key=lambda x: x[1]['receipt_count'], reverse=True))
                
    except Exception as e:
        print(f"Error reading receipts: {str(e)}")
        flash('Error loading receipts', 'error')
        receivers = {}
    
    return render_template('view_receipts.html', receivers=receivers)

@app.route('/admin/receipts/<receiver_name>')
def view_receiver_receipts(receiver_name):
    """View all receipts for a specific receiver"""
    if not session.get('admin_logged_in') and not session.get('receipt_logged_in'):
        return redirect(url_for('admin_login'))
    
    receipts = []
    
    try:
        # Map folder names to display names
        receiver_display_names = {
            
            'Laxmi_Nivas': 'Laxmi Nivas',
            
            'Govardhini_Reddy': 'Govardhini Reddy',
            'Sheshank': 'Sheshank',
            'Raghava': 'Raghava'
            
        }
        
        display_name = receiver_display_names.get(receiver_name, receiver_name.replace('_', ' '))
        
        # Get receipts from file system
        receipts_base_dir = os.path.join(app.root_path, 'static', 'receipts')
        receiver_dir = os.path.join(receipts_base_dir, receiver_name)
        
        if os.path.exists(receiver_dir):
            for filename in os.listdir(receiver_dir):
                if filename.endswith('.pdf'):
                    file_path = os.path.join(receiver_dir, filename)
                    stat_info = os.stat(file_path)
                    
                    receipt_info = {
                        'filename': filename,
                        'filepath': f"/static/receipts/{receiver_name}/{filename}",
                        'receipt_no': filename.replace('receipt_', '').replace('.pdf', ''),
                        'size': stat_info.st_size,
                        'modified_time': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'type': 'file_system'
                    }
                    receipts.append(receipt_info)
        
        # Also get receipts from database for this receiver
        with open(DATABASE_FILE, 'r') as f:
            data = json.load(f)
            
        for individual in data.get('individuals', []):
            if (individual.get('payment_method') == 'cash' and 
                individual.get('cash_receiver_name') == display_name.split(' (')[0] and
                individual.get('cash_receipt_photo')):
                
                receipt_filename = individual['cash_receipt_photo']
                
                # Check if this receipt already exists in our list
                existing_receipt = next((r for r in receipts if r['filename'] == receipt_filename), None)
                
                if not existing_receipt:
                    receipt_info = {
                        'filename': receipt_filename,
                        'filepath': f"/view_document/{receipt_filename}",
                        'receipt_no': individual.get('receipt_number', 'N/A'),
                        'size': 'N/A',
                        'modified_time': individual.get('payment_date', 'N/A'),
                        'individual_id': individual['individual_id'],
                        'name': individual['name'],
                        'email': individual['email'],
                        'amount': individual.get('registration_fee', 'N/A'),
                        'year': individual.get('year', 'N/A'),
                        'branch': individual.get('branch', 'N/A'),
                        'type': 'database'
                    }
                    receipts.append(receipt_info)
        
        # Sort by receipt number (extract numeric part for sorting)
        def get_receipt_number(receipt):
            receipt_no = receipt['receipt_no']
            # Extract numeric part from receipt number
            numbers = ''.join(filter(str.isdigit, receipt_no))
            return int(numbers) if numbers else 0
        
        receipts.sort(key=get_receipt_number, reverse=True)
        
    except Exception as e:
        print(f"Error reading receiver receipts: {str(e)}")
        flash('Error loading receipts', 'error')
    
    return render_template('receiver_receipts.html', 
                         receiver_name=display_name,
                         receipts=receipts)

@app.route('/view_receipt_file/<path:filename>')
def view_receipt_file(filename):
    """Serve receipt files"""
    if not session.get('admin_logged_in') and not session.get('receipt_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        # Security check
        filename = secure_filename(filename)
        if not filename:
            return "Invalid filename", 400
        
        # Build file path
        file_path = os.path.join(app.root_path, 'static', 'receipts', filename)
        
        # Check if file exists directly in receipts folder
        if not os.path.exists(file_path):
            # Check in receiver subfolders
            receipts_base_dir = os.path.join(app.root_path, 'static', 'receipts')
            for receiver_folder in os.listdir(receipts_base_dir):
                receiver_path = os.path.join(receipts_base_dir, receiver_folder, filename)
                if os.path.exists(receiver_path):
                    file_path = receiver_path
                    break
            else:
                return "File not found", 404
        
        return send_file(file_path, as_attachment=False)
    
    except Exception as e:
        print(f"Error serving receipt file: {str(e)}")
        return f"Server error: {str(e)}", 500
    
@app.route('/admin/excel-upload')
def admin_excel_upload():
    """Admin page for Excel upload"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('admin_excel_upload.html')

@app.route('/api/upload-student-data', methods=['POST'])
def upload_student_data():
    """API endpoint to upload student data from Excel"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        students = data.get('students', [])
        
        if not students:
            return jsonify({'success': False, 'message': 'No student data provided'}), 400
        
        # Load existing student data
        if os.path.exists(STUDENT_MASTER_FILE):
            with open(STUDENT_MASTER_FILE, 'r') as f:
                existing_data = json.load(f)
        else:
            existing_data = {'students': []}
        
        # Create a set of existing roll numbers for quick lookup
        existing_roll_numbers = {student['roll_number'] for student in existing_data['students']}
        
        new_students = []
        updated_count = 0
        new_count = 0
        
        for student in students:
            roll_number = str(student.get('Roll Number', '')).strip().upper()
            name = str(student.get('Name', '')).strip()
            year = str(student.get('Year', '')).strip()
            branch = str(student.get('Branch', '')).strip()
            section = str(student.get('Section', '')).strip() if student.get('Section') else None
            
            if not all([roll_number, name, year, branch]):
                continue  # Skip incomplete records
            
            student_data = {
                'roll_number': roll_number,
                'name': name,
                'year': year,
                'branch': branch,
                'section': section,
                'added_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'added_by': session.get('admin_id', 'unknown')
            }
            
            if roll_number in existing_roll_numbers:
                # Update existing student
                for idx, existing_student in enumerate(existing_data['students']):
                    if existing_student['roll_number'] == roll_number:
                        existing_data['students'][idx] = student_data
                        updated_count += 1
                        break
            else:
                # Add new student
                existing_data['students'].append(student_data)
                new_count += 1
        
        # Save updated data
        with open(STUDENT_MASTER_FILE, 'w') as f:
            json.dump(existing_data, f, indent=4)
        
        message = f"Successfully uploaded {len(students)} records. New: {new_count}, Updated: {updated_count}"
        return jsonify({
            'success': True, 
            'message': message,
            'new_count': new_count,
            'updated_count': updated_count
        })
        
    except Exception as e:
        print(f"Error uploading student data: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/student-stats')
def get_student_stats():
    """Get student database statistics"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        # Student master data stats
        total_students = 0
        last_upload = None
        
        if os.path.exists(STUDENT_MASTER_FILE):
            with open(STUDENT_MASTER_FILE, 'r') as f:
                student_data = json.load(f)
                total_students = len(student_data.get('students', []))
                if total_students > 0:
                    # Get the latest added date
                    dates = [s.get('added_date') for s in student_data['students'] if s.get('added_date')]
                    if dates:
                        last_upload = max(dates)
                        # Format the date for display
                        try:
                            last_upload_dt = datetime.strptime(last_upload, '%Y-%m-%d %H:%M:%S')
                            last_upload = last_upload_dt.strftime('%b %d, %Y')
                        except:
                            pass  # Keep original format if parsing fails

        # Get registered participants count from main database
        registered_count = 0
        if os.path.exists(DATABASE_FILE):
            with open(DATABASE_FILE, 'r') as f:
                main_data = json.load(f)
                registered_count = len(main_data.get('individuals', []))
                # Also count team members if needed
                for team in main_data.get('teams', []):
                    registered_count += len(team.get('members', []))

        return jsonify({
            'success': True,
            'total_students': total_students,
            'last_upload': last_upload or 'Never',
            'registered_count': registered_count
        })
        
    except Exception as e:
        print(f"Error getting student stats: {str(e)}")
        return jsonify({
            'success': False, 
            'message': str(e),
            'total_students': 0,
            'last_upload': 'Error',
            'registered_count': 0
        })

@app.route('/registration-closed')
def registration_closed():
    """Display registration closed page"""
    REGISTRATION_CONTROL_FILE = 'data/registration_control.json'
    
    try:
        with open(REGISTRATION_CONTROL_FILE, 'r') as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = {
            'closed_title': 'Registration Closed',
            'closed_subtitle': 'Thank you for your interest in Freshers Fiesta 2025',
            'registration_message': 'Registration is currently closed. Please check back later.',
            'show_countdown': True,
            'countdown_date': '2025-11-09 00:00:00'
        }
    
    return render_template('registration_closed.html', settings=settings)
 
@app.route('/register-enhanced', methods=['GET', 'POST'])
def register_enhanced():
    """Enhanced registration page with roll number verification"""
    # Load hackathon config
    if not is_registration_open():
        return redirect(url_for('registration_closed'))
    try:
        with open(HACKATHON_CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except:
        config = {'payment_required': True}
    
    if request.method == 'POST':
        # Get form data
        roll_number = request.form.get('verified_roll_number', '').strip().upper()
        name = request.form.get('name', '').strip()
        year = request.form.get('year', '').strip()
        branch = request.form.get('branch', '').strip()
        section = request.form.get('section', '').strip()  # Get section from form
        gender = request.form.get('gender', '').strip()
        email = request.form.get('email', '').strip().lower()
        contact = request.form.get('contact_number', '').strip()
        
        # Validate required fields
        errors = {}
        
        if not roll_number:
            errors['roll_number'] = 'Roll number verification is required'
        if not name:
            errors['name'] = 'Name is required'
        if not year:
            errors['year'] = 'Year is required'
        if not branch:
            errors['branch'] = 'Branch is required'
        if not gender:
            errors['gender'] = 'Gender is required'
        elif gender not in ['Male', 'Female']:
            errors['gender'] = 'Please select a valid gender'
        if not email:
            errors['email'] = 'Email is required'
        elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors['email'] = 'Please enter a valid email address'
        if not contact:
            errors['contact'] = 'Contact number is required'

        if os.path.exists(DATABASE_FILE):
            with open(DATABASE_FILE, 'r') as f:
                main_data = json.load(f)
                # Check individuals
                for individual in main_data.get('individuals', []):
                    if individual.get('email') == email:
                        errors['email'] = 'Email already registered'
                    if individual.get('contact_number') == contact:
                        errors['contact'] = 'Contact number already registered'
                # Check team members
                for team in main_data.get('teams', []):
                    for member in team.get('members', []):
                        if member.get('email') == email:
                            errors['email'] = 'Email already registered'
                        if member.get('contact') == contact:
                            errors['contact'] = 'Contact number already registered'
        
        if errors:
            return render_template('register_enhanced.html',
                errors=errors,
                form_data=request.form
            )
        
        # Generate individual ID
        with team_id_lock:
            try:
                # Load main database
                with open(DATABASE_FILE, 'r+') as f:
                    try:
                        data = json.load(f)
                        if 'individuals' not in data:
                            data['individuals'] = []
                        
                        # Get the next individual ID
                        individual_id = f"IND_{len(data['individuals']) + 1:04d}"
                        
                        # Create registration data
                        registration_data = {
                            'individual_id': individual_id,
                            'roll_number': roll_number,
                            'name': name,
                            'year': year,
                            'branch': branch,
                            'section': section,  # Include section
                            'gender': gender,
                            'email': email,
                            'contact_number': contact,
                            'registration_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'payment_verified': False,
                            'payment_method': None,
                            'payment_date': None,
                            'registration_fee': 500 if year == '1st' else 600,
                            'college': 'Sphoorthy Engineering College'  # Add default college
                        }
                        
                        data['individuals'].append(registration_data)
                        f.seek(0)
                        json.dump(data, f, indent=4)
                        f.truncate()
                        
                        # Store in session for payment page
                        session['individual_data'] = registration_data
                        session['registration_fee'] = registration_data['registration_fee']
                        
                        # Redirect to payment page
                        return redirect(url_for('payment'))
                        
                    except json.JSONDecodeError:
                        # Handle corrupt file - create new database
                        data = {'individuals': []}
                        individual_id = "IND_0001"
                        registration_data = {
                            'individual_id': individual_id,
                            'roll_number': roll_number,
                            'name': name,
                            'year': year,
                            'branch': branch,
                            'section': section,  # Include section
                            'gender': gender,
                            'email': email,
                            'contact_number': contact,
                            'registration_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'payment_verified': False,
                            'payment_method': None,
                            'payment_date': None,
                            'registration_fee': 500 if year == '1st' else 600,
                            'college': 'Sphoorthy Engineering College'
                        }
                        
                        data['individuals'].append(registration_data)
                        with open(DATABASE_FILE, 'w') as f:
                            json.dump(data, f, indent=4)
                        
                        session['individual_data'] = registration_data
                        session['registration_fee'] = registration_data['registration_fee']
                        return redirect(url_for('payment'))
                        
            except Exception as e:
                flash('Error creating registration. Please try again.', 'error')
                print(f"Error in enhanced registration: {str(e)}")
                return redirect(url_for('register_enhanced'))
    
    return render_template('register_enhanced.html')
@app.route('/api/verify-roll-number', methods=['POST'])
def verify_roll_number():
    """API endpoint to verify roll number - with context-specific behavior"""
    try:
        data = request.get_json()
        roll_number = data.get('roll_number', '').strip().upper()
        context = data.get('context', 'receipt')  # Default to 'receipt' for receipt generation
        
        if not roll_number:
            return jsonify({'success': False, 'message': 'Roll number is required'}), 400
        
        # Check if roll number exists in student master data
        if not os.path.exists(STUDENT_MASTER_FILE):
            return jsonify({'success': False, 'message': 'Student database not available'}), 404
        
        with open(STUDENT_MASTER_FILE, 'r') as f:
            student_data = json.load(f)
        
        # Find student by roll number
        student = next((s for s in student_data.get('students', []) 
                       if s['roll_number'] == roll_number), None)
        
        if not student:
            return jsonify({'success': False, 'message': 'Roll number not found in database'}), 404
        
        # Check if this roll number is already registered
        is_registered = False
        registration_info = {}
        
        if os.path.exists(DATABASE_FILE):
            with open(DATABASE_FILE, 'r') as f:
                main_data = json.load(f)
                
                # Check individuals
                existing_individual = next((ind for ind in main_data.get('individuals', []) 
                                         if ind.get('roll_number') == roll_number), None)
                
                # Check team members
                existing_team_member = None
                for team in main_data.get('teams', []):
                    for member in team.get('members', []):
                        if member.get('rollno') == roll_number:
                            existing_team_member = member
                            break
                    if existing_team_member:
                        break
                
                if existing_individual or existing_team_member:
                    is_registered = True
                    
                    if existing_individual:
                        registration_info = {
                            'type': 'individual',
                            'name': existing_individual.get('name'),
                            'email': existing_individual.get('email'),
                            'contact': existing_individual.get('contact_number'),
                            'payment_status': 'verified' if existing_individual.get('payment_verified') else 'pending'
                        }
                    elif existing_team_member:
                        registration_info = {
                            'type': 'team_member',
                            'name': existing_team_member.get('name'),
                            'email': existing_team_member.get('email'),
                            'contact': existing_team_member.get('contact'),
                            'payment_status': 'team_member'
                        }
        
        # Different behavior based on context
        # For receipt generation, allow both registered and unregistered students
        if context == 'registration' and is_registered:
            return jsonify({
                'success': False, 
                'message': 'This roll number is already registered. Please use a different roll number.',
                'is_registered': True
            }), 400
        
        # For receipt context, allow both registered and unregistered students
        return jsonify({
            'success': True,
            'student': {
                'name': student['name'],
                'year': student['year'],
                'branch': student['branch'],
                'section': student.get('section', 'N/A')  # Ensure section is included
            },
            'is_registered': is_registered,
            'registration_info': registration_info if is_registered else None
        })
        
    except Exception as e:
        print(f"Error verifying roll number: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'}), 500
    
@app.route('/admin')
def admin_dashboard():
    """Admin dashboard route"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    # Get basic statistics
    stats = {}
    try:
        # Student master data count
        if os.path.exists(STUDENT_MASTER_FILE):
            with open(STUDENT_MASTER_FILE, 'r') as f:
                student_data = json.load(f)
                stats['total_students'] = len(student_data.get('students', []))
        
        # Total participants from main database only
        if os.path.exists(DATABASE_FILE):
            with open(DATABASE_FILE, 'r') as f:
                main_data = json.load(f)
                stats['total_participants'] = len(main_data.get('individuals', [])) + len(main_data.get('teams', []))
                
    except Exception as e:
        print(f"Error loading stats: {str(e)}")
        stats = {'total_students': 0, 'total_participants': 0}
    
    return render_template('admin_dashboard.html', stats=stats)


def get_teams_from_database():
    """Get all teams from database with error handling"""
    try:
        with open(DATABASE_FILE, 'r') as f:
            data = json.load(f)
            return data.get('teams', [])
    except Exception as e:
        print(f"Error reading database: {str(e)}")
        return []

def get_team_name(team_id):
    """Get team name from database"""
    teams = get_teams_from_database()
    team = next((t for t in teams if t['team_id'] == team_id), None)
    return team['team_name'] if team else "Unknown Team"

def get_member_name(team_id, member_id):
    """Get member name from database"""
    teams = get_teams_from_database()
    team = next((t for t in teams if t['team_id'] == team_id), None)
    if team:
        member = next((m for m in team['members'] if m['id'] == member_id), None)
        return member['name'] if member else "Unknown Member"
    return "Unknown Member"

def get_member_gender(team_id, member_id):
    """Get member gender from database"""
    teams = get_teams_from_database()
    team = next((t for t in teams if t['team_id'] == team_id), None)
    if team:
        member = next((m for m in team['members'] if m['id'] == member_id), None)
        return member.get('gender', 'Unknown') if member else 'Unknown'
    return 'Unknown'

def get_member_contact(team_id, member_id):
    """Get member contact from database"""
    teams = get_teams_from_database()
    team = next((t for t in teams if t['team_id'] == team_id), None)
    if team:
        member = next((m for m in team['members'] if m['id'] == member_id), None)
        return member.get('contact', 'Unknown') if member else 'Unknown'
    return 'Unknown'

def find_receipt_file(filename):
    """Find receipt file in various locations"""
    # Check uploads folder
    uploads_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(uploads_path):
        return uploads_path
    
    # Check receipts folder
    receipts_path = os.path.join(app.root_path, 'static', 'receipts', filename)
    if os.path.exists(receipts_path):
        return receipts_path
    
    # Check receiver subfolders
    receipts_base_dir = os.path.join(app.root_path, 'static', 'receipts')
    if os.path.exists(receipts_base_dir):
        for receiver_folder in os.listdir(receipts_base_dir):
            receiver_path = os.path.join(receipts_base_dir, receiver_folder, filename)
            if os.path.exists(receiver_path):
                return receiver_path
    
    return None

def find_team_by_id(team_id):
    """Find and return a team dict by its ID from the database."""
    if not team_id:
        return None
    if not os.path.exists(DATABASE_FILE):
        return None
    try:
        with open(DATABASE_FILE, 'r') as f:
            data = json.load(f)
            for team in data.get('teams', []):
                if team.get('team_id') == team_id:
                    class TeamObj(dict):
                        def __getattr__(self, name):
                            return self[name] if name in self else None
                        def __setattr__(self, name, value):
                            self[name] = value
                    return TeamObj(team)
    except Exception as e:
        print(f"Error in find_team_by_id: {e}")
    return None

def save_team(team):
    """Update the team in the database file."""
    if not team or not team.get('team_id'):
        return False
    if not os.path.exists(DATABASE_FILE):
        return False
    try:
        with open(DATABASE_FILE, 'r+') as f:
            data = json.load(f)
            teams = data.get('teams', [])
            for idx, t in enumerate(teams):
                if t.get('team_id') == team['team_id']:
                    teams[idx] = dict(team)
                    break
            else:
                teams.append(dict(team))
            data['teams'] = teams
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
        return True
    except Exception as e:
        print(f"Error in save_team: {e}")
        return False


def create_receipt_pdf(data):
    """Generate a professional PDF receipt with clean styling and save in receiver-specific folder."""
    try:
        # Create receiver-specific folder path
        receiver_name = data['receiver_name'].replace(' ', '_')
        receipts_base_dir = os.path.join(app.root_path, 'static', 'receipts')
        receiver_dir = os.path.join(receipts_base_dir, receiver_name)
        
        # Ensure directories exist
        os.makedirs(receiver_dir, exist_ok=True)

        # Create safe filename
        filename = f"receipt_{data['receipt_no']}.pdf"
        pdf_path = os.path.join(receiver_dir, filename)

        # Create PDF document with smaller margins
        doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                              rightMargin=36, leftMargin=36,
                              topMargin=36, bottomMargin=36)
        # Get default styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        styles.add(ParagraphStyle(name='ReceiptTitle', 
                                fontSize=16, 
                                leading=18,
                                alignment=TA_CENTER,
                                spaceAfter=12,
                                fontName='Helvetica-Bold'))
        
        styles.add(ParagraphStyle(name='ReceiptHeader', 
                                fontSize=10, 
                                leading=12,
                                alignment=TA_LEFT,
                                spaceAfter=6))
        
        styles.add(ParagraphStyle(name='ReceiptBold', 
                                fontSize=10, 
                                leading=12,
                                alignment=TA_LEFT,
                                spaceAfter=6,
                                fontName='Helvetica-Bold'))
        
        styles.add(ParagraphStyle(name='SectionHeader', 
                                fontSize=12, 
                                leading=14,
                                alignment=TA_LEFT,
                                spaceAfter=8,
                                fontName='Helvetica-Bold',
                                textColor=colors.HexColor('#333333')))
        
        styles.add(ParagraphStyle(name='ItemLabel', 
                                fontSize=10, 
                                leading=12,
                                alignment=TA_LEFT,
                                spaceAfter=2))
        
        styles.add(ParagraphStyle(name='ItemValue', 
                                fontSize=10, 
                                leading=12,
                                alignment=TA_RIGHT,
                                spaceAfter=2))
        
        styles.add(ParagraphStyle(name='TotalLabel', 
                                fontSize=10, 
                                leading=12,
                                alignment=TA_LEFT,
                                spaceAfter=2,
                                fontName='Helvetica-Bold'))
        
        styles.add(ParagraphStyle(name='TotalValue', 
                                fontSize=10, 
                                leading=12,
                                alignment=TA_RIGHT,
                                spaceAfter=2,
                                fontName='Helvetica-Bold'))
        
        styles.add(ParagraphStyle(name='FooterText', 
                                fontSize=8, 
                                leading=10,
                                alignment=TA_CENTER,
                                spaceAfter=6,
                                textColor=colors.HexColor('#666666')))
        
        # Story (content elements)
        story = []
        
        # Title
        story.append(Paragraph("PAYMENT RECEIPT", styles['ReceiptTitle']))
        
        # Receipt number and date
        receipt_info = [
            Paragraph(f"<b>Receipt Number #</b> {data['receipt_no']}", styles['ReceiptHeader']),
            Paragraph(f"<b>Date:</b> {data['timestamp']}", styles['ReceiptHeader'])
        ]
        story.extend(receipt_info)
        story.append(Spacer(1, 12))
        
        # Horizontal line
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#CCCCCC')))
        story.append(Spacer(1, 12))
        
        # Billed By section
        story.append(Paragraph("BILLED BY", styles['SectionHeader']))
        billed_by = [
            Paragraph("<b>SmartnLight Innovations</b>", styles['ReceiptBold']),
            Paragraph("Freshers Fiesta 2025", styles['ReceiptHeader']),
            Paragraph("Email: smartnlightinnovations@gmail.com", styles['ReceiptHeader']),
            Paragraph("Phone: +91 9059160424", styles['ReceiptHeader'])
        ]
        story.extend(billed_by)
        story.append(Spacer(1, 12))
        
        # Horizontal line
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#CCCCCC')))
        story.append(Spacer(1, 12))
        
        # Payer Information
        story.append(Paragraph("PAYER INFORMATION", styles['SectionHeader']))
        payer_info = [
            Paragraph(f"<b>Name:</b> {data['viewer_name']}", styles['ReceiptHeader']),
            Paragraph(f"<b>Email:</b> {data['viewer_email']}", styles['ReceiptHeader']),
            Paragraph(f"<b>Contact:</b> {data['contact_number']}", styles['ReceiptHeader'])
        ]
        story.extend(payer_info)
        story.append(Spacer(1, 12))
        
        # Payment Details
        story.append(Paragraph("PAYMENT DETAILS", styles['SectionHeader']))
        
        # Create payment table
        payment_data = [
            ["1.", "Event Registration Fee", f"Rs. {data['amount']}.00"],
            ["", "Total", f"Rs. {data['amount']}.00"]
        ]
        
        # Calculate column widths (10%, 60%, 30%)
        col_widths = [doc.width*0.1, doc.width*0.6, doc.width*0.3]
        
        payment_table = Table(payment_data, colWidths=col_widths)
        
        # Style the table
        payment_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('LINEABOVE', (1, -1), (-1, -1), 1, colors.HexColor('#333333')),
            ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(payment_table)
        story.append(Spacer(1, 8))
        
        # Total in words
        amount_in_words = num2words(float(data['amount']), lang='en_IN').upper()
        story.append(Paragraph(f"<b>Total (in words):</b> {amount_in_words} RUPEES ONLY", styles['ReceiptHeader']))
        story.append(Spacer(1, 12))
        
        # Tax information
        tax_data = [
            ["", "Amount", f"Rs. {data['amount']}.00"],
            ["", "CGST", "Rs. 0.00"],
            ["", "SGST", "Rs. 0.00"]
        ]
        
        tax_table = Table(tax_data, colWidths=col_widths)
        tax_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ]))
        
        story.append(tax_table)
        story.append(Spacer(1, 12))
        
        # Payment method and receiver's name
        payment_method = [
            Paragraph("<b>Payment Method:</b> Cash", styles['ReceiptHeader']),
            Paragraph(f"<b>Received by:</b> {data['receiver_name']}", styles['ReceiptHeader']),
            Paragraph("<b>Date of Payment:</b> " + data['timestamp'], styles['ReceiptHeader'])
        ]
        story.extend(payment_method)
        story.append(Spacer(1, 20))
        
        # Thank you message
        story.append(Paragraph("Thank you for your payment!", styles['ReceiptBold']))
        story.append(Spacer(1, 8))
        
        # Footer contact
        footer_contact = Paragraph("For any queries, email at <b>smartnlightinnovations@gmail.com</b>, call on <b>+91 9059160424</b>", 
                                 styles['FooterText'])
        story.append(footer_contact)
        
        # Build the PDF
        doc.build(story)

        print(f"✅ Receipt saved to: {pdf_path}")
        return pdf_path

    except Exception as e:
        app.logger.error(f"Error in create_receipt_pdf: {str(e)}")
        raise


def generate_qr_code(data, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)

def send_receipt_email(recipient_email, receipt_data, pdf_path):
    """
    Send a responsive email with the PDF receipt attached.
    """
    with app.app_context():
        try:
            subject = f"Payment Receipt {receipt_data['receipt_no']} - Freshers Fiesta 2025"
            
            # HTML email content
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css">
    <style>
        /* Base styles */
        body {{
            font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #444;
            max-width: 600px;
            margin: 0 auto;
            padding: 0;
            background-color: #f9f9f9;
        }}
        .email-container {{
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            margin: 20px auto;
        }}
        .email-header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 30px 20px;
            text-align: center;
            color: white;
        }}
        .logo-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 30px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        .logo {{
            height: 60px;
            width: auto;
            object-fit: contain;
        }}
        .developer-logo {{
            height: 50px;
            width: auto;
            object-fit: contain;
        }}
        .receipt-title {{
            font-size: 28px;
            font-weight: 700;
            margin: 10px 0;
            color: white;
            letter-spacing: 1px;
        }}
        .receipt-subtitle {{
            font-size: 16px;
            opacity: 0.9;
        }}
        .email-body {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 1px solid #eaeaea;
        }}
        .section:last-child {{
            border-bottom: none;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 15px;
            color: #1e3c72;
            display: flex;
            align-items: center;
        }}
        .section-title:before {{
            content: "";
            display: inline-block;
            width: 6px;
            height: 20px;
            background-color: #3498db;
            margin-right: 10px;
            border-radius: 3px;
        }}
        .info-item {{
            display: flex;
            margin-bottom: 10px;
            font-size: 15px;
        }}
        .info-item strong {{
            min-width: 120px;
            display: inline-block;
            color: #555;
        }}
        .info-value {{
            color: #222;
            font-weight: 500;
        }}
        .amount-highlight {{
            font-size: 22px;
            font-weight: 700;
            color: #27ae60;
        }}
        .contact-person {{
            background-color: #f5f7fa;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #3498db;
        }}
        .contact-person strong {{
            color: #1e3c72;
        }}
        .event-details {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .email-footer {{
            background-color: #f5f7fa;
            padding: 25px;
            text-align: center;
            border-top: 1px solid #eaeaea;
        }}
        .footer-logos {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        .footer-logo {{
            height: 50px;
            width: auto;
        }}
        .developer-section {{
            background-color: #e8f4fd;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
        }}
        .contact-links {{
            margin: 20px 0;
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 15px;
        }}
        .contact-links a {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            color: #3498db;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s ease;
            padding: 8px 12px;
            border-radius: 6px;
            background-color: rgba(52, 152, 219, 0.1);
        }}
        .contact-links a:hover {{
            color: #1e3c72;
            background-color: rgba(52, 152, 219, 0.2);
            transform: translateY(-2px);
        }}
        .copyright {{
            font-size: 13px;
            color: #7f8c8d;
            margin-top: 20px;
        }}
        .thank-you {{
            font-size: 16px;
            color: #555;
            margin: 20px 0;
            line-height: 1.6;
        }}
        
        /* Responsive adjustments */
        @media only screen and (max-width: 600px) {{
            .logo-container {{
                flex-direction: column;
                gap: 15px;
            }}
            .logo {{
                height: 50px;
            }}
            .developer-logo {{
                height: 40px;
            }}
            .receipt-title {{
                font-size: 24px;
            }}
            .email-body {{
                padding: 20px;
            }}
            .section-title {{
                font-size: 16px;
            }}
            .info-item {{
                flex-direction: column;
            }}
            .info-item strong {{
                min-width: auto;
                margin-bottom: 3px;
            }}
            .contact-links {{
                flex-direction: column;
                gap: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="email-header">
            <div class="logo-container">
                <img src="https://i.postimg.cc/YqKYfsQd/snl.png" alt="SmartnLight Innovations" class="logo">
            </div>
            <div class="receipt-title">PAYMENT RECEIPT</div>
            <div class="receipt-subtitle">Official confirmation of your payment</div>
        </div>
        
        <div class="email-body">
            <div class="event-details">
                <div class="section-title">Event Details</div>
                <div class="info-item">
                    <strong>Event:</strong>
                    <span class="info-value">Freshers Fiesta 2025</span>
                </div>
                <div class="info-item">
                    <strong>Date:</strong>
                    <span class="info-value">November 09, 2025</span>
                </div>
                <div class="info-item">
                    <strong>Location:</strong>
                    <span class="info-value">SPHN GROUNDS</span>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">Payer Information</div>
                <div class="info-item">
                    <strong>Name:</strong>
                    <span class="info-value">{receipt_data['viewer_name']}</span>
                </div>
                <div class="info-item">
                    <strong>Email:</strong>
                    <span class="info-value">{receipt_data['viewer_email']}</span>
                </div>
                <div class="info-item">
                    <strong>Contact:</strong>
                    <span class="info-value">{receipt_data['contact_number']}</span>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">Payment Details</div>
                <div class="info-item">
                    <strong>Receipt No:</strong>
                    <span class="info-value">{receipt_data['receipt_no']}</span>
                </div>
                <div class="info-item">
                    <strong>Amount:</strong>
                    <span class="info-value amount-highlight">₹{receipt_data['amount']}</span>
                </div>
                <div class="info-item">
                    <strong>Received by:</strong>
                    <span class="info-value">{receipt_data['receiver_name']}</span>
                </div>
                <div class="info-item">
                    <strong>Date & Time:</strong>
                    <span class="info-value">{receipt_data['timestamp']}</span>
                </div>
            </div>
            
            <div class="developer-section">
                <div class="section-title">Technical Support</div>
                <img src="https://i.postimg.cc/YqKYfsQd/snl.png" alt="SmartnLight Innovations" class="developer-logo">
                <div style="margin: 10px 0;"><strong>SmartnLight Innovations</strong></div>
                <div style="margin-bottom: 15px;">24/7 Technical Support Available</div>
                <div class="contact-links">
                    <a href="https://smartnlightinnovation.netlify.app" target="_blank">
                        <i class="fas fa-globe"></i> Visit Website
                    </a>
                    <a href="tel:+919059160424">
                        <i class="fas fa-phone"></i> +91 9059160424
                    </a>
                    <a href="mailto:smartnlightinnovations@gmail.com">
                        <i class="fas fa-envelope"></i> Email Support
                    </a>
                </div>
            </div>
            
            <div class="thank-you">
                Thank you for your payment for Freshers Fiesta 2025. This is an official receipt for payment received. 
                Please keep this receipt for your records. A copy of your receipt is attached 
                to this email for your convenience.
            </div>
        </div>
        
        <div class="email-footer">
            <div class="footer-logos">
                <img src="https://i.postimg.cc/YqKYfsQd/snl.png" alt="SmartnLight Innovations" class="footer-logo">
            </div>
            
            <h4>SmartnLight Innovations</h4>
            
            <div class="contact-links">
                <a href="mailto:smartnlightinnovations@gmail.com">
                    <i class="fas fa-envelope"></i> Email Us
                </a>
                <a href="tel:+919059160424">
                    <i class="fas fa-phone"></i> Call Support
                </a>
                <a href="https://smartnlightinnovation.netlify.app" target="_blank">
                    <i class="fas fa-globe"></i> Our Website
                </a>
            </div>
            
            <div class="copyright">
                &copy; {datetime.now().year} SmartnLight Innovations. All rights reserved.
            </div>
        </div>
    </div>
</body>
</html>
            """
            
            # Plain text version
            text = f"""
Dear {receipt_data['viewer_name']},

Thank you for your payment for Freshers Fiesta 2025. 
Please find your payment details below and the attached receipt for your records.

EVENT DETAILS
-------------
Event: Freshers Fiesta 2025
Date: November 09, 2025
Location: SPHN GROUNDS

PAYER INFORMATION
-----------------
Name: {receipt_data['viewer_name']}
Email: {receipt_data['viewer_email']}
Contact: {receipt_data['contact_number']}

PAYMENT DETAILS
---------------
Receipt No: {receipt_data['receipt_no']}
Amount: ₹{receipt_data['amount']}
Received by: {receipt_data['receiver_name']}
Date & Time: {receipt_data['timestamp']}

TECHNICAL SUPPORT
-----------------
SmartnLight Innovations
24/7 Technical Support Available
Website: https://smartnlightinnovation.netlify.app
Phone: +91 9059160424
Email: smartnlightinnovations@gmail.com

This is an official receipt for payment received. Please keep this receipt for your records.

Best regards,
SmartnLight Innovations Team
            """
            
            # Create message
            msg = Message(subject, recipients=[recipient_email])
            msg.body = text
            msg.html = html
            
            # Attach PDF
            with open(pdf_path, 'rb') as pdf_file:
                msg.attach(
                    filename=f"Receipt_{receipt_data['receipt_no']}.pdf",
                    content_type='application/pdf',
                    data=pdf_file.read()
                )
            
            # Send email
            mail = app.extensions.get('mail')
            if mail:
                mail.send(msg)
                print(f"✅ Email sent with receipt from: {receipt_data['receiver_name']}")
            else:
                print("Flask-Mail extension not initialized!")
                
        except Exception as e:
            print(f"Failed to send receipt email to {recipient_email}: {e}")
            raise

def log_email(team_id, action, recipient_email, success=True, error=None):
    """Log email sending attempts"""
    try:
        email_logs = []
        if os.path.exists(EMAIL_LOGS_FILE):
            with open(EMAIL_LOGS_FILE, 'r') as f:
                email_logs = json.load(f)
        
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'team_id': team_id,
            'action': action,
            'recipient': recipient_email,
            'success': success,
            'error': error,
            'sent_by': session.get('admin_id', 'unknown')
        }
        
        email_logs.append(log_entry)
        
        with open(EMAIL_LOGS_FILE, 'w') as f:
            json.dump(email_logs, f, indent=4)
    except Exception as e:
        print(f"Failed to log email: {str(e)}")
     
def get_next_receipt_number():
    counter_file = Path(app.root_path) / 'receipt_counter.txt'
    
    try:
        with open(counter_file, 'r') as f:
            last_number = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        last_number = 0
    
    next_number = last_number + 1
    
    with open(counter_file, 'w') as f:
        f.write(str(next_number))
    
    return next_number

# Call initialization when app starts
initialize_files()
@app.route('/test-pdf')
def test_pdf():
    test_data = {
        'viewer_name': 'Test User',
        'viewer_email': 'test@example.com',
        'team_id': 'Test Team',
        'contact_number': '1234567890',
        'receiver_name': 'Test Receiver',
        'amount': '500',
        'receipt_no': 'RC-99999',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    pdf_path = create_receipt_pdf(test_data)
    return send_file(pdf_path, as_attachment=True)

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    # Default configuration
    default_config = {
        'payment_required': True,
        'registration_fee': 500
    }
    
    if request.method == 'POST':
        try:
            # Get form data
            payment_required = request.form.get('payment_required') == 'on'
            registration_fee = int(request.form.get('registration_fee', 500))
            
            # Update configuration
            config = {
                'payment_required': payment_required,
                'registration_fee': registration_fee
            }
            
            # Save to file
            with open(HACKATHON_CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            
            flash('Settings updated successfully!', 'success')
        except Exception as e:
            flash(f'Error saving settings: {str(e)}', 'error')
    
    # Load current config
    try:
        with open(HACKATHON_CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except:
        config = default_config
    
    return render_template('admin_settings.html', config=config)

@app.route('/network-test')
def network_test():
    import socket
    results = []
    
    # Test common email ports
    ports_to_test = [587, 465, 25]
    
    for port in ports_to_test:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('smtp.gmail.com', port))
            status = "✅ OPEN" if result == 0 else "❌ BLOCKED"
            results.append(f"Port {port}: {status}")
            sock.close()
        except Exception as e:
            results.append(f"Port {port}: ❌ ERROR - {str(e)}")
    
    return "<br>".join(results)

@app.route('/check_roll_number', methods=['POST'])
def check_roll_number():
    roll_no = request.json.get('roll_no', '').strip().upper()
    if not roll_no:
        return jsonify({'exists': False})
    
    # Check for existing roll number in the JSON database
    existing_roll = False
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'r') as f:
            try:
                data = json.load(f)
                for team in data.get('teams', []):
                    for member in team.get('members', []):
                        if member.get('rollno', '').strip().upper() == roll_no:
                            existing_roll = True
                            break
                    if existing_roll:
                        break
            except Exception:
                pass

    return jsonify({'exists': existing_roll})

@app.route('/admin/homepage', methods=['GET', 'POST'])
def admin_homepage():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        try:
            # Get form data
            config = {
                'hero_title': request.form.get('hero_title', ''),
                'hero_subtitle': request.form.get('hero_subtitle', ''),
                'event_date': request.form.get('event_date', ''),
                'event_location': request.form.get('event_location', ''),
                'registration_deadline': request.form.get('registration_deadline', ''),
                'about_event': request.form.get('about_event', ''),
                'requirements': [
                    request.form.get('requirement1', ''),
                    request.form.get('requirement2', ''),
                    request.form.get('requirement3', ''),
                    request.form.get('requirement4', ''),
                    request.form.get('requirement5', '')
                ]
            }
            
            # Validate - ensure no empty requirements
            config['requirements'] = [req for req in config['requirements'] if req.strip()]
            
            # Save to file
            with open(HOMEPAGE_CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            
            flash('Homepage content updated successfully!', 'success')
            return redirect(url_for('admin_homepage'))
        
        except Exception as e:
            flash(f'Error saving homepage content: {str(e)}', 'error')
    
    # Load current config
    try:
        with open(HOMEPAGE_CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except:
        # If error loading, use defaults
        config = {
            'hero_title': '36 Hours Hackathon Registration',
            'hero_subtitle': 'Register your team for the 36 Hours Hackathon event and showcase your skills',
            'event_date': 'July 21-23, 2025',
            'event_location': 'Sphoorthy Engineering College Campus',
            'registration_deadline': 'July 15, 2025',
            'about_event': 'Join us for an exciting competition where teams showcase their skills and compete for amazing prizes. The event will feature multiple challenges testing various aspects of technical and creative abilities.',
            'requirements': [
                'Teams must have 3-4 members',
                'Complete all required member information',
                'Payment must be completed for registration',
                'Members can be from any Institutions',
                'Registration deadline: July 15, 2025'
            ]
        }
    
    # Ensure we have exactly 5 requirements (pad with empty strings if needed)
    while len(config['requirements']) < 5:
        config['requirements'].append('')
    
    return render_template('admin_homepage.html', config=config)



@app.route('/check_team_name', methods=['POST'])
def check_team_name():
    team_name = request.json.get('team_name', '').strip().upper()
    if not team_name:
        return jsonify({'exists': False})
    
    # Check for existing team name in the JSON database
    existing_team = False
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'r') as f:
            try:
                data = json.load(f)
                for team in data.get('teams', []):
                    if team.get('team_name', '').strip().upper() == team_name:
                        existing_team = True
                        break
            except Exception:
                pass

    return jsonify({'exists': existing_team})

@app.route('/check_member_details', methods=['POST'])
def check_member_details():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    contact = data.get('contact', '').strip()
    
    if not email and not contact:
        return jsonify({'error': 'No data provided'}), 400
    
    # Check database for existing details in both individuals and teams
    existing = {'email': False, 'contact': False}
    
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'r') as f:
            try:
                db_data = json.load(f)
                
                # Check individuals
                for individual in db_data.get('individuals', []):
                    if email and individual.get('email', '').lower() == email:
                        existing['email'] = True
                    if contact and individual.get('contact_number', '') == contact:
                        existing['contact'] = True
                
                # Check team members
                for team in db_data.get('teams', []):
                    for member in team.get('members', []):
                        if email and member.get('email', '').lower() == email:
                            existing['email'] = True
                        if contact and member.get('contact', '') == contact:
                            existing['contact'] = True
                            
            except Exception as e:
                print(f"Error checking member details: {str(e)}")
    
    return jsonify(existing)

@app.route('/get_scan_log')
def get_scan_log():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        if not os.path.exists(SCANNED_LOG_FILE):
            return jsonify([])

        with open(SCANNED_LOG_FILE, 'r') as f:
            log_data = json.load(f)

        # Combine all entries from both categories
        all_entries = []
        
        # Process entry logs
        for entry in log_data.get('entries', []):
            # Get proper name and year
            name = entry.get('name', 'Unknown')
            year = entry.get('year', 'N/A')
            
            # If name is still Unknown, try to get from participant info
            if name == 'Unknown' and 'participant_info' in entry:
                name = entry['participant_info'].get('name', 'Unknown')
                year = entry['participant_info'].get('year', 'N/A')
            
            all_entries.append({
                'timestamp': entry.get('timestamp'),
                'scan_type': 'entry',
                'name': name,
                'year': year,
                'branch': entry.get('branch', 'N/A'),
                'participant_type': entry.get('participant_type', 'unknown'),
                'team_name': entry.get('team_name', 'N/A'),
                'status': 'Success'
            })

        # Process food logs
        for entry in log_data.get('food', []):
            # Get proper name and year
            name = entry.get('name', 'Unknown')
            year = entry.get('year', 'N/A')
            
            # If name is still Unknown, try to get from participant info
            if name == 'Unknown' and 'participant_info' in entry:
                name = entry['participant_info'].get('name', 'Unknown')
                year = entry['participant_info'].get('year', 'N/A')
            
            all_entries.append({
                'timestamp': entry.get('timestamp'),
                'scan_type': 'food',
                'name': name,
                'year': year,
                'branch': entry.get('branch', 'N/A'),
                'participant_type': entry.get('participant_type', 'unknown'),
                'team_name': entry.get('team_name', 'N/A'),
                'status': 'Success'
            })

        # Sort by timestamp (newest first)
        all_entries.sort(key=lambda x: (
            datetime.strptime(x['timestamp'], '%Y-%m-%d %H:%M:%S') 
            if x['timestamp'] else datetime.min
        ), reverse=True)

        return jsonify(all_entries)

    except Exception as e:
        print(f"Error loading scan log: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/get_team_members/<team_id>')
def get_team_members(team_id):
    with open(DATABASE_FILE, 'r') as f:
        data = json.load(f)
        team = next((t for t in data['teams'] if t['team_id'] == team_id), None)
        if team:
            members = [{'id': m['id'], 'name': m['name']} for m in team['members']]
            return jsonify({'members': members})
    return jsonify({'members': []})


@app.route('/update_payment_status/<participant_id>', methods=['POST'])
def update_payment_status(participant_id):
    print(f"DEBUG: update_payment_status called with participant_id: {participant_id}")
    
    # Check admin authentication
    if not session.get('admin_logged_in'):
        print("DEBUG: Unauthorized - admin not logged in")
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        print(f"DEBUG: Request JSON data: {data}")
        
        if not data:
            print("DEBUG: No JSON data received")
            return jsonify({'success': False, 'message': 'No JSON data received'}), 400
            
        action = data.get('action')
        print(f"DEBUG: Action received: {action}")
        
        # Validate action
        if action not in ['approve', 'reject']:
            print(f"DEBUG: Invalid action: {action}")
            return jsonify({'success': False, 'message': 'Invalid action'}), 400
            
        # Load database
        print("DEBUG: Loading database...")
        with open(DATABASE_FILE, 'r+') as f:
            try:
                db_data = json.load(f)
                participant_found = False
                participant_type = None
                participant_data = None
                
                print(f"DEBUG: Looking for participant: {participant_id}")
                print(f"DEBUG: Total individuals: {len(db_data.get('individuals', []))}")
                print(f"DEBUG: Total teams: {len(db_data.get('teams', []))}")
                
                # First, try to find by individual_id (like IND_0001)
                for i, individual in enumerate(db_data.get('individuals', [])):
                    if individual.get('individual_id') == participant_id:
                        participant_found = True
                        participant_type = 'individual'
                        participant_data = individual.copy()
                        print(f"DEBUG: Found individual at index {i}: {individual.get('individual_id')}")
                        # Update payment status for individual
                        db_data['individuals'][i]['payment_verified'] = (action == 'approve')
                        db_data['individuals'][i]['payment_status'] = 'approved' if action == 'approve' else 'rejected'
                        db_data['individuals'][i]['payment_review_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        db_data['individuals'][i]['payment_review_by'] = session.get('admin_id', 'unknown')
                        break
                
                # If not found by individual_id, try by team_id
                if not participant_found:
                    for i, team in enumerate(db_data.get('teams', [])):
                        if team.get('team_id') == participant_id:
                            participant_found = True
                            participant_type = 'team'
                            participant_data = team.copy()
                            print(f"DEBUG: Found team at index {i}: {team.get('team_id')}")
                            # Update payment status for team
                            db_data['teams'][i]['payment_verified'] = (action == 'approve')
                            db_data['teams'][i]['payment_status'] = 'approved' if action == 'approve' else 'rejected'
                            db_data['teams'][i]['payment_review_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            db_data['teams'][i]['payment_review_by'] = session.get('admin_id', 'unknown')
                            break
                
                # If still not found, try by database index (fallback for old data)
                if not participant_found:
                    print("DEBUG: Trying database index lookup...")
                    # Try individuals by index
                    for i, individual in enumerate(db_data.get('individuals', [])):
                        if str(i) == participant_id:
                            participant_found = True
                            participant_type = 'individual_by_index'
                            participant_data = individual.copy()
                            print(f"DEBUG: Found individual by index {i}")
                            db_data['individuals'][i]['payment_verified'] = (action == 'approve')
                            db_data['individuals'][i]['payment_status'] = 'approved' if action == 'approve' else 'rejected'
                            db_data['individuals'][i]['payment_review_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            db_data['individuals'][i]['payment_review_by'] = session.get('admin_id', 'unknown')
                            break
                    
                    # Try teams by index
                    if not participant_found:
                        for i, team in enumerate(db_data.get('teams', [])):
                            if str(i) == participant_id:
                                participant_found = True
                                participant_type = 'team_by_index'
                                participant_data = team.copy()
                                print(f"DEBUG: Found team by index {i}")
                                db_data['teams'][i]['payment_verified'] = (action == 'approve')
                                db_data['teams'][i]['payment_status'] = 'approved' if action == 'approve' else 'rejected'
                                db_data['teams'][i]['payment_review_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                db_data['teams'][i]['payment_review_by'] = session.get('admin_id', 'unknown')
                                break
                
                if not participant_found:
                    print(f"DEBUG: Participant not found: {participant_id}")
                    return jsonify({
                        'success': False, 
                        'message': f'Participant not found: {participant_id}'
                    }), 404
                
                print(f"DEBUG: Successfully updated {participant_type}: {participant_id}")
                
                # Save changes
                f.seek(0)
                json.dump(db_data, f, indent=4)
                f.truncate()
                
                # Send verification email if payment was approved for individual
                if (action == 'approve' and participant_type in ['individual', 'individual_by_index'] 
                    and participant_data and participant_data.get('email')):
                    try:
                        threading.Thread(
                            target=send_payment_verification_email_individual,
                            args=(participant_data['email'], participant_data)
                        ).start()
                        print(f"✅ Payment verification email queued for: {participant_data['email']}")
                    except Exception as email_error:
                        print(f"❌ Failed to queue verification email: {email_error}")
                
                return jsonify({
                    'success': True,
                    'message': f'Payment {action}d successfully',
                    'new_status': action == 'approve'
                })
                
            except json.JSONDecodeError as e:
                print(f"DEBUG: JSON decode error: {e}")
                return jsonify({
                    'success': False,
                    'message': 'Database error',
                    'error': str(e)
                }), 500
                
    except Exception as e:
        print(f"DEBUG: General error: {e}")
        return jsonify({
            'success': False,
            'message': 'Server error',
            'error': str(e)
        }), 500
    

@app.route('/download_ticket/<individual_id>')
def download_ticket(individual_id):
    """Download the ticket PDF"""
    try:
        # Load individual data
        with open(DATABASE_FILE, 'r') as f:
            data = json.load(f)
            individual = next((ind for ind in data.get('individuals', []) if ind['individual_id'] == individual_id), None)
        
        if not individual:
            flash('Individual not found', 'error')
            return redirect(url_for('index'))
        
        # Generate QR code
        qr_data = {
            'individual_id': individual['individual_id'],
            'name': individual['name'],
            'rollno': individual['rollno'],
            'year': individual['year'],
            'email': individual['email'],
            'college': individual['college'],
            'branch': individual['branch']
        }
        
        qr_img = generate_qr_code_image(json.dumps(qr_data))
        qr_img_base64 = base64.b64encode(qr_img.getvalue()).decode('utf-8')
        
        # Create ticket PDF
        pdf_path = create_ticket_pdf(individual, qr_img_base64)
        
        if pdf_path and os.path.exists(pdf_path):
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=f"Event_Ticket_{individual_id}.pdf",
                mimetype='application/pdf'
            )
        else:
            flash('Error generating PDF', 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        print(f"Error downloading ticket: {str(e)}")
        flash('Error downloading ticket', 'error')
        return redirect(url_for('index'))
    
@app.route('/generate_qr/<team_id>')
def generate_qr(team_id):
    """Generate QR code for team with proper error handling"""
    if not session.get('admin_logged_in') and not session.get('teams_logged_in'):
        return "Unauthorized", 401

    try:
        # Look up team data
        with open(DATABASE_FILE, 'r') as f:
            try:
                data = json.load(f)
                team = next((t for t in data['teams'] if t['team_id'] == team_id), None)
            except (json.JSONDecodeError, KeyError):
                return "Database error", 500
        
        if not team:
            return "Team not found", 404

        # Generate QR code data
        qr_data = {
            'team_id': team['team_id'],
            'team_name': team['team_name'],
            'members': [{'id': m['id'], 'name': m['name']} for m in team['members']],
            'type': 'team'
        }

        return generate_qr_code_response(qr_data, team_id, 'team')
        
    except Exception as e:
        print(f"QR generation error: {str(e)}")
        return f"QR generation failed: {str(e)}", 500

@app.route('/generate_qr_individual/<individual_id>')
def generate_qr_individual(individual_id):
    """Generate QR code for individual with proper error handling"""
    if not session.get('admin_logged_in') and not session.get('teams_logged_in'):
        return "Unauthorized", 401

    try:
        # Look up individual data
        with open(DATABASE_FILE, 'r') as f:
            try:
                data = json.load(f)
                individual = next((ind for ind in data.get('individuals', []) 
                                 if ind['individual_id'] == individual_id), None)
            except (json.JSONDecodeError, KeyError):
                return "Database error", 500
        
        if not individual:
            return "Individual not found", 404

        # Generate QR code data for individual
        qr_data = {
            'individual_id': individual['individual_id'],
            'name': individual['name'],
            'rollno': individual.get('roll_number', individual.get('rollno', '')),
            'email': individual.get('email'),
            'college': individual.get('college'),
            'branch': individual.get('branch'),
            'year': individual.get('year'),
            'type': 'individual'
        }

        return generate_qr_code_response(qr_data, individual_id, 'individual')
        
    except Exception as e:
        print(f"QR generation error: {str(e)}")
        return f"QR generation failed: {str(e)}", 500

def generate_qr_code_response(qr_data, participant_id, participant_type):
    """Generate QR code image and return as response"""
    try:
        # Generate the QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        
        # Create image with better contrast
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to memory buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        # For view requests
        if request.args.get('view'):
            response = send_file(
                buffer,
                mimetype='image/png',
                as_attachment=False
            )
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
        
        # For download requests
        return send_file(
            buffer,
            mimetype='image/png',
            as_attachment=True,
            download_name=f"{participant_id}_qr.png"
        )
        
    except Exception as e:
        print(f"QR image creation error: {str(e)}")
        # Return a simple error image
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (200, 200), color='white')
        d = ImageDraw.Draw(img)
        d.text((10, 90), "QR Error", fill='black')
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return send_file(buffer, mimetype='image/png')
    
@app.route('/download_qr/<team_id>')
def download_qr(team_id):
    qr_path = os.path.join('static', 'qr_images', f"{team_id}.png")
    if not os.path.exists(qr_path):
        return "QR code not found", 404
    
    return send_file(qr_path, as_attachment=True, download_name=f"{team_id}_qr.png")
# Add this route to your Flask app
@app.route('/get_sections')
def get_sections():
    branch = request.args.get('branch')
    # Return sections based on branch - this should match your actual data structure
    sections = {
        'CSE': ['A', 'B', 'C'],
        'ECE': ['A', 'B'],  
        'EEE': ['A'],
        # Add other branches and their sections
    }
    return jsonify(sections.get(branch, []))


@app.route('/get_participant_documents/<participant_id>')
def get_participant_documents(participant_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        with open(DATABASE_FILE, 'r') as f:
            data = json.load(f)
        
        documents = []
        
        # Search in individuals
        individual = next((ind for ind in data.get('individuals', []) if ind['individual_id'] == participant_id), None)
        if individual:
            # Check for online payment screenshot
            if individual.get('payment_screenshot'):
                filename = individual['payment_screenshot']
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(file_path):
                    documents.append({
                        'filename': filename,
                        'filepath': f'/view_document/{filename}',  # Use the route
                        'type': 'Payment Screenshot'
                    })
            
            # Check for cash receipt photo
            if individual.get('cash_receipt_photo'):
                filename = individual['cash_receipt_photo']
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(file_path):
                    documents.append({
                        'filename': filename,
                        'filepath': f'/view_document/{filename}',  # Use the route
                        'type': 'Cash Receipt'
                    })
        
        return jsonify({
            'participant_id': participant_id,
            'documents': documents,
            'total_documents': len(documents)
        })
    
    except Exception as e:
        print(f"Error fetching documents: {str(e)}")
        return jsonify({
            'participant_id': participant_id,
            'documents': [],
            'error': str(e)
        }), 500

@app.route('/view_document/<filename>')
def view_document(filename):
    if not session.get('admin_logged_in') and not session.get('receipt_logged_in'):
        return "Unauthorized", 401
    
    try:
        # Security check
        filename = secure_filename(filename)
        if not filename:
            return "Invalid filename", 400
        
        # First, check in uploads folder (for payment screenshots)
        uploads_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], filename)
        
        # Second, check in receipts folder (for generated receipts)
        receipts_path = os.path.join(app.root_path, 'static', 'receipts', filename)
        
        # Third, check if it's a receiver-specific receipt
        file_path = None
        if os.path.exists(uploads_path):
            file_path = uploads_path
        elif os.path.exists(receipts_path):
            file_path = receipts_path
        else:
            # Check in receiver-specific subfolders
            receipts_base_dir = os.path.join(app.root_path, 'static', 'receipts')
            if os.path.exists(receipts_base_dir):
                for receiver_folder in os.listdir(receipts_base_dir):
                    receiver_path = os.path.join(receipts_base_dir, receiver_folder, filename)
                    if os.path.exists(receiver_path):
                        file_path = receiver_path
                        break
        
        if not file_path:
            return "File not found", 404
        
        # Determine MIME type
        file_extension = filename.lower().split('.')[-1]
        mime_types = {
            'png': 'image/png',
            'jpg': 'image/jpeg', 
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'pdf': 'application/pdf'
        }
        
        mimetype = mime_types.get(file_extension, 'application/octet-stream')
        
        return send_file(file_path, mimetype=mimetype)
    
    except Exception as e:
        print(f"Error in view_document: {str(e)}")
        return f"Server error: {str(e)}", 500


@app.route('/admin/export/<export_type>')
def export_data(export_type):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if export_type == 'teams':
        teams = get_teams_from_database()
        
        # Create CSV in memory
        output = BytesIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Team ID', 'Team Name', 'Payment Status', 
            'Member Name', 'Email', 'Contact', 
            'College', 'Branch', 'Year', 'Gender',
            'Registration Date'
        ])
        
        # Write data
        for team in teams:
            for member in team.get('members', []):
                writer.writerow([
                    team['team_id'],
                    team['team_name'],
                    'Verified' if team.get('payment_verified') else 'Pending',
                    member['name'],
                    member['email'],
                    member['contact'],
                    member['college'],
                    member['branch'],
                    member['year'],
                    member.get('gender', ''),
                    team.get('registration_date', '')
                ])
        
        output.seek(0)
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name='teams_export.csv'
        )
    
    elif export_type == 'logs':
        try:
            with open(SCANNED_LOG_FILE, 'r') as f:
                log_data = json.load(f)
        except Exception:
            log_data = {'entries': [], 'food': {st: [] for st in SCAN_TYPES if st != 'entry'}}
        
        # Create CSV in memory
        output = BytesIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Timestamp', 'Scan Type', 'Team ID', 
            'Team Name', 'Member ID', 'Member Name'
        ])
        
        # Write entry logs
        for entry in log_data.get('entries', []):
            for i, member_id in enumerate(entry.get('members', [])):
                writer.writerow([
                    entry.get('timestamp'),
                    'entry',
                    entry.get('team_id'),
                    entry.get('team_name', 'Unknown Team'),
                    member_id,
                    entry.get('member_names', [])[i] if i < len(entry.get('member_names', [])) else 'Unknown Member'
                ])
        
        # Write food logs
        for meal_type in ['breakfast', 'lunch', 'dinner']:
            for entry in log_data.get('food', {}).get(meal_type, []):
                for i, member_id in enumerate(entry.get('members', [])):
                    writer.writerow([
                        entry.get('timestamp'),
                        meal_type,
                        entry.get('team_id'),
                        entry.get('team_name', 'Unknown Team'),
                        member_id,
                        entry.get('member_names', [])[i] if i < len(entry.get('member_names', [])) else 'Unknown Member'
                    ])
        
        output.seek(0)
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name='scan_logs_export.csv'
        )
    
    else:
        flash('Invalid export type', 'error')
        return redirect(url_for('admin'))
    



# Basic routes
@app.route('/')
def index():
    """Homepage route"""
    try:
        with open(HOMEPAGE_CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except:
        config = {
            'hero_title': '36 Hours Hackathon Registration',
            'hero_subtitle': 'Register your team for the 36 Hours Hackathon event and showcase your skills',
            'event_date': 'July 21-23, 2025',
            'event_location': 'Sphoorthy Engineering College Campus',
            'registration_deadline': 'July 15, 2025',
            'about_event': 'Join us for an exciting competition where teams showcase their skills and compete for amazing prizes. The event will feature multiple challenges testing various aspects of technical and creative abilities.',
            'requirements': [
                'Teams must have 3-4 members',
                'Complete all required member information',
                'Payment must be completed for registration',
                'Members can be from any Institutions',
                'Registration deadline: July 15, 2025'
            ]
        }
    
    return render_template('index.html', config=config)

                      
# Admin routes
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Admin login route"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_CREDENTIALS['username'] and password == ADMIN_CREDENTIALS['password']:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('admin_login.html')

@app.route('/admin/teams')
def view_teams():
    """View teams and individuals route"""
    if not session.get('admin_logged_in') and not session.get('teams_logged_in'):
        return redirect(url_for('teams_login'))
    
    try:
        with open(DATABASE_FILE, 'r') as f:
            data = json.load(f)
        
        individuals = data.get('individuals', [])
        teams = data.get('teams', [])
        
        all_participants = []
        
        # Initialize payment statistics with proper structure
        payment_stats = {
            'total_cash': 0,
            'total_online': 0,
            'total_verified': 0,
            'total_pending': 0,
            'cash_receivers': {},
            'payment_methods': {'cash': 0, 'online': 0}
        }
        
        # Add individuals
        for individual in individuals:
            # Get registration fee - handle both string and integer values
            registration_fee = individual.get('registration_fee', 500)
            if isinstance(registration_fee, str):
                try:
                    registration_fee = int(registration_fee)
                except (ValueError, TypeError):
                    registration_fee = 500 if individual.get('year') == '1st' else 600
            
            participant_data = {
                'type': 'individual',
                'id': individual['individual_id'],
                'name': individual['name'],
                'email': individual['email'],
                'contact': individual['contact_number'],
                'college': individual['college'],
                'branch': individual['branch'],
                'year': individual['year'],
                'gender': individual['gender'],
                'rollno': individual.get('roll_number', ''),
                'section': individual.get('section'),
                'payment_verified': individual.get('payment_verified', False),
                'payment_method': individual.get('payment_method'),
                'payment_id': individual.get('payment_id'),
                'registration_date': individual.get('registration_date'),
                'cash_receiver_name': individual.get('cash_receiver_name'),
                'receipt_number': individual.get('receipt_number'),
                'payment_screenshot': individual.get('payment_screenshot'),
                'cash_receipt_photo': individual.get('cash_receipt_photo'),
                'registration_fee': registration_fee
            }
            all_participants.append(participant_data)
            
            # Update payment statistics - FIXED LOGIC
            payment_method = individual.get('payment_method')
            is_verified = individual.get('payment_verified', False)
            
            if payment_method == 'cash':
                payment_stats['payment_methods']['cash'] += 1
                if is_verified:
                    payment_stats['total_verified'] += 1
                    payment_stats['total_cash'] += registration_fee
                    
                    # Track cash receivers - FIXED: Handle None/Unknown receiver names
                    receiver = individual.get('cash_receiver_name')
                    if not receiver or receiver.strip() == '':
                        receiver = 'Not Specified'
                    
                    if receiver in payment_stats['cash_receivers']:
                        payment_stats['cash_receivers'][receiver]['count'] += 1
                        payment_stats['cash_receivers'][receiver]['amount'] += registration_fee
                    else:
                        payment_stats['cash_receivers'][receiver] = {
                            'count': 1,
                            'amount': registration_fee
                        }
                else:
                    payment_stats['total_pending'] += 1
                    
            elif payment_method == 'online':
                payment_stats['payment_methods']['online'] += 1
                if is_verified:
                    payment_stats['total_verified'] += 1
                    payment_stats['total_online'] += registration_fee
                else:
                    payment_stats['total_pending'] += 1
            else:
                # No payment method set yet
                payment_stats['total_pending'] += 1
        
        # Calculate statistics
        gender_counts = {'Male': 0, 'Female': 0}
        branch_counts = {}
        section_counts = {}
        year_counts = {'1st': 0, '2nd': 0}
        college_counts = {}
        
        # Separate amounts for first and second year
        first_year_amount = 0
        second_year_amount = 0
        
        for participant in all_participants:
            # Gender counts
            gender = participant.get('gender')
            if gender in gender_counts:
                gender_counts[gender] += 1
            
            # Branch counts
            branch = participant.get('branch', 'Unknown')
            branch_counts[branch] = branch_counts.get(branch, 0) + 1
            
            # Section counts (only for Sphoorthy students)
            if participant.get('college') == 'Sphoorthy Engineering College' and participant.get('section'):
                section = participant.get('section')
                section_counts[section] = section_counts.get(section, 0) + 1
            
            # Year counts and amounts
            year = participant.get('year')
            if year in year_counts:
                year_counts[year] += 1
            
            # Calculate year-wise amounts for verified payments
            if participant.get('payment_verified'):
                fee = participant.get('registration_fee', 0)
                if year == '1st':
                    first_year_amount += fee
                elif year == '2nd':
                    second_year_amount += fee
            
            # College counts
            college = participant.get('college', 'Unknown')
            college_counts[college] = college_counts.get(college, 0) + 1
        
        # Calculate total amount
        total_amount = payment_stats['total_cash'] + payment_stats['total_online']
        
        # Sort cash receivers by amount (highest first) - FIXED sorting
        sorted_cash_receivers = {}
        if payment_stats['cash_receivers']:
            sorted_items = sorted(
                payment_stats['cash_receivers'].items(),
                key=lambda x: x[1]['amount'],
                reverse=True
            )
            sorted_cash_receivers = dict(sorted_items)
        
        # Debug output to console
        print(f"DEBUG: Total participants: {len(all_participants)}")
        print(f"DEBUG: Payment stats - Cash: {payment_stats['total_cash']}, Online: {payment_stats['total_online']}")
        print(f"DEBUG: Cash receivers: {sorted_cash_receivers}")
        print(f"DEBUG: First year amount: {first_year_amount}, Second year amount: {second_year_amount}")
        
        return render_template('view_teams.html', 
                             participants=all_participants,
                             total_participants=len(all_participants),
                             gender_counts=gender_counts,
                             branch_counts=branch_counts,
                             section_counts=section_counts,
                             year_counts=year_counts,
                             college_counts=college_counts,
                             total_amount=total_amount,
                             first_year_amount=first_year_amount,
                             second_year_amount=second_year_amount,
                             payment_stats=payment_stats,
                             cash_receivers=sorted_cash_receivers,
                             is_admin=session.get('admin_logged_in', False))
    
    except Exception as e:
        print(f"Error in view_teams: {str(e)}")
        flash('Error loading participants data', 'error')
        return redirect(url_for('admin_dashboard'))
    
@app.route('/admin/scan', methods=['GET', 'POST'])
def scan_qr():
    """QR code scanning route"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'GET':
        return render_template('scan_qr.html')
    
    elif request.method == 'POST':
        try:
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Request must be JSON',
                    'code': 'INVALID_REQUEST'
                }), 400

            data = request.get_json()
            qr_data_str = data.get('qr_data')
            scan_type = data.get('scan_type')

            if not all([qr_data_str, scan_type]):
                return jsonify({
                    'success': False,
                    'message': 'Missing QR data or scan type',
                    'code': 'MISSING_DATA'
                }), 400

            # Parse QR data
            try:
                qr_data = json.loads(qr_data_str)
            except json.JSONDecodeError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid JSON in QR code',
                    'code': 'INVALID_QR_DATA'
                }), 400

            # Determine if it's individual or team QR code
            is_individual = 'individual_id' in qr_data
            is_team = 'team_id' in qr_data

            if not (is_individual or is_team):
                return jsonify({
                    'success': False,
                    'message': 'Invalid QR code format',
                    'code': 'INVALID_QR_FORMAT'
                }), 400

            # Load database to verify participant exists
            with open(DATABASE_FILE, 'r') as f:
                db_data = json.load(f)

            participant_info = None
            participant_type = None

            if is_individual:
                individual_id = qr_data['individual_id']
                
                for ind in db_data.get('individuals', []):
                    if ind['individual_id'] == individual_id:
                        participant_info = {
                            'id': individual_id,
                            'name': ind['name'],
                            'rollno': ind.get('rollno', ''),
                            'email': ind.get('email', ''),
                            'college': ind.get('college', ''),
                            'branch': ind.get('branch', '')
                        }
                        participant_type = 'individual'
                        break
                
                if not participant_info:
                    return jsonify({
                        'success': False,
                        'message': 'Individual not found in database',
                        'code': 'PARTICIPANT_NOT_FOUND'
                    }), 404

            else:
                team_id = qr_data['team_id']
                member_id = qr_data.get('member_id')
                
                team_found = None
                for team in db_data.get('teams', []):
                    if team['team_id'] == team_id:
                        team_found = team
                        break
                
                if not team_found:
                    return jsonify({
                        'success': False,
                        'message': 'Team not found',
                        'code': 'TEAM_NOT_FOUND'
                    }), 404

                member_found = None
                if member_id:
                    for member in team_found.get('members', []):
                        if member['id'] == member_id:
                            member_found = member
                            break
                else:
                    member_found = team_found.get('members', [{}])[0]

                if not member_found:
                    return jsonify({
                        'success': False,
                        'message': 'Team member not found',
                        'code': 'MEMBER_NOT_FOUND'
                    }), 404

                participant_info = {
                    'id': f"{team_id}_{member_found['id']}",
                    'name': member_found['name'],
                    'rollno': member_found.get('rollno', ''),
                    'email': member_found.get('email', ''),
                    'college': member_found.get('college', ''),
                    'branch': member_found.get('branch', ''),
                    'team_id': team_id,
                    'team_name': team_found.get('team_name', 'Unknown Team')
                }
                participant_type = 'team'

            # Check payment verification
            if is_individual:
                individual_data = next((ind for ind in db_data.get('individuals', []) if ind['individual_id'] == participant_info['id']), None)
                if individual_data and not individual_data.get('payment_verified', False):
                    return jsonify({
                        'success': False,
                        'message': 'Payment not verified for this individual',
                        'code': 'PAYMENT_NOT_VERIFIED'
                    }), 403
            else:
                team_data = next((team for team in db_data.get('teams', []) if team['team_id'] == participant_info['team_id']), None)
                if team_data and not team_data.get('payment_verified', False):
                    return jsonify({
                        'success': False,
                        'message': 'Payment not verified for this team',
                        'code': 'PAYMENT_NOT_VERIFIED'
                    }), 403

            # Load scan log
            if not os.path.exists(SCANNED_LOG_FILE):
                with open(SCANNED_LOG_FILE, 'w') as f:
                    json.dump({'entries': [], 'food': []}, f)

            with open(SCANNED_LOG_FILE, 'r') as f:
                log_data = json.load(f)

            # Check for duplicates (prevent re-scan within 2 hours)
            now = datetime.now(IST)
            is_duplicate = False
            
            log_category = log_data['entries'] if scan_type == 'entry' else log_data['food']
            
            for entry in log_category[-50:]:
                entry_time_naive = datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S')
                entry_time = IST.localize(entry_time_naive)
                time_diff = (now - entry_time).total_seconds()
                if (entry.get('participant_id') == participant_info['id'] and 
                    entry.get('scan_type') == scan_type and
                    time_diff < 7200):
                    is_duplicate = True
                    break

            if is_duplicate:
                return jsonify({
                    'success': False,
                    'message': f'Already scanned for {scan_type} in the last 2 hours',
                    'code': 'DUPLICATE_SCAN'
                }), 400

            # Create log entry
            log_entry = {
                'timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
                'scan_type': scan_type,
                'participant_id': participant_info['id'],
                'name': participant_info['name'],
                'rollno': participant_info['rollno'],
                'email': participant_info.get('email', ''),
                'college': participant_info.get('college', ''),
                'branch': participant_info.get('branch', ''),
                'participant_type': participant_type,
                'scanner_id': session.get('admin_id', 'unknown')
            }

            if participant_type == 'team':
                log_entry.update({
                    'team_id': participant_info['team_id'],
                    'team_name': participant_info['team_name']
                })

            if scan_type == 'entry':
                log_data['entries'].append(log_entry)
            else:
                log_data['food'].append(log_entry)

            with open(SCANNED_LOG_FILE, 'w') as f:
                json.dump(log_data, f, indent=4)

            return jsonify({
                'success': True,
                'message': f'Successfully scanned {participant_info["name"]} for {scan_type}',
                'data': log_entry
            })

        except Exception as e:
            print(f"Scan error: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error processing scan: {str(e)}',
                'code': 'SERVER_ERROR'
            }), 500

# Utility functions
def check_existing_values(field, value):
    """Check if a value already exists in the database for a specific field"""
    if not os.path.exists(DATABASE_FILE):
        return False
        
    try:
        with open(DATABASE_FILE, 'r') as f:
            data = json.load(f)
            for team in data.get('teams', []):
                for member in team.get('members', []):
                    if member.get(field, '').lower() == value.lower():
                        return True
            for individual in data.get('individuals', []):
                if individual.get(field, '').lower() == value.lower():
                    return True
    except Exception:
        pass
    return False

def generate_qr_code_image(data):
    """Generate QR code image from data"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


# Add this route to test email
@app.route('/test-email')
def test_email():
    try:
        msg = Message(
            subject='Test Email',
            recipients=['test@example.com'],
            body='This is a test email'
        )
        mail.send(msg)
        return 'Email sent successfully'
    except Exception as e:
        return f'Email failed: {str(e)}'
    
def create_ticket_pdf(individual_data, qr_img_base64):
    """Generate a professional event ticket PDF"""
    try:
        # Ensure tickets directory exists
        tickets_dir = os.path.join(app.root_path, 'static', 'tickets')
        os.makedirs(tickets_dir, exist_ok=True)

        # Create safe filename
        filename = f"ticket_{individual_data['individual_id']}.pdf"
        pdf_path = os.path.join(tickets_dir, filename)

        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                              rightMargin=20, leftMargin=20,
                              topMargin=20, bottomMargin=20)
        
        # Get default styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        styles.add(ParagraphStyle(name='TicketTitle', 
                                fontSize=20, 
                                leading=24,
                                alignment=TA_CENTER,
                                spaceAfter=12,
                                fontName='Helvetica-Bold',
                                textColor=colors.HexColor('#1e3c72')))
        
        styles.add(ParagraphStyle(name='TicketSubtitle', 
                                fontSize=14, 
                                leading=16,
                                alignment=TA_CENTER,
                                spaceAfter=20,
                                fontName='Helvetica-Bold',
                                textColor=colors.HexColor('#2a5298')))
        
        styles.add(ParagraphStyle(name='InfoLabel', 
                                fontSize=10, 
                                leading=12,
                                alignment=TA_LEFT,
                                spaceAfter=2,
                                fontName='Helvetica-Bold'))
        
        styles.add(ParagraphStyle(name='InfoValue', 
                                fontSize=10, 
                                leading=12,
                                alignment=TA_LEFT,
                                spaceAfter=8))
        
        styles.add(ParagraphStyle(name='DeveloperText', 
                                fontSize=8, 
                                leading=10,
                                alignment=TA_CENTER,
                                textColor=colors.HexColor('#666666')))
        
        # Story (content elements)
        story = []
        
        # Title
        story.append(Paragraph("FRESHERS FIESTA 2025", styles['TicketTitle']))
        story.append(Paragraph("Official Event Ticket", styles['TicketSubtitle']))
        
        # Event details
        event_data = [
            ["Date:", "November 09, 2025"],
            ["Location:", "SPHN GROUNDS"],
            ["Registration ID:", individual_data['individual_id']]
        ]
        
        event_table = Table(event_data, colWidths=[doc.width*0.3, doc.width*0.7])
        event_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(event_table)
        story.append(Spacer(1, 15))
        
        # Horizontal line
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#CCCCCC')))
        story.append(Spacer(1, 15))
        
        # Participant information
        story.append(Paragraph("PARTICIPANT INFORMATION", styles['InfoLabel']))
        
        participant_data = [
            ["Name:", individual_data['name']],
            ["Email:", individual_data['email']],
            ["Contact:", individual_data['contact']],
            ["College:", individual_data['college']],
            ["Branch:", individual_data['branch']],
            ["Year:", individual_data['year']],
            ["Registration Date:", individual_data['registration_date']]
        ]
        
        if individual_data.get('section'):
            participant_data.append(["Section:", individual_data['section']])
        
        participant_data.append(["Roll Number:", individual_data['rollno']])
        
        participant_table = Table(participant_data, colWidths=[doc.width*0.3, doc.width*0.7])
        participant_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(participant_table)
        story.append(Spacer(1, 20))
        
        # QR Code
        try:
            # Decode base64 QR code and create ImageReader
            qr_img_data = base64.b64decode(qr_img_base64)
            qr_buffer = BytesIO(qr_img_data)
            qr_image = Image(qr_buffer, width=120, height=120)
            qr_image.hAlign = 'CENTER'
            story.append(qr_image)
            story.append(Spacer(1, 10))
            story.append(Paragraph("Scan for verification", 
                                 ParagraphStyle(name='QRCaption', 
                                              fontSize=8, 
                                              alignment=TA_CENTER,
                                              textColor=colors.HexColor('#666666'))))
        except Exception as e:
            print(f"Error adding QR code to PDF: {e}")
            story.append(Paragraph("QR Code: " + individual_data['individual_id'], 
                                 ParagraphStyle(name='QRFallback', 
                                              fontSize=10, 
                                              alignment=TA_CENTER,
                                              textColor=colors.HexColor('#666666'))))
        
        story.append(Spacer(1, 20))
        
        # Developer Information Section
        story.append(HRFlowable(width="100%", thickness=0.5, lineCap='round', color=colors.HexColor('#CCCCCC')))
        story.append(Spacer(1, 10))
        
        developer_info = [
            Paragraph("<b>🛠️ Developed by Smart N Light Innovations</b>", 
                     ParagraphStyle(name='DeveloperHeader',
                                  fontSize=9,
                                  alignment=TA_CENTER,
                                  textColor=colors.HexColor('#1e3c72'))),
            Paragraph("24/7 Technical Support Available", 
                     ParagraphStyle(name='DeveloperSub',
                                  fontSize=8,
                                  alignment=TA_CENTER,
                                  textColor=colors.HexColor('#666666'))),
            Paragraph("Contact: +91 9059160424 | Email: smartnlightinnovations@gmail.com", 
                     ParagraphStyle(name='DeveloperContact',
                                  fontSize=7,
                                  alignment=TA_CENTER,
                                  textColor=colors.HexColor('#666666'))),
            Paragraph("Website: https://smartnlightinnovation.netlify.app", 
                     ParagraphStyle(name='DeveloperWebsite',
                                  fontSize=7,
                                  alignment=TA_CENTER,
                                  textColor=colors.HexColor('#666666')))
        ]
        
        for info in developer_info:
            story.append(info)
            story.append(Spacer(1, 3))
        
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=0.5, lineCap='round', color=colors.HexColor('#CCCCCC')))
        story.append(Spacer(1, 10))
        
        # Footer instructions
        instructions = [
            "• Present this ticket at the event registration desk",
            "• Keep this ticket accessible on your phone or print it",
            "• This ticket is required for entry and meals",
            "• For any queries, contact: +91 9059160424 (24/7 Support)"
        ]
        
        for instruction in instructions:
            story.append(Paragraph(instruction, 
                                 ParagraphStyle(name='Instruction', 
                                              fontSize=8, 
                                              alignment=TA_LEFT,
                                              textColor=colors.HexColor('#666666'),
                                              leftIndent=10)))
            story.append(Spacer(1, 4))
        
        story.append(Spacer(1, 15))
        
        # Footer with dual branding
        footer_data = [
            ["Organized by:", "Technical Partner:"],
            ["Creators Club", "Smart N Light Innovations"],
            ["Sphoorthy Engineering College", "24/7 Support: +91 9059160424"]
        ]
        
        footer_table = Table(footer_data, colWidths=[doc.width*0.5, doc.width*0.5])
        footer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#666666')),
        ]))
        
        story.append(footer_table)
        story.append(Spacer(1, 5))
        
        # Final copyright
        footer_text = f"© {datetime.now().year} All rights reserved | Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        story.append(Paragraph(footer_text, 
                             ParagraphStyle(name='Footer', 
                                          fontSize=6, 
                                          alignment=TA_CENTER,
                                          textColor=colors.HexColor('#999999'))))
        
        # Build the PDF
        doc.build(story)
        
        print(f"✅ Ticket PDF generated: {pdf_path}")
        return pdf_path

    except Exception as e:
        app.logger.error(f"Error in create_ticket_pdf: {str(e)}")
        raise
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')
   
@app.errorhandler(404)
def not_found_error(error):
    try:
        return render_template('404.html'), 404
    except:
        return "Page not found", 404

@app.errorhandler(500)
def internal_error(error):
    try:
        return render_template('500.html'), 500
    except:
        return "Internal server error", 500
    
# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))



@app.route('/receipt-login', methods=['GET', 'POST'])
def receipt_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == RECEIPT_CREDENTIALS['username'] and password == RECEIPT_CREDENTIALS['password']:
            session['receipt_logged_in'] = True
            return redirect(url_for('generate_receipt'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('receipt_login.html')

@app.route('/api/check-existing-receipt', methods=['POST'])
def check_existing_receipt():
    """Check if a receipt already exists for a roll number"""
    if not session.get('admin_logged_in') and not session.get('receipt_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        roll_number = data.get('roll_number', '').strip().upper()
        
        if not roll_number:
            return jsonify({'success': False, 'message': 'Roll number is required'}), 400
        
        # Check if receipt exists for this roll number
        receipt_exists = False
        existing_receipt = None
        
        if os.path.exists(DATABASE_FILE):
            with open(DATABASE_FILE, 'r') as f:
                db_data = json.load(f)
                
                # Check individuals for existing receipt
                for individual in db_data.get('individuals', []):
                    if (individual.get('roll_number') == roll_number and 
                        individual.get('payment_method') == 'cash' and 
                        individual.get('cash_receipt_photo')):
                        receipt_exists = True
                        existing_receipt = {
                            'receipt_number': individual.get('receipt_number'),
                            'payment_date': individual.get('payment_date'),
                            'receiver_name': individual.get('cash_receiver_name')
                        }
                        break
        
        return jsonify({
            'success': True,
            'receipt_exists': receipt_exists,
            'existing_receipt': existing_receipt
        })
        
    except Exception as e:
        print(f"Error checking existing receipt: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'}), 500
    

@app.route('/admin/generate_receipt', methods=['GET', 'POST'])
def generate_receipt():
    print("Form data received:", request.form)
    print("Files received:", request.files)
    
    form = ReceiptForm()

    if form.validate_on_submit():
        try:
            # Get roll number from form
            roll_number = request.form.get('roll_number', '').strip().upper()
            
            # Check if receipt already exists for this roll number
            if roll_number:
                with open(DATABASE_FILE, 'r') as f:
                    db_data = json.load(f)
                    
                    for individual in db_data.get('individuals', []):
                        if (individual.get('roll_number') == roll_number and 
                            individual.get('payment_method') == 'cash' and 
                            individual.get('cash_receipt_photo')):
                            flash('A receipt has already been generated for this roll number. Cannot generate another one.', 'error')
                            return redirect(url_for('generate_receipt'))

            # Generate receipt number
            receipt_number = get_next_receipt_number()
            receipt_no = f"RC-{receipt_number:05d}"
            
            # Prepare receipt data
            receipt_data = {
                'viewer_name': form.viewer_name.data,
                'viewer_email': form.viewer_email.data,
                'contact_number': form.contact_number.data,
                'receiver_name': form.receiver_name.data,
                'year': form.year.data,
                'amount': form.amount.data,
                'receipt_no': receipt_no,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # Generate PDF in receiver-specific folder
            pdf_path = create_receipt_pdf(receipt_data)

            # Store the relative path in the database, not just filename
            receipt_filename = os.path.basename(pdf_path)
            receiver_name = form.receiver_name.data.replace(' ', '_')
            relative_path = f"static/receipts/{receiver_name}/{receipt_filename}"

            # Update individual data with the correct path
            # Find and update the individual in the database
            with open(DATABASE_FILE, 'r') as f:
                db_data = json.load(f)
                
            updated = False
            for individual in db_data.get('individuals', []):
                if individual.get('roll_number') == roll_number:
                    individual['cash_receipt_photo'] = relative_path
                    updated = True
                    break
            
            # Save updated database
            if updated:
                with open(DATABASE_FILE, 'w') as f:
                    json.dump(db_data, f, indent=4)
            
            if not os.path.exists(pdf_path):
                raise Exception("Failed to create PDF file")
            
            # Send email
            send_receipt_email(receipt_data['viewer_email'], receipt_data, pdf_path)
            
            # Log receipt generation
            log_receipt_generation(receipt_data)
            
            flash('Receipt generated and sent successfully!', 'success')
            return redirect(url_for('generate_receipt'))
            
        except Exception as e:
            app.logger.error(f"Error generating receipt: {str(e)}", exc_info=True)
            flash(f'Error generating receipt: {str(e)}', 'error')

    elif request.method == 'POST' and not form.validate():
        # Form validation failed
        error_messages = []
        for field, errors in form.errors.items():
            for error in errors:
                error_messages.append(f"{getattr(form, field).label.text}: {error}")
        flash('; '.join(error_messages), 'error')

    return render_template('generate_receipt.html', form=form)

@app.route('/debug-receipts')
def debug_receipts():
    """Debug route to check receipt files"""
    if not session.get('admin_logged_in'):
        return "Unauthorized", 401
    
    receipts_info = []
    receipts_base_dir = os.path.join(app.root_path, 'static', 'receipts')
    
    if os.path.exists(receipts_base_dir):
        for root, dirs, files in os.walk(receipts_base_dir):
            for file in files:
                if file.endswith('.pdf'):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, app.root_path)
                    receipts_info.append({
                        'filename': file,
                        'full_path': full_path,
                        'relative_path': relative_path,
                        'exists': os.path.exists(full_path)
                    })
    
    return jsonify(receipts_info)
def log_receipt_generation(receipt_data):
    """Log receipt generation for tracking"""
    try:
        receipt_logs_file = 'data/receipt_logs.json'
        receipt_logs = []
        
        if os.path.exists(receipt_logs_file):
            with open(receipt_logs_file, 'r') as f:
                receipt_logs = json.load(f)
        
        log_entry = {
            'receipt_no': receipt_data['receipt_no'],
            'receiver_name': receipt_data['receiver_name'],
            'payer_name': receipt_data['viewer_name'],
            'amount': receipt_data['amount'],
            'timestamp': receipt_data['timestamp'],
            'generated_by': session.get('admin_id', 'unknown')
        }
        
        receipt_logs.append(log_entry)
        
        with open(receipt_logs_file, 'w') as f:
            json.dump(receipt_logs, f, indent=4)
            
        print(f"✅ Receipt logged: {receipt_data['receipt_no']} by {receipt_data['receiver_name']}")
        
    except Exception as e:
        print(f"Error logging receipt: {str(e)}")

@app.route('/teams-login', methods=['GET', 'POST'])
def teams_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == TEAMS_CREDENTIALS['username'] and password == TEAMS_CREDENTIALS['password']:
            session['teams_logged_in'] = True
            return redirect(url_for('view_teams'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('teams_login.html')


@app.template_filter('formatdate')
def format_date(value, format='%d %b %Y'):
    if isinstance(value, str):
        try:
            # Try to parse the string if it's in ISO format
            value = datetime.fromisoformat(value)
        except ValueError:
            return value  # Return as-is if we can't parse it
    if hasattr(value, 'strftime'):
        return value.strftime(format)
    return value
    

@app.route('/message-center', methods=['GET', 'POST'])
def message_center():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        recipients_type = request.form.get('recipients_type', 'all')
        
        if not subject or not message:
            flash('Subject and message are required', 'error')
            return redirect(url_for('message_center'))
        
        # Get recipients based on type
        recipients = []
        with open(DATABASE_FILE, 'r') as f:
            data = json.load(f)
            
            # Add individuals to recipients
            for individual in data.get('individuals', []):
                if individual.get('email'):
                    recipients.append({
                        'name': individual.get('name'),
                        'email': individual.get('email'),
                        'type': 'individual',
                        'individual_id': individual.get('individual_id')
                    })
            
            # Add team members to recipients
            for team in data.get('teams', []):
                if recipients_type == 'all' or \
                   (recipients_type == 'paid' and team.get('payment_verified')) or \
                   (recipients_type == 'unpaid' and not team.get('payment_verified')):
                    for member in team.get('members', []):
                        if member.get('email'):
                            recipients.append({
                                'name': member.get('name'),
                                'email': member.get('email'),
                                'team': team.get('team_name'),
                                'team_id': team.get('team_id'),
                                'type': 'team_member'
                            })
        
        if not recipients:
            flash('No recipients found for the selected criteria', 'warning')
            return redirect(url_for('message_center'))
        
        # Remove duplicate emails
        unique_recipients = []
        seen_emails = set()
        for recipient in recipients:
            if recipient['email'] not in seen_emails:
                seen_emails.add(recipient['email'])
                unique_recipients.append(recipient)
        
        recipients = unique_recipients
        
        # Handle file attachments
        attachments = []
        if 'attachments' in request.files:
            for file in request.files.getlist('attachments'):
                if file.filename != '':
                    if not allowed_file(file.filename):
                        flash(f'File type not allowed: {file.filename}', 'error')
                        continue
                    
                    # Ensure upload directory exists
                    upload_dir = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Generate secure filename
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(upload_dir, filename)
                    
                    # Save file
                    file.save(file_path)
                    print(f"DEBUG: Saved attachment: {file_path}")
                    
                    file_data = file.read()
                    attachments.append({
                        'filename': filename,
                        'content_type': file.content_type,
                        'data': file_data,
                        'file_path': file_path
                    })
        
        # Create email log entry
        email_log = {
            'id': str(uuid.uuid4()),
            'subject': subject,
            'message': message,
            'recipients_type': recipients_type,
            'total_recipients': len(recipients),
            'sent_by': session.get('admin_id', 'unknown'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'recipients': recipients[:100],  # Store first 100 recipients for reference
            'attachments': [{'filename': a['filename']} for a in attachments] if attachments else []
        }
        
        # Save to email logs
        try:
            email_logs = []
            if os.path.exists(EMAIL_LOGS_FILE):
                with open(EMAIL_LOGS_FILE, 'r') as f:
                    email_logs = json.load(f)
            
            email_logs.append(email_log)
            
            with open(EMAIL_LOGS_FILE, 'w') as f:
                json.dump(email_logs, f, indent=4)
        except Exception as e:
            app.logger.error(f"Failed to save email log: {str(e)}")
        
        # Send emails in background thread
        def send_messages():
            with app.app_context():
                sent_count = 0
                failed_count = 0
                
                for recipient in recipients:
                    try:
                        # Create professional HTML email
                        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body {{
            font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #444;
            max-width: 600px;
            margin: 0 auto;
            padding: 0;
            background-color: #f9f9f9;
        }}
        .email-container {{
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            margin: 20px auto;
        }}
        .email-header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 30px 20px;
            text-align: center;
            color: white;
        }}
        .logo-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 30px;
            margin-bottom: 20px;
        }}
        .logo {{
            height: 60px;
            width: auto;
            object-fit: contain;
        }}
        .email-title {{
            font-size: 28px;
            font-weight: 700;
            margin: 10px 0;
            color: white;
            letter-spacing: 1px;
        }}
        .email-subtitle {{
            font-size: 16px;
            opacity: 0.9;
            margin-bottom: 10px;
        }}
        .email-body {{
            padding: 30px;
        }}
        .message-content {{
            font-size: 16px;
            color: #555;
            margin: 20px 0;
            line-height: 1.6;
            white-space: pre-line;
        }}
        .developer-info {{
            background-color: #e8f5e8;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #28a745;
            text-align: center;
        }}
        .contact-info {{
            background-color: #f5f7fa;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #3498db;
        }}
        .email-footer {{
            background-color: #f5f7fa;
            padding: 25px;
            text-align: center;
            border-top: 1px solid #eaeaea;
        }}
        .footer-logos {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        .footer-logo {{
            height: 50px;
            width: auto;
        }}
        .company-name {{
            font-size: 18px;
            font-weight: 600;
            color: #1e3c72;
            margin: 10px 0;
        }}
        .contact-links {{
            margin: 20px 0;
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 15px;
        }}
        .contact-links a {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            color: #3498db;
            text-decoration: none;
            font-weight: 500;
            padding: 8px 12px;
            border-radius: 6px;
            background-color: rgba(52, 152, 219, 0.1);
            transition: all 0.3s ease;
        }}
        .contact-links a:hover {{
            color: #1e3c72;
            background-color: rgba(52, 152, 219, 0.2);
            transform: translateY(-2px);
        }}
        .copyright {{
            font-size: 13px;
            color: #7f8c8d;
            margin-top: 20px;
        }}
        .event-highlight {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
        }}
        @media only screen and (max-width: 600px) {{
            .logo-container {{
                flex-direction: column;
                gap: 15px;
            }}
            .logo {{
                height: 50px;
            }}
            .email-title {{
                font-size: 24px;
            }}
            .email-body {{
                padding: 20px;
            }}
            .contact-links {{
                flex-direction: column;
                gap: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="email-header">
            <div class="logo-container">
                <img src="https://i.postimg.cc/YqKYfsQd/snl.png" alt="Smart N Light Innovations" class="logo">
            </div>
            <div class="email-title">{subject}</div>
            <div class="email-subtitle">Freshers Fiesta 2025 - Smart N Light Innovations</div>
        </div>
        
        <div class="email-body">
            <div class="event-highlight">
                <h3 style="margin: 0 0 10px 0;">🎉 Freshers Fiesta 2025</h3>
                <p style="margin: 0; opacity: 0.9;">November 09, 2025 | SPHN GROUNDS</p>
            </div>
            
            <div class="message-content">
                {message}
            </div>
            
            <div class="developer-info">
                <h4 style="margin: 0 0 10px 0; color: #155724;">🛠️ Developed by Smart N Light Innovations</h4>
                <p style="margin: 0; color: #155724;">
                    Contact us 24/7 for technical support and inquiries
                </p>
            </div>
            
            <div class="contact-info">
                <strong>For any queries, please contact:</strong><br>
                Smart N Light Innovations<br>
                Phone: <a href="tel:+919059160424" style="color: #3498db; text-decoration: none;">+91 9059160424</a> (Available 24/7)<br>
                Email: <a href="mailto:smartnlightinnovations@gmail.com" style="color: #3498db; text-decoration: none;">smartnlightinnovations@gmail.com</a>
            </div>
        </div>
        
        <div class="email-footer">
            <div class="footer-logos">
                <img src="https://i.postimg.cc/YqKYfsQd/snl.png" alt="Smart N Light Innovations" class="footer-logo">
            </div>
            
            <div class="company-name">Smart N Light Innovations</div>
            
            <div class="contact-links">
                <a href="https://smartnlightinnovation.netlify.app" target="_blank">
                    <i class="fas fa-globe"></i> Visit Our Website
                </a>
                <a href="https://wa.me/919059160424" target="_blank">
                    <i class="fab fa-whatsapp"></i> WhatsApp (24/7)
                </a>
                <a href="mailto:smartnlightinnovations@gmail.com">
                    <i class="fas fa-envelope"></i> Email Us
                </a>
            </div>
            
            <div class="copyright">
                &copy; {datetime.now().year} Smart N Light Innovations. All rights reserved.
            </div>
        </div>
    </div>
</body>
</html>
                        """

                        # Plain text version
                        text_content = f"""
{subject}

Freshers Fiesta 2025 - Smart N Light Innovations

{message}

🛠️ Developed by Smart N Light Innovations
Contact us 24/7 for technical support and inquiries

FOR ANY QUERIES:
----------------
Smart N Light Innovations
Phone: +91 9059160424 (Available 24/7)
Email: smartnlightinnovations@gmail.com

COMPANY INFORMATION:
-------------------
Website: https://smartnlightinnovation.netlify.app
WhatsApp: +91 9059160424
Email: smartnlightinnovations@gmail.com

EVENT DETAILS:
-------------
Freshers Fiesta 2025
Date: November 09, 2025
Location: SPHN GROUNDS

© {datetime.now().year} Smart N Light Innovations. All rights reserved.
                        """

                        msg = Message(
                            subject=subject,
                            recipients=[recipient['email']],
                            body=text_content,
                            html=html_content
                        )
                        
                        # Add attachments
                        for attachment in attachments:
                            try:
                                with open(attachment['file_path'], 'rb') as f:
                                    msg.attach(
                                        filename=attachment['filename'],
                                        content_type=attachment['content_type'],
                                        data=f.read(),
                                        disposition='attachment'
                                    )
                            except Exception as e:
                                app.logger.error(f"Failed to attach file {attachment['filename']}: {str(e)}")
                        
                        mail.send(msg)
                        sent_count += 1
                        print(f"✅ Email sent to: {recipient['email']}")
                        
                    except Exception as e:
                        failed_count += 1
                        app.logger.error(f"Failed to send to {recipient['email']}: {str(e)}")
                
                # Update log with actual sent count
                try:
                    if os.path.exists(EMAIL_LOGS_FILE):
                        with open(EMAIL_LOGS_FILE, 'r') as f:
                            email_logs = json.load(f)
                        
                        for log in reversed(email_logs):
                            if log['id'] == email_log['id']:
                                log['actually_sent'] = sent_count
                                log['failed_count'] = failed_count
                                log['completion_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                break
                        
                        with open(EMAIL_LOGS_FILE, 'w') as f:
                            json.dump(email_logs, f, indent=4)
                            
                        print(f"✅ Email sending completed: {sent_count} sent, {failed_count} failed")
                        
                except Exception as e:
                    app.logger.error(f"Failed to update email log: {str(e)}")
        
        # Start email sending in background
        threading.Thread(target=send_messages).start()
        
        flash(f'Message is being sent to {len(recipients)} recipients', 'success')
        return redirect(url_for('message_center'))
    
    # Load email history for display
    email_history = []
    try:
        if os.path.exists(EMAIL_LOGS_FILE):
            with open(EMAIL_LOGS_FILE, 'r') as f:
                email_history = json.load(f)
                email_history.reverse()
    except Exception as e:
        app.logger.error(f"Failed to load email history: {str(e)}")
    
    return render_template('message_center.html', email_history=email_history)

@app.route('/get-email/<email_id>')
def get_email(email_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        with open(EMAIL_LOGS_FILE, 'r') as f:
            email_logs = json.load(f)
        
        email = next((e for e in email_logs if e['id'] == email_id), None)
        
        if email:
            return jsonify({
                'success': True,
                'email': email
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Email not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/resend-email/<email_id>', methods=['POST'])
def resend_email(email_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        with open(EMAIL_LOGS_FILE, 'r') as f:
            email_logs = json.load(f)
        
        email_to_resend = next((e for e in email_logs if e['id'] == email_id), None)
        
        if not email_to_resend:
            return jsonify({'success': False, 'message': 'Email not found'}), 404
        
        # Send emails in background thread
        def send_messages():
            with app.app_context():
                sent_count = 0
                for recipient in email_to_resend.get('recipients', []):
                    try:
                        msg = Message(
                            subject=f"Resent: {email_to_resend['subject']}",
                            recipients=[recipient['email']],
                            html=render_template(
                                'email_message.html',
                                subject=email_to_resend['subject'],
                                message=email_to_resend['message'],
                                recipient=recipient
                            )
                        )
                        
                        # If you want to include original attachments in resend,
                        # you would need to store them differently (not in this example)
                        
                        mail.send(msg)
                        sent_count += 1
                    except Exception as e:
                        app.logger.error(f"Failed to resend to {recipient['email']}: {str(e)}")
                
                # Create new log entry for the resend
                new_log = {
                    'id': str(uuid.uuid4()),
                    'subject': f"Resent: {email_to_resend['subject']}",
                    'message': email_to_resend['message'],
                    'recipients_type': 'resend-' + email_to_resend['id'],
                    'total_recipients': len(email_to_resend.get('recipients', [])),
                    'actually_sent': sent_count,
                    'sent_by': session.get('admin_id', 'unknown') + ' (resend)',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'original_email_id': email_id,
                    'attachments': email_to_resend.get('attachments', [])
                }
                
                try:
                    email_logs.append(new_log)
                    with open(EMAIL_LOGS_FILE, 'w') as f:
                        json.dump(email_logs, f, indent=4)
                except Exception as e:
                    app.logger.error(f"Failed to save resend log: {str(e)}")
        
        threading.Thread(target=send_messages).start()
        
        return jsonify({'success': True, 'message': 'Email is being resent'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit



@app.route('/debug-email')
def debug_email():
    try:
        print("🔧 Testing email configuration...")
        print(f"📧 Server: {app.config.get('MAIL_SERVER')}")
        print(f"📧 Port: {app.config.get('MAIL_PORT')}")
        print(f"📧 TLS: {app.config.get('MAIL_USE_TLS')}")
        print(f"📧 SSL: {app.config.get('MAIL_USE_SSL', 'Not set')}")
        print(f"📧 Username: {app.config.get('MAIL_USERNAME')}")
        print(f"📧 Password length: {len(app.config.get('MAIL_PASSWORD', ''))}")
        
        # Test basic connection
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex(('smtp.gmail.com', 587))
            if result == 0:
                print("✅ Network connection to smtp.gmail.com:587 is OK")
            else:
                print(f"❌ Cannot reach smtp.gmail.com:587 - error {result}")
            sock.close()
        except Exception as e:
            print(f"❌ Network test failed: {e}")
        
        # Test SMTP connection
        try:
            with mail.connect() as conn:
                print("✅ SMTP connection successful!")
                return "Email configuration is correct! SMTP connection successful."
        except Exception as e:
            print(f"❌ SMTP connection failed: {str(e)}")
            return f"SMTP connection failed: {str(e)}"
        
    except Exception as e:
        return f"Debug error: {str(e)}"

@app.route('/success')
def success():
    """Success page after registration"""
    individual_data = session.get('individual_data')
    qr_img_base64 = session.get('qr_img_base64')
    
    if not individual_data or not qr_img_base64:
        flash('Registration data not found', 'error')
        return redirect(url_for('register'))
    
    # Generate the ticket image for email attachment
    ticket_image_data = generate_ticket_image(individual_data, qr_img_base64)
    
    return render_template('success.html', 
                         individual=individual_data, 
                         qr_img=qr_img_base64,
                         ticket_image_data=ticket_image_data)
@app.route('/payment', methods=['GET', 'POST'])
def payment():
    """Payment processing route"""
    # Load hackathon config
    try:
        with open(HACKATHON_CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except:
        config = {'payment_required': True}
    
    if not config.get('payment_required'):
        flash('This hackathon does not require payment', 'info')
        return redirect(url_for('register_enhanced'))
    
    # Check for individual data instead of team data
    if 'individual_data' not in session:
        flash('Please complete your registration first', 'error')
        return redirect(url_for('register_enhanced'))
    
    individual_data = session['individual_data']
    registration_fee = session.get('registration_fee', 500)
    
    # Verify the individual hasn't already completed payment
    with open(DATABASE_FILE, 'r') as f:
        try:
            data = json.load(f)
            existing_individual = next((ind for ind in data.get('individuals', []) if ind['individual_id'] == individual_data['individual_id']), None)
            if existing_individual and existing_individual.get('payment_id'):
                flash('This registration has already completed payment', 'error')
                session.pop('individual_data', None)
                session.pop('registration_fee', None)
                return redirect(url_for('register_enhanced'))
        except json.JSONDecodeError:
            pass
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method', 'online')
        
        if payment_method == 'online':
            payment_id = request.form.get('payment_id')
            if not payment_id:
                flash('Please enter your payment ID', 'error')
                return redirect(url_for('payment'))
            
            # Handle file upload for online payments only
            payment_screenshot = None
            if 'payment_screenshot' in request.files:
                file = request.files['payment_screenshot']
                if file and file.filename != '' and allowed_file(file.filename):
                    # Ensure upload directory exists
                    upload_dir = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Generate secure filename
                    file_ext = file.filename.rsplit('.', 1)[1].lower()
                    filename = f"payment_{individual_data['individual_id']}.{file_ext}"
                    file_path = os.path.join(upload_dir, filename)
                    
                    # Save file
                    file.save(file_path)
                    print(f"DEBUG: Saved payment screenshot to: {file_path}")
                    print(f"DEBUG: File exists: {os.path.exists(file_path)}")
                    
                    payment_screenshot = filename
                elif file.filename:
                    flash('Invalid file type for payment screenshot', 'error')
                    return redirect(url_for('payment'))
            
            # Update individual data with payment info
            individual_data['payment_method'] = 'online'
            individual_data['payment_verified'] = False
            individual_data['payment_id'] = payment_id
            individual_data['payment_screenshot'] = payment_screenshot
            individual_data['cash_receipt_photo'] = None  # Clear cash receipt if any
        
        else:  # Cash payment - REMOVED FILE UPLOAD FUNCTIONALITY
            cash_receiver_name = request.form.get('cash_receiver_name')
            cash_received_at = request.form.get('cash_received_at')
            
            if not cash_receiver_name or not cash_received_at:
                flash('Please fill all required fields for cash payment', 'error')
                return redirect(url_for('payment'))
            
            # NO FILE UPLOAD FOR CASH PAYMENTS - REMOVED THE FILE UPLOAD LOGIC
            # Update individual data with cash payment info
            individual_data['payment_method'] = 'cash'
            individual_data['payment_verified'] = False
            individual_data['cash_receiver_name'] = cash_receiver_name
            individual_data['cash_received_at'] = cash_received_at
            individual_data['cash_receipt_photo'] = None  # No file upload for cash payments
            individual_data['payment_screenshot'] = None  # Clear payment screenshot if any
            individual_data['payment_id'] = None  # Clear payment ID for cash payments
        
        # Common fields for both payment methods
        individual_data['payment_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        individual_data['registration_fee'] = registration_fee
        
        # Save to database with thread-safe locking
        with team_id_lock:
            try:
                with open(DATABASE_FILE, 'r+') as f:
                    try:
                        data = json.load(f)
                        if 'individuals' not in data:
                            data['individuals'] = []
                        
                        # Find and update the existing individual record
                        updated = False
                        for idx, individual in enumerate(data['individuals']):
                            if individual['individual_id'] == individual_data['individual_id']:
                                # Update all fields
                                data['individuals'][idx].update({
                                    'payment_method': individual_data['payment_method'],
                                    'payment_verified': individual_data['payment_verified'],
                                    'payment_date': individual_data['payment_date'],
                                    'registration_fee': individual_data['registration_fee'],
                                    'payment_screenshot': individual_data.get('payment_screenshot'),
                                    'cash_receipt_photo': individual_data.get('cash_receipt_photo'),
                                    'payment_id': individual_data.get('payment_id'),
                                    'cash_receiver_name': individual_data.get('cash_receiver_name'),
                                    'cash_received_at': individual_data.get('cash_received_at'),
                                    'receipt_number': individual_data.get('receipt_number')
                                })
                                updated = True
                                break
                        
                        if not updated:
                            # This shouldn't happen, but if it does, append the full data
                            data['individuals'].append(individual_data)
                        
                        f.seek(0)
                        json.dump(data, f, indent=4)
                        f.truncate()
                        
                        print(f"DEBUG: Updated database for {individual_data['individual_id']}")
                        print(f"DEBUG: Payment screenshot: {individual_data.get('payment_screenshot')}")
                        print(f"DEBUG: Cash receipt: {individual_data.get('cash_receipt_photo')}")
                        
                    except json.JSONDecodeError as e:
                        print(f"DEBUG: JSON decode error: {e}")
                        # Handle corrupt file by creating new one
                        data = {'individuals': [individual_data]}
                        with open(DATABASE_FILE, 'w') as f:
                            json.dump(data, f, indent=4)
            except Exception as e:
                flash('Error saving payment details. Please try again.', 'error')
                print(f"Error in payment processing: {str(e)}")
                return redirect(url_for('payment'))
        
        # Generate QR code for individual - FIXED: Handle both 'rollno' and 'roll_number'
        qr_data = {
            'individual_id': individual_data['individual_id'],
            'name': individual_data['name'],
            'rollno': individual_data.get('rollno') or individual_data.get('roll_number', ''),  # Handle both keys
            'year': individual_data['year'],
            'branch': individual_data['branch'],
            'fee_paid': registration_fee
        }
        
        qr_img = generate_qr_code_image(json.dumps(qr_data))
        qr_img_base64 = base64.b64encode(qr_img.getvalue()).decode('utf-8')

        # Generate ticket image for email attachment
        ticket_image_path = generate_ticket_image_for_email(individual_data, qr_img_base64)
        
        # Store in session for success page
        session['individual_data'] = individual_data
        session['qr_img_base64'] = qr_img_base64
        session['ticket_generated'] = True

        # Send thank you email to the individual with ticket attachment
        if individual_data['email']:
            threading.Thread(
                target=send_thank_you_email_individual, 
                args=(individual_data['email'], individual_data, qr_img_base64, ticket_image_path)
            ).start()
        
        flash('Payment details submitted successfully! Your registration will be complete after admin verification.', 'success')
        return render_template('success.html', individual=individual_data, qr_img=qr_img_base64)
    
    return render_template('payment.html', 
                         individual=individual_data, 
                         phonepe_qr=PHONEPE_QR_CODE,
                         registration_fee=registration_fee)

def generate_ticket_image(individual_data, qr_img_base64):
    """Generate ticket image using HTML2Canvas via JavaScript"""
    # This function will be called by the template to generate the image
    # The actual image generation happens in the browser
    return {
        'individual_id': individual_data['individual_id'],
        'name': individual_data['name'],
        'qr_data': qr_img_base64
    }

def generate_ticket_image_for_email(individual_data, qr_img_base64):
    """Generate a professional ticket image for email attachment"""
    try:
        # Create temporary directory for ticket images
        ticket_dir = os.path.join(app.root_path, 'static', 'temp_tickets')
        os.makedirs(ticket_dir, exist_ok=True)
        
        filename = f"ticket_{individual_data['individual_id']}.png"
        ticket_path = os.path.join(ticket_dir, filename)
        
        # Create a PDF buffer
        pdf_buffer = BytesIO()
        
        # Create PDF with custom size for ticket (4x6 inches)
        custom_size = (4 * 72, 6 * 72)  # 4x6 inches in points
        c = canvas.Canvas(pdf_buffer, pagesize=custom_size)
        
        # Set up colors
        primary_color = colors.HexColor('#1e3c72')
        secondary_color = colors.HexColor('#2a5298')
        accent_color = colors.HexColor('#f72585')
        
        # Draw background with gradient effect
        c.setFillColor(colors.white)
        c.rect(0, 0, custom_size[0], custom_size[1], fill=1, stroke=0)
        
        # Add header section
        c.setFillColor(primary_color)
        c.rect(0, custom_size[1] - 80, custom_size[0], 80, fill=1, stroke=0)
        
        # Header text
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(custom_size[0] / 2, custom_size[1] - 35, "CREATORS CLUB")
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(custom_size[0] / 2, custom_size[1] - 55, "36 HOURS HACKATHON")
        
        # Add event details
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(20, custom_size[1] - 100, "EVENT TICKET")
        
        # Draw separator line
        c.setStrokeColor(primary_color)
        c.setLineWidth(1)
        c.line(20, custom_size[1] - 110, custom_size[0] - 20, custom_size[1] - 110)
        
        # Participant information
        info_y = custom_size[1] - 130
        c.setFont("Helvetica-Bold", 9)
        c.drawString(20, info_y, "NAME:")
        c.setFont("Helvetica", 9)
        c.drawString(60, info_y, individual_data['name'][:25])
        
        info_y -= 20
        c.setFont("Helvetica-Bold", 9)
        c.drawString(20, info_y, "ID:")
        c.setFont("Helvetica", 9)
        c.drawString(60, info_y, individual_data['individual_id'])
        
        info_y -= 20
        c.setFont("Helvetica-Bold", 9)
        c.drawString(20, info_y, "COLLEGE:")
        c.setFont("Helvetica", 9)
        college_text = individual_data['college'][:20] + "..." if len(individual_data['college']) > 20 else individual_data['college']
        c.drawString(60, info_y, college_text)
        
        info_y -= 20
        c.setFont("Helvetica-Bold", 9)
        c.drawString(20, info_y, "BRANCH:")
        c.setFont("Helvetica", 9)
        c.drawString(60, info_y, individual_data['branch'])
        
        info_y -= 20
        c.setFont("Helvetica-Bold", 9)
        c.drawString(20, info_y, "YEAR:")
        c.setFont("Helvetica", 9)
        c.drawString(60, info_y, individual_data['year'])
        
        # Add QR code on the right side
        qr_size = 120
        qr_x = custom_size[0] - qr_size - 20
        qr_y = custom_size[1] - 280
        
        try:
            qr_img_data = base64.b64decode(qr_img_base64)
            qr_image = ImageReader(BytesIO(qr_img_data))
            c.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size)
        except Exception as e:
            print(f"Error drawing QR code: {e}")
            # Fallback: Draw a placeholder
            c.setFillColor(colors.lightgrey)
            c.rect(qr_x, qr_y, qr_size, qr_size, fill=1, stroke=0)
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 8)
            c.drawString(qr_x + 10, qr_y + qr_size/2, "QR CODE")
        
        # Add event date and location
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(20, 80, "DATE: JULY 21-23, 2025")
        c.drawString(20, 65, "LOCATION: SPHOORTHY ENGINEERING COLLEGE")
        
        # Add footer instructions
        c.setFillColor(colors.gray)
        c.setFont("Helvetica-Oblique", 7)
        c.drawString(20, 40, "Present this ticket at event registration")
        c.drawString(20, 30, "Keep this ticket accessible on your phone")
        
        # Add generated timestamp
        c.setFont("Helvetica", 6)
        c.drawString(20, 15, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        c.save()
        
        # Convert PDF to PNG (simplified approach - in production use proper PDF to image conversion)
        # For now, we'll create a simple PNG using the QR code as the main visual
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a new image
        img_width, img_height = 600, 400
        img = Image.new('RGB', (img_width, img_height), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            # Load a font (using default font if not available)
            try:
                font_large = ImageFont.truetype("arial.ttf", 24)
                font_medium = ImageFont.truetype("arial.ttf", 18)
                font_small = ImageFont.truetype("arial.ttf", 14)
                font_xsmall = ImageFont.truetype("arial.ttf", 12)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
                font_xsmall = ImageFont.load_default()
            
            # Draw header
            draw.rectangle([0, 0, img_width, 80], fill='#1e3c72')
            draw.text((img_width//2, 30), "CREATORS CLUB", fill='white', font=font_large, anchor='mm')
            draw.text((img_width//2, 60), "36 HOURS HACKATHON", fill='white', font=font_medium, anchor='mm')
            
            # Draw participant info
            draw.text((20, 100), f"Name: {individual_data['name']}", fill='black', font=font_medium)
            draw.text((20, 130), f"ID: {individual_data['individual_id']}", fill='black', font=font_small)
            draw.text((20, 160), f"College: {individual_data['college']}", fill='black', font=font_small)
            draw.text((20, 190), f"Branch: {individual_data['branch']}", fill='black', font=font_small)
            draw.text((20, 220), f"Year: {individual_data['year']}", fill='black', font=font_small)
            
            # Draw QR code
            qr_img = Image.open(BytesIO(base64.b64decode(qr_img_base64)))
            qr_img = qr_img.resize((150, 150))
            img.paste(qr_img, (img_width - 170, 100))
            
            # Draw event details
            draw.text((20, 260), "Date: July 21-23, 2025", fill='black', font=font_small)
            draw.text((20, 290), "Location: Sphoorthy Engineering College", fill='black', font=font_small)
            
            # Draw footer
            draw.text((20, 350), "Present this ticket at event registration", fill='gray', font=font_xsmall)
            draw.text((20, 370), f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", fill='gray', font=font_xsmall)
            
        except Exception as e:
            print(f"Error creating PIL image: {e}")
            # Create a simple fallback image
            draw.rectangle([0, 0, img_width, img_height], fill='white')
            draw.text((img_width//2, img_height//2), f"Ticket: {individual_data['individual_id']}", fill='black', anchor='mm')
        
        # Save the image
        img.save(ticket_path, 'PNG')
        print(f"✅ Ticket image generated: {ticket_path}")
        
        return ticket_path
        
    except Exception as e:
        print(f"❌ Error generating ticket image: {e}")
        return None

def send_thank_you_email_individual(recipient_email, individual_data, qr_img_base64, ticket_image_path=None):
    """Send thank you email to individual with QR code and ticket image attachment"""
    def send_email():
        with app.app_context():
            try:
                # Load homepage config for event details
                try:
                    with open(HOMEPAGE_CONFIG_FILE, 'r') as f:
                        homepage_config = json.load(f)
                except:
                    homepage_config = {
                        'hero_title': 'Freshers Fiesta 2025',
                        'event_date': 'November 09, 2025',
                        'event_location': 'SPHN GROUNDS'
                    }

                subject = f"Registration Confirmed - {individual_data['name']}"
                
                # HTML email content
                html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #444;
            max-width: 600px;
            margin: 0 auto;
            padding: 0;
            background-color: #f9f9f9;
        }}
        .email-container {{
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            margin: 20px auto;
        }}
        .email-header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 30px 20px;
            text-align: center;
            color: white;
        }}
        .email-title {{
            font-size: 28px;
            font-weight: 700;
            margin: 10px 0;
            color: white;
            letter-spacing: 1px;
        }}
        .email-subtitle {{
            font-size: 16px;
            opacity: 0.9;
        }}
        .email-body {{
            padding: 30px;
        }}
        .ticket-preview {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            color: white;
            text-align: center;
        }}
        .info-section {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #3498db;
        }}
        .qr-section {{
            text-align: center;
            margin: 25px 0;
        }}
        .qr-code {{
            max-width: 200px;
            height: auto;
            margin: 10px auto;
            display: block;
            border: 2px solid #eaeaea;
            border-radius: 8px;
            padding: 10px;
            background: white;
        }}
        .attachment-note {{
            background-color: #e8f5e8;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #28a745;
        }}
        .developer-info {{
            background-color: #fff3cd;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #ffc107;
            text-align: center;
        }}
        .email-footer {{
            background-color: #f5f7fa;
            padding: 25px;
            text-align: center;
            border-top: 1px solid #eaeaea;
        }}
        .contact-links {{
            margin: 20px 0;
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 15px;
        }}
        .contact-links a {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            color: #3498db;
            text-decoration: none;
            font-weight: 500;
            padding: 8px 12px;
            border-radius: 6px;
            background-color: rgba(52, 152, 219, 0.1);
        }}
        .copyright {{
            font-size: 13px;
            color: #7f8c8d;
            margin-top: 20px;
        }}
        @media only screen and (max-width: 600px) {{
            .email-title {{
                font-size: 24px;
            }}
            .email-body {{
                padding: 20px;
            }}
            .contact-links {{
                flex-direction: column;
                gap: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="email-header">
            <div class="email-title">REGISTRATION CONFIRMED</div>
            <div class="email-subtitle">Freshers Fiesta 2025 - Your Journey Begins!</div>
        </div>
        
        <div class="email-body">
            <div class="ticket-preview">
                <h3 style="margin: 0 0 10px 0;">🎫 Your Event Ticket</h3>
                <p style="margin: 0; opacity: 0.9;">Attached to this email for your convenience</p>
            </div>
            
            <div class="info-section">
                <h4 style="margin: 0 0 15px 0; color: #1e3c72;">Registration Details</h4>
                <p><strong>Name:</strong> {individual_data['name']}</p>
                <p><strong>Registration ID:</strong> {individual_data['individual_id']}</p>
                <p><strong>Email:</strong> {individual_data['email']}</p>
                <p><strong>College:</strong> {individual_data['college']}</p>
                <p><strong>Branch:</strong> {individual_data['branch']}</p>
                <p><strong>Year:</strong> {individual_data['year']}</p>
                <p><strong>Registration Date:</strong> {individual_data['registration_date']}</p>
            </div>
            
            <div class="qr-section">
                <h4 style="color: #1e3c72;">Your Event QR Code</h4>
                <img src="data:image/png;base64,{qr_img_base64}" alt="QR Code" class="qr-code" />
                <p style="color: #666; font-size: 14px;">Present this QR code at the event for check-in</p>
            </div>
            
            <div class="developer-info">
                <h4 style="margin: 0 0 10px 0; color: #856404;">🛠️ Developed by Smart N Light Innovations</h4>
                <p style="margin: 0; color: #856404;">
                    Contact us 24/7 for technical support and inquiries
                </p>
            </div>
            
            <div class="attachment-note">
                <h4 style="margin: 0 0 10px 0; color: #155724;">📎 Ticket Attached</h4>
                <p style="margin: 0; color: #155724;">
                    Your event ticket has been attached to this email as <strong>event_ticket.png</strong>. 
                    You can download it and present it at the event registration desk.
                </p>
            </div>
            
            <div style="background-color: #e2f0fd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3498db;">
                <h4 style="margin: 0 0 10px 0; color: #0d6efd;">Next Steps</h4>
                <ul style="margin: 0; padding-left: 20px; color: #0d6efd;">
                    <li>Save your ticket image and QR code</li>
                    <li>Present them at the event registration</li>
                    <li>Keep this email for reference</li>
                    <li>You'll receive event updates as the date approaches</li>
                </ul>
            </div>
        </div>
        
        <div class="email-footer">
            <h4 style="margin: 0 0 15px 0; color: #1e3c72;">Smart N Light Innovations</h4>
            
            <div class="contact-links">
                <a href="https://smartnlightinnovation.netlify.app" target="_blank">
                    <i class="fas fa-globe"></i> Visit Our Website
                </a>
                <a href="https://wa.me/919059160424" target="_blank">
                    <i class="fab fa-whatsapp"></i> WhatsApp (24/7)
                </a>
                <a href="mailto:smartnlightinnovations@gmail.com">
                    <i class="fas fa-envelope"></i> Email Us
                </a>
            </div>
            
            <div class="copyright">
                &copy; {datetime.now().year} Smart N Light Innovations. All rights reserved.
            </div>
        </div>
    </div>
</body>
</html>
                """
                
                # Plain text version
                text = f"""
REGISTRATION CONFIRMED - FRESHERS FIESTA 2025

Dear {individual_data['name']},

Thank you for registering for Freshers Fiesta 2025!

YOUR REGISTRATION DETAILS:
Name: {individual_data['name']}
Registration ID: {individual_data['individual_id']}
Email: {individual_data['email']}
College: {individual_data['college']}
Branch: {individual_data['branch']}
Year: {individual_data['year']}
Registration Date: {individual_data['registration_date']}

EVENT DETAILS:
Event: Freshers Fiesta 2025
Date: November 09, 2025
Location: SPHN GROUNDS

DEVELOPER INFORMATION:
🛠️ Developed by Smart N Light Innovations
Contact us 24/7 for technical support and inquiries

YOUR EVENT TICKET:
Your event ticket has been attached to this email as event_ticket.png. 
Please download it and present it at the event registration desk.

NEXT STEPS:
- Save your ticket image and QR code
- Present them at the event registration
- Keep this email for reference
- You'll receive event updates as the date approaches

For any questions or technical support, please contact us:
Phone: +91 9059160424 (Available 24/7)
Website: https://smartnlightinnovation.netlify.app
Email: smartnlightinnovations@gmail.com

Smart N Light Innovations
© {datetime.now().year} All rights reserved.

Best regards,
Smart N Light Innovations Team
                """
                
                # Create message
                msg = Message(subject, recipients=[recipient_email])
                msg.body = text
                msg.html = html
                
                # Attach QR code
                qr_img_data = base64.b64decode(qr_img_base64)
                msg.attach(
                    filename="event_qr_code.png",
                    content_type="image/png",
                    data=qr_img_data
                )
                
                # Attach ticket image if available
                if ticket_image_path and os.path.exists(ticket_image_path):
                    with open(ticket_image_path, 'rb') as f:
                        msg.attach(
                            filename="event_ticket.png",
                            content_type="image/png",
                            data=f.read()
                        )
                    print(f"✅ Ticket image attached to email for {recipient_email}")
                else:
                    print(f"⚠️ Ticket image not found for attachment: {ticket_image_path}")
                
                # Send email
                mail.send(msg)
                print(f"✅ Email sent successfully to: {recipient_email}")
                
                # Clean up temporary ticket file after sending
                if ticket_image_path and os.path.exists(ticket_image_path):
                    try:
                        os.remove(ticket_image_path)
                        print(f"✅ Cleaned up temporary ticket file: {ticket_image_path}")
                    except Exception as e:
                        print(f"⚠️ Could not remove temporary file: {e}")
                
                return True
                
            except Exception as e:
                print(f"❌ Failed to send thank you email to {recipient_email}: {e}")
                # Clean up temporary file even if email fails
                if ticket_image_path and os.path.exists(ticket_image_path):
                    try:
                        os.remove(ticket_image_path)
                    except:
                        pass
                return False
    
    # Start the email sending in a background thread
    threading.Thread(target=send_email).start()
    return True

@app.route('/send-message', methods=['POST'])
def send_message():
    if 'attachments' in request.files:
        files = request.files.getlist('attachments')
        for file in files:
            if file.filename != '':
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                else:
                    flash('Invalid file type')
                    return redirect(request.url)
    # Rest of your message handling...
    
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    # Initialize before running  
    initialize_files()
    
    app.run(debug=True, host='0.0.0.0', port=5001)
