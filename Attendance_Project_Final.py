import mysql.connector
import cv2
import numpy as np
import face_recognition
from datetime import datetime
import os
import customtkinter as ctk
import time
import qrcode
from PIL import Image
from PIL import ImageTk
from tkinter import StringVar, Listbox, END

ctk.set_appearance_mode("Dark")
path = "AttendanceList"
images = []
classnames = []
myList = os.listdir(path)
for cl in myList:
    curimg = cv2.imread(f'{path}/{cl}')
    images.append(curimg)
    classnames.append(os.path.splitext(cl)[0])

def findEncodings(images):
    encodelist = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face_encodings = face_recognition.face_encodings(img)
        if len(face_encodings) > 0:
            encode = face_encodings[0]
            encodelist.append(encode)
    return encodelist

encodeListKnown = findEncodings(images)

time = datetime.now()
timesD = time.strftime('%D')
def markAttendance(name):
    with open('Attendance.csv', 'r+') as f:
        myDataList = f.readlines()
        nameList = []
        for line in myDataList:
            entry = line.split(',')
            nameList.append(entry[0])
        if name not in nameList:
            now = datetime.now()
            times = now.strftime('%H:%M:%S')
            dtString = now.strftime('%D,%H:%M:%S')
            f.writelines(f'\n{name},{dtString},"PRESENT"')
            mydb = mysql.connector.connect(host="localhost", user="root", passwd="OIS@12345", database="testdb")
            mycursor = mydb.cursor()
            sqlFormula = "INSERT INTO attendance (Name,Date,Time,Status) VALUES (%s, %s, %s, %s)"
            studentInto = (name, timesD, times, "PRESENT")
            mycursor.execute(sqlFormula, studentInto)
            mydb.commit()


path2 = "AttendanceListQR"
files = os.listdir(path)

for file in files:
    name = os.path.splitext(file)[0]

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(name)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    qr_img.save(f"{path2}/{name}.png")

