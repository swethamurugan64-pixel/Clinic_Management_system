from flask import Flask,render_template,request,redirect,url_for,flash
from database import get_connection
from datetime import datetime

app=Flask(__name__)


medicines = {
    "Paracetamol": 25.0,
    "Amoxicillin": 50.0,
    "Cough Syrup": 80.0,
    "Vitamin C": 40.0,
    "Pain Relief Gel": 100.0
}

##Home page - search by contact
@app.route('/',methods=['GET','POST'])
def home():
    if request.method=='POST':
        contact=request.form['contact'].strip()
        if not contact:
            flash("Please enter a contact number.")

        conn=get_connection()
        cur=conn.cursor(dictionary=True)
        cur.execute("select * from patients where Contact=%s",(contact,))
        patient=cur.fetchone()
        conn.close()

        if patient:
            #Existing patient
            return redirect(url_for('existing_patient',contact=contact))
        else:
            #New patient
            return redirect(url_for('new_patient',contact=contact))
    return render_template('index.html')

#Existing patient - show suggestions
@app.route('/existing/<contact>')
def existing_patient(contact):
    conn=get_connection()
    cur=conn.cursor(dictionary=True,buffered=True)

    #Get patient details
    cur.execute("""select Patient_name,Contact,Age,Gender from patients where Contact=%s order by Patient_id desc limit 1""",(contact,))
    patient=cur.fetchone()

    if not patient:
        flash("No record found for this contact.")
        conn.close()
        return redirect(url_for('home'))

    # Get all past purchases
    cur.execute("""
        SELECT Medicine, Quantity, Total_price
        FROM patients
        WHERE Contact = %s
    """, (contact,))
    purchases = cur.fetchall()

    # Suggested medicines — top 3 most frequently bought
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
        purchases=purchases,
        suggested=suggested,
        total_spent=total_spent,
        medicines=medicines
        )

#New patient - collect info and show medicine list
@app.route('/new/<contact>')
def new_patient(contact):
    return render_template('new_patient.html',contact=contact,medicines=medicines)

#Save purchase (for both new & existing)
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
    query = """INSERT INTO patients(Patient_name, Contact, Age, Gender, Medicine, Quantity, Total_price)
               VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    cur.execute(query, (name, contact, age, gender, medicine, qty, total))
    conn.commit()

    # Fetch all purchases by this patient (to show full bill)
    cur.execute("""
        SELECT Medicine, Quantity, Total_price
        FROM patients
        WHERE Contact = %s
        ORDER BY Patient_id DESC
        LIMIT 5
    """, (contact,))
    bill_items = cur.fetchall()
    conn.close()

    # Calculate grand total
    grand_total = sum([item[2] for item in bill_items])

    return render_template(
        'output.html',
        name=name,
        contact=contact,
        age=age,
        gender=gender,
        bill_items=bill_items,
        grand_total=grand_total
    )


#Run flask app
if __name__=='__main__':
    @app.context_processor
    def inject_now():
        return {'now': datetime.now}
    app.run(host='0.0.0.0', port=10000)

