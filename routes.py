from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, current_app, Response
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from models import db, User, Student, Professor, Subject, Attendance
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta, date, time
from forms import StudentRegistrationForm, ProfessorRegistrationForm, LoginForm, StudentEditForm, EmailReportForm
from face_utils import encode_face, compare_faces
import base64, json
from PIL import Image
from io import BytesIO
import numpy as np
import face_recognition
import ast
import serial
import time as t
from collections import defaultdict


def decode_base64_image(data):
    img_bytes = base64.b64decode(data.split(',')[1] if ',' in data else data)
    img = Image.open(BytesIO(img_bytes)).convert('RGB')
    return np.array(img)


app_routes = Blueprint('routes', __name__)

# --- Decorators ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def professor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not (current_user.is_professor or current_user.is_admin):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# --- Dashboard (role-based) ---
@app_routes.route('/')
@login_required
def dashboard():
    if current_user.is_admin:
        return render_template('dashboard.html')
    elif current_user.is_professor:
        return redirect(url_for('routes.professor_dashboard'))
    elif current_user.is_student:
        return redirect(url_for('routes.student_dashboard'))
    else:
        flash('Unknown user role!', 'danger')
        return redirect(url_for('routes.logout'))

# --- Professor Dashboard ---
@app_routes.route('/professor_dashboard', methods=['GET', 'POST'])
@login_required
@professor_required
def professor_dashboard():
    professor = Professor.query.filter_by(user_id=current_user.id).first()
    if not professor:
        flash("Professor account not found!", "danger")
        return redirect(url_for('routes.login'))
    subjects = Subject.query.filter_by(professor_id=professor.id).all()
    subject_id = request.args.get('subject_id', type=int) or request.form.get('subject_id', type=int)
    selected_subject = Subject.query.get(subject_id) if subject_id else None

    # Filtering by date
    start_date = request.values.get('start_date')
    end_date = request.values.get('end_date')

    query = Attendance.query.join(Student).filter(
        Attendance.subject_id == subject_id
    ) if selected_subject else Attendance.query.filter(False)

    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(Attendance.timestamp >= start_dt)
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        query = query.filter(Attendance.timestamp <= end_dt)

    records = query.order_by(Attendance.timestamp.desc()).all() if selected_subject else []
    total = sum(1 for r in records if r.status in ["Present", "Late", "Excuse", "Absent"])
    present = sum(1 for r in records if r.status == "Present")
    logged_out = sum(1 for r in records if r.status == "Logged Out")
    late = sum(1 for r in records if r.status == "Late")
    excused = sum(1 for r in records if r.status == "Excused")
    absent = sum(1 for r in records if r.status == "Absent")
    percentage = (present / total * 100) if total > 0 else 0
    attendance_summary = {
        "total": total,
        "present": present,
        "logged_out": logged_out,
        "late": late,
        "excused": excused,
        "absent": absent
    }

    # Display real name
    display_name = f"{professor.last_name}, {professor.first_name}"
    if professor.middle_name:
        display_name += f" {professor.middle_name}"
    if professor.suffix:
        display_name += f" {professor.suffix}"

    # Handle Send Email POST
    if request.method == "POST" and "send_report" in request.form:
        recipient = request.form.get("email")
        if recipient and records:
            bads = [r.id for r in records if r.student is None]
            if bads:
                print(f"WWARNING: These Attendance IDs have no student: {bads}")
            # Generate CSV or table for the email
            csv_rows = ["Student ID,Student Name,Date,Time,Status"]
            for r in records:
                if r.student is None:
                    print(f"Warning: Attendance ID {r.id} has no student! Skipping.")
                    continue
                csv_rows.append(f'{r.student.student_id},"{r.student.last_name}, {r.student.first_name}",'
                                f'{r.timestamp.strftime("%Y-%m-%d")},{r.timestamp.strftime("%I:%M %p")},{r.status}')
            csv_data = "\n".join(csv_rows)

            msg = Message(f"Attendance Report for {selected_subject.name}",
                          recipients=[recipient])
            msg.body = f"Attendance Report for {selected_subject.name}\n\nSee attached CSV file."
            msg.attach(f"{selected_subject.name}-attendance.csv", "text/csv", csv_data)
            current_app.extensions['mail'].send(msg)
            flash("Report sent to " + recipient, "success")
        else:
            flash("Recipient email and at least one record required.", "danger")

    return render_template(
        "professor_dashboard.html",
        subjects=subjects,
        selected_subject=selected_subject,
        selected_subject_id=str(subject_id) if subject_id else "",
        records=records,
        attendance_summary=attendance_summary,
        percentage=percentage,
        display_name=display_name,
        start_date=start_date or "",
        end_date=end_date or ""
    )

    # Handle email report (just a placeholder logic, put your real email code)
    if request.args.get('send_report') and recipient_email and records:
        # send_attendance_report(recipient_email, records)
        flash("Attendance report sent to {}".format(recipient_email), "success")

    return render_template(
        "professor_dashboard.html",
        professor=professor,
        subjects=subjects,
        selected_subject=selected_subject,
        selected_subject_id=str(selected_subject_id) if selected_subject_id else "",
        start_date=start_date or "",
        end_date=end_date or "",
        recipient_email=recipient_email or "",
        records=records
    )

