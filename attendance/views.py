from datetime import datetime
import cv2
import numpy as np

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Student, Attendance
from .face_engine import get_face_feature, compare_faces


def home(request):
    return render(request, "attendance/home.html")


def dashboard(request):
    today = timezone.localdate()

    total_students = Student.objects.count()
    today_attendance = Attendance.objects.filter(date=today).count()
    recent_attendance = Attendance.objects.select_related(
        "student"
    ).all()[:10]

    return render(
        request,
        "attendance/dashboard.html",
        {
            "total_students": total_students,
            "today_attendance": today_attendance,
            "recent_attendance": recent_attendance,
        }
    )


def about(request):
    return render(request, "attendance/about.html")


def analysis(request):
    today = timezone.localdate()

    # Attendance Analysis Period = 26 days
    TOTAL_DAYS = 26

    # Current 26-day attendance period
    start_date = today - timezone.timedelta(days=TOTAL_DAYS - 1)

    total_students = Student.objects.count()

    # Only attendance records from the current 26-day period
    period_attendance = Attendance.objects.filter(
        date__range=[start_date, today]
    )

    today_attendance = period_attendance.filter(
        date=today,
        status="Present"
    ).count()

    total_attendance = period_attendance.filter(
        status="Present"
    ).count()

    # Today's attendance records for In Time / Out Time
    today_records = Attendance.objects.filter(
        date=today
    )

    today_attendance_map = {
        record.student_id: record
        for record in today_records
    }

    student_attendance = []

    for student in Student.objects.all().order_by("name"):

        # Get this student's attendance only from the 26-day period
        student_records = period_attendance.filter(
            student=student,
            status="Present"
        ).order_by("-date")

        # Unique present days
        present_days = student_records.values("date").distinct().count()

        # Remaining days are absent
        absent_days = max(TOTAL_DAYS - present_days, 0)

        # Attendance percentage
        attendance_percentage = (
            (present_days / TOTAL_DAYS) * 100
            if TOTAL_DAYS > 0 else 0
        )

        attendance_dates = list(
            student_records.values_list("date", flat=True)
        )

        # Today's In Time and Out Time
        today_record = today_attendance_map.get(student.id)

        student_attendance.append({
            "student": student,
            "in_time": today_record.in_time if today_record else None,
            "out_time": today_record.out_time if today_record else None,
            "present_days": present_days,
            "absent_days": absent_days,
            "total_days": TOTAL_DAYS,
            "percentage": round(attendance_percentage, 1),
            "attendance_dates": attendance_dates,
        })

    return render(
        request,
        "attendance/analysis.html",
        {
            "total_students": total_students,
            "today_attendance": today_attendance,
            "total_attendance": total_attendance,
            "total_days": TOTAL_DAYS,
            "start_date": start_date,
            "end_date": today,
            "student_attendance": student_attendance,
        }
    )


def contact(request):
    return render(request, "attendance/contact.html")


def register_student(request):

    if request.method == "POST":

        student = Student(
            name=request.POST.get("name"),
            roll_number=request.POST.get("roll_number"),
            email=request.POST.get("email"),
            course=request.POST.get("course"),
            semester=request.POST.get("semester"),
            photo=request.FILES.get("photo"),
        )

        student.save()

        return redirect("register_student")

    students = Student.objects.all().order_by("-registered_at")

    return render(
        request,
        "attendance/register_student.html",
        {
            "students": students
        }
    )


def edit_student(request, student_id):

    student = get_object_or_404(
        Student,
        id=student_id
    )

    if request.method == "POST":

        student.name = request.POST.get("name")
        student.roll_number = request.POST.get("roll_number")
        student.email = request.POST.get("email")
        student.course = request.POST.get("course")
        student.semester = request.POST.get("semester")

        if request.FILES.get("photo"):
            student.photo = request.FILES.get("photo")

        student.save()

        return redirect("register_student")

    return render(
        request,
        "attendance/edit_student.html",
        {
            "student": student
        }
    )


def delete_student(request, student_id):

    student = get_object_or_404(
        Student,
        id=student_id
    )

    if request.method == "POST":
        student.delete()

    return redirect("register_student")


def attendance_list(request):

    attendances = Attendance.objects.select_related(
        "student"
    ).all()

    return render(
        request,
        "attendance/attendance_list.html",
        {
            "attendances": attendances
        }
    )


def take_attendance(request):

    today = timezone.localdate()

    today_attendance = Attendance.objects.filter(
        date=today
    ).select_related("student")

    return render(
        request,
        "attendance/take_attendance.html",
        {
            "today_attendance": today_attendance
        }
    )


