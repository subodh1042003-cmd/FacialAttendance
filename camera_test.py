import cv2

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera open nahi hua")
    exit()

print("Camera started. Q press karke close karo.")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Frame nahi mila")
        break

    cv2.imshow("Facial Attendance - Camera Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print("Camera closed.")