# --- Student Dashboard ---
@app_routes.route('/student_dashboard')
@login_required
def student_dashboard():
    if not getattr(current_user, "is_student", False):
        abort(403)
    student = Student.query.filter_by(user_id=current_user.id).first()
    if student is None:
        flash("Student profile not found. Please contact admin.", "danger")
        return redirect(url_for('routes.logout'))

    subjects = Subject.query.all()
    subject_id = request.args.get("subject_id", type=int)
    selected_subject = None

    # Get records (filtered by subject if needed)
    if subject_id:
        selected_subject = Subject.query.filter_by(id=subject_id).first()
        records = Attendance.query.filter_by(
            student_id=student.id,
            subject_id=subject_id
        ).order_by(Attendance.timestamp.desc()).all()
    else:
        records = Attendance.query.filter_by(
            student_id=student.id
        ).order_by(Attendance.timestamp.desc()).all()

    # --- Group by (subject, date) for one row per day per subject ---
    grouped = defaultdict(lambda: {"date": None, "login": None, "logout": None, "status": None})
    for r in records:
        key = (r.subject_id, r.timestamp.date())
        # Set the date for display
        if grouped[key]["date"] is None:
            grouped[key]["date"] = r.timestamp
        # Save first Present/Late/Excused as login
        if r.status in ["Present", "Late", "Excused"] and grouped[key]["login"] is None:
            grouped[key]["login"] = r.timestamp
            grouped[key]["status"] = r.status
        # Save first Logged Out as logout
        if r.status == "Logged Out" and grouped[key]["logout"] is None:
            grouped[key]["logout"] = r.timestamp

    # Convert grouped data to a display list
    display_records = []
    for k, v in grouped.items():
        display_records.append({
            "date": v["date"],
            "login": v["login"],
            "logout": v["logout"],
            "status": v["status"]
        })

    # Sort by date (DESC)
    display_records.sort(key=lambda x: x["date"], reverse=True)

    # Compute attendance percentage (Present only, ignore Logged Out, like before)
    total_sessions = sum(1 for r in display_records if r["status"] is not None)
    present_count = sum(1 for r in display_records if r["status"] == "Present")
    percentage = (present_count / total_sessions) * 100 if total_sessions > 0 else 0

    return render_template(
        'student_dashboard.html',
        student=student,
        subjects=subjects,
        records=display_records,
        selected_subject_id=str(subject_id) if subject_id else "",
        percentage=percentage
    )


# --- Login / Logout ---
@app_routes.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('routes.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app_routes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.login'))
    
    
def decode_base64_image(data):
    img_bytes = base64.b64decode(data.split(',')[1] if ',' in data else data)
    img = Image.open(BytesIO(img_bytes)).convert('RGB')
    return np.array(img)

