import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Swetha*1243",
        database="clinicdb"
    )
                                   
