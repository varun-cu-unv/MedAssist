from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os
from urllib.parse import quote
from flask_mail import Mail, Message
from dotenv import load_dotenv
import datetime
import requests
import json
import difflib

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this')

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '69688986'),
    'database': os.getenv('DB_NAME', 'medassist_db')
}

def get_db_connection():
    """Create and return a database connection."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

def init_database():
    """Initialize the database and create tables if they don't exist."""
    try:
        # First, connect without specifying database to create it
        temp_config = DB_CONFIG.copy()
        temp_config.pop('database')
        
        connection = mysql.connector.connect(**temp_config)
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS medassist_db")
        cursor.close()
        connection.close()
        
        # Now connect to the database and create tables
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Create users table
            create_users_table = """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_users_table)
            
            # Create appointments table
            create_appointments_table = """
            CREATE TABLE IF NOT EXISTS appointments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                patient_name VARCHAR(100) NOT NULL,
                patient_email VARCHAR(100) NOT NULL,
                patient_phone VARCHAR(20) NOT NULL,
                specialty VARCHAR(50) NOT NULL,
                doctor VARCHAR(100) NOT NULL,
                appointment_date DATE NOT NULL,
                appointment_time TIME NOT NULL,
                appointment_type VARCHAR(50) NOT NULL,
                symptoms TEXT,
                insurance VARCHAR(50),
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
            cursor.execute(create_appointments_table)
            
            # Medical Records table
            create_medical_records_table = """
            CREATE TABLE IF NOT EXISTS medical_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                record_type VARCHAR(50) NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                date_recorded DATE NOT NULL,
                healthcare_provider VARCHAR(255),
                attachment_path VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
            cursor.execute(create_medical_records_table)
            
            # Medications table
            create_medications_table = """
            CREATE TABLE IF NOT EXISTS medications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                medication_name VARCHAR(255) NOT NULL,
                dosage VARCHAR(100),
                frequency VARCHAR(100),
                start_date DATE,
                end_date DATE,
                prescribing_doctor VARCHAR(255),
                notes TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
            cursor.execute(create_medications_table)
            
            # Vital Signs table
            create_vital_signs_table = """
            CREATE TABLE IF NOT EXISTS vital_signs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                measurement_date DATE NOT NULL,
                blood_pressure_systolic INT,
                blood_pressure_diastolic INT,
                heart_rate INT,
                temperature DECIMAL(4,1),
                weight DECIMAL(5,1),
                height DECIMAL(5,1),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
            cursor.execute(create_vital_signs_table)
            
            # Lab Results table
            create_lab_results_table = """
            CREATE TABLE IF NOT EXISTS lab_results (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                test_name VARCHAR(255) NOT NULL,
                result_value VARCHAR(255),
                reference_range VARCHAR(255),
                test_date DATE NOT NULL,
                lab_name VARCHAR(255),
                doctor_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
            cursor.execute(create_lab_results_table)
            
            # Emergency Contacts table
            create_emergency_contacts_table = """
            CREATE TABLE IF NOT EXISTS emergency_contacts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                contact_name VARCHAR(255) NOT NULL,
                relationship VARCHAR(100),
                phone_number VARCHAR(20) NOT NULL,
                email VARCHAR(255),
                is_primary BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
            cursor.execute(create_emergency_contacts_table)
            
            # Drug Info Cache table for local drug database
            create_drug_info_table = """
            CREATE TABLE IF NOT EXISTS drug_info_cache (
                id INT AUTO_INCREMENT PRIMARY KEY,
                generic_name VARCHAR(255) UNIQUE NOT NULL,
                brand_name VARCHAR(255),
                manufacturer VARCHAR(255),
                indications TEXT,
                dosage TEXT,
                warnings TEXT,
                side_effects TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_drug_info_table)
            
            connection.commit()
            cursor.close()
            connection.close()
            print("Database and tables created successfully!")
            
    except mysql.connector.Error as err:
        print(f"Error initializing database: {err}")

def send_welcome_email(username, email):
    """Send welcome email to new user."""
    try:
        msg = Message(
            subject='Welcome to MedAssist!',
            recipients=[email]
        )
        
        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #3B38A0, #4ECDC4); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .logo {{ font-size: 2rem; font-weight: bold; margin-bottom: 10px; }}
                .btn {{ background: #3B38A0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; display: inline-block; margin: 20px 0; }}
                .features {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .feature {{ margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">MedAssist</div>
                    <h1>Welcome to Your Health Journey!</h1>
                </div>
                <div class="content">
                    <h2>Hello {username}!</h2>
                    <p>Thank you for joining MedAssist - your AI-powered health companion.</p>
                    
                    <div class="features">
                        <h3>What you can do with MedAssist:</h3>
                        <div class="feature"><strong>AI Health Assistant</strong> - Get personalized health recommendations</div>
                        <div class="feature"><strong>Appointment Booking</strong> - Schedule medical appointments easily</div>
                        <div class="feature"><strong>Health Records</strong> - Manage your complete medical history</div>
                        <div class="feature"><strong>Medication Tracking</strong> - Track prescriptions and reminders</div>
                        <div class="feature"><strong>Drug Information Chat</strong> - Ask about any medication instantly</div>
                    </div>
                    
                    <p>Ready to get started?</p>
                    <a href="http://localhost:5000/dashboard" class="btn">Go to Dashboard</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        mail.send(msg)
        print(f"Welcome email sent to {email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_appointment_confirmation(appointment_data):
    """Send appointment confirmation email."""
    try:
        msg = Message(
            subject='Appointment Confirmation - MedAssist',
            recipients=[appointment_data['patient_email']]
        )
        
        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #3B38A0, #4ECDC4); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .appointment-details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4ECDC4; }}
                .detail-row {{ display: flex; justify-content: space-between; margin: 10px 0; }}
                .label {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>MedAssist</h1>
                    <h2>Appointment Confirmed!</h2>
                </div>
                <div class="content">
                    <p>Dear {appointment_data['patient_name']},</p>
                    <p>Your appointment has been successfully booked.</p>
                    
                    <div class="appointment-details">
                        <div class="detail-row">
                            <span class="label">Patient Name:</span>
                            <span>{appointment_data['patient_name']}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Doctor:</span>
                            <span>{appointment_data['doctor']}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Date:</span>
                            <span>{appointment_data['appointment_date']}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Time:</span>
                            <span>{appointment_data['appointment_time']}</span>
                        </div>
                    </div>
                    
                    <p>Thank you for choosing MedAssist!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        mail.send(msg)
        print(f"Appointment confirmation sent to {appointment_data['patient_email']}")
        return True
    except Exception as e:
        print(f"Error sending appointment email: {e}")
        return False

# Enhanced Drug Information Functions
def get_local_drug_info_with_fuzzy_search(drug_name):
    """Get drug information with fuzzy matching for common misspellings."""
    
    # Enhanced local drug database including cytarabine
    local_drugs = {
        'paracetamol': {
            'generic_name': 'Acetaminophen (Paracetamol)',
            'brand_name': 'Tylenol, Panadol, Calpol',
            'manufacturer': 'Various',
            'indications': 'Used to treat pain and reduce fever. Commonly used for headaches, muscle aches, arthritis, backaches, toothaches, colds, and fevers.',
            'dosage': 'Adults: 325-650 mg every 4-6 hours or 1000 mg every 6-8 hours. Maximum 4000 mg per day.',
            'warnings': 'Do not exceed recommended dose. Overdose can cause serious liver damage that may be fatal.',
            'side_effects': 'Generally well tolerated when used as directed. Rare side effects may include nausea, stomach pain, loss of appetite.'
        },
        'acetaminophen': {
            'generic_name': 'Acetaminophen',
            'brand_name': 'Tylenol, Panadol, Calpol',
            'manufacturer': 'Various',
            'indications': 'Used to treat pain and reduce fever. Commonly used for headaches, muscle aches, arthritis, backaches, toothaches, colds, and fevers.',
            'dosage': 'Adults: 325-650 mg every 4-6 hours or 1000 mg every 6-8 hours. Maximum 4000 mg per day.',
            'warnings': 'Do not exceed recommended dose. Overdose can cause serious liver damage.',
            'side_effects': 'Generally well tolerated. May cause nausea, stomach pain, loss of appetite, or rash in rare cases.'
        },
        'ibuprofen': {
            'generic_name': 'Ibuprofen',
            'brand_name': 'Advil, Motrin, Nurofen',
            'manufacturer': 'Various',
            'indications': 'NSAID used to reduce fever and treat pain or inflammation caused by conditions such as headache, toothache, back pain, arthritis.',
            'dosage': 'Adults: 200-400 mg every 4-6 hours as needed. Maximum 1200 mg per day for OTC use.',
            'warnings': 'May increase risk of heart attack or stroke. Can cause stomach bleeding and ulcers.',
            'side_effects': 'Common: Stomach upset, heartburn, nausea, vomiting, headache, diarrhea, constipation, dizziness.'
        },
        'aspirin': {
            'generic_name': 'Aspirin (Acetylsalicylic Acid)',
            'brand_name': 'Bayer, Bufferin, Ecotrin',
            'manufacturer': 'Various',
            'indications': 'Used to reduce fever and relieve mild to moderate pain. Also used in low doses to prevent heart attacks and strokes.',
            'dosage': 'Adults: 325-650 mg every 4 hours for pain/fever. For cardiovascular protection: 81 mg daily.',
            'warnings': 'Can cause stomach bleeding and ulcers. Do not give to children under 16 due to risk of Reye\'s syndrome.',
            'side_effects': 'Common: Stomach irritation, heartburn, drowsiness, headache, mild nausea.'
        },
        'metformin': {
            'generic_name': 'Metformin',
            'brand_name': 'Glucophage, Fortamet, Glumetza',
            'manufacturer': 'Various',
            'indications': 'Used to treat type 2 diabetes mellitus. Helps control blood sugar levels by decreasing glucose production in the liver.',
            'dosage': 'Adults: Usually start with 500 mg twice daily or 850 mg once daily with meals. May gradually increase to maximum 2000-2550 mg daily.',
            'warnings': 'May cause lactic acidosis (rare but serious). Avoid excessive alcohol consumption. Monitor kidney function regularly.',
            'side_effects': 'Common: Diarrhea, nausea, vomiting, gas, weakness, indigestion, abdominal discomfort, headache, metallic taste.'
        },
        'lisinopril': {
            'generic_name': 'Lisinopril',
            'brand_name': 'Prinivil, Zestril',
            'manufacturer': 'Various',
            'indications': 'ACE inhibitor used to treat high blood pressure (hypertension), heart failure, and to improve survival after heart attacks.',
            'dosage': 'Adults: Usually start with 10 mg once daily. May increase to 20-40 mg daily based on response.',
            'warnings': 'Can cause severe drop in blood pressure. May cause birth defects - do not use during pregnancy.',
            'side_effects': 'Common: Dry persistent cough, dizziness, headache, fatigue, nausea, low blood pressure.'
        },
        'amoxicillin': {
            'generic_name': 'Amoxicillin',
            'brand_name': 'Amoxil, Trimox',
            'manufacturer': 'Various',
            'indications': 'Penicillin antibiotic used to treat various bacterial infections including respiratory tract infections, urinary tract infections, skin infections.',
            'dosage': 'Adults: 250-500 mg every 8 hours or 500-875 mg every 12 hours. Complete full course even if feeling better.',
            'warnings': 'Do not use if allergic to penicillin. May reduce effectiveness of birth control pills.',
            'side_effects': 'Common: Nausea, vomiting, diarrhea, stomach pain, headache, dizziness.'
        },
        'omeprazole': {
            'generic_name': 'Omeprazole',
            'brand_name': 'Prilosec, Losec',
            'manufacturer': 'Various',
            'indications': 'Proton pump inhibitor used to treat GERD, stomach ulcers, duodenal ulcers. Reduces stomach acid production.',
            'dosage': 'Adults: 20-40 mg once daily before breakfast. Take 30-60 minutes before eating.',
            'warnings': 'Long-term use may increase risk of bone fractures, vitamin B12 deficiency, and kidney problems.',
            'side_effects': 'Common: Headache, diarrhea, nausea, vomiting, stomach pain, gas, dizziness.'
        },
        'cytarabine': {
            'generic_name': 'Cytarabine',
            'brand_name': 'Cytosar-U, Tarabine PFS, Ara-C',
            'manufacturer': 'Various',
            'indications': 'Antineoplastic agent used to treat acute lymphocytic leukemia, acute myelogenous leukemia, chronic myelogenous leukemia, and certain lymphomas. Works by interfering with DNA synthesis in cancer cells.',
            'dosage': 'Dosage varies greatly depending on the specific condition being treated, patient factors, and treatment protocol. Typically given as intravenous infusion. Common regimens range from 100-200 mg/m² daily for 5-10 days. Must be administered by qualified healthcare professionals only.',
            'warnings': 'Severe myelosuppression (bone marrow suppression), cytarabine syndrome, neurotoxicity at high doses, hepatotoxicity. Requires close monitoring of blood counts, liver function, and neurological status. Only for use under strict medical supervision in specialized cancer treatment facilities.',
            'side_effects': 'Common: Severe nausea and vomiting, diarrhea, mouth sores, fever, bone marrow suppression leading to increased infection risk, bleeding, and anemia. Serious: Liver toxicity, lung problems, neurological effects (especially at high doses), severe infections due to immunosuppression.'
        }
    }
    
    # Common misspellings and alternative names
    drug_aliases = {
        'paracitamol': 'paracetamol',
        'paracitemol': 'paracetamol',
        'tylenol': 'acetaminophen',
        'panadol': 'paracetamol',
        'advil': 'ibuprofen',
        'motrin': 'ibuprofen',
        'glucophage': 'metformin',
        'prinivil': 'lisinopril',
        'zestril': 'lisinopril',
        'cytosar': 'cytarabine',
        'ara-c': 'cytarabine',
        'cytosar-u': 'cytarabine',
        'tarabine': 'cytarabine'
    }
    
    drug_name_lower = drug_name.lower().strip()
    
    # Check direct match first
    if drug_name_lower in local_drugs:
        return local_drugs[drug_name_lower]
    
    # Check aliases for common misspellings
    if drug_name_lower in drug_aliases:
        corrected_name = drug_aliases[drug_name_lower]
        if corrected_name in local_drugs:
            result = local_drugs[corrected_name].copy()
            result['_corrected_from'] = drug_name
            result['_corrected_to'] = corrected_name
            return result
    
    # Use fuzzy matching for close spellings
    drug_names = list(local_drugs.keys()) + list(drug_aliases.keys())
    close_matches = difflib.get_close_matches(drug_name_lower, drug_names, n=1, cutoff=0.6)
    
    if close_matches:
        match = close_matches[0]
        if match in local_drugs:
            result = local_drugs[match].copy()
            result['_corrected_from'] = drug_name
            result['_corrected_to'] = match
            return result
        elif match in drug_aliases:
            corrected_name = drug_aliases[match]
            if corrected_name in local_drugs:
                result = local_drugs[corrected_name].copy()
                result['_corrected_from'] = drug_name
                result['_corrected_to'] = corrected_name
                return result
    
    return None

def search_openfda_exact(drug_name):
    """Search OpenFDA with exact generic name match."""
    try:
        url = f"https://api.fda.gov/drug/label.json?search=openfda.generic_name.exact:\"{drug_name}\"&limit=1"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                return parse_fda_result(data['results'][0])
    except Exception as e:
        print(f"OpenFDA exact search error: {e}")
    
    return None

def search_openfda_broad(drug_name):
    """Search OpenFDA with broader search terms."""
    try:
        url = f"https://api.fda.gov/drug/label.json?search=openfda.generic_name:{drug_name}&limit=1"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                return parse_fda_result(data['results'][0])
        
        # Try searching in brand names too
        url = f"https://api.fda.gov/drug/label.json?search=openfda.brand_name:{drug_name}&limit=1"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                return parse_fda_result(data['results'][0])
                
    except Exception as e:
        print(f"OpenFDA broad search error: {e}")
    
    return None

def parse_fda_result(result):
    """Parse FDA API result into standardized format."""
    try:
        return {
            'generic_name': result.get('openfda', {}).get('generic_name', ['Unknown'])[0],
            'brand_name': result.get('openfda', {}).get('brand_name', ['N/A'])[0] if result.get('openfda', {}).get('brand_name') else 'N/A',
            'manufacturer': result.get('openfda', {}).get('manufacturer_name', ['N/A'])[0] if result.get('openfda', {}).get('manufacturer_name') else 'N/A',
            'indications': result.get('indications_and_usage', ['No information available'])[0] if result.get('indications_and_usage') else 'No information available',
            'dosage': result.get('dosage_and_administration', ['No information available'])[0] if result.get('dosage_and_administration') else 'No information available',
            'warnings': result.get('warnings', ['No warnings listed'])[0] if result.get('warnings') else 'No warnings listed',
            'side_effects': result.get('adverse_reactions', ['No side effects listed'])[0] if result.get('adverse_reactions') else 'No side effects listed'
        }
    except Exception as e:
        print(f"Error parsing FDA result: {e}")
        return None

def validate_fda_result(drug_info, original_query):
    """Validate that FDA result is relevant to the query."""
    if not drug_info or not drug_info.get('generic_name'):
        return False
    
    query_lower = original_query.lower()
    generic_name_lower = drug_info['generic_name'].lower()
    
    # If the names are completely different, it's likely wrong
    if not any(word in generic_name_lower for word in query_lower.split() if len(word) > 2):
        return False
    
    # Additional validation: check if it's a reasonable drug result
    suspicious_names = ['povidone', 'iodine', 'sodium', 'solution']
    if any(name in generic_name_lower for name in suspicious_names):
        return False
    
    return True

def get_drug_suggestions(drug_name):
    """Provide helpful suggestions when drug is not found."""
    available_drugs = [
        'paracetamol', 'acetaminophen', 'ibuprofen', 'aspirin', 
        'metformin', 'lisinopril', 'amoxicillin', 'omeprazole', 'cytarabine'
    ]
    
    # Check if it's a close match to any available drug
    close_matches = difflib.get_close_matches(drug_name.lower(), available_drugs, n=3, cutoff=0.4)
    
    if close_matches:
        suggestions = ", ".join(close_matches)
        return f"Did you mean one of these: {suggestions}?"
    else:
        return f"I have detailed information about these common drugs: {', '.join(available_drugs[:6])}. Try searching for one of these!"

# Basic Routes
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not username or not email or not password:
        error_msg = quote("Please fill in all fields.")
        return redirect(f'/?error={error_msg}')
    
    if len(password) < 6:
        error_msg = quote("Password must be at least 6 characters long.")
        return redirect(f'/?error={error_msg}')
    
    hashed_password = generate_password_hash(password)
    
    connection = get_db_connection()
    if not connection:
        error_msg = quote("Database connection failed.")
        return redirect(f'/?error={error_msg}')
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
        if cursor.fetchone():
            error_msg = quote("Username or email already exists.")
            return redirect(f'/?error={error_msg}')
        
        insert_query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (username, email, hashed_password))
        connection.commit()
        
        send_welcome_email(username, email)
        
        success_msg = quote("Account created successfully! Please check your email and sign in.")
        return redirect(f'/?success={success_msg}')
        
    except mysql.connector.Error as err:
        error_msg = quote(f"Registration failed: {str(err)}")
        return redirect(f'/?error={error_msg}')
    
    finally:
        cursor.close()
        connection.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        error_msg = quote("Please enter both username and password.")
        return redirect(f'/?error={error_msg}')
    
    connection = get_db_connection()
    if not connection:
        error_msg = quote("Database connection failed.")
        return redirect(f'/?error={error_msg}')
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect('/dashboard')
        else:
            error_msg = quote("Invalid username or password.")
            return redirect(f'/?error={error_msg}')
            
    except mysql.connector.Error as err:
        error_msg = quote(f"Login failed: {str(err)}")
        return redirect(f'/?error={error_msg}')
    
    finally:
        cursor.close()
        connection.close()

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
    return render_template('dashboard.html', username=session.get('username', 'User'))

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    success_msg = quote("You have been logged out successfully.")
    return redirect(f'/?success={success_msg}')

# Appointment Routes
@app.route('/appointment')
def appointment():
    if 'user_id' not in session:
        return redirect('/')
    return render_template('appointment.html', username=session.get('username', 'User'))

@app.route('/book-appointment', methods=['POST'])
def book_appointment():
    if 'user_id' not in session:
        return redirect('/')
    
    appointment_data = {
        'user_id': session['user_id'],
        'patient_name': request.form.get('patient_name'),
        'patient_email': request.form.get('patient_email'),
        'patient_phone': request.form.get('patient_phone'),
        'specialty': request.form.get('specialty'),
        'doctor': request.form.get('doctor'),
        'appointment_date': request.form.get('appointment_date'),
        'appointment_time': request.form.get('appointment_time'),
        'appointment_type': request.form.get('appointment_type'),
        'symptoms': request.form.get('symptoms'),
        'insurance': request.form.get('insurance')
    }
    
    connection = get_db_connection()
    if not connection:
        return redirect('/appointment?error=Database connection failed')
    
    try:
        cursor = connection.cursor()
        
        insert_query = """
        INSERT INTO appointments (user_id, patient_name, patient_email, patient_phone, 
                                specialty, doctor, appointment_date, appointment_time, 
                                appointment_type, symptoms, insurance)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (
            appointment_data['user_id'], appointment_data['patient_name'],
            appointment_data['patient_email'], appointment_data['patient_phone'],
            appointment_data['specialty'], appointment_data['doctor'],
            appointment_data['appointment_date'], appointment_data['appointment_time'],
            appointment_data['appointment_type'], appointment_data['symptoms'],
            appointment_data['insurance']
        ))
        
        connection.commit()
        send_appointment_confirmation(appointment_data)
        
        return redirect('/appointment?success=Appointment booked successfully!')
        
    except mysql.connector.Error as err:
        return redirect(f'/appointment?error=Booking failed: {str(err)}')
    
    finally:
        cursor.close()
        connection.close()

# EHR Routes
@app.route('/health-records')
def health_records():
    if 'user_id' not in session:
        return redirect('/')
    return render_template('health_records.html', username=session.get('username', 'User'))

@app.route('/medical-records')
def medical_records():
    if 'user_id' not in session:
        return redirect('/')
    
    connection = get_db_connection()
    records = []
    
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT id, record_type, title, description, date_recorded, 
                       healthcare_provider, created_at 
                FROM medical_records 
                WHERE user_id = %s 
                ORDER BY date_recorded DESC
            """, (session['user_id'],))
            records = cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error fetching medical records: {err}")
        finally:
            cursor.close()
            connection.close()
    
    return render_template('medical_records.html', 
                         records=records, 
                         username=session.get('username', 'User'))

@app.route('/add-medical-record', methods=['POST'])
def add_medical_record():
    if 'user_id' not in session:
        return redirect('/')
    
    record_type = request.form.get('record_type')
    title = request.form.get('title')
    description = request.form.get('description')
    date_recorded = request.form.get('date_recorded')
    healthcare_provider = request.form.get('healthcare_provider')
    
    if not all([record_type, title, date_recorded]):
        return redirect('/medical-records?error=Please fill in required fields')
    
    connection = get_db_connection()
    if not connection:
        return redirect('/medical-records?error=Database connection failed')
    
    try:
        cursor = connection.cursor()
        insert_query = """
        INSERT INTO medical_records (user_id, record_type, title, description, 
                                   date_recorded, healthcare_provider)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            session['user_id'], record_type, title, description,
            date_recorded, healthcare_provider
        ))
        connection.commit()
        return redirect('/medical-records?success=Medical record added successfully!')
        
    except mysql.connector.Error as err:
        return redirect(f'/medical-records?error=Failed to add record: {str(err)}')
    
    finally:
        cursor.close()
        connection.close()

@app.route('/delete-medical-record/<int:record_id>', methods=['POST'])
def delete_medical_record(record_id):
    if 'user_id' not in session:
        return redirect('/')
    
    connection = get_db_connection()
    if not connection:
        return redirect('/medical-records?error=Database connection failed')
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("SELECT user_id FROM medical_records WHERE id = %s", (record_id,))
        record = cursor.fetchone()
        
        if not record:
            return redirect('/medical-records?error=Record not found')
        
        if record[0] != session['user_id']:
            return redirect('/medical-records?error=Unauthorized access')
        
        cursor.execute("DELETE FROM medical_records WHERE id = %s", (record_id,))
        connection.commit()
        
        return redirect('/medical-records?success=Medical record deleted successfully!')
        
    except mysql.connector.Error as err:
        return redirect(f'/medical-records?error=Failed to delete record: {str(err)}')
    
    finally:
        cursor.close()
        connection.close()

@app.route('/medications')
def medications():
    if 'user_id' not in session:
        return redirect('/')
    
    connection = get_db_connection()
    medications = []
    
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT id, medication_name, dosage, frequency, start_date, 
                       end_date, prescribing_doctor, is_active, notes
                FROM medications 
                WHERE user_id = %s 
                ORDER BY is_active DESC, start_date DESC
            """, (session['user_id'],))
            medications = cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error fetching medications: {err}")
        finally:
            cursor.close()
            connection.close()
    
    return render_template('medications.html', 
                         medications=medications, 
                         username=session.get('username', 'User'))

@app.route('/add-medication', methods=['POST'])
def add_medication():
    if 'user_id' not in session:
        return redirect('/')
    
    medication_name = request.form.get('medication_name')
    dosage = request.form.get('dosage')
    frequency = request.form.get('frequency')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    prescribing_doctor = request.form.get('prescribing_doctor')
    notes = request.form.get('notes')
    
    if not all([medication_name, dosage, frequency, start_date]):
        return redirect('/medications?error=Please fill in required fields')
    
    connection = get_db_connection()
    if not connection:
        return redirect('/medications?error=Database connection failed')
    
    try:
        cursor = connection.cursor()
        insert_query = """
        INSERT INTO medications (user_id, medication_name, dosage, frequency, 
                               start_date, end_date, prescribing_doctor, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            session['user_id'], medication_name, dosage, frequency,
            start_date, end_date or None, prescribing_doctor, notes
        ))
        connection.commit()
        return redirect('/medications?success=Medication added successfully!')
        
    except mysql.connector.Error as err:
        return redirect(f'/medications?error=Failed to add medication: {str(err)}')
    
    finally:
        cursor.close()
        connection.close()

@app.route('/vital-signs')
def vital_signs():
    if 'user_id' not in session:
        return redirect('/')
    
    connection = get_db_connection()
    vitals = []
    
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT id, measurement_date, blood_pressure_systolic, 
                       blood_pressure_diastolic, heart_rate, temperature, 
                       weight, height, notes
                FROM vital_signs 
                WHERE user_id = %s 
                ORDER BY measurement_date DESC
            """, (session['user_id'],))
            vitals = cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error fetching vital signs: {err}")
        finally:
            cursor.close()
            connection.close()
    
    return render_template('vital_signs.html', 
                         vitals=vitals, 
                         username=session.get('username', 'User'))

@app.route('/add-vital-signs', methods=['POST'])
def add_vital_signs():
    if 'user_id' not in session:
        return redirect('/')
    
    measurement_date = request.form.get('measurement_date')
    systolic = request.form.get('blood_pressure_systolic')
    diastolic = request.form.get('blood_pressure_diastolic')
    heart_rate = request.form.get('heart_rate')
    temperature = request.form.get('temperature')
    weight = request.form.get('weight')
    height = request.form.get('height')
    notes = request.form.get('notes')
    
    if not measurement_date:
        return redirect('/vital-signs?error=Please select a measurement date')
    
    connection = get_db_connection()
    if not connection:
        return redirect('/vital-signs?error=Database connection failed')
    
    try:
        cursor = connection.cursor()
        insert_query = """
        INSERT INTO vital_signs (user_id, measurement_date, blood_pressure_systolic,
                               blood_pressure_diastolic, heart_rate, temperature,
                               weight, height, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            session['user_id'], measurement_date, 
            systolic or None, diastolic or None, heart_rate or None,
            temperature or None, weight or None, height or None, notes
        ))
        connection.commit()
        return redirect('/vital-signs?success=Vital signs added successfully!')
        
    except mysql.connector.Error as err:
        return redirect(f'/vital-signs?error=Failed to add vital signs: {str(err)}')
    
    finally:
        cursor.close()
        connection.close()

# Drug Information Chatbot Routes
@app.route('/drug-info-chat')
def drug_info_chat():
    if 'user_id' not in session:
        return redirect('/')
    return render_template('drug_chat.html', username=session.get('username', 'User'))

# SINGLE drug info route - this replaces both previous versions
@app.route('/get-drug-info', methods=['POST'])
def get_drug_info():
    """Get drug information with improved spelling correction and validation."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    drug_name = data.get('drug_name', '').strip()
    
    if not drug_name:
        return jsonify({'error': 'Please enter a drug name'}), 400
    
    # Method 1: Try local database with fuzzy matching first
    try:
        drug_info = get_local_drug_info_with_fuzzy_search(drug_name)
        if drug_info:
            message = f"Here's information about {drug_info['generic_name']}:"
            
            # Add correction message if spelling was corrected
            if '_corrected_from' in drug_info:
                message = f"Did you mean '{drug_info['_corrected_to']}'? Here's information about {drug_info['generic_name']}:"
                # Remove correction metadata before sending
                del drug_info['_corrected_from']
                del drug_info['_corrected_to']
            
            return jsonify({
                'success': True,
                'drug_info': drug_info,
                'message': message,
                'source': 'local'
            })
    except Exception as e:
        print(f"Local database search failed: {e}")
    
    # Method 2: Try OpenFDA API only if local search fails
    if len(drug_name) < 3:
        return jsonify({
            'success': False,
            'message': "Please enter a complete drug name (at least 3 characters)."
        })
    
    try:
        # Try OpenFDA with better validation
        drug_info = search_openfda_exact(drug_name)
        if drug_info and validate_fda_result(drug_info, drug_name):
            return jsonify({
                'success': True,
                'drug_info': drug_info,
                'message': f"Here's information about {drug_info['generic_name']}:",
                'source': 'fda'
            })
    except Exception as e:
        print(f"OpenFDA search failed: {e}")
    
    # Method 3: Try broader FDA search
    try:
        drug_info = search_openfda_broad(drug_name)
        if drug_info and validate_fda_result(drug_info, drug_name):
            return jsonify({
                'success': True,
                'drug_info': drug_info,
                'message': f"Here's information about {drug_info['generic_name']}:",
                'source': 'fda'
            })
    except Exception as e:
        print(f"OpenFDA broad search failed: {e}")
    
    # Provide helpful suggestions
    suggestions = get_drug_suggestions(drug_name)
    return jsonify({
        'success': False,
        'message': f"Sorry, I couldn't find information about '{drug_name}'. {suggestions}"
    })
# Add these imports at the top of your existing app.py
import openai
from google.cloud import translate_v2 as translate
import base64
import tempfile

# Add this class after your existing functions (around line 300)
class MultiLanguageService:
    def __init__(self):
        self.translate_client = None
        try:
            if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                self.translate_client = translate.Client()
        except:
            pass
    
    def translate_text(self, text, source_lang, target_lang):
        if source_lang == target_lang:
            return text
        
        if self.translate_client:
            try:
                result = self.translate_client.translate(
                    text, source_language=source_lang, target_language=target_lang
                )
                return result['translatedText']
            except:
                pass
        
        # Simple fallback dictionary
        if source_lang == 'hi' and target_lang == 'en':
            hindi_to_eng = {'दवा': 'medicine', 'बुखार': 'fever'}
            for hindi, eng in hindi_to_eng.items():
                text = text.replace(hindi, eng)
        
        return text

# Initialize service
ml_service = MultiLanguageService()

# Replace your existing /get-drug-info route with this enhanced version
@app.route('/get-drug-info', methods=['POST'])
def get_drug_info():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    drug_name = data.get('drug_name', '').strip()
    user_language = data.get('language', 'en')
    
    if not drug_name:
        return jsonify({'error': 'Please enter a drug name'}), 400
    
    # Translate to English if needed
    if user_language != 'en':
        drug_name = ml_service.translate_text(drug_name, user_language, 'en')
    
    # Your existing drug search logic
    drug_info = get_local_drug_info_with_fuzzy_search(drug_name)
    if drug_info:
        # Translate response back to user language
        if user_language != 'en':
            if drug_info.get('indications'):
                drug_info['indications'] = ml_service.translate_text(drug_info['indications'], 'en', user_language)
            if drug_info.get('side_effects'):
                drug_info['side_effects'] = ml_service.translate_text(drug_info['side_effects'], 'en', user_language)
        
        message = f"Here's information about {drug_info['generic_name']}:"
        if user_language != 'en':
            message = ml_service.translate_text(message, 'en', user_language)
        
        return jsonify({
            'success': True,
            'drug_info': drug_info,
            'message': message,
            'source': 'local'
        })
    
    # Your existing fallback logic
    suggestions = get_drug_suggestions(drug_name)
    return jsonify({
        'success': False,
        'message': f"Sorry, I couldn't find information about '{drug_name}'. {suggestions}"
    })

if __name__ == '__main__':
    # Initialize database on startup
    init_database()
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)