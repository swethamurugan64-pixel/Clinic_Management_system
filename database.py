import mysql.connector
import os

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    port=os.getenv("DB_PORT")
)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS patients (
  Patient_id INT AUTO_INCREMENT PRIMARY KEY,
  Patient_name VARCHAR(100),
  Contact VARCHAR(15),
  Age INT,
  Gender VARCHAR(10),
  Medicine VARCHAR(50),
  Quantity INT,
  Total_price DECIMAL(10,2)
)
""")

conn.commit()
conn.close()
print("✅ Table 'patients' created successfully!")

