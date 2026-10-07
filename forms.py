from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SelectField,
    BooleanField,
    SubmitField,
    HiddenField,
    DateField
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

# ----- STUDENT REGISTRATION FORM -----
class StudentRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    student_id = StringField('Student ID Number', validators=[DataRequired(), Length(max=20)])
    rfid_tag = StringField('RFID Tag', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    middle_name = StringField('Middle Name', validators=[Optional(), Length(max=50)])
    suffix = StringField('Suffix', validators=[Optional(), Length(max=10)])
    parent_contact = StringField('Parent Contact Number', validators=[DataRequired(), Length(max=20)])
    enrollment_status = SelectField(
        'Enrollment Status',
        choices=[('Enrolled', 'Enrolled'), ('Not Enrolled', 'Not Enrolled')],
        validators=[DataRequired()]
    )
    face_images = HiddenField('Face Image (base64)', validators=[DataRequired()])
    consent = BooleanField('I agree to the Terms and Privacy Policy', validators=[DataRequired()])
    submit = SubmitField('Register Account')

# ----- PROFESSOR REGISTRATION FORM -----
class ProfessorRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    middle_name = StringField('Middle Name', validators=[Optional(), Length(max=50)])
    suffix = StringField('Suffix', validators=[Optional(), Length(max=10)])
    consent = BooleanField('I agree to the Terms and Privacy Policy', validators=[DataRequired()])
    submit = SubmitField('Register Account')

# ----- ADMIN REGISTRATION FORM (OPTIONAL, if needed) -----
class AdminRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    consent = BooleanField('I agree to the Terms and Privacy Policy', validators=[DataRequired()])
    submit = SubmitField('Register Account')

# ----- UNIVERSAL LOGIN FORM -----
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

# ----- EMAIL REPORT FORM -----
class EmailReportForm(FlaskForm):
    date_from = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    date_to = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    email = StringField('Recipient Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Report')

# ----- STUDENT EDIT FORM (for Admin/Professor Editing) -----
class StudentEditForm(FlaskForm):
    student_id = StringField('Student ID Number', validators=[DataRequired(), Length(max=20)])
    rfid_tag = StringField('RFID Tag', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    middle_name = StringField('Middle Name', validators=[Optional(), Length(max=50)])
    suffix = StringField('Suffix', validators=[Optional(), Length(max=10)])
    parent_contact = StringField('Parent Contact Number', validators=[DataRequired(), Length(max=20)])
    enrollment_status = SelectField(
        'Enrollment Status',
        choices=[('Enrolled', 'Enrolled'), ('Not Enrolled', 'Not Enrolled')],
        validators=[DataRequired()]
    )
    face_image = HiddenField('Face Image (base64)')
    submit = SubmitField('Update Student')
