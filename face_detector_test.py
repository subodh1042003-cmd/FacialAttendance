import cv2

MODEL = "attendance/models/face_detection_yunet_2023mar.onnx"

detector = cv2.FaceDetectorYN.create(
    MODEL,
    "",
    (320, 320),
    0.9,
    0.3,
    5000
)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera open nahi hua")
    exit()

print("Face Detection started. Q press karke close karo.")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Frame nahi mila")
        break

    height, width = frame.shape[:2]
    detector.setInputSize((width, height))

    _, faces = detector.detect(frame)

    if faces is not None:
        for face in faces:
            x, y, w, h = face[:4].astype(int)

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                "Face Detected",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

    cv2.imshow("Facial Attendance - Face Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

print("Face Detection closed.")