@app_routes.route('/register/student', methods=['GET', 'POST'])
@login_required
@admin_required
def register_student():
    form = StudentRegistrationForm()
    if form.validate_on_submit():
        print("\n--- REGISTRATION SUBMIT ---")
        print("Face Images Raw:", request.form.get('face_images'))
        face_images_json = request.form.get('face_images', '[]')
        try:
            import ast
            face_images = ast.literal_eval(face_images_json) if isinstance(face_images_json, str) else face_images_json
        except Exception as e:
            print("FACE IMAGES PARSE FAIL:", e)
            face_images = []
        print("Parsed face_images:", face_images)
        
        # ENCODING
        face_encoding = None
        if face_images and len(face_images) > 0:
            try:
                img_np = decode_base64_image(face_images[0])
                print("Image shape:", img_np.shape)
                import face_recognition
                encodings = face_recognition.face_encodings(img_np)
                print("Face encodings:", encodings)
                if encodings:
                    face_encoding = list(encodings[0])
            except Exception as e:
                print("Face encoding error:", e)
        
        print("Final face_encoding to save:", face_encoding)

        if not face_encoding:
            flash('Face encoding failed! Please retake registration with a clear face photo.', 'danger')
            print("FACE ENCODING FAILED—no DB save.")
            return render_template('register_student.html', form=form)

        # UNIQUE USER CHECK
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()
        if existing_user:
            flash('Username or email already exists.', 'danger')
            print("USER EXISTS, NO DB SAVE.")
            return render_template('register_student.html', form=form)

        # CREATE USER
        from werkzeug.security import generate_password_hash
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data),
            is_student=True
        )
        db.session.add(user)
        db.session.commit()

        # CREATE STUDENT
        student = Student(
            user_id=user.id,
            student_id=form.student_id.data,
            rfid_tag=form.rfid_tag.data,
            last_name=form.last_name.data,
            first_name=form.first_name.data,
            middle_name=form.middle_name.data,
            suffix=form.suffix.data,
            parent_contact=form.parent_contact.data,
            enrollment_status=form.enrollment_status.data,
            face_images=face_images_json,
            face_encoding=face_encoding,
        )
        db.session.add(student)
        db.session.commit()
        print(f"Registered Student {student.student_id}, encoding len: {len(face_encoding) if face_encoding else 0}")

        flash('Student registered successfully!', 'success')
        return redirect(url_for('routes.login'))

    else:
        print("Form errors:", form.errors)
    return render_template('register_student.html', form=form)

# --- PROFESSOR REGISTRATION ---
@app_routes.route('/register/professor', methods=['GET', 'POST'])
@login_required
@admin_required
def register_professor():
    form = ProfessorRegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()
        if existing_user:
            flash('Username or email already exists.', 'danger')
            return render_template('register_professor.html', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data),
            is_professor=True
        )
        db.session.add(user)
        db.session.commit()

        professor = Professor(
            user_id=user.id,
            last_name=form.last_name.data,
            first_name=form.first_name.data,
            middle_name=form.middle_name.data,
            suffix=form.suffix.data,
        )
        db.session.add(professor)
        db.session.commit()
        flash('Professor registered successfully!', 'success')
        return redirect(url_for('routes.login'))
    return render_template('register_professor.html', form=form)
    
    # SHOW FORM ERRORS
    if form.errors:
        print('FORM ERRORS:', form.errors)
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", "danger")

    return render_template('register.html', form=form)


