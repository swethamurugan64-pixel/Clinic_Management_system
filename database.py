import mysql.connector

def get_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",    
        password="Swetha*1243",  
        database="clinicdb",   
        port=3306   
    )
    return conn

