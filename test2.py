import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime, date
import plotly.express as px

# Database Connection Function with improved error handling
def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Aditya@2003",
            database="student_management_system_new",
            autocommit=False,
            connect_timeout=5
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"Database connection failed: {err}")
        return None

# Enhanced fetch_data function with transaction management
def fetch_data(query, params=None):
    conn = get_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(dictionary=True)
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        result = cursor.fetchall()
        return result
    except mysql.connector.Error as err:
        st.error(f"Database query error: {err}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Enhanced execute_query function with transaction management
def execute_query(query, params=None, many=False):
    conn = get_connection()
    if not conn:
        return False, "Connection failed"
    
    try:
        cursor = conn.cursor()
        
        if many and isinstance(params, list):
            cursor.executemany(query, params)
        else:
            cursor.execute(query, params)
        
        conn.commit()
        return True, "Operation completed successfully"
    except mysql.connector.Error as err:
        conn.rollback()
        return False, f"Database error: {err}"
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# App title and sidebar
st.set_page_config(page_title="University Management System", layout="wide")
st.title("University Management System")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a page:", 
    ["Dashboard", "Students", "Courses", "Faculty", "Departments", "Enrollments", "Sections", "Library"])

# Helper function for CRUD operations (modified for Courses, Departments, etc.)
def display_crud_interface(entity_name, columns, key_column, display_query, 
                         insert_query=None, update_query=None, delete_query=None,
                         form_fields=None, get_record_query=None):
    st.header(f"{entity_name} Management")
    
    tab1, tab2, tab3, tab4 = st.tabs(["View", "Add", "Update", "Delete"])
    
    with tab1:
        records = fetch_data(display_query)
        if records:
            df = pd.DataFrame(records)
            st.dataframe(df)
        else:
            st.info(f"No {entity_name.lower()} records found")
    
    if insert_query and form_fields:
        with tab2:
            with st.form(f"add_{entity_name.lower()}_form"):
                inputs = {}
                st.subheader(f"Add New {entity_name}")
                
                for field in form_fields:
                    field_name = field.get('name', 'unknown')
                    field_label = field.get('label', 'Unnamed Field')
                    field_type = field.get('type', 'text')
                    
                    if field_type == 'text':
                        inputs[field_name] = st.text_input(field_label, key=f"add_{field_name}")
                    elif field_type == 'select':
                        options = fetch_data(field['query']) if 'query' in field else field.get('options', [])
                        display_field = field.get('display_field', 'name')
                        value_field = field.get('value_field', 'id')
                        
                        if options and isinstance(options[0], dict):
                            option_dict = {str(o[display_field]): o[value_field] for o in options}
                        else:
                            option_dict = {str(o): o for o in options}
                        
                        selected_display = st.selectbox(
                            field_label,
                            list(option_dict.keys()),
                            key=f"add_{field_name}")
                        
                        inputs[field_name] = option_dict[selected_display]
                    elif field_type == 'date':
                        inputs[field_name] = st.date_input(field_label, key=f"add_{field_name}")
                    elif field_type == 'number':
                        min_val = float(field.get('min_value', 0))
                        max_val = float(field.get('max_value', 1000000))
                        value = float(field.get('value', min_val))
                        step = float(field.get('step', 1))
                        
                        inputs[field_name] = st.number_input(
                            field_label,
                            min_value=min_val,
                            max_value=max_val,
                            value=value,
                            step=step,
                            key=f"add_{field_name}"
                        )
                
                submitted = st.form_submit_button(f"Add {entity_name}")
                if submitted:
                    try:
                        params = tuple(inputs[field['name']] for field in form_fields)
                        success, message = execute_query(insert_query, params)
                        if success:
                            st.success(f"{entity_name} added successfully!")
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")

    if update_query and form_fields and get_record_query:
        with tab3:
            if records:
                # Handle composite keys
                if ',' in key_column:
                    key_parts = [k.strip() for k in key_column.split(',')]
                    record_options = []
                    for r in records:
                        key_values = [str(r[k]) for k in key_parts]
                        display_values = [r.get('name', r.get('title', '')) for k in key_parts]
                        record_options.append(" - ".join(key_values + display_values))
                else:
                    record_options = [f"{r[key_column]} - {r.get('name', r.get('title', ''))}" for r in records]
                
                selected_record = st.selectbox(
                    f"Select {entity_name} to update",
                    record_options,
                    key=f"update_select_{entity_name}")
                
                # Get the record ID(s)
                if ',' in key_column:
                    selected_index = record_options.index(selected_record)
                    selected_keys = records[selected_index]
                    key_params = tuple(selected_keys[k.strip()] for k in key_column.split(','))
                else:
                    record_id = int(selected_record.split('-')[0].strip())
                    key_params = (record_id,)
                
                current_record = fetch_data(get_record_query, key_params)
                
                if current_record:
                    st.subheader("Current Record Details")
                    st.write(pd.DataFrame(current_record))
                    st.markdown("---")
                    st.subheader("Update Record")
                    
                    with st.form(f"update_{entity_name.lower()}_form"):
                        inputs = {}
                        for field in form_fields:
                            field_name = field.get('name', 'unknown')
                            field_label = field.get('label', 'Unnamed Field')
                            field_type = field.get('type', 'text')
                            current_value = current_record[0].get(field_name)
                            
                            if field_type == 'text':
                                inputs[field_name] = st.text_input(
                                    field_label,
                                    value=current_value,
                                    key=f"update_{field_name}")
                            elif field_type == 'select':
                                options = fetch_data(field['query']) if 'query' in field else field.get('options', [])
                                display_field = field.get('display_field', 'name')
                                value_field = field.get('value_field', 'id')
                                
                                if options and isinstance(options[0], dict):
                                    option_dict = {str(o[display_field]): o[value_field] for o in options}
                                else:
                                    option_dict = {str(o): o for o in options}
                                
                                current_option = next((k for k, v in option_dict.items() if v == current_value), None)
                                selected = st.selectbox(
                                    field_label,
                                    list(option_dict.keys()),
                                    index=list(option_dict.keys()).index(current_option) if current_option in option_dict else 0,
                                    key=f"update_{field_name}")
                                inputs[field_name] = option_dict.get(selected)
                            elif field_type == 'date':
                                inputs[field_name] = st.date_input(
                                    field_label,
                                    value=current_value if current_value else date.today(),
                                    key=f"update_{field_name}")
                            elif field_type == 'number':
                                min_val = float(field.get('min_value', 0))
                                max_val = float(field.get('max_value', 1000000))
                                step = float(field.get('step', 1))
                                current_val = float(current_value) if current_value is not None else min_val
                                
                                inputs[field_name] = st.number_input(
                                    field_label,
                                    value=current_val,
                                    min_value=min_val,
                                    max_value=max_val,
                                    step=step,
                                    key=f"update_{field_name}"
                                )
                        
                        if st.form_submit_button(f"Update {entity_name}"):
                            params = tuple(list(inputs.values()) + list(key_params))
                            success, message = execute_query(update_query, params)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                else:
                    st.warning("Record not found")
            else:
                st.info(f"No {entity_name.lower()} records to update")

    if delete_query:
        with tab4:
            if records:
                if ',' in key_column:
                    key_parts = [k.strip() for k in key_column.split(',')]
                    record_options = []
                    for r in records:
                        key_values = [str(r[k]) for k in key_parts]
                        display_values = [r.get('name', r.get('title', '')) for k in key_parts]
                        record_options.append(" - ".join(key_values + display_values))
                else:
                    record_options = [f"{r[key_column]} - {r.get('name', r.get('title', ''))}" for r in records]
                
                selected_record = st.selectbox(
                    f"Select {entity_name} to delete",
                    record_options,
                    key=f"delete_select_{entity_name}")
                
                # Get the record ID(s)
                if ',' in key_column:
                    selected_index = record_options.index(selected_record)
                    selected_keys = records[selected_index]
                    key_params = tuple(selected_keys[k.strip()] for k in key_column.split(','))
                else:
                    record_id = int(selected_record.split('-')[0].strip())
                    key_params = (record_id,)
                
                if st.button(f"Delete {entity_name}", key=f"delete_{entity_name}"):
                    success, message = execute_query(delete_query, key_params)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.info(f"No {entity_name.lower()} records to delete")

