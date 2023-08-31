
import pickle
import cvzone
import numpy as np
import firebase_admin
from google.cloud import storage
from google.cloud.storage import client
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from firebase_admin import firestore


# Initialize Firebase with your credentials
cred = credentials.Certificate("D:/Codes/ParkEase/serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://parkease-58fcc-default-rtdb.firebaseio.com/',
    'storageBucket': 'gs://parkease-58fcc.appspot.com'
})
db = firestore.client()
# Video feed
cap = cv2.VideoCapture('carPark.mp4')

with open('CarParkPos', 'rb') as f:
    posList = pickle.load(f)

width, height = 107, 48

# Reference to the root of your database


prev_space_counter = None  # Variable to store the previous space counter value
spot_id='qXuWA6U0J7xa3TyoYEEM'
doc_ref = db.collection('spots').document(spot_id)
doc_snapshot = doc_ref.get()
if doc_snapshot.exists:
   pass
else:
    print("Document does not exist.")


def checkParkingSpace(imgPro, img1):
    spaceCounter = 0
    imgBlueprint = np.ones_like(img1) * 255  # Blank blueprint image
    imgMask = np.zeros_like(img1, dtype=np.uint8)  # Mask for occupied spaces

    # Generate vacant and filled space images
    imgVacant = imgBlueprint.copy()
    imgFilled = imgBlueprint.copy()

    for pos in posList:
        x, y = pos

        imgCrop = imgPro[y:y + height, x:x + width]
        count = cv2.countNonZero(imgCrop)

        if count < 900:
            color = (0, 255, 0)  # Available space (green)
            thickness = -1  # Fill the space with color
            spaceCounter += 1
        else:
            color = (0, 0, 255)  # Occupied space (red)
            thickness = 2

        cv2.rectangle(img, pos, (pos[0] + width, pos[1] + height), color, thickness)
        cv2.rectangle(imgBlueprint, pos, (pos[0] + width, pos[1] + height), color, thickness)
        cvzone.putTextRect(img, str(count), (x, y + height - 3), scale=1,
                           thickness=2, offset=0, colorR=color)

        # Update the mask with occupied spaces
        if thickness == 2:
            imgMask[y:y + height, x:x + width] = 255

        # Draw borders for vacant and filled spaces
        if count < 900:
            cv2.rectangle(imgVacant, pos, (pos[0] + width, pos[1] + height), (0, 255, 0), 2)  # Green border for vacant spaces
        else:
            cv2.rectangle(imgFilled, pos, (pos[0] + width, pos[1] + height), (0, 0, 255), 2)  # Red border for filled spaces

    print(spaceCounter)
    cvzone.putTextRect(img, f'Free: {spaceCounter}/{len(posList)}', (100, 50), scale=3,
                       thickness=5, offset=20, colorR=(0, 200, 0))
    cvzone.putTextRect(imgBlueprint, f'Free: {spaceCounter}/{len(posList)}', (100, 50), scale=3,
                       thickness=5, offset=20, colorR=(0, 200, 0))

    # Display vacant and filled space images


    # Check if the spot_id exists in the database
    # Add a new record

    # Update the space_counter value in the database only if it has changed
    global prev_space_counter
    if spaceCounter != prev_space_counter:
        cv2.imshow('Vacant Spaces', imgVacant)
        cv2.imshow('Filled Spaces', imgFilled)
        bucket = storage.bucket(app=firebase_admin.get_app(), name='parkease-58fcc.appspot.com')
        blob = bucket.blob(f'parking_images/{spot_id}.jpg')
        cv2.imwrite(f'{spot_id}.jpg', imgFilled)
        blob.upload_from_filename(f'{spot_id}.jpg')
        image_url = blob.public_url
        doc_ref.update({
            'spaceCounter': spaceCounter
        })
        prev_space_counter = spaceCounter






while True:

    if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    success, img = cap.read()
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, (3, 3), 1)
    imgThreshold = cv2.adaptiveThreshold(imgBlur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                         cv2.THRESH_BINARY_INV, 25, 16)
    imgMedian = cv2.medianBlur(imgThreshold, 5)
    kernel = np.ones((3, 3), np.uint8)
    imgDilate = cv2.dilate(imgMedian, kernel, iterations=1)

    checkParkingSpace(imgDilate,imgGray)
    cv2.imshow("Image", img)
    cv2.waitKey(10)

    imgDilate = cv2.dilate(imgMedian, kernel, iterations=1)

    checkParkingSpace(imgDilate, imgGray)
    cv2.imshow("Image", img)
    cv2.waitKey(10)