def takeQRAttendance():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    detector = cv2.QRCodeDetector()
    while cap.isOpened():
        success, img = cap.read()
        if not success:
            print("Failed to read frame from video stream")
            break

        start = time.perf_counter()
        value, points, qrcode = detector.detectAndDecode(img)
        if value != "":
            x1 = points[0][0][0]
            y1 = points[0][0][1]
            x2 = points[0][2][0]
            y2 = points[0][2][1]

            x_center = int((x2-x1) / 2 + x1)
            y_center = int((y2-y1) / 2 + y1)

            cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 10)
            cv2.circle(img, (x_center, y_center), 3, (0, 0, 255), cv2.FILLED)
            cv2.putText(img, str(value), (30, 120), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
            markAttendance(value)

        cv2.putText(img, "Press 'Q' to exit", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow("QR Code Recognition", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    showAttendanceDetailsQR()

def takeFaceRecognitionAttendance():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    frame_skip = 10
    while cap.isOpened():
        for _ in range(frame_skip):
            cap.grab()
        success, img = cap.read()
        if not success:
            print("Failed to read frame from video stream")
            break

        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        facesCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

        for encodeFace, faceLoc in zip(encodeCurFrame, facesCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                name = classnames[matchIndex]
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                cv2.rectangle(img, (x1, y1), (x2, y2), (193, 134, 46), 2)
                cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (193, 134, 46), cv2.FILLED)
                cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                markAttendance(name)

        cv2.putText(img, "Press 'Q' to exit", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow('Face Recognition', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    showAttendanceDetailsFaceRecognition()

def showAttendanceDetailsQR():
    def toggle_fullscreen(event):
        if event.keysym == 'Escape':
            details_window.attributes("-fullscreen", not details_window.attributes("-fullscreen"))
    details_window = ctk.CTk()
    details_window.title("Attendance Details - QR Code")
    details_window.geometry("1920x1080")
    details_window.attributes("-fullscreen", True)
    details_window.bind('<Escape>', toggle_fullscreen)
    image = Image.open("Background_Image2.jpg")
    resize = image.resize((1935, 1090))
    img = ImageTk.PhotoImage(resize)
    i5 = ctk.CTkLabel(master=details_window, text="", image=img)
    i5.pack()
    frame3 = ctk.CTkFrame(master=i5, width=460, height=460, corner_radius=50)
    frame3.configure(background_corner_colors=["#5f8d4c", "#1f4420", "#112c1d", "#0f241f"])
    frame3.place(relx=0.5, rely=0.5, anchor="center")
    with open('Attendance.csv', 'r') as f:
        lines = f.readlines()
        if len(lines) > 0:
            most_recent_record = lines[-1].strip().split(',')
            if len(most_recent_record) >= 4:
                name = most_recent_record[0]
                datetime_str = most_recent_record[1]
                record_status = most_recent_record[3]
                label_recent_record = ctk.CTkLabel(master=frame3,
                                                   text=f"Most Recent Record:\nName: {name}\nDatetime: {datetime_str}\nStatus: {record_status}",
                                                   font=("Arial", 23, "bold"))
                label_recent_record.place(relx=0.5, rely=0.23, anchor="center")
            else:
                label_recent_record = ctk.CTkLabel(master=frame3, text="No recent record found", font=("Arial", 15))
                label_recent_record.place(relx=0.5, rely=0.23, anchor="center")

    def openRecords():
        os.system('Attendance.csv')

    btn_open_records = ctk.CTkButton(master=frame3, text="Open Records",  font=("Helvetica", 19), height=40, width=150,
                                     corner_radius=100,command=openRecords, fg_color="#307033", hover_color="#308633")
    btn_open_records.place(relx=0.5, rely=0.44, anchor="center")

    def takeNextAttendance():
        details_window.destroy()
        takeQRAttendance()

    btn_next_attendance = ctk.CTkButton(master=frame3, text="Take Next Attendance",  font=("Helvetica", 19), height=40, width=150,
                                        command=takeNextAttendance, fg_color="#307033", hover_color="#308633")
    btn_next_attendance.place(relx=0.5, rely=0.56, anchor="center")

    def startFaceRecognitionAttendance():
        details_window.destroy()
        takeFaceRecognitionAttendance()

    btn_qr_attendance = ctk.CTkButton(master=frame3, text="Face Recognition", font=("Helvetica", 19), height=40, width=150,
                                      corner_radius=100, command=startFaceRecognitionAttendance, fg_color="#307033", hover_color="#308633")
    btn_qr_attendance.place(relx=0.5, rely=0.68, anchor="center")

    def logout():
        details_window.destroy()
        StaffloginScreen()

    btn_Logout = ctk.CTkButton(master=frame3, text="Logout", font=("Helvetica", 19), height=40, width=150, corner_radius=100,
                               command=logout, fg_color="#307033", hover_color="#308633")
    btn_Logout.place(relx=0.5, rely=0.80, anchor="center")

    details_window.mainloop()

def showAttendanceDetailsFaceRecognition():
    def toggle_fullscreen(event):
        if event.keysym == 'Escape':
            details_window.attributes("-fullscreen", not details_window.attributes("-fullscreen"))

    details_window = ctk.CTk()
    details_window.title("Attendance Details - Face Recognition")
    details_window.geometry("1920x1080")
    details_window.attributes("-fullscreen", True)
    details_window.bind('<Escape>', toggle_fullscreen)
    image = Image.open("Background_Image2.jpg")
    resize = image.resize((1935, 1090))
    img5 = ImageTk.PhotoImage(resize)
    i5 = ctk.CTkLabel(master=details_window, text="", image=img5)
    i5.pack()
    frame3 = ctk.CTkFrame(master=i5, width=460, height=460, corner_radius=50)
    frame3.configure(background_corner_colors=["#5f8d4c", "#1f4420", "#112c1d", "#0f241f"])
    frame3.place(relx=0.5, rely=0.5, anchor="center")
    with open('Attendance.csv', 'r') as f:
        lines = f.readlines()
        if len(lines) > 0:
            most_recent_record = lines[-1].strip().split(',')
            if len(most_recent_record) >= 4:
                name = most_recent_record[0]
                datetime_str = most_recent_record[1]
                record_status = most_recent_record[3]
                label_recent_record = ctk.CTkLabel(master=frame3, text=f"Most Recent Record:\nName: {name}\nDatetime: {datetime_str}\nStatus: {record_status}",
font=("Arial", 23, "bold"))
                label_recent_record.place(relx=0.5, rely=0.23, anchor="center")
            else:
                label_recent_record = ctk.CTkLabel(master=frame3, text="No recent record found", font=("Arial", 15))
                label_recent_record.place(relx=0.5, rely=0.23, anchor="center")

    def openRecords():
        os.system('Attendance.csv')

    btn_open_records = ctk.CTkButton(master=frame3, text="Open Records",  font=("Helvetica", 19), height=40, width=150,
                                     corner_radius=100, command=openRecords, fg_color="#307033", hover_color="#308633")
    btn_open_records.place(relx=0.5, rely=0.44, anchor="center")

    def takeNextAttendance():
        details_window.destroy()
        takeFaceRecognitionAttendance()

    btn_next_attendance = ctk.CTkButton(master=frame3, text="Take Next Attendance", font=("Helvetica", 19), height=40, width=150,
                                        corner_radius=100, command=takeNextAttendance, fg_color="#307033", hover_color="#308633")
    btn_next_attendance.place(relx=0.5, rely=0.56, anchor="center")

    def startQRAttendance():
        details_window.destroy()
        takeQRAttendance()

    btn_qr_attendance = ctk.CTkButton(master=frame3, text="QR Code Recognition", font=("Helvetica", 19), height=40, width=150,
                                      corner_radius=100, command=startQRAttendance, fg_color="#307033", hover_color="#308633")
    btn_qr_attendance.place(relx=0.5, rely=0.68, anchor="center")

    def logout():
        details_window.destroy()
        StaffloginScreen()

    btn_Logout = ctk.CTkButton(master=frame3, text="Logout", font=("Helvetica", 19), height=40, width=150,
                               corner_radius=100, command=logout, fg_color="#307033", hover_color="#308633")
    btn_Logout.place(relx=0.5, rely=0.80, anchor="center")


    details_window.mainloop()

def studentLoginPage():
    def toggle_fullscreen(event):
        if event.keysym == 'Escape':
            StudentLogin.attributes("-fullscreen", not StudentLogin.attributes("-fullscreen"))
    StudentLogin = ctk.CTk()
    StudentLogin.title("Student Login")
    StudentLogin.geometry("1920x1080")
    StudentLogin.attributes("-fullscreen", True)
    StudentLogin.bind('<Escape>', toggle_fullscreen)
    image = Image.open("Background_Image2.jpg")
    resize = image.resize((1935, 1090))
    img1 = ImageTk.PhotoImage(resize)
    i1 = ctk.CTkLabel(master=StudentLogin, image=img1)
    i1.pack()
    frame2 = ctk.CTkFrame(master=StudentLogin, width=460, height=460, corner_radius=50)
    frame2.configure(background_corner_colors=["#5f8d4c", "#1f4420", "#112c1d", "#0f241f"])
    frame2.place(relx=0.5, rely=0.5, anchor="center")

    image = Image.open("Background_Image2.jpg")
    resize = image.resize((1935, 1090))
    img1 = ImageTk.PhotoImage(resize)
    i1 = ctk.CTkLabel(master=StudentLogin, text="", image=img1)
    i1.pack()
    frame = ctk.CTkFrame(master=StudentLogin, width=460, height=460, corner_radius=50)
    frame.configure(background_corner_colors=["#5f8d4c", "#1f4420", "#112c1d", "#0f241f"])
    frame.place(relx=0.5, rely=0.5, anchor="center")

    l2 = ctk.CTkLabel(master=frame, text="STUDENT LOG IN", font=("Arial", 35, "bold"))
    l2.place(relx=0.5, rely=0.2, anchor="center")
    entry1 = ctk.CTkEntry(master=frame, height=40, width=220, placeholder_text="Admission No", )
    entry1.place(relx=0.5, rely=0.36, anchor="center")
    entry2 = ctk.CTkEntry(master=frame, height=40, width=220, placeholder_text="Password", show="*")
    entry2.place(relx=0.5, rely=0.48, anchor="center")

    def specificStudentWindow():
        def toggle_fullscreen(event):
            if event.keysym == 'Escape':
                StudentLogin2.attributes("-fullscreen", not StudentLogin2.attributes("-fullscreen"))
        StudentLogin2 = ctk.CTk()
        StudentLogin2.title("Student Login")
        StudentLogin2.geometry("1920x1080")
        StudentLogin2.attributes("-fullscreen", True)
        StudentLogin2.bind('<Escape>', toggle_fullscreen)
        image = Image.open("Background_Image2.jpg")
        resize = image.resize((1935, 1090))
        img1 = ImageTk.PhotoImage(resize)
        i1 = ctk.CTkLabel(master=StudentLogin2, text="", image=img1)
        i1.pack()
        frame = ctk.CTkFrame(master=StudentLogin2, width=460, height=460, corner_radius=50)
        frame.configure(background_corner_colors=["#5f8d4c", "#1f4420", "#112c1d", "#0f241f"])
        frame.place(relx=0.5, rely=0.5, anchor="center")

        l2 = ctk.CTkLabel(master=frame, text="STUDENT DETAILS:", font=("Arial", 35, "bold"))
        l2.place(relx=0.5, rely=0.2, anchor="center")
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="OIS@12345",
            database="testdb"
        )
        mycursor2 = mydb.cursor()
        mycursor = mydb.cursor()
        mycursor.execute("SELECT * FROM registration WHERE AdmissionNo = %s AND Password = %s", (username1, password1))
        result = mycursor.fetchall()
        for i in result:
            print(i)
            Name = i[0]
            ClassSection = i[1]
            DOB = i[2]
            Gender = i[3]
            Nationality = i[4]
            Email = i[5]
            PhoneNo = i[6]
            AdmissionNo = i[7]
        l3 = ctk.CTkLabel(master=frame, text="Name: " + Name, font=("Arial", 20, "bold"))
        l3.place(relx=0.5, rely=0.30, anchor="center")
        l4 = ctk.CTkLabel(master=frame, text="Class: " + ClassSection, font=("Arial", 20, "bold"))
        l4.place(relx=0.5, rely=0.35, anchor="center")
        l5 = ctk.CTkLabel(master=frame, text="Date Of Birth: " + DOB, font=("Arial", 20, "bold"))
        l5.place(relx=0.5, rely=0.4, anchor="center")
        l6 = ctk.CTkLabel(master=frame, text="Gender: " + Gender, font=("Arial", 20, "bold"))
        l6.place(relx=0.5, rely=0.45, anchor="center")
        l7 = ctk.CTkLabel(master=frame, text="Nationality: " + Nationality, font=("Arial", 20, "bold"))
        l7.place(relx=0.5, rely=0.5, anchor="center")
        l8 = ctk.CTkLabel(master=frame, text="Email: " + Email, font=("Arial", 20, "bold"))
        l8.place(relx=0.5, rely=0.55, anchor="center")
        l9 = ctk.CTkLabel(master=frame, text="Phone No: " + PhoneNo, font=("Arial", 20, "bold"))
        l9.place(relx=0.5, rely=0.6, anchor="center")
        l10 = ctk.CTkLabel(master=frame, text="Admission No: " + AdmissionNo, font=("Arial", 20, "bold"))
        l10.place(relx=0.5, rely=0.65, anchor="center")
        mycursor2.execute("SELECT * FROM attendance WHERE Name = %s", (Name,))
        result2  = mycursor2.fetchall()
        for i in result2:
            StatusTime = i[2] + " " + i[3]
        l11 = ctk.CTkLabel(master=frame, text="Status: " + StatusTime, font=("Arial", 20, "bold"))
        l11.place(relx=0.5, rely=0.7, anchor="center")
        def Back3():
            StudentLogin2.destroy()

        Login_btn = ctk.CTkButton(master=frame, height=30, width=180, text="BACK", corner_radius=100,
                                  command=Back3, fg_color="#307033", hover_color="#308633")
        Login_btn.place(relx=0.5, rely=0.8, anchor="center")
        StudentLogin2.mainloop()

    def checkLogin():
        global username1
        username1 = entry1.get()
        global password1
        password1 = entry2.get()
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="OIS@12345",
            database="testdb"
        )
        mycursor = mydb.cursor()
        mycursor.execute("SELECT * FROM registration WHERE AdmissionNo = %s AND Password = %s", (username1, password1))
        result = mycursor.fetchall()
        mydb.close()
        if result:
            StudentLogin.destroy()
            specificStudentWindow()
        else:
            l3 = ctk.CTkLabel(master=frame, text="Wrong username or password", font=("Arial", 10), text_color="red")
            l3.place(relx=0.5, rely=0.56, anchor="center")


    def toggle_password():
        if entry2.cget("show") == "":
            entry2.configure(show="*")
            showbtn.configure(text="")
        else:
            entry2.configure(show="")
            showbtn.configure(text="")

    icon_path = "passshow.png"
    icon_image = ctk.CTkImage(light_image=Image.open(icon_path), dark_image=Image.open(icon_path), size=(10, 10))
    showbtn = ctk.CTkButton(master=frame, height=5, width=5, text="", image=icon_image, command=toggle_password,
                            fg_color="#2b2b2b", hover_color="#808080", corner_radius=100)
    showbtn.place(relx=0.76, rely=0.46)
    Login_btn = ctk.CTkButton(master=frame, height=30, width=220, text="LOGIN", corner_radius=100,
                              command=checkLogin, fg_color="#307033", hover_color="#308633")
    Login_btn.place(relx=0.5, rely=0.63, anchor="center")

    def on_enter_press(event):
        if event.keycode == 13:
            checkLogin()

    StudentLogin.bind('<Return>', on_enter_press)

    def Back():
        StudentLogin.destroy()
        StartWindow()

    Login_btn = ctk.CTkButton(master=frame, height=30, width=180, text="BACK", corner_radius=100,
                              command=Back, fg_color="#307033", hover_color="#308633")
    Login_btn.place(relx=0.5, rely=0.72, anchor="center")

    StudentLogin.mainloop()
def studentRegisterPage():
    def toggle_fullscreen(event):
        if event.keysym == 'Escape':
            studentRegister.attributes("-fullscreen", not studentRegister.attributes("-fullscreen"))
    studentRegister = ctk.CTk()
    studentRegister.geometry("1920x1080")
    studentRegister.title("Student Register")
    studentRegister.attributes("-fullscreen", True)
    studentRegister.bind('<Escape>', toggle_fullscreen)
    image = Image.open("Background_Image2.jpg")
    resize = image.resize((1935, 1090))
    img1 = ImageTk.PhotoImage(resize)
    i1 = ctk.CTkLabel(master=studentRegister, text="", image=img1)
    i1.pack()
    frame2 = ctk.CTkFrame(master=studentRegister, width=800, height=600, corner_radius=50)
    frame2.configure(background_corner_colors=["#000000", "#04101e", "#25532e", "#1b452f"])
    frame2.place(relx=0.5, rely=0.5, anchor="center")
    label1 = ctk.CTkLabel(master=frame2, text="Student Registration:", font=("Arial", 36, "bold"))
    label1.place(relx=0.15, rely=0.15, anchor="w")
    entry1 = ctk.CTkEntry(master=frame2, height=40, width=220, placeholder_text="Name")
    entry1.place(relx=0.15, rely=0.30, anchor="w")
    entry2 = ctk.CTkEntry(master=frame2, height=40, width=220, placeholder_text="Class")
    entry2.place(relx=0.15, rely=0.40, anchor="w")
    entry3 = ctk.CTkEntry(master=frame2, height=40, width=220, placeholder_text="Admission Number")
    entry3.place(relx=0.15, rely=0.50, anchor="w")
    entry4 = ctk.CTkEntry(master=frame2, height=40, width=220, placeholder_text="Date Of Birth (DD-MM-YYYY)")
    entry4.place(relx=0.15, rely=0.60, anchor="w")
    entry5 = ctk.CTkEntry(master=frame2, height=40, width=220, placeholder_text="Gender")
    entry5.place(relx=0.55, rely=0.30, anchor="w")
    entry6 = ctk.CTkEntry(master=frame2, height=40, width=220, placeholder_text="Nationality")
    entry6.place(relx=0.55, rely=0.40, anchor="w")
    entry7 = ctk.CTkEntry(master=frame2, height=40, width=220, placeholder_text="Email")
    entry7.place(relx=0.55, rely=0.50, anchor="w")
    entry8 = ctk.CTkEntry(master=frame2, height=40, width=220, placeholder_text="Phone Number")
    entry8.place(relx=0.55, rely=0.60, anchor="w")
    entry9 = ctk.CTkEntry(master=frame2, height=40, width=220, placeholder_text="Password", show="*")
    entry9.place(relx=0.55, rely=0.70, anchor="w")
    def toggle_password():
        if entry9.cget("show") == "":
            entry9.configure(show="*")
            showbtn.configure(text="")
        else:
            entry9.configure(show="")
            showbtn.configure(text="")
    icon_path = "passshow.png"
    icon_image = ctk.CTkImage(light_image=Image.open(icon_path), dark_image=Image.open(icon_path), size=(10, 10))
    showbtn = ctk.CTkButton(master=frame2, height=5, width=5, text="", image=icon_image, command=toggle_password,
                            fg_color="#2b2b2b", hover_color="#808080")
    showbtn.place(relx=0.83, rely=0.70, anchor="w")
    def submitDetails():
        l10 = ctk.CTkLabel(master=frame2, text="Submitted successfully", font=("Arial", 11, "bold"))
        l10.place(relx=0.15, rely=0.82)
        Name = entry1.get()
        Class = entry2.get()
        AdmissionNumber = entry3.get()
        DateOfBirth = entry4.get()
        Gender = entry5.get()
        Nationality = entry6.get()
        Email = entry7.get()
        PhoneNumber = entry8.get()
        password = entry9.get()
        mydb = mysql.connector.connect(host="localhost", user="root", passwd="OIS@12345", database="testdb")
        mycursor = mydb.cursor()
        sqlFormula2 = "INSERT INTO registration (Name,ClassSection,DOB,Gender,Nationality,Email,PhoneNo,AdmissionNo,Password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        studentInto2 = (Name, Class, DateOfBirth, Gender, Nationality, Email, PhoneNumber,     AdmissionNumber, password)
        mycursor.execute(sqlFormula2, studentInto2)
        mydb.commit()
        studentRegister.destroy()
        studentMenu()
    btn_Logout = ctk.CTkButton(master=frame2, height=30, width=200, text="Submit", command=submitDetails,  font=("Helvetica", 15), corner_radius=100, fg_color="#307033", hover_color="#308633")
    btn_Logout.place(relx=0.15, rely=0.75, anchor="w")
    studentRegister.mainloop()
def mainScreen():
    def startQRAttendance():
        app.destroy()
        takeQRAttendance()
    def startFaceRecognitionAttendance():
        app.destroy()
        takeFaceRecognitionAttendance()
    def logout():
        app.destroy()
        StaffloginScreen()
    def toggle_fullscreen(event):
        if event.keysym == 'Escape':
            app.attributes("-fullscreen", not app.attributes("-fullscreen"))
    def close_search_window(search_window):
        app.deiconify()
        search_window.destroy()
    def open_name_details_window(names_title):
        def toggle_fullscreen(event):
            if event.keysym == 'Escape':
                StudentLogin2.attributes("-fullscreen", not StudentLogin2.attributes("-fullscreen"))
        StudentLogin2 = ctk.CTkToplevel(app)
        StudentLogin2.title("Student Login")
        StudentLogin2.geometry("1920x1080")
        StudentLogin2.attributes("-fullscreen", True)
        StudentLogin2.bind('<Escape>', toggle_fullscreen)
        image = Image.open("Background_Image2.jpg")
        resize = image.resize((1935, 1090))
        img1 = ImageTk.PhotoImage(resize)
        i1 = ctk.CTkLabel(master=StudentLogin2, text="", image=img1)
        i1.pack()
        frame = ctk.CTkFrame(master=StudentLogin2, width=460, height=460, corner_radius=50)
        frame.configure(background_corner_colors=["#5f8d4c", "#1f4420", "#112c1d", "#0f241f"])
        frame.place(relx=0.5, rely=0.5, anchor="center")

        l2 = ctk.CTkLabel(master=frame, text="STUDENT DETAILS:", font=("Arial", 35, "bold"))
        l2.place(relx=0.5, rely=0.2, anchor="center")
        try:
            mydb = mysql.connector.connect(host="localhost", user="root", passwd="OIS@12345", database="testdb")
            mycursor = mydb.cursor()
            mycursor2 = mydb.cursor()

            mycursor.execute("SELECT * FROM registration WHERE Name = %s", (names_title,))
            result = mycursor.fetchall()
            mydb.close()
            if result:
                for i in result:
                    print(i)
                    Name = i[0]
                    ClassSection = i[1]
                    DOB = i[2]
                    Gender = i[3]
                    Nationality = i[4]
                    Email = i[5]
                    PhoneNo = i[6]
                    AdmissionNo = i[7]
                l3 = ctk.CTkLabel(master=frame, text="Name: " + Name, font=("Arial", 20, "bold"))
                l3.place(relx=0.5, rely=0.30, anchor="center")
                l4 = ctk.CTkLabel(master=frame, text="Class: " + ClassSection, font=("Arial", 20, "bold"))
                l4.place(relx=0.5, rely=0.35, anchor="center")
                l5 = ctk.CTkLabel(master=frame, text="Date Of Birth: " + DOB, font=("Arial", 20, "bold"))
                l5.place(relx=0.5, rely=0.4, anchor="center")
                l6 = ctk.CTkLabel(master=frame, text="Gender: " + Gender, font=("Arial", 20, "bold"))
                l6.place(relx=0.5, rely=0.45, anchor="center")
                l7 = ctk.CTkLabel(master=frame, text="Nationality: " + Nationality, font=("Arial", 20, "bold"))
                l7.place(relx=0.5, rely=0.5, anchor="center")
                l8 = ctk.CTkLabel(master=frame, text="Email: " + Email, font=("Arial", 20, "bold"))
                l8.place(relx=0.5, rely=0.55, anchor="center")
                l9 = ctk.CTkLabel(master=frame, text="Phone No: " + PhoneNo, font=("Arial", 20, "bold"))
                l9.place(relx=0.5, rely=0.6, anchor="center")
                l10 = ctk.CTkLabel(master=frame, text="Admission No: " + AdmissionNo, font=("Arial", 20, "bold"))
                l10.place(relx=0.5, rely=0.65, anchor="center")
                mycursor2.execute("SELECT * FROM attendance WHERE Name = %s", (Name,))
                result2  = mycursor2.fetchall()
                for i in result2:
                    StatusTime = i[2] + " " + i[3]
                l11 = ctk.CTkLabel(master=frame, text="Status: " + StatusTime, font=("Arial", 20, "bold"))
                l11.place(relx=0.5, rely=0.7, anchor="center")
        except mysql.connector.Error as e:
            print(f"Error accessing database: {e}")
        def Back3():
            StudentLogin2.destroy()
            search_window.wm_state("zoomed")

        Login_btn = ctk.CTkButton(master=frame, height=30, width=180, text="BACK", corner_radius=100, command=Back3, fg_color="#307033", hover_color="#308633")
        Login_btn.place(relx=0.5, rely=0.8, anchor="center")
    def open_search_window():
        def show_all_names():
            all_namess_window = ctk.CTkToplevel(app)
            all_namess_window.title("Student Search")
            all_namess_window.geometry("1920x1080")
            all_namess_window.attributes("-fullscreen", True)
            all_namess_window.bind('<Escape>', toggle_fullscreen)
            image = Image.open("Background_Image2.jpg")
            resize = image.resize((1935, 1090))
            img1 = ImageTk.PhotoImage(resize)
            i1 = ctk.CTkLabel(master= all_namess_window, text="", image=img1)
            i1.pack()
            frame = ctk.CTkFrame(master= all_namess_window, width=460, height=460, corner_radius=50)
            frame.configure(background_corner_colors=["#5f8d4c", "#1f4420", "#112c1d", "#0f241f"])
            frame.place(relx=0.5, rely=0.5, anchor="center")
            results_listbox = Listbox(frame, height=20, width=50, fg="white", font=("Arial", 20))
            results_listbox.pack(relx=0.5, rely=0.5)
            results_listbox.configure(background= all_namess_window.cget('background'))
            try:
                mydb = mysql.connector.connect(host="localhost", user="root", passwd="OIS@12345", database="testdb")
                mycursor = mydb.cursor()
                mycursor.execute("SELECT Name FROM Registration")
                results = mycursor.fetchall()
                for names in results:
                    results_listbox.insert(END, names[0])
                mydb.close()
            except mysql.connector.Error as e:
                print(f"Error accessing database: {e}")
        app.withdraw()
        global search_window
        search_window = ctk.CTkToplevel(app)
        search_window.title("Student Search")
        search_window.geometry("1920x1080")
        search_window.attributes("-fullscreen", True)
        search_window.bind('<Escape>', toggle_fullscreen)
        image = Image.open("Background_Image2.jpg")
        resize = image.resize((1935, 1090))
        img1 = ImageTk.PhotoImage(resize)
        i1 = ctk.CTkLabel(master=search_window, text="", image=img1)
        i1.pack()
        frame = ctk.CTkFrame(master=search_window, width=460, height=460, corner_radius=50)
        frame.configure(background_corner_colors=["#5f8d4c", "#1f4420", "#112c1d", "#0f241f"])
        frame.place(relx=0.5, rely=0.5, anchor="center")

        nameo_details = ctk.CTkLabel(master=frame, text="Search Names:", font=("Arial", 32, "bold"))
        nameo_details.place(relx=0.5, rely=0.2, anchor="center")
        title1 = ctk.CTkEntry(master=frame, height=40, width=220)
        title1.place(relx=0.5, rely=0.35, anchor="center")

        search_var = StringVar()
        title1.configure(textvariable=search_var)
        search_var.trace_add("write", lambda name, index, mode, sv=search_var: update_search_results(sv, search_window))
        results_listbox = Listbox(search_window, height=5, width=30, fg="white")
        results_listbox.place(relx=0.5, rely=0.55, anchor="center")
        results_listbox.configure(background=search_window.cget('background'))
        btn = ctk.CTkButton(frame, text="All Students List", command=show_all_names)
        btn.place(relx=0.5, rely=0.9, anchor="center")
        icon_path5 = "close2.png"
        icon_image5 = ctk.CTkImage(light_image=Image.open(icon_path5), dark_image=Image.open(icon_path5), size=(20, 20))
        exit = ctk.CTkButton(master=frame, height=5, width=5, text="", image=icon_image5, command=lambda: close_search_window(search_window),  font=("Helvetica", 10),
fg_color="#2b2b2b", hover_color="#2b2b2b", anchor="center", corner_radius=100)
        exit.place(relx=0.9, rely=0.1, anchor="center")

        def update_search_results(sv, search_window):
            query = sv.get()
            results_listbox.delete(0, END)

            if len(query) >= 2:
                try:
                    mydb = mysql.connector.connect(host="localhost", user="root", passwd="OIS@12345", database="testdb")
                    mycursor = mydb.cursor()
                    mycursor.execute("SELECT Name FROM Registration WHERE Name LIKE %s", (f"%{query}%",))
                    results = mycursor.fetchall()
                    for names in results:
                        results_listbox.insert(END, names[0])
                    mydb.close()
                except mysql.connector.Error as e:
                    print(f"Error accessing database: {e}")
        def show_name_details(event):
            selection = results_listbox.curselection()
            if selection:
                selected_name = results_listbox.get(selection[0])
                open_name_details_window(selected_name)
                search_window.wm_state("iconic")

        results_listbox.bind("<<ListboxSelect>>", show_name_details)

        search_window.protocol("WM_DELETE_WINDOW", lambda: close_search_window(search_window))

    app = ctk.CTk()
    app.title("Selection Page")
    app.geometry("1920x1080")
    app.attributes("-fullscreen", True)
    app.bind('<Escape>', toggle_fullscreen)
    image = Image.open("Background_Image2.jpg")
    resize = image.resize((1935, 1090))
    img1 = ImageTk.PhotoImage(resize)
    i1 = ctk.CTkLabel(master=app, text="", image=img1)
    i1.pack()
    frame2 = ctk.CTkFrame(master=app, width=460, height=460, corner_radius=50)
    frame2.configure(background_corner_colors=["#5f8d4c", "#1f4420", "#112c1d", "#0f241f"])
    frame2.place(relx=0.5, rely=0.5, anchor="center")

    label1 = ctk.CTkLabel(master=frame2, text="ATTENDANCE APP", font=("Arial", 32, "bold"))
    label1.place(relx=0.5, rely=0.2, anchor="center")
    btn_qr_attendance = ctk.CTkButton(master=frame2, height=50, width=130, text="QR Code Attendance", font=("Helvetica", 15),
                                      command=startQRAttendance, fg_color="#307033", corner_radius=100, hover_color="#308633")
    btn_qr_attendance.place(relx=0.5, rely=0.5, anchor="center")

    btn_face_recognition_attendance = ctk.CTkButton(master=frame2, height=50, width=130, text="Face Recognition Attendance",
                                                    font=("Helvetica", 15), command=startFaceRecognitionAttendance, fg_color="#307033",
                                                    hover_color="#308633", corner_radius=100)
    btn_face_recognition_attendance.place(relx=0.5, rely=0.35, anchor="center")
    btn_face_recognition_attendance = ctk.CTkButton(master=frame2, height=50, width=130,
                                                    text="Student Search",
                                                    font=("Helvetica", 15), command=open_search_window,
                                                    fg_color="#307033",
                                                    hover_color="#308633", corner_radius=100)
    btn_face_recognition_attendance.place(relx=0.5, rely=0.65, anchor="center")

    btn_Logout = ctk.CTkButton(master=frame2, height=50, width=130, text="Logout", font=("Helvetica", 15), corner_radius=100,
                               command=logout, fg_color="#307033", hover_color="#308633")
    btn_Logout.place(relx=0.5, rely=0.8, anchor="center")

    app.mainloop()

def StaffloginScreen():
    def toggle_fullscreen(event):
        if event.keysym == 'Escape':
            login_window.attributes("-fullscreen", not login_window.attributes("-fullscreen"))
    login_window = ctk.CTk()
    login_window.geometry("1920x1080")
    login_window.attributes("-fullscreen", True)
    login_window.title("Login")
    login_window.bind('<Escape>', toggle_fullscreen)

    def checkLogin():
        username = entry1.get()
        password = entry2.get()
        if username == "12F" and password == "OIS@12345":
            login_window.destroy()
            mainScreen()
        else:
            l3 = ctk.CTkLabel(master=frame, text="Wrong username or password", font=("Arial", 10), text_color="red")
            l3.place(relx=0.5, rely=0.56, anchor="center")

    image = Image.open("Background_Image2.jpg")
    resize = image.resize((1935, 1090))
    img1 = ImageTk.PhotoImage(resize)
    i1 = ctk.CTkLabel(master=login_window, text="", image=img1)
    i1.pack()
    frame = ctk.CTkFrame(master=login_window, width=460, height=460, corner_radius=50)
    frame.configure(background_corner_colors=["#5f8d4c", "#1f4420", "#112c1d", "#0f241f"])
    frame.place(relx=0.5, rely=0.5, anchor="center")

    l2 = ctk.CTkLabel(master=frame, text="ADMIN LOG IN", font=("Arial", 35, "bold"))
    l2.place(relx=0.5, rely=0.2, anchor="center")
    l9 = ctk.CTkLabel(master=frame, text="By: Ayaan,Akash,Jefin", font=("Arial", 11, "bold"))
    l9.place(relx=0.67, rely=0.89)
    entry1 = ctk.CTkEntry(master=frame, height=40, width=220, placeholder_text="Username", )
    entry1.place(relx=0.5, rely=0.36, anchor="center")
    entry2 = ctk.CTkEntry(master=frame, height=40, width=220, placeholder_text="Password", show="*")
    entry2.place(relx=0.5, rely=0.48, anchor="center")

    Login_btn = ctk.CTkButton(master=frame, height=30, width=220, text="LOGIN", corner_radius=100, command=checkLogin,
                              fg_color="#307033", hover_color="#308633")
    Login_btn.place(relx=0.5, rely=0.63, anchor="center")

    def toggle_password():
        if entry2.cget("show") == "":
            entry2.configure(show="*")
            showbtn.configure(text="")
        else:
            entry2.configure(show="")
            showbtn.configure(text="")

    icon_path = "passshow.png"
    icon_image = ctk.CTkImage(light_image=Image.open(icon_path), dark_image=Image.open(icon_path), size=(10, 10))
    showbtn = ctk.CTkButton(master=frame, height=5, width=5, text="", image=icon_image, command=toggle_password,
                            fg_color="#2b2b2b", hover_color="#808080", corner_radius=100)
    showbtn.place(relx=0.76, rely=0.46)
    def on_enter_press(event):
        if event.keycode == 13:
            checkLogin()

    login_window.bind('<Return>', on_enter_press)

    def Back():
        login_window.destroy()
        StartWindow()

    Login_btn = ctk.CTkButton(master=frame, height=30, width=180, text="BACK", corner_radius=100, command=Back,
                              fg_color="#307033", hover_color="#308633")
    Login_btn.place(relx=0.5, rely=0.72, anchor="center")

    login_window.mainloop()

def studentMenu():
    def studentRegistorwin():
        Student.destroy()
        studentRegisterPage()

    def studentLoginwin():
        Student.destroy()
        studentLoginPage()

    def backWindow():
        Student.destroy()
        StartWindow()

    def toggle_fullscreen(event):
        if event.keysym == 'Escape':
            Student.attributes("-fullscreen", not Student.attributes("-fullscreen"))
    Student = ctk.CTk()
    Student.geometry("1920x1080")
    Student.attributes("-fullscreen", True)
    Student.title("Student Options")
    Student.bind('<Escape>', toggle_fullscreen)
    image = Image.open("Background_Image2.jpg")
    resize = image.resize((1935, 1090))
    img2 = ImageTk.PhotoImage(resize)
    i2 = ctk.CTkLabel(master=Student, image=img2)
    i2.pack()
    frame3 = ctk.CTkFrame(master=Student, width=460, height=460, corner_radius=50)
    frame3.configure(background_corner_colors=["#5f8d4c", "#1f4420", "#112c1d", "#0f241f"])
    frame3.place(relx=0.5, rely=0.5, anchor="center")

    label1 = ctk.CTkLabel(master=frame3, text="Login/Register", font=("Arial", 46, "bold"))
    label1.place(relx=0.5, rely=0.2, anchor="center")
    btn_admin_login = ctk.CTkButton(master=frame3, height=50, width=230, text="Login", command=studentLoginwin, font=("Helvetica", 19), fg_color="#307033", corner_radius=100, hover_color="#308633")
    btn_admin_login.place(relx=0.5, rely=0.40, anchor="center")

    btn_student_login = ctk.CTkButton(master=frame3, height=50, width=230, text="Register", command=studentRegistorwin, font=("Helvetica", 19), fg_color="#307033", corner_radius=100, hover_color="#308633")
    btn_student_login.place(relx=0.5, rely=0.60, anchor="center")

    Login_btn = ctk.CTkButton(master=frame3, height=30, width=180, text="BACK", corner_radius=100, command=backWindow, fg_color="#307033", hover_color="#308633")
    Login_btn.place(relx=0.5, rely=0.78, anchor="center")
    Student.mainloop()

def StartWindow():
    ctk.set_default_color_theme("green")
    def studentLoginOpen():
        InitialApp.destroy()
        studentMenu()
    def StaffLoginClose():
        InitialApp.destroy()
        StaffloginScreen()
    def exitWindow():
        InitialApp.destroy()
    def toggle_fullscreen(event):
        if event.keysym == 'Escape':
            InitialApp.attributes("-fullscreen", not InitialApp.attributes("-fullscreen"))

    InitialApp = ctk.CTk()
    InitialApp.geometry("1920x1080")
    InitialApp.attributes("-fullscreen", True)
    InitialApp.title("Attendance System")
    InitialApp.bind('<Escape>', toggle_fullscreen)
    image = Image.open("Background_Image2.jpg")
    resize = image.resize((1935, 1090))
    img1 = ImageTk.PhotoImage(resize)
    i1 = ctk.CTkLabel(master=InitialApp, image=img1)
    i1.pack()
    frame2 = ctk.CTkFrame(master=InitialApp, width=460, height=460, corner_radius=50)
    frame2.configure(background_corner_colors=["#5f8d4c", "#1f4420", "#112c1d", "#0f241f"])
    frame2.place(relx=0.5, rely=0.5, anchor="center")

    label1 = ctk.CTkLabel(master=frame2, text="Sign in As:", font=("Arial", 46, "bold"))
    label1.place(relx=0.5, rely=0.2, anchor="center")
    btn_admin_login = ctk.CTkButton(master=frame2, height=50, width=230, text="STAFF", font=("Helvetica", 19), command=StaffLoginClose,
                                    fg_color="#307033", corner_radius=100, hover_color="#308633")
    btn_admin_login.place(relx=0.5, rely=0.45, anchor="center")

    btn_student_login = ctk.CTkButton(master=frame2, height=50, width=230, text="STUDENT", command=studentLoginOpen, font=("Helvetica", 19),
                                      fg_color="#307033", corner_radius=100, hover_color="#308633")
    btn_student_login.place(relx=0.5, rely=0.65, anchor="center")
    icon_path5 = "close2.png"
    icon_image5 = ctk.CTkImage(light_image=Image.open(icon_path5), dark_image=Image.open(icon_path5), size=(20, 20))
    exit = ctk.CTkButton(master=frame2, height=5, width=5, text="", image=icon_image5, command=exitWindow, font=("Helvetica", 10),
                         fg_color="#2b2b2b", hover_color="#2b2b2b", anchor="center", corner_radius=100)
    exit.place(relx=0.9, rely=0.1, anchor="center")
    InitialApp.mainloop()
StartWindow()