# Dashboard page
if page == "Dashboard":
    st.header("University Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Student count by status
        student_count = fetch_data("SELECT status, COUNT(*) as count FROM Student GROUP BY status")
        if student_count:
            df_students = pd.DataFrame(student_count)
            st.subheader("Students by Status")
            fig = px.pie(df_students, values='count', names='status', hole=0.3)
            st.plotly_chart(fig)
        else:
            st.warning("No student data available")
    
    with col2:
        # Faculty count by department
        faculty_query = """
        SELECT d.dept_name, COUNT(*) as count 
        FROM Faculty f 
        JOIN Department d ON f.dept_id = d.dept_id 
        GROUP BY d.dept_name
        """
        faculty_count = fetch_data(faculty_query)
        if faculty_count:
            df_faculty = pd.DataFrame(faculty_count)
            st.subheader("Faculty by Department")
            fig = px.bar(df_faculty, x='dept_name', y='count')
            st.plotly_chart(fig)
        else:
            st.warning("No faculty data available")
    
    # Recent enrollments
    st.subheader("Recent Enrollments")
    recent_enrollments = fetch_data("""
    SELECT p.first_name, p.last_name, c.title as course, 
           s.semester, s.year, e.enrollment_date
    FROM Enrollment e
    JOIN Student st ON e.student_id = st.student_id
    JOIN Person p ON st.person_id = p.person_id
    JOIN Section s ON e.section_id = s.section_id
    JOIN Course c ON s.course_id = c.course_id
    ORDER BY e.enrollment_date DESC
    LIMIT 10
    """)
    
    if recent_enrollments:
        st.dataframe(pd.DataFrame(recent_enrollments))
    else:
        st.info("No recent enrollments to display")

# Students page - Modified to use text inputs instead of dropdown
elif page == "Students":
    st.header("Student Management")
    
    tab1, tab2, tab3, tab4 = st.tabs(["View", "Add", "Update", "Delete"])
    
    with tab1:
        # View existing students
        records = fetch_data("""
            SELECT s.student_id, p.first_name, p.last_name, p.email, 
                   p.gender, s.enrollment_date, s.status,
                   d.dept_name as department
            FROM Student s
            JOIN Person p ON s.person_id = p.person_id
            LEFT JOIN Department d ON s.dept_id = d.dept_id
            ORDER BY s.student_id
        """)
        if records:
            df = pd.DataFrame(records)
            st.dataframe(df)
        else:
            st.info("No student records found")
    
    with tab2:
        # Add new student with person details
        with st.form("add_student_form"):
            st.subheader("Add New Student")
            
            # Person details
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name", key="add_first_name")
                date_of_birth = st.date_input("Date of Birth", key="add_dob")
                contact_number = st.text_input("Contact Number", key="add_contact")
            with col2:
                last_name = st.text_input("Last Name", key="add_last_name")
                gender = st.selectbox("Gender", ['Male', 'Female', 'Other'], key="add_gender")
                email = st.text_input("Email", key="add_email")
            
            # Student details
            enrollment_date = st.date_input("Enrollment Date", key="add_enrollment_date")
            status = st.selectbox("Status", ['Active', 'Inactive', 'Graduated', 'Suspended'], key="add_status")
            
            # Department selection
            departments = fetch_data("SELECT dept_id, dept_name FROM Department")
            dept_options = {d['dept_name']: d['dept_id'] for d in departments} if departments else {}
            selected_dept = st.selectbox("Department", list(dept_options.keys()), key="add_dept")
            dept_id = dept_options.get(selected_dept)
            
            submitted = st.form_submit_button("Add Student")
            if submitted:
                if not all([first_name, last_name, email, enrollment_date]):
                    st.error("Please fill all required fields")
                else:
                    try:
                        # First create the Person record
                        person_query = """
                            INSERT INTO Person 
                            (first_name, last_name, date_of_birth, gender, contact_number, email, person_type)
                            VALUES (%s, %s, %s, %s, %s, %s, 'Student')
                        """
                        person_params = (
                            first_name, last_name, date_of_birth, gender, 
                            contact_number, email
                        )
                        
                        # Execute in a transaction
                        conn = get_connection()
                        if conn:
                            cursor = conn.cursor()
                            
                            # Insert Person
                            cursor.execute(person_query, person_params)
                            person_id = cursor.lastrowid
                            
                            # Insert Student
                            student_query = """
                                INSERT INTO Student 
                                (person_id, enrollment_date, status, dept_id)
                                VALUES (%s, %s, %s, %s)
                            """
                            student_params = (
                                person_id, enrollment_date, status, dept_id
                            )
                            cursor.execute(student_query, student_params)
                            
                            conn.commit()
                            st.success("Student added successfully!")
                            st.rerun()
                    except mysql.connector.Error as err:
                        if conn:
                            conn.rollback()
                        st.error(f"Database error: {err}")
                    except Exception as e:
                        if conn:
                            conn.rollback()
                        st.error(f"An error occurred: {str(e)}")
                    finally:
                        if conn and conn.is_connected():
                            cursor.close()
                            conn.close()

    with tab3:
        # Update student
        if records:
            record_options = [f"{r['student_id']} - {r['first_name']} {r['last_name']}" for r in records]
            selected_record = st.selectbox(
                "Select Student to update",
                record_options,
                key="update_select_student")
            
            student_id = int(selected_record.split('-')[0].strip())
            current_student = fetch_data("""
                SELECT s.student_id, p.first_name, p.last_name, p.email, p.gender, p.date_of_birth, p.contact_number,
                       s.enrollment_date, s.status, s.dept_id
                FROM Student s
                JOIN Person p ON s.person_id = p.person_id
                WHERE s.student_id = %s
            """, (student_id,))
            
            if current_student:
                current = current_student[0]
                st.subheader("Current Student Details")
                st.write(pd.DataFrame([current]))
                st.markdown("---")
                st.subheader("Update Student")
                
                with st.form("update_student_form"):
                    # Person details
                    col1, col2 = st.columns(2)
                    with col1:
                        new_first_name = st.text_input("First Name", value=current['first_name'], key="update_first_name")
                        new_dob = st.date_input("Date of Birth", value=current['date_of_birth'], key="update_dob")
                        new_contact = st.text_input("Contact Number", value=current['contact_number'], key="update_contact")
                    with col2:
                        new_last_name = st.text_input("Last Name", value=current['last_name'], key="update_last_name")
                        new_gender = st.selectbox("Gender", ['Male', 'Female', 'Other'], 
                                                index=['Male', 'Female', 'Other'].index(current['gender']), 
                                                key="update_gender")
                        new_email = st.text_input("Email", value=current['email'], key="update_email")
                    
                    # Student details
                    new_enrollment_date = st.date_input("Enrollment Date", value=current['enrollment_date'], key="update_enrollment_date")
                    new_status = st.selectbox("Status", ['Active', 'Inactive', 'Graduated', 'Suspended'], 
                                           index=['Active', 'Inactive', 'Graduated', 'Suspended'].index(current['status']), 
                                           key="update_status")
                    
                    # Department selection
                    departments = fetch_data("SELECT dept_id, dept_name FROM Department")
                    current_dept = fetch_data("SELECT dept_name FROM Department WHERE dept_id = %s", (current['dept_id'],))
                    current_dept_name = current_dept[0]['dept_name'] if current_dept else None
                    dept_options = {d['dept_name']: d['dept_id'] for d in departments} if departments else {}
                    selected_dept = st.selectbox("Department", list(dept_options.keys()), 
                                               index=list(dept_options.keys()).index(current_dept_name) if current_dept_name in dept_options else 0,
                                               key="update_dept")
                    new_dept_id = dept_options.get(selected_dept)
                    
                    if st.form_submit_button("Update Student"):
                        try:
                            # Update Person record
                            person_update_query = """
                                UPDATE Person SET
                                first_name = %s, last_name = %s, date_of_birth = %s,
                                gender = %s, contact_number = %s, email = %s
                                WHERE person_id = (SELECT person_id FROM Student WHERE student_id = %s)
                            """
                            person_update_params = (
                                new_first_name, new_last_name, new_dob,
                                new_gender, new_contact, new_email, student_id
                            )
                            
                            # Update Student record
                            student_update_query = """
                                UPDATE Student SET
                                enrollment_date = %s, status = %s, dept_id = %s
                                WHERE student_id = %s
                            """
                            student_update_params = (
                                new_enrollment_date, new_status, new_dept_id, student_id
                            )
                            
                            # Execute in transaction
                            conn = get_connection()
                            if conn:
                                cursor = conn.cursor()
                                cursor.execute(person_update_query, person_update_params)
                                cursor.execute(student_update_query, student_update_params)
                                conn.commit()
                                st.success("Student updated successfully!")
                                st.rerun()
                        except mysql.connector.Error as err:
                            if conn:
                                conn.rollback()
                            st.error(f"Database error: {err}")
                        except Exception as e:
                            if conn:
                                conn.rollback()
                            st.error(f"An error occurred: {str(e)}")
                        finally:
                            if conn and conn.is_connected():
                                cursor.close()
                                conn.close()
            else:
                st.warning("Student not found")
        else:
            st.info("No student records to update")
    
    with tab4:
        # Delete student
        if records:
            record_options = [f"{r['student_id']} - {r['first_name']} {r['last_name']}" for r in records]
            selected_record = st.selectbox(
                "Select Student to delete",
                record_options,
                key="delete_select_student")
            
            student_id = int(selected_record.split('-')[0].strip())
            
            student_details = fetch_data("""
                SELECT s.student_id, p.first_name, p.last_name, p.email, 
                       s.enrollment_date, s.status, d.dept_name as department
                FROM Student s
                JOIN Person p ON s.person_id = p.person_id
                LEFT JOIN Department d ON s.dept_id = d.dept_id
                WHERE s.student_id = %s
            """, (student_id,))
            
            if student_details:
                st.subheader("Student to be Deleted")
                st.write(pd.DataFrame(student_details))
                
                confirm = st.checkbox("I confirm I want to delete this student", key=f"confirm_delete_{student_id}")
                
                if st.button("Delete Student", disabled=not confirm, key="delete_student"):
                    try:
                        # Delete in transaction (Student first due to foreign key constraints)
                        conn = get_connection()
                        if conn:
                            cursor = conn.cursor()
                            
                            # Get person_id first
                            cursor.execute("SELECT person_id FROM Student WHERE student_id = %s", (student_id,))
                            person_id = cursor.fetchone()[0]
                            
                            # Delete Student
                            cursor.execute("DELETE FROM Student WHERE student_id = %s", (student_id,))
                            
                            # Delete Person
                            cursor.execute("DELETE FROM Person WHERE person_id = %s", (person_id,))
                            
                            conn.commit()
                            st.success("Student deleted successfully!")
                            st.rerun()
                    except mysql.connector.Error as err:
                        if conn:
                            conn.rollback()
                        st.error(f"Database error: {err}")
                    except Exception as e:
                        if conn:
                            conn.rollback()
                        st.error(f"An error occurred: {str(e)}")
                    finally:
                        if conn and conn.is_connected():
                            cursor.close()
                            conn.close()
            else:
                st.warning("Student details not found")
        else:
            st.info("No student records to delete")

# Faculty page - Modified to use text inputs instead of dropdown
elif page == "Faculty":
    st.header("Faculty Management")
    
    tab1, tab2, tab3, tab4 = st.tabs(["View", "Add", "Update", "Delete"])
    
    with tab1:
        # View existing faculty
        records = fetch_data("""
            SELECT f.faculty_id, p.first_name, p.last_name, p.email,
                   f.faculty_rank, f.specialization, d.dept_name as department
            FROM Faculty f
            JOIN Person p ON f.person_id = p.person_id
            LEFT JOIN Department d ON f.dept_id = d.dept_id
            ORDER BY p.last_name, p.first_name
        """)
        if records:
            df = pd.DataFrame(records)
            st.dataframe(df)
        else:
            st.info("No faculty records found")
    
    with tab2:
        # Add new faculty with person details
        with st.form("add_faculty_form"):
            st.subheader("Add New Faculty")
            
            # Person details
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name", key="add_faculty_first_name")
                date_of_birth = st.date_input("Date of Birth", key="add_faculty_dob")
                contact_number = st.text_input("Contact Number", key="add_faculty_contact")
            with col2:
                last_name = st.text_input("Last Name", key="add_faculty_last_name")
                gender = st.selectbox("Gender", ['Male', 'Female', 'Other'], key="add_faculty_gender")
                email = st.text_input("Email", key="add_faculty_email")
            
            # Faculty details
            hire_date = st.date_input("Hire Date", key="add_faculty_hire_date")
            faculty_rank = st.text_input("Rank", key="add_faculty_rank")
            specialization = st.text_input("Specialization", key="add_faculty_specialization")
            
            # Department selection
            departments = fetch_data("SELECT dept_id, dept_name FROM Department")
            dept_options = {d['dept_name']: d['dept_id'] for d in departments} if departments else {}
            selected_dept = st.selectbox("Department", list(dept_options.keys()), key="add_faculty_dept")
            dept_id = dept_options.get(selected_dept)
            
            submitted = st.form_submit_button("Add Faculty")
            if submitted:
                if not all([first_name, last_name, email, hire_date, faculty_rank]):
                    st.error("Please fill all required fields")
                else:
                    try:
                        # First create the Person record
                        person_query = """
                            INSERT INTO Person 
                            (first_name, last_name, date_of_birth, gender, contact_number, email, person_type)
                            VALUES (%s, %s, %s, %s, %s, %s, 'Faculty')
                        """
                        person_params = (
                            first_name, last_name, date_of_birth, gender, 
                            contact_number, email
                        )
                        
                        # Execute in a transaction
                        conn = get_connection()
                        if conn:
                            cursor = conn.cursor()
                            
                            # Insert Person
                            cursor.execute(person_query, person_params)
                            person_id = cursor.lastrowid
                            
                            # Insert Faculty
                            faculty_query = """
                                INSERT INTO Faculty 
                                (person_id, hire_date, faculty_rank, specialization, dept_id)
                                VALUES (%s, %s, %s, %s, %s)
                            """
                            faculty_params = (
                                person_id, hire_date, faculty_rank, specialization, dept_id
                            )
                            cursor.execute(faculty_query, faculty_params)
                            
                            conn.commit()
                            st.success("Faculty added successfully!")
                            st.rerun()
                    except mysql.connector.Error as err:
                        if conn:
                            conn.rollback()
                        st.error(f"Database error: {err}")
                    except Exception as e:
                        if conn:
                            conn.rollback()
                        st.error(f"An error occurred: {str(e)}")
                    finally:
                        if conn and conn.is_connected():
                            cursor.close()
                            conn.close()

    with tab3:
        # Update faculty
        if records:
            record_options = [f"{r['faculty_id']} - {r['first_name']} {r['last_name']}" for r in records]
            selected_record = st.selectbox(
                "Select Faculty to update",
                record_options,
                key="update_select_faculty")
            
            faculty_id = int(selected_record.split('-')[0].strip())
            current_faculty = fetch_data("""
                SELECT f.faculty_id, p.first_name, p.last_name, p.email, p.gender, p.date_of_birth, p.contact_number,
                       f.hire_date, f.faculty_rank, f.specialization, f.dept_id
                FROM Faculty f
                JOIN Person p ON f.person_id = p.person_id
                WHERE f.faculty_id = %s
            """, (faculty_id,))
            
            if current_faculty:
                current = current_faculty[0]
                st.subheader("Current Faculty Details")
                st.write(pd.DataFrame([current]))
                st.markdown("---")
                st.subheader("Update Faculty")
                
                with st.form("update_faculty_form"):
                    # Person details
                    col1, col2 = st.columns(2)
                    with col1:
                        new_first_name = st.text_input("First Name", value=current['first_name'], key="update_faculty_first_name")
                        new_dob = st.date_input("Date of Birth", value=current['date_of_birth'], key="update_faculty_dob")
                        new_contact = st.text_input("Contact Number", value=current['contact_number'], key="update_faculty_contact")
                    with col2:
                        new_last_name = st.text_input("Last Name", value=current['last_name'], key="update_faculty_last_name")
                        new_gender = st.selectbox("Gender", ['Male', 'Female', 'Other'], 
                                                index=['Male', 'Female', 'Other'].index(current['gender']), 
                                                key="update_faculty_gender")
                        new_email = st.text_input("Email", value=current['email'], key="update_faculty_email")
                    
                    # Faculty details
                    new_hire_date = st.date_input("Hire Date", value=current['hire_date'], key="update_faculty_hire_date")
                    new_faculty_rank = st.text_input("Rank", value=current['faculty_rank'], key="update_faculty_rank")
                    new_specialization = st.text_input("Specialization", value=current['specialization'], key="update_faculty_specialization")
                    
                    # Department selection
                    departments = fetch_data("SELECT dept_id, dept_name FROM Department")
                    current_dept = fetch_data("SELECT dept_name FROM Department WHERE dept_id = %s", (current['dept_id'],))
                    current_dept_name = current_dept[0]['dept_name'] if current_dept else None
                    dept_options = {d['dept_name']: d['dept_id'] for d in departments} if departments else {}
                    selected_dept = st.selectbox("Department", list(dept_options.keys()), 
                                               index=list(dept_options.keys()).index(current_dept_name) if current_dept_name in dept_options else 0,
                                               key="update_faculty_dept")
                    new_dept_id = dept_options.get(selected_dept)
                    
                    if st.form_submit_button("Update Faculty"):
                        try:
                            # Update Person record
                            person_update_query = """
                                UPDATE Person SET
                                first_name = %s, last_name = %s, date_of_birth = %s,
                                gender = %s, contact_number = %s, email = %s
                                WHERE person_id = (SELECT person_id FROM Faculty WHERE faculty_id = %s)
                            """
                            person_update_params = (
                                new_first_name, new_last_name, new_dob,
                                new_gender, new_contact, new_email, faculty_id
                            )
                            
                            # Update Faculty record
                            faculty_update_query = """
                                UPDATE Faculty SET
                                hire_date = %s, faculty_rank = %s, specialization = %s, dept_id = %s
                                WHERE faculty_id = %s
                            """
                            faculty_update_params = (
                                new_hire_date, new_faculty_rank, new_specialization, new_dept_id, faculty_id
                            )
                            
                            # Execute in transaction
                            conn = get_connection()
                            if conn:
                                cursor = conn.cursor()
                                cursor.execute(person_update_query, person_update_params)
                                cursor.execute(faculty_update_query, faculty_update_params)
                                conn.commit()
                                st.success("Faculty updated successfully!")
                                st.rerun()
                        except mysql.connector.Error as err:
                            if conn:
                                conn.rollback()
                            st.error(f"Database error: {err}")
                        except Exception as e:
                            if conn:
                                conn.rollback()
                            st.error(f"An error occurred: {str(e)}")
                        finally:
                            if conn and conn.is_connected():
                                cursor.close()
                                conn.close()
            else:
                st.warning("Faculty not found")
        else:
            st.info("No faculty records to update")
    
    with tab4:
        # Delete faculty
        if records:
            record_options = [f"{r['faculty_id']} - {r['first_name']} {r['last_name']}" for r in records]
            selected_record = st.selectbox(
                "Select Faculty to delete",
                record_options,
                key="delete_select_faculty")
            
            faculty_id = int(selected_record.split('-')[0].strip())
            
            faculty_details = fetch_data("""
                SELECT f.faculty_id, p.first_name, p.last_name, p.email,
                       f.faculty_rank, f.specialization, d.dept_name as department
                FROM Faculty f
                JOIN Person p ON f.person_id = p.person_id
                LEFT JOIN Department d ON f.dept_id = d.dept_id
                WHERE f.faculty_id = %s
            """, (faculty_id,))
            
            if faculty_details:
                st.subheader("Faculty to be Deleted")
                st.write(pd.DataFrame(faculty_details))
                
                confirm = st.checkbox("I confirm I want to delete this faculty", key=f"confirm_delete_{faculty_id}")
                
                if st.button("Delete Faculty", disabled=not confirm, key="delete_faculty"):
                    try:
                        conn = get_connection()
                        if conn:
                            cursor = conn.cursor()
                            
                            # First check if faculty is an advisor to any clubs
                            cursor.execute("SELECT COUNT(*) FROM Club WHERE faculty_advisor_id = %s", (faculty_id,))
                            advisor_count = cursor.fetchone()[0]
                            
                            if advisor_count > 0:
                                st.error("Cannot delete faculty member who is advising clubs. Please reassign clubs first.")
                            else:
                                # Get person_id first
                                cursor.execute("SELECT person_id FROM Faculty WHERE faculty_id = %s", (faculty_id,))
                                person_id = cursor.fetchone()[0]
                                
                                # Delete Faculty
                                cursor.execute("DELETE FROM Faculty WHERE faculty_id = %s", (faculty_id,))
                                
                                # Delete Person
                                cursor.execute("DELETE FROM Person WHERE person_id = %s", (person_id,))
                                
                                conn.commit()
                                st.success("Faculty deleted successfully!")
                                st.rerun()
                    except mysql.connector.Error as err:
                        if conn:
                            conn.rollback()
                        st.error(f"Database error: {err}")
                    except Exception as e:
                        if conn:
                            conn.rollback()
                        st.error(f"An error occurred: {str(e)}")
                    finally:
                        if conn and conn.is_connected():
                            cursor.close()
                            conn.close()
            else:
                st.warning("Faculty details not found")
        else:
            st.info("No faculty records to delete")

# Courses page (using the original CRUD interface)
elif page == "Courses":
    display_crud_interface(
        entity_name="Course",
        columns=["course_id", "title", "credits", "description", "department"],
        key_column="course_id",
        display_query="""
        SELECT c.course_id, c.title, c.credits, c.description, d.dept_name as department
        FROM Course c
        JOIN Department d ON c.dept_id = d.dept_id
        ORDER BY c.course_id
        """,
        insert_query="""
        INSERT INTO Course (title, credits, description, dept_id)
        VALUES (%s, %s, %s, %s)
        """,
        update_query="""
        UPDATE Course 
        SET title = %s, credits = %s, description = %s, dept_id = %s 
        WHERE course_id = %s
        """,
        delete_query="DELETE FROM Course WHERE course_id = %s",
        form_fields=[
            {
                'name': 'title',
                'label': 'Title',
                'type': 'text'
            },
            {
                'name': 'credits',
                'label': 'Credits',
                'type': 'number',
                'min_value': 0,
                'max_value': 10,
                'step': 0.5
            },
            {
                'name': 'description',
                'label': 'Description',
                'type': 'text'
            },
            {
                'name': 'dept_id',
                'label': 'Department',
                'type': 'select',
                'query': "SELECT dept_id, dept_name FROM Department",
                'display_field': 'dept_name',
                'value_field': 'dept_id'
            }
        ],
        get_record_query="""
        SELECT title, credits, description, dept_id
        FROM Course
        WHERE course_id = %s
        """
    )

# Departments page (using the original CRUD interface)
elif page == "Departments":
    display_crud_interface(
        entity_name="Department",
        columns=["dept_id", "dept_name", "building", "budget", "head_name"],
        key_column="dept_id",
        display_query="""
        SELECT d.dept_id, d.dept_name, d.building, d.budget,
               CONCAT(p.first_name, ' ', p.last_name) as head_name
        FROM Department d
        LEFT JOIN Faculty f ON d.head_faculty_id = f.faculty_id
        LEFT JOIN Person p ON f.person_id = p.person_id
        ORDER BY d.dept_name
        """,
        insert_query="""
        INSERT INTO Department (dept_name, building, budget, head_faculty_id)
        VALUES (%s, %s, %s, %s)
        """,
        update_query="""
        UPDATE Department 
        SET dept_name = %s, building = %s, budget = %s, head_faculty_id = %s 
        WHERE dept_id = %s
        """,
        delete_query="DELETE FROM Department WHERE dept_id = %s",
        form_fields=[
            {
                'name': 'dept_name',
                'label': 'Department Name',
                'type': 'text'
            },
            {
                'name': 'building',
                'label': 'Building',
                'type': 'text'
            },
            {
                'name': 'budget',
                'label': 'Budget',
                'type': 'number',
                'min_value': 0,
                'step': 1000
            },
            {
                'name': 'head_faculty_id',
                'label': 'Department Head',
                'type': 'select',
                'query': """
                    SELECT f.faculty_id, CONCAT(p.first_name, ' ', p.last_name) as name 
                    FROM Faculty f
                    JOIN Person p ON f.person_id = p.person_id
                """,
                'display_field': 'name',
                'value_field': 'faculty_id'
            }
        ],
        get_record_query="""
        SELECT dept_name, building, budget, head_faculty_id
        FROM Department
        WHERE dept_id = %s
        """
    )

# Enrollments page (using the original CRUD interface)
elif page == "Enrollments":
    display_crud_interface(
        entity_name="Enrollment",
        columns=["student_name", "course_title", "semester", "year", "enrollment_date", "grade"],
        key_column="student_id,section_id",
        display_query="""
        SELECT e.student_id, e.section_id,
               CONCAT(p.first_name, ' ', p.last_name) as student_name,
               c.title as course_title, s.semester, s.year, 
               e.enrollment_date, g.letter_grade as grade
        FROM Enrollment e
        JOIN Student st ON e.student_id = st.student_id
        JOIN Person p ON st.person_id = p.person_id
        JOIN Section s ON e.section_id = s.section_id
        JOIN Course c ON s.course_id = c.course_id
        LEFT JOIN Grade g ON e.grade_id = g.grade_id
        ORDER BY e.enrollment_date DESC
        """,
        insert_query="""
        INSERT INTO Enrollment (student_id, section_id, enrollment_date)
        VALUES (%s, %s, %s)
        """,
        update_query="""
        UPDATE Enrollment 
        SET student_id = %s, section_id = %s, enrollment_date = %s 
        WHERE student_id = %s AND section_id = %s
        """,
        delete_query="DELETE FROM Enrollment WHERE student_id = %s AND section_id = %s",
        form_fields=[
            {
                'name': 'student_id',
                'label': 'Student',
                'type': 'select',
                'query': """
                    SELECT s.student_id, CONCAT(p.first_name, ' ', p.last_name) as name
                    FROM Student s
                    JOIN Person p ON s.person_id = p.person_id
                """,
                'display_field': 'name',
                'value_field': 'student_id'
            },
            {
                'name': 'section_id',
                'label': 'Section',
                'type': 'select',
                'query': """
                    SELECT s.section_id, 
                           CONCAT(c.title, ' (', s.semester, ' ', s.year, ')') as name
                    FROM Section s
                    JOIN Course c ON s.course_id = c.course_id
                """,
                'display_field': 'name',
                'value_field': 'section_id'
            },
            {
                'name': 'enrollment_date',
                'label': 'Enrollment Date',
                'type': 'date'
            }
        ],
        get_record_query="""
        SELECT student_id, section_id, enrollment_date
        FROM Enrollment
        WHERE student_id = %s AND section_id = %s
        """
    )

# Sections page (using the original CRUD interface)
elif page == "Sections":
    display_crud_interface(
        entity_name="Section",
        columns=["section_id", "course_title", "semester", "year", "room_number", "faculty_name"],
        key_column="section_id",
        display_query="""
        SELECT s.section_id, c.title as course_title, s.semester, s.year, 
               s.room_number, CONCAT(p.first_name, ' ', p.last_name) as faculty_name
        FROM Section s
        JOIN Course c ON s.course_id = c.course_id
        JOIN Faculty f ON s.faculty_id = f.faculty_id
        JOIN Person p ON f.person_id = p.person_id
        ORDER BY s.year DESC, s.semester
        """,
        insert_query="""
        INSERT INTO Section (course_id, semester, year, room_number, faculty_id)
        VALUES (%s, %s, %s, %s, %s)
        """,
        update_query="""
        UPDATE Section 
        SET course_id = %s, semester = %s, year = %s, room_number = %s, faculty_id = %s 
        WHERE section_id = %s
        """,
        delete_query="DELETE FROM Section WHERE section_id = %s",
        form_fields=[
            {
                'name': 'course_id',
                'label': 'Course',
                'type': 'select',
                'query': "SELECT course_id, title FROM Course",
                'display_field': 'title',
                'value_field': 'course_id'
            },
            {
                'name': 'semester',
                'label': 'Semester',
                'type': 'select',
                'options': ['Fall', 'Spring', 'Summer'],
                'display_field': '',
                'value_field': ''
            },
            {
                'name': 'year',
                'label': 'Year',
                'type': 'number',
                'min_value': 2000,
                'max_value': 2100,
                'step': 1
            },
            {
                'name': 'room_number',
                'label': 'Room Number',
                'type': 'text'
            },
            {
                'name': 'faculty_id',
                'label': 'Faculty',
                'type': 'select',
                'query': """
                    SELECT f.faculty_id, CONCAT(p.first_name, ' ', p.last_name) as name
                    FROM Faculty f
                    JOIN Person p ON f.person_id = p.person_id
                """,
                'display_field': 'name',
                'value_field': 'faculty_id'
            }
        ],
        get_record_query="""
        SELECT course_id, semester, year, room_number, faculty_id
        FROM Section
        WHERE section_id = %s
        """
    )

# Library page (using the original CRUD interface)
elif page == "Library":
    display_crud_interface(
        entity_name="Library Book",
        columns=["book_id", "title", "author", "isbn", "status", "facility"],
        key_column="book_id",
        display_query="""
        SELECT b.book_id, b.title, b.author, b.isbn, b.status, f.facility_type as facility
        FROM Library_Book b
        JOIN Facility f ON b.facility_id = f.facility_id
        ORDER BY b.title
        """,
        insert_query="""
        INSERT INTO Library_Book (title, author, isbn, status, facility_id)
        VALUES (%s, %s, %s, %s, %s)
        """,
        update_query="""
        UPDATE Library_Book 
        SET title = %s, author = %s, isbn = %s, status = %s, facility_id = %s 
        WHERE book_id = %s
        """,
        delete_query="DELETE FROM Library_Book WHERE book_id = %s",
        form_fields=[
            {
                'name': 'title',
                'label': 'Title',
                'type': 'text'
            },
            {
                'name': 'author',
                'label': 'Author',
                'type': 'text'
            },
            {
                'name': 'isbn',
                'label': 'ISBN',
                'type': 'text'
            },
            {
                'name': 'status',
                'label': 'Status',
                'type': 'select',
                'options': ['Available', 'Checked Out', 'Lost'],
                'display_field': '',
                'value_field': ''
            },
            {
                'name': 'facility_id',
                'label': 'Facility',
                'type': 'select',
                'query': "SELECT facility_id, facility_type FROM Facility WHERE facility_type = 'Library'",
                'display_field': 'facility_type',
                'value_field': 'facility_id'
            }
        ],
        get_record_query="""
        SELECT title, author, isbn, status, facility_id
        FROM Library_Book
        WHERE book_id = %s
        """
    )

# Add a footer
st.markdown("---")
st.caption("University Management System - Created with Streamlit")