import urllib.request
url="http://192.168.1.74"
AWB = True
#Importing OpenCV Library for basic image processing functions
import cv2
#Numpy for array related functions
import numpy as np
#Dlib for deep learning based Modules and face landmark detection
import dlib 
#face_utils for basic operations of conversion
from imutils import face_utils
from pygame import mixer
#Get path of laravel
import subprocess
#Get serial of GPS-module
import serial


mixer.init()
sound = mixer.Sound('mixkit-classic-alarm-995.wav')

#Initializing the face detector and landmark detector
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_Landmarks.dat")

#Initializing the camera and taking the instance
cap = cv2.VideoCapture(url + ":81/stream")

#status marking for current state
sleep = 0
drowsy = 0
active = 0
state= ""
color=(0,0,0)

# Open a serial connection to the ESP32
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

def compute(ptA,ptB):
    dist = np.linalg.norm(ptA - ptB)
    return dist

def blinked(a,b,c,d,e,f):
    up = compute(b,d) + compute(c,e)
    down = compute(a,f)
    ratio = up/(2.0*down)
    
    #Checking if it is blinked
    if(ratio>0.25):
        return 2
    elif(ratio>0.21 and ratio<=0.25):
            return 1
    else:
            return 0


while True:
    _, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = detector(gray)
    #detected face in faces array
    for face in faces:
        
        x1 = face.left()
        y1 = face.top()
        x2 = face.right()
        y2 = face.bottom()

        face_frame = frame.copy()
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        landmarks = predictor(gray, face)
        landmarks = face_utils.shape_to_np(landmarks)

        #The numbers are actually the landmarks which will show eye
        left_blink = blinked(landmarks[36],landmarks[37],
             landmarks[38], landmarks[41], landmarks[40], landmarks[39])
        right_blink = blinked(landmarks[42], landmarks[43],
             landmarks[44], landmarks[47], landmarks[46], landmarks[45])

        #Now judge what to do for the eye blinks
        if(left_blink==0 or right_blink==0):
            sleep+=1
            drowsy=0
            active=0
            if(sleep>6):
                state="SLEEPING !!!"
                color=(0,0,255)
                try:
                    sound.play()
                    # Send a message to the ESP32 to trigger the GPS module
                    ser.write(b'1')

                except:
                    
                    pass
                # Send alert to Laravel database
                subprocess.call(["php", "/path/to/alert_script.php", "drowsy", "Driver is sleeping"])
        
        elif(left_blink==1 or right_blink==1):
            sleep=0
            active=0
            drowsy+=1
            if(drowsy>6):
                state="Drowsy !"
                color = (255,0,0)
                # Send alert to Laravel database
                subprocess.call(["php", "/path/to/alert_script.php", "drowsy", "Driver is drowsy"])
        
        else:
            drowsy=0
            sleep=0
            active+=1
            if(active>6):
                state="Active :)"
                color = (0,255,0)
                try:
                    sound.stop()
                    # Send a message to the ESP32 to stop the GPS module
                    ser.write(b'STOP\n')

                except:

                    pass
                # Send alert to Laravel database
                subprocess.call(["php", "/path/to/alert_script.php", "active", "Driver is active"])
                
        cv2.putText(frame, state, (100,100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color,3)

        for n in range(36, 48):
            (x,y) = landmarks[n]
            cv2.circle(frame, (x,y), 1, (255, 255, 255), -1)

    cv2.imshow("Frame", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        ser.close()
        break
