# 🎓 Smart Attendance Monitoring System

> A Raspberry Pi-powered attendance monitoring system that combines **RFID Authentication**, **Face Recognition**, **SMS Notification**, and a **Web-Based Management System** to provide secure, automated, and reliable attendance tracking for educational institutions.

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-Web_Framework-black?logo=flask)
![Django](https://img.shields.io/badge/Django-Web_Framework-green?logo=django)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer_Vision-red?logo=opencv)
![MySQL](https://img.shields.io/badge/MySQL-Database-orange?logo=mysql)
![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi-Hardware-C51A4A?logo=raspberrypi)

---

# 📖 Capstone Project Overview

The **Smart Attendance Monitoring System** is an undergraduate capstone project designed to improve the security and efficiency of attendance monitoring in educational institutions.

Unlike traditional RFID attendance systems, this project utilizes **dual-factor verification** by combining **RFID authentication** and **Face Recognition** before recording attendance. This approach prevents students from lending their RFID cards to classmates, ensuring that only the registered student can successfully check in or check out.

The system runs on a **Raspberry Pi** equipped with a touchscreen display, RFID reader, and Raspberry Pi camera. Attendance records are synchronized with a web application, allowing professors and students to monitor attendance in real time.

Additionally, the system automatically sends **SMS notifications** to parents or guardians whenever a student successfully performs a **Time In** or **Time Out** transaction.

---

# 🎯 Objectives

- Automate classroom attendance monitoring
- Improve attendance accuracy
- Eliminate manual attendance recording
- Prevent proxy attendance using dual authentication
- Provide real-time attendance reports
- Notify parents or guardians through SMS
- Offer a centralized web-based attendance management system

---

# ✨ Key Features

## 🖥 Raspberry Pi Attendance Terminal

- Touchscreen User Interface
- Subject Selection
- Professor Selection
- RFID Card Authentication
- Face Recognition Verification
- Automatic Time In
- Automatic Time Out
- Attendance Validation
- Real-time Database Synchronization

---

## 🎓 Student Portal

- View Attendance History
- View Time In Records
- View Time Out Records
- Attendance Summary
- Personal Attendance Monitoring

---

## 👨‍🏫 Professor Dashboard

- View Attendance Per Subject
- Daily Attendance Reports
- Search Student Records
- Monitor Student Attendance
- Attendance History
- Dashboard Analytics

---

## 📱 SMS Notification

After every successful attendance transaction, the system automatically sends an SMS notification to the student's registered parent or guardian.

Example:

```
Smart Attendance Monitoring System

Student:
Juan Dela Cruz

Subject:
Computer Programming

Status:
TIME IN

Date:
July 30, 2026

Time:
08:05 AM

Your child has successfully entered today's class.
```

The same process is performed during **Time Out**.

---

## 🔒 Security Features

- RFID Authentication
- Face Recognition Verification
- Dual Authentication
- Prevention of Proxy Attendance
- Secure Attendance Logging
- User Authentication
- Session Management

---

# ⚙️ Attendance Workflow

```
Student

     │
     ▼

Select Subject

     │
     ▼

Select Professor

     │
     ▼

Tap RFID Card

     │
     ▼

Verify RFID

     │
     ▼

Capture Face

     │
     ▼

Face Recognition

     │
     ▼

Face Matched?

     │
 ┌───┴────┐
 │        │
No       Yes
 │        │
 ▼        ▼
Reject   Save Attendance
          │
          ▼
Send SMS Notification
          │
          ▼
Attendance Complete
```

The same workflow is applied during **Time Out**.

---

# 🏗 System Architecture

```
                        +----------------------+
                        | Raspberry Pi         |
                        |----------------------|
                        | Python               |
                        | Flask                |
                        | RFID Reader          |
                        | Pi Camera            |
                        | Touchscreen          |
                        +----------+-----------+
                                   |
                                   |
                              MySQL Database
                                   |
           +-----------------------+-----------------------+
           |                                               |
           |                                               |
+----------v-----------+                     +-------------v------------+
| Student Dashboard    |                     | Professor Dashboard      |
|----------------------|                     |--------------------------|
| Attendance History   |                     | Attendance Reports       |
| Time In / Time Out   |                     | Student Monitoring       |
| Attendance Summary   |                     | Search Students          |
+----------------------+                     +--------------------------+
```

---

# 🛠 Technology Stack

## Programming Language

- Python

## Backend Framework

- Flask
- Django

## Frontend

- HTML5
- CSS3
- JavaScript
- Bootstrap

## Database

- MySQL

## Computer Vision

- OpenCV
- Face Recognition

## Hardware

- Raspberry Pi
- Raspberry Pi Camera
- RFID Reader
- RFID Cards
- Touchscreen Display

## Notifications

- SMS Gateway

---

# 📂 System Modules

### Attendance Terminal

- Subject Selection
- Professor Selection
- RFID Reader
- Face Recognition
- Attendance Recording

### Student Module

- Attendance Logs
- Attendance History
- Attendance Summary

### Professor Module

- Dashboard
- Subject Attendance
- Student Monitoring
- Attendance Reports

### Authentication Module

- RFID Verification
- Face Verification
- User Authentication

### Notification Module

- SMS Notification
- Attendance Confirmation

---

# 📸 Screenshots

> Replace these placeholders with actual screenshots from your project.

## Raspberry Pi Attendance Terminal

```
Insert Screenshot Here
```

---

## Subject Selection

```
Insert Screenshot Here
```

---

## RFID Authentication

```
Insert Screenshot Here
```

---

## Face Recognition

```
Insert Screenshot Here
```

---

## Professor Dashboard

```
Insert Screenshot Here
```

---

## Student Dashboard

```
Insert Screenshot Here
```

---

# 🚀 Future Improvements

- Mobile Application
- QR Code Attendance
- Face Recognition Optimization
- Cloud Database Integration
- REST API
- Email Notification
- Push Notification
- Attendance Analytics
- AI-based Face Recognition Enhancement
- Multi-campus Support

---

# 👨‍💻 My Contribution

As one of the developers of this capstone project, my responsibilities included:

- Raspberry Pi Development
- Python Programming
- Flask Backend Development
- Hardware and Software Integration
- RFID Reader Integration
- Face Recognition Implementation
- Attendance Logic Development
- Database Integration
- SMS Notification Integration
- Testing and Debugging

---

# 📚 Learning Outcomes

This project strengthened my knowledge and practical experience in:

- Python Programming
- Flask Framework
- Django Framework
- Raspberry Pi Development
- Computer Vision
- OpenCV
- Face Recognition
- MySQL Database
- Web Application Development
- Hardware and Software Integration
- Software Design
- System Testing

---

# 📄 License

This project was developed as an undergraduate **Capstone Project** for educational and academic purposes.

---

# 👤 Author

**Anjo Olorosisimo,**
**Ivan Marasigan,**
**Nickson Salvador,**
**Maria Kristina Magalang,**
**Winnie Distor,**

Bachelor of Science in Information Technology (BSIT)

GitHub: **https://github.com/alesana-dev**

---

## ⭐ Support

If you found this project interesting, please consider giving it a **⭐ Star** on GitHub.