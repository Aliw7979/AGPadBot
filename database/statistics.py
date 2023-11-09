import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta

# MySQL Database Configuration
db_config = {
    'host': 'localhost',
    'database': 'stats',
    'user': 'ali',
    'password': '123',
}

# Function to connect to MySQL database
def connect():
    try:
        conn = mysql.connector.connect(**db_config)
        if conn.is_connected():
            print('Connected to MySQL database')
            return conn
    except Error as e:
        print(f'Error connecting to MySQL database: {e}')

# Function to create the userstats table
def create_table(conn):
    try:
        query = """
            CREATE TABLE IF NOT EXISTS userstats (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                registration_date DATETIME NOT NULL
            )
        """
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
    except Error as e:
        print(f'Error creating userstats table: {e}')

# Function to insert a new user registration into the database
def insert_user(conn, user_id):
    try:
        query = "INSERT INTO userstats (user_id, registration_date) VALUES (%s, %s)"
        registration_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor = conn.cursor()
        cursor.execute(query, (user_id, registration_date))
        conn.commit()
    except Error as e:
        print(f'Error inserting stats into the database: {e}')

# Function to retrieve user registration statistics
def get_user_statistics(conn):
    try:
        cursor = conn.cursor()

        # Weekly Count
        start_date = datetime.now() - timedelta(days=7)
        query = "SELECT COUNT(*) FROM userstats WHERE registration_date >= %s"
        cursor.execute(query, (start_date,))
        weekly_count = cursor.fetchone()[0]

        # Daily Count
        today = datetime.now().strftime('%Y-%m-%d')
        query = "SELECT COUNT(*) FROM userstats WHERE DATE(registration_date) = %s"
        cursor.execute(query, (today,))
        daily_count = cursor.fetchone()[0]

        # Yearly Count
        current_year = datetime.now().year
        query = "SELECT COUNT(*) FROM userstats WHERE YEAR(registration_date) = %s"
        cursor.execute(query, (current_year,))
        yearly_count = cursor.fetchone()[0]

        # Total Count
        query = "SELECT COUNT(*) FROM userstats"
        cursor.execute(query)
        total_count = cursor.fetchone()[0]

        return weekly_count, daily_count, yearly_count, total_count

    except Error as e:
        print(f'Error retrieving user statistics from the database: {e}')

# Telegram Bot Start Function
def start(update, context):
    user_id = update.effective_user.id

    # Connect to MySQL database
    conn = connect()

    # Create the userstats table if it doesn't exist
    create_table(conn)

    # Insert user registration into the database
    insert_user(conn, user_id)

    # Retrieve user statistics
    weekly_count, daily_count, yearly_count, total_count = get_user_statistics(conn)

    # Close the database connection
    conn.close()

    # Send statistics message to the user
    message = f"User Statistics:\n\nWeekly Count: {weekly_count}\nDaily Count: {daily_count}\nYearly Count: {yearly_count}\nTotal Count: {total_count}"
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)