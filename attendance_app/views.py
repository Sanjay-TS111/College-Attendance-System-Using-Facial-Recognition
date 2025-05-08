from django.shortcuts import render, redirect , get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from .models import Timetable, Student, Attendance ,User
from .forms import TimetableForm
import face_recognition
import pickle
import base64
from io import BytesIO
from PIL import Image
import cv2
import numpy as np

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'attendance_app/login.html')


@login_required
def dashboard(request):
    return render(request, 'attendance_app/dashboard.html')


@login_required
def create_timetable(request):
    if request.method == 'POST':
        form = TimetableForm(request.POST)
        if form.is_valid():
            timetable = form.save(commit=False)
            timetable.teacher = request.user
            timetable.save()
            messages.success(request, 'Timetable entry created successfully.')
            return redirect('create_timetable')
    else:
        form = TimetableForm()
    timetables = Timetable.objects.filter(teacher=request.user)
    return render(request, 'attendance_app/create_timetable.html', {'form': form, 'timetables': timetables})


def mark_attendance(request):
    if request.method == 'POST':
        image_data = request.POST.get('image_data')

        if not image_data:
            messages.error(request, 'No image data received.')
            return redirect('mark_attendance')

        try:
    
            format, imgstr = image_data.split(';base64,')
            img_bytes = base64.b64decode(imgstr)
            img = Image.open(BytesIO(img_bytes))
            rgb_frame = np.array(img.convert('RGB'))

            known_face_encodings = []
            known_face_names = []

            students = Student.objects.all()
            for student in students:
                encoding = pickle.loads(student.face_encoding)
                known_face_encodings.append(encoding)
                known_face_names.append(student.name)

            if not known_face_encodings:
                messages.error(request, 'No students registered in the system.')
                return redirect('mark_attendance')

            face_locations = face_recognition.face_locations(rgb_frame)
            if not face_locations:
                messages.error(request, 'No faces detected in the image.')
                return redirect('mark_attendance')

            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            face_recognized = False
            student_name = None

            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    student_name = known_face_names[best_match_index]
                    face_recognized = True
                    break

            if face_recognized:
                current_day = timezone.now().strftime('%A')
                current_time = timezone.now().time()

                timetable_entries = Timetable.objects.filter(day_of_week__iexact=current_day)
                subject_name = None
                for entry in timetable_entries:
                    if entry.start_time <= current_time <= entry.end_time:
                        subject_name = entry.subject_name
                        break

                if subject_name:
                    student = Student.objects.get(name=student_name)
                    Attendance.objects.create(student=student, subject=subject_name, status='Present')
                    messages.success(request, f'Attendance marked for {student_name} in {subject_name}.')
                    return redirect('index') 
                else:
                    messages.error(request, 'No scheduled class at this time.')
                    return redirect('index')
            else:
                messages.error(request, 'Face not recognized.')
                return redirect('index')

        except Exception as e:
            print(f"Error: {str(e)}")
            messages.error(request, f'Error processing image: {str(e)}')
            return redirect('mark_attendance')

    return render(request, 'attendance_app/mark_attendance.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        confirm = request.POST['confirm']

        if password != confirm:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            user = User.objects.create_user(username=username, password=password)
            messages.success(request, f"Student {name} registered successfully.")
            return redirect('login')
    return render(request, 'attendance_app/register.html')

def logout_view(request):
    logout(request)
    return redirect('login')



def student_register(request):
    if request.method == 'POST':
        name = request.POST['name']
        image_data = request.POST['image_data']

        if not image_data:
            messages.error(request, "No image captured.")
            return redirect('student_register')
        
        format, imgstr = image_data.split(';base64,') 
        image_bytes = base64.b64decode(imgstr)
        image = Image.open(BytesIO(image_bytes))
        rgb_image = image.convert('RGB')
        np_image = np.array(rgb_image)

        face_locations = face_recognition.face_locations(np_image)
        if not face_locations:
            messages.error(request, "No face detected.")
            return redirect('student_register')

        face_encoding = face_recognition.face_encodings(np_image, face_locations)[0]
        encoding_pickle = pickle.dumps(face_encoding)

        Student.objects.create(name=name, face_encoding=encoding_pickle)
        messages.success(request, f"Student {name} registered successfully.")
        return redirect('student_register')

    return render(request, 'attendance_app/student_register.html')



def index(request):
    return render(request,'attendance_app/index.html')



@login_required
def attendance_records(request):
    student_query = request.GET.get("student", "")
    subject_query = request.GET.get("subject", "")
    date_query = request.GET.get("date", "")

    records = Attendance.objects.all()

    if student_query:
        records = records.filter(student__name__icontains=student_query)
    if subject_query:
        records = records.filter(subject__icontains=subject_query)
    if date_query:
        records = records.filter(timestamp__date=date_query)

    return render(request, "attendance_app/attendance_records.html", {
        "records": records,
    })

def student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    subject_query = request.GET.get("subject", "")
    date_query = request.GET.get("date", "")

    records = Attendance.objects.filter(student=student)

    if subject_query:
        records = records.filter(subject__icontains=subject_query)
    if date_query:
        records = records.filter(timestamp__date=date_query)

    return render(request, "attendance_app/student_detail.html", {
        "student": student,
        "records": records
    })

def about(request):
    return render(request,'attendance_app/about.html')



def delete_timetable(request, id):
    timetable = get_object_or_404(Timetable, id=id)
    timetable.delete()
    return redirect('create_timetable')  # Use the name of your view that renders the timetable page