# --- Admin Panel: Manage Subjects (Add/Edit/Delete/Assign Professor) ---
@app_routes.route('/admin/subjects', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_subjects():
    professors = Professor.query.all()
    if request.method == 'POST':
        name = request.form.get('name').strip()
        professor_id = request.form.get('professor_id', type=int)
        if Subject.query.filter_by(name=name).first():
            flash("Subject name already exists.", "danger")
        else:
            subj = Subject(name=name, professor_id=professor_id)
            db.session.add(subj)
            db.session.commit()
            flash("Subject added.", "success")
        return redirect(url_for('routes.admin_subjects'))
    subjects = Subject.query.all()
    return render_template('admin_subjects.html', subjects=subjects, professors=professors)


@app_routes.route('/admin/subjects/edit/<int:subject_id>', methods=['POST'])
@login_required
@admin_required
def edit_subject(subject_id):
    subj = Subject.query.get_or_404(subject_id)
    new_name = request.form.get('name').strip()
    new_professor_id = request.form.get('professor_id', type=int)

    # Check if another subject already has this name
    existing = Subject.query.filter(Subject.name == new_name, Subject.id != subject_id).first()
    if existing:
        flash("Another subject with this name already exists.", "danger")
    else:
        subj.name = new_name
        subj.professor_id = new_professor_id
        db.session.commit()
        flash("Subject updated.", "success")

    return redirect(url_for('routes.admin_subjects'))

@app_routes.route('/admin/subjects/delete/<int:subject_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_subject(subject_id):
    subj = Subject.query.get_or_404(subject_id)
    db.session.delete(subj)
    db.session.commit()
    flash("Subject deleted.", "success")
    return redirect(url_for('routes.admin_subjects'))

# --- Attendance Panel for Professor/Admin (filtered) ---
from collections import defaultdict

@app_routes.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance_panel():
    form = EmailReportForm()

    # Filter by subject (search filter)
    subject_id = request.args.get("subject_id", type=int)
    subjects = Subject.query.all()

    # Query records depending on role
    if getattr(current_user, "is_admin", False):
        base_query = Attendance.query
    else:
        professor = Professor.query.filter_by(user_id=current_user.id).first()
        subject_ids = [s.id for s in Subject.query.filter_by(professor_id=professor.id).all()] if professor else []
        base_query = Attendance.query.filter(Attendance.subject_id.in_(subject_ids))

    if subject_id:
        base_query = base_query.filter(Attendance.subject_id == subject_id)

    base_query = base_query.order_by(Attendance.timestamp.desc())

    # Fetch all records
    records = base_query.all()

    # --- GROUP BY student_id, subject_id, date ---
    grouped = defaultdict(lambda: {
        "student_id": None, "student_name": None, "subject": None,
        "date": None, "login": None, "logout": None, "status": None, "id": None
    })
    for r in records:
        if r.student is None:
            continue  # skip orphaned
        key = (r.student_id, r.subject_id, r.timestamp.date())
        entry = grouped[key]
        entry["student_id"] = r.student.student_id
        entry["student_name"] = f"{r.student.last_name}, {r.student.first_name}"
        entry["subject"] = r.subject.name if r.subject else ""
        entry["date"] = r.timestamp.date()
        if entry["login"] is None and r.status in ["Present", "Late", "Excused"]:
            entry["login"] = r.timestamp
            entry["status"] = r.status
            entry["id"] = r.id
        if r.status == "Logged Out" and entry["logout"] is None:
            entry["logout"] = r.timestamp

    display_records = list(grouped.values())
    display_records.sort(key=lambda x: (x["date"], x["student_id"]), reverse=True)

    # --- EMAIL LOGIC (optional, keep if needed) ---
    if request.method == 'POST':
        recipient = request.form.get('recipient') or form.email.data
        if recipient:
            csv_rows = ["Student ID Number,Student Name,Date,Login,Logout,Status"]
            for r in display_records:
                csv_rows.append(f'{r["student_id"]},"{r["student_name"]}",{r["date"]},'
                                f'{r["login"].strftime("%I:%M %p") if r["login"] else ""},'
                                f'{r["logout"].strftime("%I:%M %p") if r["logout"] else ""},'
                                f'{r["status"] or ""}')
            csv_data = "\n".join(csv_rows)
            try:
                from flask_mail import Message
                from flask import current_app
                mail = current_app.extensions['mail']
                msg = Message("Attendance Report", recipients=[recipient])
                msg.body = "See attached CSV attendance report."
                msg.attach("attendance_report.csv", "text/csv", csv_data)
                mail.send(msg)
                flash(f"Attendance report sent to {recipient}", "success")
            except Exception as e:
                flash(f"Failed to send email: {e}", "danger")
        else:
            flash("Recipient email is required.", "danger")
        return redirect(url_for('routes.attendance_panel'))

    return render_template(
        'attendance.html',
        records=display_records,
        form=form,
        subjects=subjects,
        selected_subject_id=str(subject_id) if subject_id else ""
    )


    # --- EMAIL LOGIC (optional, can keep as is) ---
    if request.method == 'POST':
        recipient = request.form.get('recipient')
        if recipient:
            csv_rows = ["Student ID Number,Student Name,Subject,Date,Login,Logout,Status"]
            for r in records:
                csv_rows.append(f'{r["student"].student_id if r["student"] else ""},'
                                f'"{r["student"].last_name if r["student"] else ""}, {r["student"].first_name if r["student"] else ""}",'
                                f'{r["subject"].name if r["subject"] else ""},'
                                f'{r["date"].strftime("%Y-%m-%d") if r["date"] else ""},'
                                f'{r["login"].strftime("%I:%M %p") if r["login"] else ""},'
                                f'{r["logout"].strftime("%I:%M %p") if r["logout"] else ""},'
                                f'{r["status"] if r["status"] else ""}')
            csv_data = "\n".join(csv_rows)
            try:
                msg = Message("Attendance Report", recipients=[recipient])
                msg.body = "See attached CSV attendance report."
                msg.attach("attendance_report.csv", "text/csv", csv_data)
                mail.send(msg)
                flash(f"Attendance report sent to {recipient}", "success")
            except Exception as e:
                flash(f"Failed to send email: {e}", "danger")
        else:
            flash("Recipient email is required.", "danger")
        return redirect(url_for('routes.attendance_panel'))

    return render_template(
        'attendance.html',
        records=records,
        subjects=subjects,
        selected_subject_id=str(subject_id) if subject_id else "",
        form=form
    )

    
# --- Edit Attendance (Prof/Admin only) ---
@app_routes.route('/attendance/edit/<int:attendance_id>', methods=['GET', 'POST'])
@login_required
def edit_attendance(attendance_id):
    att = Attendance.query.get_or_404(attendance_id)
    subject_id = request.args.get('subject_id')
    
    if request.method == 'POST':
        new_status = request.form.get('status')
        subject_id = request.form.get('status_id')
        if new_status in ["Present", "Late", "Excused", "Absent", "Logged Out"]:
            att.status = new_status
            db.session.commit()
            flash("Attendance updated.", "success")
        else:
            flash("Invalid status.", "danger")
        return redirect(url_for('routes.professor_dashboard', subject_id=subject_id))

    # For GET, render the form
    return render_template('edit_attendance.html', record=att)

# --- API: Attendance Submission ---
@app_routes.route('/api/attendance', methods=['POST'])
def api_attendance():
    data = request.json
    rfid = data.get('rfid_tag')
    face_image_b64_1 = data.get('face_image1')
    face_image_b64_2 = data.get('face_image2')
    professor_username = data.get('professor')
    subject_name = data.get('subject')
    student = Student.query.filter_by(rfid_tag=rfid).first()
    if not student:
        return jsonify({'success': False, 'message': 'RFID not found'}), 404
    prof = User.query.filter_by(username=professor_username, is_professor=True).first()
    subj = Subject.query.filter_by(name=subject_name, professor_id=prof.id if prof else None).first()
    if not prof or not subj:
        return jsonify({'success': False, 'message': 'Invalid professor or subject'}), 400
    today = date.today()
    latest = Attendance.query.filter(
        Attendance.student_id == student.id,
        Attendance.timestamp >= datetime.combine(today, time.min),
        Attendance.timestamp <= datetime.combine(today, time.max),
    ).order_by(Attendance.timestamp.desc()).first()
    new_status = "Present" if not latest or latest.status == "Logged Out" else "Logged Out"
    att = Attendance(
        student_id=student.id,
        timestamp=datetime.now(),
        status=new_status,
        professor_id=prof.id,
        subject_id=subj.id
    )
    db.session.add(att)
    db.session.commit()
    return jsonify({'success': True, 'message': f'{new_status} recorded.'})

# --- Kiosk Page ---
@app_routes.route('/kiosk')
@login_required
def kiosk():
    professors = Professor.query.all()
    subjects = Subject.query.all()
    return render_template('kiosk.html', professors=professors, subjects=subjects, hide_nav=True)

# --- Admin Panel (all students) ---
@app_routes.route('/admin')
@login_required
@admin_required
def admin_panel():
    students = Student.query.all()
    return render_template('admin.html', students=students)

# --- Edit Student ---
@app_routes.route('/student/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
@professor_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    form = StudentEditForm(obj=student)
    if form.validate_on_submit():
        student.student_id = form.student_id.data
        student.rfid_tag = form.rfid_tag.data
        student.last_name = form.last_name.data
        student.first_name = form.first_name.data
        student.middle_name = form.middle_name.data
        student.suffix = form.suffix.data
        student.parent_contact = form.parent_contact.data
        student.enrollment_status = form.enrollment_status.data
        db.session.commit()
        flash('Student updated!', 'success')
        return redirect(url_for('routes.admin_panel'))
    return render_template('edit_student.html', form=form, student=student)

# --- Delete Student ---
@app_routes.route('/student/<int:student_id>/delete', methods=['POST'])
@login_required
@professor_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted!', 'success')
    return redirect(url_for('routes.admin_panel'))

# --- Send Attendance Report (prof/admin only, add this for template url_for!) ---
@app_routes.route('/send_attendance_report', methods=['GET', 'POST'])
@login_required
@professor_required
def send_attendance_report():
    form = EmailReportForm()
    if form.validate_on_submit():
        # Get validated data directly from form
        start_date = form.date_from.data
        end_date = form.date_to.data
        recipient = form.email.data

        # Query and send email here
        from datetime import datetime, timedelta
        # (Add one day to include the end_date itself)
        end_dt = end_date + timedelta(days=1)
        records = Attendance.query.filter(
            Attendance.timestamp >= start_date,
            Attendance.timestamp < end_dt
        ).order_by(Attendance.timestamp.desc()).all()

        # Build CSV
        csv_rows = ["Student ID,Student Name,Date,Time,Status"]
        for r in records:
            csv_rows.append(f'{r.student.student_id},"{r.student.last_name}, {r.student.first_name}",'
                            f'{r.timestamp.strftime("%Y-%m-%d")},{r.timestamp.strftime("%I:%M %p")},{r.status}')
        csv_data = "\n".join(csv_rows)
        try:
            msg = Message("Attendance Report", recipients=[recipient])
            msg.body = f"Attached is the attendance report from {start_date} to {end_date}."
            msg.attach("attendance_report.csv", "text/csv", csv_data)
            mail = current_app.extensions['mail']
            mail.send(msg)
            flash(f"Attendance report sent to {recipient}", "success")
        except Exception as e:
            flash(f"Failed to send email: {e}", "danger")
        return redirect(url_for('routes.attendance_panel'))
    else:
        if form.errors:
            flash('Invalid email form: ' + str(form.errors), 'danger')
    return redirect(url_for('routes.attendance_panel'))


@app_routes.route('/attendance_analytics')
@login_required
@professor_required
def attendance_analytics():
    import os
    from sqlalchemy import func

    try:
        status_counts = (
            db.session.query(Attendance.status, func.count(Attendance.status))
            .group_by(Attendance.status)
            .all()
        )
        print("status_counts:", status_counts)
    except Exception as e:
        print("EXCEPTION DURING STATUS COUNTS:", e)
        status_counts = []

    status_labels = [row[0] for row in status_counts]
    status_values = [row[1] for row in status_counts]

    if not status_labels:
        status_labels = ["No Data"]
        status_values = [0]

    return render_template(
        'attendance_analytics.html',
        status_labels=status_labels,
        status_values=status_values
    )


@app_routes.route('/api/attendance_tap', methods=['POST'])
def api_attendance_tap():
    data = request.get_json() if request.is_json else request.form

    # --- Extract data ---
    rfid_tag = data.get("rfid_tag")
    subject_id = data.get("subject_id")
    professor_id = data.get("professor_id")
    start_time_str = data.get("start_time")
    face_image1 = data.get("face_image1")
    face_image2 = data.get("face_image2")
    print(f"Received RFID: {rfid_tag} | Subject: {subject_id} | Prof: {professor_id}")

    # --- Validate IDs ---
    try:
        subject_id = int(subject_id)
        professor_id = int(professor_id)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid subject or professor ID.'}), 400

    # --- Find student by RFID ---
    student = Student.query.filter_by(rfid_tag=rfid_tag).first()
    if not student:
        return jsonify({'success': False, 'message': 'RFID not found.'}), 404

    # --- Decode images ---
    def decode_image(base64_str):
        if not base64_str:
            return None
        try:
            img_bytes = base64.b64decode(base64_str.split(',')[1] if ',' in base64_str else base64_str)
            img = Image.open(BytesIO(img_bytes)).convert('RGB')
            return np.array(img)
        except Exception as e:
            print("Image decode error:", e)
            return None

    if not face_image1 or not face_image2:
        return jsonify({'success': False, 'message': 'Face images missing. Please try again.'}), 400

    img_np1 = decode_image(face_image1)
    img_np2 = decode_image(face_image2)
    if img_np1 is None or img_np2 is None:
        return jsonify({'success': False, 'message': 'Error decoding face images. Try again.'}), 400

    # --- Liveness check ---
    def simple_blink_liveness(img1, img2):
        enc1 = encode_face(img1)
        enc2 = encode_face(img2)
        if enc1 is not None and enc2 is not None and not np.allclose(enc1, enc2):
            return True
        return False
    if not simple_blink_liveness(img_np1, img_np2):
        return jsonify({'success': False, 'message': 'Liveness check failed. Please blink!'}), 400

    # --- Load student's registered face encoding ---
    known_encoding = student.face_encoding
    if not known_encoding:
        return jsonify({'success': False, 'message': 'No face encoding found for this student. Please register face.'}), 400
    try:
        if isinstance(known_encoding, str):
            known_encoding = np.array(ast.literal_eval(known_encoding))
        else:
            known_encoding = np.array(known_encoding)
    except Exception as e:
        print("Known encoding parse error:", e)
        return jsonify({'success': False, 'message': 'Invalid face encoding in DB.'}), 400

    # --- Encode new face & compare ---
    test_encoding = encode_face(img_np1)
    if test_encoding is None:
        return jsonify({'success': False, 'message': 'Face not detected. Please try again.'}), 400
    matched = compare_faces([known_encoding], test_encoding, tolerance=0.4)
    if not (matched and matched[0]):
        return jsonify({'success': False, 'message': 'Face does not match registered student.'}), 400

    # --- Attendance logic ---
    now = datetime.now()
    today = date.today()
    if not start_time_str:
        return jsonify({'success': False, 'message': 'Please select the subject start time.'}), 400
    try:
        subject_start_time = datetime.strptime(start_time_str, "%H:%M:%S").time()
    except Exception:
        return jsonify({'success': False, 'message': 'Invalid start time format.'}), 400
    grace_period = timedelta(minutes=15)
    subject_start_dt = datetime.combine(today, subject_start_time)

    present_record = Attendance.query.filter(
        Attendance.student_id == student.id,
        Attendance.subject_id == subject_id,
        Attendance.timestamp >= datetime.combine(today, time.min),
        Attendance.timestamp <= datetime.combine(today, time.max),
        Attendance.status.in_(["Present", "Late"])
    ).first()
    logout_record = Attendance.query.filter(
        Attendance.student_id == student.id,
        Attendance.subject_id == subject_id,
        Attendance.timestamp >= datetime.combine(today, time.min),
        Attendance.timestamp <= datetime.combine(today, time.max),
        Attendance.status == "Logged Out"
    ).first()

    if not present_record:
        status = "Late" if now > (subject_start_dt + grace_period) else "Present"
        attendance = Attendance(
            student_id=student.id,
            subject_id=subject_id,
            professor_id=professor_id,
            timestamp=now,
            status=status
        )
        db.session.add(attendance)
        db.session.commit()

        # ---- Send SMS to Parent ----
        msg_time = now.strftime('%I:%M %p')
        msg_date = now.strftime('%Y-%m-%d')
        try:
            send_sms(
                student.parent_contact,
                f"{student.first_name} {student.last_name} entered the classroom in Pateros Technological College at {msg_time} on {msg_date}. God Bless!"
            )
        except Exception as e:
            print("SMS error:", e)

        return jsonify({'success': True, 'message': f"Attendance recorded: {status}"})
    elif not logout_record:
        attendance = Attendance(
            student_id=student.id,
            subject_id=subject_id,
            professor_id=professor_id,
            timestamp=now,
            status="Logged Out"
        )
        db.session.add(attendance)
        db.session.commit()
        
        msg_time = now.strftime('%I:%M %p')
        msg_date = now.strftime('%Y-%m-%d')
        try:
            send_sms(
                student.parent_contact,
                f"{student.first_name} {student.last_name} has left the classroom in Pateros Technological College at {msg_time} on {msg_date}. God Bless!"
            )
        except Exception as e:
            print("SMS error:", e)
        
        return jsonify({'success': True, 'message': "Logged Out. Have a nice day!"})
    else:
        return jsonify({'success': False, 'message': "You already logged out today for this subject."}), 400

# --- SMS Function (SIM900) ---
def send_sms(phone, message):
    SERIAL_PORT = '/dev/ttyS0'  # Port
    try:
        gsm = serial.Serial(SERIAL_PORT, 9600, timeout=5)
        t.sleep(0.5)
        gsm.write(b'AT\r')
        t.sleep(0.5)
        gsm.write(b'AT+CMGF=1\r')
        t.sleep(0.5)
        gsm.write(('AT+CMGS="{}"\r'.format(phone)).encode())
        t.sleep(0.5)
        gsm.write(message.encode() + b"\r")
        t.sleep(0.5)
        gsm.write(bytes([26]))  # Ctrl+Z
        t.sleep(3)
        gsm.close()
        print(f"SMS sent to {phone}!")
    except Exception as e:
        print("SMS failed:", e)

        

@app_routes.route('/download_attendance_csv')
@login_required
@professor_required
def download_attendance_csv():
    subject_id = request.args.get('subject_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Get subject
    subject = Subject.query.get(subject_id)
    if not subject:
        return "Subject not found.", 404

    # Filter attendance records
    query = Attendance.query.join(Student).filter(
        Attendance.subject_id == subject_id
    )
    if start_date:
        query = query.filter(Attendance.timestamp >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        query = query.filter(Attendance.timestamp <= datetime.strptime(end_date, "%Y-%m-%d"))

    records = query.order_by(Attendance.timestamp.asc()).all()

    # --- Pair login/logout per student per day ---
    # Key: (student_id, date), Value: dict { "login": time, "logout": time, ... }
    logbook = defaultdict(lambda: {"login": None, "logout": None, "status": None, "student": None})

    for r in records:
        if r.student is None:
            continue
        key = (r.student.student_id, r.timestamp.date())
        logbook[key]["student"] = r.student
        # If first Present/Late, set as login
        if r.status in ["Present", "Late"] and logbook[key]["login"] is None:
            logbook[key]["login"] = r.timestamp.strftime("%Y-%m-%d %H:%M")
            logbook[key]["status"] = r.status
        # If Logged Out, set as logout
        if r.status == "Logged Out":
            logbook[key]["logout"] = r.timestamp.strftime("%Y-%m-%d %H:%M")

    # --- CSV Format ---
    csv_rows = ["Student ID,Student Name,Login Time,Logout Time,Status"]
    for (sid, date_), data in logbook.items():
        s = data["student"]
        csv_rows.append(
            f'{s.student_id},"{s.last_name}, {s.first_name}",{data["login"] or ""},{data["logout"] or ""},{data["status"] or ""}'
        )
    csv_data = "\n".join(csv_rows)

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={subject.name}_attendance.csv"}
    )