@require_POST
def mark_attendance_from_camera(request):
    image_file = request.FILES.get("image")

    if not image_file:
        return JsonResponse({
            "success": False,
            "message": "No camera image received."
        })

    try:
        image_bytes = np.frombuffer(image_file.read(), np.uint8)
        image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)

        if image is None:
            return JsonResponse({
                "success": False,
                "message": "Invalid camera image."
            })

        captured_feature = get_face_feature(image)

        if captured_feature is None:
            return JsonResponse({
                "success": False,
                "message": "No face detected. Please look at the camera."
            })

        best_student = None
        best_score = -1

        students = Student.objects.exclude(photo="")

        for student in students:
            if not student.photo:
                continue

            try:
                registered_image = cv2.imread(student.photo.path)

                if registered_image is None:
                    continue

                registered_feature = get_face_feature(registered_image)

                if registered_feature is None:
                    continue

                score = compare_faces(
                    captured_feature,
                    registered_feature
                )

                if score > best_score:
                    best_score = score
                    best_student = student

            except Exception:
                continue

        MATCH_THRESHOLD = 0.363

        if best_student is None or best_score < MATCH_THRESHOLD:
            return JsonResponse({
                "success": False,
                "message": "Face not recognized.",
                "score": round(float(best_score), 3)
            })

        today = timezone.localdate()
        current_time = timezone.localtime().time()

        attendance = Attendance.objects.filter(
            student=best_student,
            date=today
        ).first()

        # FIRST SCAN = IN TIME
        if attendance is None:
            attendance = Attendance.objects.create(
                student=best_student,
                date=today,
                in_time=current_time,
                status="Present"
            )

            return JsonResponse({
                "success": True,
                "action": "in",
                "student": best_student.name,
                "roll_number": best_student.roll_number,
                "in_time": current_time.strftime("%I:%M:%S %p"),
                "out_time": None,
                "score": round(float(best_score), 3),
                "message": (
                    f"IN marked: {best_student.name} "
                    f"({best_student.roll_number}) at "
                    f"{current_time.strftime('%I:%M:%S %p')}"
                )
            })

        # SECOND SCAN = OUT TIME
        # OUT is allowed only after 5 minutes from IN.
        if attendance.out_time is None:

            if attendance.in_time is None:
                return JsonResponse({
                    "success": False,
                    "message": "IN time is missing."
                })

            # Calculate elapsed time from IN to current scan.
            in_datetime = timezone.make_aware(
                datetime.combine(today, attendance.in_time)
            )
            now_datetime = timezone.localtime()
            elapsed_seconds = (
                now_datetime - in_datetime
            ).total_seconds()

            MINIMUM_OUT_SECONDS = 5 * 60

            # Less than 5 minutes: do NOT mark OUT.
            if elapsed_seconds < MINIMUM_OUT_SECONDS:
                remaining_seconds = int(
                    MINIMUM_OUT_SECONDS - elapsed_seconds
                )
                remaining_minutes = remaining_seconds // 60
                remaining_secs = remaining_seconds % 60

                return JsonResponse({
                    "success": False,
                    "action": "waiting",
                    "student": best_student.name,
                    "roll_number": best_student.roll_number,
                    "in_time": attendance.in_time.strftime(
                        "%I:%M:%S %p"
                    ),
                    "out_time": None,
                    "score": round(float(best_score), 3),
                    "message": (
                        f"{best_student.name} recognized. "
                        f"OUT available after "
                        f"{remaining_minutes}m "
                        f"{remaining_secs}s."
                    )
                })

            # 5 minutes completed: automatically mark OUT.
            attendance.out_time = current_time
            attendance.save(update_fields=["out_time"])

            return JsonResponse({
                "success": True,
                "action": "out",
                "student": best_student.name,
                "roll_number": best_student.roll_number,
                "in_time": (
                    attendance.in_time.strftime("%I:%M:%S %p")
                    if attendance.in_time else None
                ),
                "out_time": current_time.strftime("%I:%M:%S %p"),
                "score": round(float(best_score), 3),
                "message": (
                    f"OUT marked automatically: "
                    f"{best_student.name} "
                    f"({best_student.roll_number}) at "
                    f"{current_time.strftime('%I:%M:%S %p')}"
                )
            })

        # THIRD OR LATER SCAN
        return JsonResponse({
            "success": True,
            "action": "completed",
            "student": best_student.name,
            "roll_number": best_student.roll_number,
            "in_time": (
                attendance.in_time.strftime("%I:%M:%S %p")
                if attendance.in_time else None
            ),
            "out_time": (
                attendance.out_time.strftime("%I:%M:%S %p")
                if attendance.out_time else None
            ),
            "score": round(float(best_score), 3),
            "message": (
                f"{best_student.name} ({best_student.roll_number}) "
                "already has IN and OUT time today."
            )
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": f"Attendance error: {str(e)}"
        })

