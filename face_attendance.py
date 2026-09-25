import os
import cv2
import django
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "faceattendance.settings")
django.setup()

from attendance.models import Student, Attendance
from attendance.face_engine import detector, recognizer, get_face_feature


THRESHOLD = 0.363


def load_students():
    students = []

    for student in Student.objects.all():
        if not student.photo:
            continue

        try:
            image = cv2.imread(student.photo.path)

            if image is None:
                continue

            feature = get_face_feature(image)

            if feature is not None:
                students.append((student, feature))
                print(f"Loaded: {student.name} ({student.roll_number})")

        except Exception as e:
            print(f"Error loading {student.name}: {e}")

    return students


def mark_attendance(student):
    attendance, created = Attendance.objects.get_or_create(
        student=student,
        date=timezone.localdate(),
        defaults={"status": "Present"}
    )

    if created:
        print(
            f"ATTENDANCE MARKED: "
            f"{student.name} - {student.roll_number}"
        )
    else:
        print(
            f"Already Present Today: "
            f"{student.name} - {student.roll_number}"
        )


def main():
    print("=" * 60)
    print("FACIAL RECOGNITION ATTENDANCE SYSTEM")
    print("=" * 60)

    students = load_students()

    if not students:
        print("No registered student face found.")
        return

    print(f"Registered faces loaded: {len(students)}")
    print("Camera starting...")
    print("Press Q to close.")

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("ERROR: Camera open nahi hua.")
        return

    marked_this_session = set()

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        height, width = frame.shape[:2]
        detector.setInputSize((width, height))

        _, faces = detector.detect(frame)

        if faces is not None:

            for face in faces:
                x, y, w, h = face[:4].astype(int)

                try:
                    aligned = recognizer.alignCrop(frame, face)
                    feature = recognizer.feature(aligned)
                except Exception:
                    continue

                best_student = None
                best_score = -1

                for student, saved_feature in students:

                    score = recognizer.match(
                        feature,
                        saved_feature,
                        cv2.FaceRecognizerSF_FR_COSINE
                    )

                    if score > best_score:
                        best_score = score
                        best_student = student

                if best_student and best_score >= THRESHOLD:

                    cv2.rectangle(
                        frame,
                        (x, y),
                        (x + w, y + h),
                        (0, 255, 0),
                        2
                    )

                    cv2.putText(
                        frame,
                        best_student.name,
                        (x, y - 35),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2
                    )

                    cv2.putText(
                        frame,
                        f"Match: {best_score:.2f}",
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 255, 0),
                        2
                    )

                    if best_student.id not in marked_this_session:
                        mark_attendance(best_student)
                        marked_this_session.add(best_student.id)

                else:

                    cv2.rectangle(
                        frame,
                        (x, y),
                        (x + w, y + h),
                        (0, 0, 255),
                        2
                    )

                    cv2.putText(
                        frame,
                        "Unknown Face",
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2
                    )

        cv2.imshow("Facial Attendance System", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    print("Attendance camera closed.")


if __name__ == "__main__":
    main()
