import logging
import json

# Logging konfigurācija (gan konsolē, gan failā)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler("dienasgramata.log"),
        logging.StreamHandler()
    ]
)

# ===== FUNKCIJAS =====

def login_user(user_id):
    logging.debug(f"Login attempt | user_id={user_id}")
    
    if not user_id:
        logging.warning("Login failed | reason=empty_user_id")
        return False
    
    logging.info(f"User logged in | user_id={user_id}")
    return True


def add_grade(student_id, subject, grade):
    logging.debug(f"Add grade attempt | student_id={student_id}, subject={subject}, grade={grade}")
    
    if grade < 1 or grade > 10:
        logging.error(f"Invalid grade | student_id={student_id}, grade={grade}")
        return False
    
    logging.info(f"Grade added | student_id={student_id}, subject={subject}, grade={grade}")
    return True


def save_data(data):
    logging.debug(f"Saving data | data={json.dumps(data)}")
    
    try:
        if not data:
            raise ValueError("Empty data")
        
        logging.info("Data saved successfully")
        return True
    
    except Exception as e:
        logging.error(f"Save failed | error={str(e)}")
        return False


def get_student(student_id):
    logging.debug(f"Fetching student | student_id={student_id}")
    
    # simulācija
    if student_id != "123":
        logging.warning(f"Student not found | student_id={student_id}")
        return None
    
    logging.info(f"Student found | student_id={student_id}")
    return {"id": "123", "name": "Jānis"}


# ===== TESTĒŠANA =====

print("\n--- SUCCESS SCENĀRIJS ---")
login_user("123")
add_grade("123", "Matemātika", 9)
save_data({"student": "123", "grade": 9})

print("\n--- WARNING SCENĀRIJS ---")
login_user("")
get_student("999")

print("\n--- ERROR SCENĀRIJS ---")
add_grade("123", "Fizika", 15)
save_data({})