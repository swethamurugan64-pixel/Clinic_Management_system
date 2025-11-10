from flask import Flask, render_template, request, redirect, url_for, flash
from database import get_connection
from datetime import datetime
import qrcode
import io
import base64

app = Flask(__name__)

medicines = {
    "Paracetamol": 25.0,
    "Amoxicillin": 50.0,
    "Cough Syrup": 80.0,
    "Vitamin C": 40.0,
    "Pain Relief Gel": 100.0
}

# HOME PAGE
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        contact = request.form['contact'].strip()
        if not contact:
            flash("Please enter a contact number.")
            return redirect(url_for('home'))

        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM patients WHERE Contact=%s", (contact,))
        patient = cur.fetchone()
        conn.close()

        if patient:
            return redirect(url_for('existing_patient', contact=contact))
        else:
            return redirect(url_for('new_patient', contact=contact))
    return render_template('index.html')

# EXISTING PATIENT PAGE
@app.route('/existing/<contact>')
def existing_patient(contact):
    conn = get_connection()
    cur = conn.cursor(dictionary=True, buffered=True)

    # Get patient details
    cur.execute("""
        SELECT Patient_name, Contact, Age, Gender
        FROM patients
        WHERE Contact=%s
        ORDER BY Patient_id DESC LIMIT 1
    """, (contact,))
    patient = cur.fetchone()

    if not patient:
        flash("No record found for this contact.")
        conn.close()
        return redirect(url_for('home'))

    # Suggested medicines (top 3)
    cur.execute("""
        SELECT Medicine, SUM(Quantity) AS total_qty
        FROM patients
        WHERE Contact = %s
        GROUP BY Medicine
        ORDER BY total_qty DESC
        LIMIT 3
    """, (contact,))
    suggested = cur.fetchall()

    # Total spent
    cur.execute("""
        SELECT SUM(Total_price) AS total_spent
        FROM patients
        WHERE Contact = %s
    """, (contact,))
    total_spent = cur.fetchone()['total_spent']

    conn.close()

    return render_template(
        'existing_patient.html',
        patient=patient,
        suggested=suggested,
        total_spent=total_spent,
        medicines=medicines
    )

# NEW PATIENT PAGE
@app.route('/new/<contact>')
def new_patient(contact):
    return render_template('new_patient.html', contact=contact, medicines=medicines)

# PURCHASE ROUTE (SAVE + SHOW ONLY LATEST BILL)
@app.route('/purchase', methods=['POST'])
def purchase():
    name = request.form.get('name')
    contact = request.form.get('contact')
    age = request.form.get('age')
    gender = request.form.get('gender')
    medicine = request.form.get('medicine')
    qty = int(request.form.get('qty'))
    total = medicines[medicine] * qty

    conn = get_connection()
    cur = conn.cursor()

    # Insert new purchase record
    query = """INSERT INTO patients (Patient_name, Contact, Age, Gender, Medicine, Quantity, Total_price)
               VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    cur.execute(query, (name, contact, age, gender, medicine, qty, total))
    conn.commit()

    # Get the ID of this inserted record
    patient_id = cur.lastrowid

    # Fetch only this latest purchase for the bill
    cur.execute("""
        SELECT Medicine, Quantity, Total_price
        FROM patients
        WHERE Patient_id = %s
    """, (patient_id,))
    bill_items = cur.fetchall()
    conn.close()

    # Calculate total for this one purchase
    grand_total = sum([item[2] for item in bill_items])

    # Generate payment link
    payment_link = f"upi://pay?pa=swethamurugan64@oksbi&pn=ClinicName&am={grand_total}&cu=INR&tn=Clinic%20Payment"

    # Generate QR code image
    qr = qrcode.make(payment_link)
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    qr_data = base64.b64encode(buf.getvalue()).decode('utf-8')

    # Render the bill page (for this purchase only)
    return render_template(
        'output.html',
        name=name,
        contact=contact,
        age=age,
        gender=gender,
        bill_items=bill_items,
        grand_total=grand_total,
        qr_data=qr_data,
        payment_link=payment_link
    )

#Run flask app
if __name__ == '__main__':
    @app.context_processor
    def inject_now():
        return {'now': datetime.now}
    import os
    # Get port dynamically from Render environment variable
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)








