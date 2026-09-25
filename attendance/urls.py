from django.urls import path

from .views import (
    home,
    dashboard,
    about,
    analysis,
    register_student,
    edit_student,
    delete_student,
    attendance_list,
    take_attendance,
    contact,
    mark_attendance_from_camera,
)

urlpatterns = [
    path("", home, name="home"),
    path("dashboard/", dashboard, name="dashboard"),
    path("about/", about, name="about"),
    path("analysis/", analysis, name="analysis"),
    path("register/", register_student, name="register_student"),
    path("student/<int:student_id>/edit/", edit_student, name="edit_student"),
    path("student/<int:student_id>/delete/", delete_student, name="delete_student"),
    path("attendance/", attendance_list, name="attendance_list"),
    path("attendance/take/", take_attendance, name="take_attendance"),
    path("attendance/mark/", mark_attendance_from_camera, name="mark_attendance_from_camera"),
    path("contact/", contact, name="contact"),
]
