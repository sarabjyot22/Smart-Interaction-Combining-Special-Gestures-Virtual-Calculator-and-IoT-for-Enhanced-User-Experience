import cv2 
import mediapipe as mp 
import numpy as np 
import math 
from math import hypot
from pynput.keyboard import Controller
import pyautogui
import screen_brightness_control as sbc
import tkinter as tk
from tkinter import messagebox
from cvzone.HandTrackingModule import HandDetector
import warnings
import serial
import collections 
from collections import deque
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

warnings.filterwarnings('ignore')
# Initialize Mediapipe Hand and Drawing modules
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Define gestures
GESTURE_LOCK = "Peace Sign"  # Index and middle fingers raised
GESTURE_UNLOCK = "Rock On Sign"  # Index and little finger raised

def drawAll(img, buttonList):
    for button in buttonList:
        x, y = button.pos
        w, h = button.size
        cv2.rectangle(img, button.pos, (x + w, y + h), (96, 96, 96), cv2.FILLED)
        cv2.putText(img, button.text, (x + 20, y + 60),
                    cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
    return img

def calculate_distance(x1, y1, x2, y2):
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return distance

# Helper function to classify gestures
def classify_gesture(landmarks):
    # Check "Peace Sign" (Lock Gesture)
    index_raised = landmarks[8].y < landmarks[6].y  # Index finger tip above joint
    middle_raised = landmarks[12].y < landmarks[10].y  # Middle finger tip above joint
    ring_closed = landmarks[16].y > landmarks[14].y  # Ring finger bent
    pinky_closed = landmarks[20].y > landmarks[18].y  # Pinky finger bent
    thumb_neutral = abs(landmarks[4].x - landmarks[3].x) < 0.02  # Thumb neutral position

    if index_raised and middle_raised and ring_closed and pinky_closed and thumb_neutral:
        return GESTURE_LOCK

    # Check "Rock On Sign" (Unlock Gesture)
    index_raised = landmarks[8].y < landmarks[6].y  # Index finger tip above joint
    pinky_raised = landmarks[20].y < landmarks[18].y  # Pinky finger tip above joint
    middle_closed = landmarks[12].y > landmarks[10].y  # Middle finger bent
    ring_closed = landmarks[16].y > landmarks[14].y  # Ring finger bent

    if index_raised and pinky_raised and middle_closed and ring_closed:
        return GESTURE_UNLOCK

    return "Unknown"

# Initialize lock state
is_locked = True
options_window_open = False  # Track if options window is open
lock_window = None  # Initialize lock window variable

def display_lock_state(is_locked):
    global lock_window
    if is_locked:
        if lock_window is None:  # Only create a new window if it doesn't exist
            lock_window = tk.Tk()
            lock_window.title("Lock State")
            label = tk.Label(lock_window, text="System Locked", font=("Helvetica", 24), fg="red")
            label.pack(padx=20, pady=20)
            lock_window.update()
    else:
        if lock_window:
            lock_window.destroy()  # Close the lock window when unlocking
            lock_window = None  # Reset the lock window variable

def main():
    global keyboard, cap, mp_hands, hands, mp_draw, screen_width, screen_height, text, tx, Button, keys, keys1, buttonList, buttonList1, list, app, delay, x, y, coff, is_locked, options_window_open
    lock_window = None
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)
    mp_draw = mp.solutions.drawing_utils

    keyboard = Controller()

    # Get the screen resolution
    screen_width, screen_height = pyautogui.size()

    text=""
    tx=""
    class Button():
        def __init__(self, pos, text, size=[70, 70]):
            self.pos = pos
            self.size = size
            self.text = text
    keys = [["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P","CL"],
            ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";","SP"],
            ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/","APR"]]
    keys1 = [["q", "w", "e", "r", "t", "y", "u", "i", "o", "p","CL"],
            ["a", "s", "d", "f", "g", "h", "j", "k", "l", ";","SP"],
            ["z", "x", "c", "v", "b", "n", "m", ",", ".", "/","APR"]]
    buttonList = []
    buttonList1 = []
    list=[] 
    for i in range(len(keys)):
        for j, key in enumerate(keys[i]):
          buttonList.append(Button([80 * j + 10, 80 * i + 10], key))
    for i in range(len(keys1)):
         for j, key in enumerate(keys1[i]):
           buttonList1.append(Button([80 * j + 10, 80* i + 10], key))

    app=0      
    delay=0 

    
    x = [300, 245, 200, 170, 145, 130, 112, 103, 93, 87, 80, 75, 70, 67, 62, 59, 57]
    y = [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
    coff = np.polyfit(x, y, 2)  
    cap = cv2.VideoCapture(0)
    cap.set(2,150)
    while True:
        success, img = cap.read()
        if not success:
            break

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                gesture = classify_gesture(hand_landmarks.landmark)

                if gesture == GESTURE_LOCK:
                    is_locked = True
                    display_lock_state(is_locked)
                elif gesture == GESTURE_UNLOCK:
                    is_locked = False
                    display_lock_state(is_locked)
                    if not options_window_open:  # Open options window only if it's not already open
                        select_option()

        cv2.imshow("Gesture Control", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def select_option():
    global options_window_open
    root = tk.Tk()
    root.title("Input Device Selection")

    label = tk.Label(root, text="Select an input device:")
    label.pack()

    mouse_button = tk.Button(root, text="Mouse", command=lambda: [root.destroy(), run_mouse()])
    mouse_button.pack()

    keyboard_button = tk.Button(root, text="Keyboard", command=lambda: [root.destroy(), run_keyboard()])
    keyboard_button.pack()

    both_button = tk.Button(root, text="Both Mouse and Keyboard", command=lambda: [root.destroy(), run_both()])
    both_button.pack()

    calculator_button = tk.Button(root, text="Calculator", command=lambda: [root.destroy(), run_calculator()])
    calculator_button.pack()

    special_gesture_button = tk.Button(root, text="Special Gesture", command=lambda: [root.destroy(), special_gesture()])
    special_gesture_button.pack()

    IOTAPP_button = tk.Button(root, text="IOT Application", command=lambda: [root.destroy(), run_IOTAPP()])
    IOTAPP_button.pack()

    options_window_open = True  # Set the flag when options window is open
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root))  # Handle window close event
    root.mainloop()

def on_close(root):
    global options_window_open
    if is_locked:
        # If locked, do not close the options window
        return
    options_window_open = False  # Reset the flag when the window is closed
    root.destroy()
    if is_locked:
        display_lock_state(is_locked)  # Reopen the lock window if the system is locked

# The rest of the functions (run_mouse, run_keyboard, run_both, run_calculator) remain unchanged

def run_mouse():
  while True :
    # Read camera frame
    ret, frame = cap.read()
    
    # Flip the frame horizontally for a later selfie-view display, and convert the BGR image to RGB.
    frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
    
    # To improve performance, optionally mark the image as not writeable to pass by reference.
    frame.flags.writeable = False
    
    # Get hand landmarks
    results = hands.process(frame)
    
    # Draw the hand annotations on the image.
    frame.flags.writeable = True
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    # Create a new window for the camera feed with landmarks
    cv2.namedWindow('mouse_handmarks')
    cv2.moveWindow('mouse_handmarks', 100, 100)
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw the hand annotations on the image.
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Get the tip of the index finger
            index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            
            # Get the tip of the thumb
            thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
            
            # Get the tip of the middle finger
            middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
            
            # Calculate the distance between the index finger and thumb
            distance_it = np.sqrt((index_tip.x - thumb_tip.x) ** 2 + (index_tip.y - thumb_tip.y) ** 2)
            
            # Calculate the distance between the middle finger and thumb
            distance_mt = np.sqrt((middle_tip.x - thumb_tip.x) ** 2 + (middle_tip.y - thumb_tip.y) ** 2)
            
            # Check if the hand is in a fist
            if distance_it < 0.05:
                # Move the mouse cursor to the position of the index finger
                x = int(index_tip.x * screen_width)
                y = int(index_tip.y * screen_height)
                x = max(0, min(x, screen_width - 1))  # boundary check
                y = max(0, min(y, screen_height - 1))  # boundary check
                pyautogui.moveTo(x, y)
                
                # Check if the thumb and index finger are close
                if distance_it < 1:
                    # Perform a left click
                    pyautogui.click()
            elif distance_mt < 0.05:
                # Move the mouse cursor to the position of the middle finger
                x = int(middle_tip.x * screen_width)
                y = int(middle_tip.y * screen_height)
                x = max(0, min(x, screen_width - 1))  # boundary check
                y = max(0, min(y, screen_height - 1))  # boundary check
                pyautogui.moveTo(x, y)
                
                # Check if the thumb and middle finger are close
                if distance_mt < 1:
                    # Perform a right click
                    pyautogui.click(button='right')
            else:
                # Move the mouse cursor to the position of the index finger
                x = int(index_tip.x * screen_width)
                y = int(index_tip.y * screen_height)
                x = max(0, min(x, screen_width - 1))  # boundary check
                y = max(0, min(y, screen_height - 1))  # boundary check
                pyautogui.moveTo(x, y)
    
    # Display the output in the new window
    cv2.imshow('mouse_handmarks', frame)
    
    # Exit on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

def run_keyboard():
    global text, app, delay
    while True:
        success, frame = cap.read()
        frame = cv2.resize(frame, (1000, 580))
        frame = cv2.flip(frame, 1)
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(img)
        landmarks = []
        
        # Select the correct button list based on the current app mode
        if app == 0:
            frame = drawAll(frame, buttonList)
            button_list = buttonList
            r = "up"
        elif app == 1:
            frame = drawAll(frame, buttonList1)
            button_list = buttonList1
            r = "down"
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                for id, lm in enumerate(hand_landmarks.landmark):
                    h, w, c = frame.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    landmarks.append([id, cx, cy])
                
                if landmarks:
                    try:
                        x5, y5 = landmarks[5][1], landmarks[5][2]
                        x17, y17 = landmarks[17][1], landmarks[17][2]
                        dis = calculate_distance(x5, y5, x17, y17)
                        A, B, C = coff
                        distanceCM = A * dis**2 + B * dis + C
                        
                        if 20 < distanceCM < 50:
                            x, y = landmarks[8][1], landmarks[8][2]
                            x2, y2 = landmarks[6][1], landmarks[6][2]
                            x3, y3 = landmarks[12][1], landmarks[12][2]
                            cv2.circle(frame, (x, y), 20, (255, 0, 255), cv2.FILLED)
                            cv2.circle(frame, (x3, y3), 20, (255, 0, 255), cv2.FILLED)
                            
                            if y2 > y:
                                for button in button_list:
                                    xb, yb = button.pos
                                    wb, hb = button.size
                                    
                                    if xb < x < xb + wb and yb < y < yb + hb:
                                        cv2.rectangle(frame, (xb - 5, yb - 5), 
                                                      (xb + wb + 5, yb + hb + 5), 
                                                      (160, 160, 160), cv2.FILLED)
                                        cv2.putText(frame, button.text, 
                                                    (xb + 20, yb + 65), 
                                                    cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
                                        dis = calculate_distance(x, y, x3, y3)
                                        
                                        if dis < 50 and delay == 0:
                                            k = button.text
                                            cv2.rectangle(frame, (xb - 5, yb - 5), 
                                                          (xb + wb + 5, yb + hb + 5), 
                                                          (255, 255, 255), cv2.FILLED)
                                            cv2.putText(frame, k, 
                                                        (xb + 20, yb + 65), 
                                                        cv2.FONT_HERSHEY_PLAIN, 4, (0, 0, 0), 4)
                                            
                                            if k == "SP":
                                                text += " "
                                                keyboard.press(" ")
                                            
                                            elif k == "CL":
                                                text = text[:-1]
                                                keyboard.press('\b')
                                            
                                            elif k == "APR":
                                                if r == "up":
                                                    app = 1
                                                    r = "down"
                                                elif r == "down":
                                                    app = 0
                                                    r = "up"
                                            
                                            else:
                                                if app == 1:  # Lowercase mode
                                                    k = k.lower()
                                                text += k
                                                keyboard.press(k)
                                            
                                            delay = 1
                    
                    except Exception as e:
                        print(f"Error: {e}")
        
        if delay != 0:
            delay += 1
            if delay > 10:
                delay = 0
        
        cv2.rectangle(frame, (20, 250), (850, 400), (255, 255, 255), cv2.FILLED)
        cv2.putText(frame, text, (30, 300), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 0), 3)
        cv2.imshow('virtual keyboard', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


def run_both():
  while True :
    global text,app,delay
    sucess,frame = cap.read()
    frame=cv2.resize(frame,(1000,580))
    frame=cv2.flip(frame,1)
    img=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
    results = hands.process(img)
    lanmark=[]
    if app==0:
       frame=drawAll(frame,buttonList) 
       list=buttonList
       r="up"
    if app==1:
       frame=drawAll(frame,buttonList1) 
       list=buttonList1 
       r="down"

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            for idx, classification in enumerate(results.multi_handedness):
              if classification.classification[0].score > 0.5 and classification.classification[0].label == "Right":
                # Draw the hand annotations on the image.
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                # Get the tip of the index finger
                index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                
                # Get the tip of the thumb
                thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                
                # Get the tip of the middle finger
                middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
                
                # Calculate the distance between the index finger and thumb
                distance_it = np.sqrt((index_tip.x - thumb_tip.x) ** 2 + (index_tip.y - thumb_tip.y) ** 2)
                
                # Calculate the distance between the middle finger and thumb
                distance_mt = np.sqrt((middle_tip.x - thumb_tip.x) ** 2 + (middle_tip.y - thumb_tip.y) ** 2)
                
                # Check if the hand is in a fist
                if distance_it < 0.05:
                    # Move the mouse cursor to the position of the index finger
                    x = int(index_tip.x * screen_width)
                    y = int(index_tip.y * screen_height)
                    x = max(0, min(x, screen_width - 1))  # boundary check
                    y = max(0, min(y, screen_height - 1))  # boundary check
                    pyautogui.moveTo(x, y)
                    
                    # Check if the thumb and index finger are close
                    if distance_it < 1:
                        # Perform a left click
                        pyautogui.click()
                elif distance_mt < 0.05:
                    # Move the mouse cursor to the position of the middle finger
                    x = int(middle_tip.x * screen_width)
                    y = int(middle_tip.y * screen_height)
                    x = max(0, min(x, screen_width - 1))  # boundary check
                    y = max(0, min(y, screen_height - 1))  # boundary check
                    pyautogui.moveTo(x, y)
                    
                    # Check if the thumb and middle finger are close
                    if distance_mt < 1:
                        # Perform a right click
                        pyautogui.click(button='right')
                else:
                    # Move the mouse cursor to the position of the index finger
                    x = int(index_tip.x * screen_width)
                    y = int(index_tip.y * screen_height)
                    x = max(0, min(x, screen_width - 1))  # boundary check
                    y = max(0, min(y, screen_height - 1))  # boundary check
                    pyautogui.moveTo(x, y)
              if classification.classification[0].score > 0.5 and classification.classification[0].label == "Left":
                   #keyboard
                   for id ,lm in enumerate(hand_landmarks.landmark):
                       hl,wl,cl=frame.shape
                       cx,cy=int(lm.x*wl),int(lm.y*hl)     
                       lanmark.append([id, cx, cy]) 

        
                   if lanmark!=0:
                          try:
                              x5,y5=lanmark[5][1],lanmark[5][2]
                              x17,y17=lanmark[17][1],lanmark[17][2]
                              dis=calculate_distance(x5,y5,x17,y17)
                              A, B, C = coff
                              distanceCM = A * dis** 2 + B * dis + C
                              if 20<distanceCM<50:
                          
                              
                                          x,y=lanmark[8][1],lanmark[8][2]
                                          x2,y2=lanmark[6][1],lanmark[6][2]
                                          x3,y3=lanmark[12][1],lanmark[12][2]
                                          cv2.circle(frame,(x,y),20,(255,0,255),cv2.FILLED)
                                          cv2.circle(frame,(x3,y3),20,(255,0,255),cv2.FILLED)
                                          
                                          
                                          if y2>y:
                                              
                                              
                                              for button in list:
                                                      xb, yb = button.pos
                                                      wb, hb = button.size
                                                      
                                                      if (xb< x< xb + wb )and (yb < y < yb + hb):
                                                          cv2.rectangle(frame, (xb - 5, yb - 5), (xb + wb + 5, yb + hb+ 5), (160,160,160), cv2.FILLED)
                                                          cv2.putText(frame, button.text, (xb + 20, yb + 65),cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
                                                          dis= calculate_distance(x,y,x3,y3)
                                                      if dis<50 and delay==0:
                                                          k=button.text
                                                          cv2.rectangle(frame, (xb - 5, yb - 5), (xb + wb + 5, yb + hb+ 5), (255, 255, 255), cv2.FILLED)
                                                          cv2.putText(frame, k, (xb + 20, yb + 65), cv2.FONT_HERSHEY_PLAIN, 4, (0, 0, 0), 4)
                                                          
                                                          if k=="SP":
                                                                  tx=' '  
                                                                  text+=tx
                                                                  keyboard.press(tx)
                                                                  
                                                          elif k=="CL":
                                                                  tx=text[: -1]
                                                                  text=""
                                                                  text+=tx
                                                                  keyboard.press('\b')
                                                                  
                                                          elif k=="APR" and r=="up":
                                                              app=1
                                                              
                                                          elif k=="APR" and r=="down":
                                                              app=0
                                                              
                                                              
                                                          else:
                                                                  text+=k
                                                                  keyboard.press(k)
                                                          delay=1
                                          

                          except:
                          
                          
                              pass  
                          
                   if delay!=0:
                    delay+=1
                    if delay>10:
                      delay=0      
            
                   cv2.rectangle(frame, (20,250), (850,400), (255, 255, 255), cv2.FILLED)
                   cv2.putText(frame, text,(30,300), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 0), 3)
    cv2.imshow('handmarks', frame )
    if cv2.waitKey(1) & 0xff==ord('q'):
           break 

def run_calculator():

    # Button class to define calculator buttons
    class Button:
        def __init__(self, pos, width, height, value):
            self.pos = pos
            self.width = width
            self.height = height
            self.value = value

        def draw(self, img):
            # Draw the button background
            cv2.rectangle(img, self.pos, (self.pos[0] + self.width, self.pos[1] + self.height),
                        (250, 251, 217), cv2.FILLED)
            # Draw the button border
            cv2.rectangle(img, self.pos, (self.pos[0] + self.width, self.pos[1] + self.height),
                        (50, 50, 50), 3)
            # Draw the button value
            cv2.putText(img, self.value, (self.pos[0] + 20, self.pos[1] + 50),
                        cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)

        def checkClicking(self, x, y):
            # Check if a point is inside the button area
            if self.pos[0] < x < self.pos[0] + self.width and self.pos[1] < y < self.pos[1] + self.height:
                return True
            else:
                return False

    # Initialize the webcam
    cap = cv2.VideoCapture(0)
    detector = HandDetector(detectionCon=0.8, maxHands=1)

    # Create buttons for the calculator, including "DEL"q
    buttonListValue = [["1", "2", "3", "+"],
                    ["4", "5", "6", "-"],
                    ["7", "8", "9", "*"],
                    ["DEL", "0", ".", "="]]
    buttonList = []

    # Get the frame width and height
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Set the center position for the calculator (center of the webcam frame)
    center_x = frame_width // 2
    center_y = frame_height // 2

    # Define the starting positions for the calculator
    calculator_width = 280
    calculator_height = 280
    start_x = center_x - calculator_width // 2
    start_y = center_y - calculator_height // 2

    # Define button positions based on the calculator's center
    for x in range(4):
        for y in range(4):
            xPos = start_x + x * 70  # Adjust starting x position
            yPos = start_y + y * 70  # Adjust starting y position
            buttonList.append(Button((xPos, yPos), 70, 70, buttonListValue[y][x]))

    # Initialize variables
    equation = ""
    delayCounter = 0

    # Define the maximum width for the equation box
    max_text_width = calculator_width - 40  # Allowing 20 pixels padding on both sides

    # Flag to track error state
    error_occurred = False

    while True:
        success, img = cap.read()
        img = cv2.flip(img, 1)

        # Detect hands
        hands, img = detector.findHands(img, flipType=False)

        # Draw calculator display (centered)
        cv2.rectangle(img, (start_x, start_y), (start_x + calculator_width, start_y + calculator_height),
                    (250, 251, 217), cv2.FILLED)
        cv2.rectangle(img, (start_x, start_y), (start_x + calculator_width, start_y + calculator_height),
                    (50, 50, 50), 3)

        # Draw the equation box at the top of the calculator
        cv2.rectangle(img, (start_x, start_y - 50), (start_x + calculator_width, start_y),
                    (250, 251, 217), cv2.FILLED)  # Background for the equation
        cv2.rectangle(img, (start_x, start_y - 50), (start_x + calculator_width, start_y),
                    (50, 50, 50), 3)  # Border for the equation display

        # Check the width of the equation text
        equation_size = cv2.getTextSize(equation, cv2.FONT_HERSHEY_PLAIN, 2, 2)[0]
        equation_width, equation_height = equation_size

        # If the equation exceeds the max width, display "Error"
        if equation_width > max_text_width:
            equation = "Error"
            error_occurred = True
        
        # Display the equation or "Error" in the top box
        cv2.putText(img, equation, (start_x + 20 , start_y - 15),
                    cv2.FONT_HERSHEY_PLAIN, 2, (50, 50, 50), 2)

        # Draw all buttons (centered)
        for button in buttonList:
            button.draw(img)

        # Check for hand input only if there's no error
        if not error_occurred and hands:
            lmList = hands[0]["lmList"]  # Landmark list for the first hand

            # Get the coordinates of the index finger tip and middle finger tip
            index_finger = lmList[8][:2]  # Tip of index finger
            middle_finger = lmList[12][:2]  # Tip of middle finger

            # Draw the points of the index and middle fingers
            cv2.circle(img, (int(index_finger[0]), int(index_finger[1])), 10, (0, 255, 0), cv2.FILLED)
            cv2.circle(img, (int(middle_finger[0]), int(middle_finger[1])), 10, (0, 255, 0), cv2.FILLED)

            # Calculate the distance between the index finger tip and middle finger tip
            distance, _, img = detector.findDistance(index_finger, middle_finger, img)
            x, y = index_finger  # Get x, y coordinates of the index finger tip

            # Check if the fingers are close enough to trigger a button click
            if distance < 50:  # Distance threshold for clicking
                for button in buttonList:
                    if button.checkClicking(x, y) and delayCounter == 0:
                        if button.value == "=":
                            try:
                                # Evaluate the equation
                                equation = str(eval(equation))
                            except:
                                equation = "Error"  # Handle invalid equations
                                error_occurred = True
                        elif button.value == "DEL":
                            # Remove the last character from the equation
                            equation = equation[:-1]
                        else:
                            equation += button.value
                        delayCounter = 1

        # Allow time between inputs (to avoid multiple presses)
        if delayCounter != 0:
            delayCounter += 1
            if delayCounter > 10:
                delayCounter = 0

        # Handle keyboard input (clear the calculator if 'C' is pressed)
        key = cv2.waitKey(1)
        if key == ord("c") and error_occurred:
            equation = ""
            error_occurred = False  # Reset the error flag
        
        if key == ord("q"):  # Quit the application
            break

        # Display the result
        cv2.imshow("Virtual Calculator", img)

    cap.release()
    cv2.destroyAllWindows()

def special_gesture():
    # Initialize Pycaw for volume control
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = interface.QueryInterface(IAudioEndpointVolume)
    vol_range = volume.GetVolumeRange()
    min_vol, max_vol = vol_range[0], vol_range[1]

    # Webcam capture
    cap = cv2.VideoCapture(0)

    # Screenshot, undo, and screen split/merge flags
    screenshot_taken = False
    undo_executed = False
    last_action = None  # Track the last action ('split' or 'merge')
    frame_buffer = deque(maxlen=3)  # Buffer to store hand positions
    gesture_stable = False
    stability_threshold = 0.05  # Threshold for gesture stability

    # Initialize MediaPipe Hands
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
    hands = mp_hands.Hands()

    # Helper function to detect if specific fingers are up
    def fingers_up(hand_landmarks):
        fingers = []
        tips = [mp_hands.HandLandmark.INDEX_FINGER_TIP,
                mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
                mp_hands.HandLandmark.RING_FINGER_TIP,
                mp_hands.HandLandmark.PINKY_TIP]
        bases = [mp_hands.HandLandmark.INDEX_FINGER_MCP,
                mp_hands.HandLandmark.MIDDLE_FINGER_MCP,
                mp_hands.HandLandmark.RING_FINGER_MCP,
                mp_hands.HandLandmark.PINKY_MCP]

        for tip, base in zip(tips, bases):
            fingers.append(hand_landmarks.landmark[tip].y < hand_landmarks.landmark[base].y)
        return fingers

    # Helper function to calculate Euclidean distance
    def calculate_distance(point1, point2):
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb_frame)

        hand_landmarks = []
        if result.multi_hand_landmarks:
            for hand_landmark in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmark, mp_hands.HAND_CONNECTIONS)
                landmarks = [(lm.x, lm.y) for lm in hand_landmark.landmark]
                hand_landmarks.append(landmarks)

            # Detect fingers up for the first hand
            fingers = fingers_up(result.multi_hand_landmarks[0])
            index_up, middle_up, ring_up, pinky_up = fingers

            # Volume control (Index finger up)
            if index_up and not middle_up and not ring_up and not pinky_up:
                thumb_tip = result.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.THUMB_TIP]
                index_tip = result.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]

                thumb_coords = (int(thumb_tip.x * frame.shape[1]), int(thumb_tip.y * frame.shape[0]))
                index_coords = (int(index_tip.x * frame.shape[1]), int(index_tip.y * frame.shape[0]))

                distance = hypot(index_coords[0] - thumb_coords[0], index_coords[1] - thumb_coords[1])
                vol = np.interp(distance, [30, 300], [min_vol, max_vol])
                volume.SetMasterVolumeLevel(vol, None)
                vol_percentage = int(volume.GetMasterVolumeLevelScalar() * 100)
                cv2.putText(frame, f"Volume: {vol_percentage}%", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Brightness control (Middle finger up)
            elif middle_up and not index_up and not ring_up and not pinky_up:
                thumb_tip = result.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.THUMB_TIP]
                middle_tip = result.multi_hand_landmarks[0].landmark[ mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

                thumb_coords = (int(thumb_tip.x * frame.shape[1]), int(thumb_tip.y * frame.shape[0]))
                middle_coords = (int(middle_tip.x * frame.shape[1]), int(middle_tip.y * frame.shape[0]))

                distance = hypot(middle_coords[0] - thumb_coords[0], middle_coords[1] - thumb_coords[1])
                brightness = int(np.clip(np.interp(distance, [30, 300], [0, 100]), 0, 100))
                sbc.set_brightness(brightness)
                cv2.putText(frame, f"Brightness: {brightness}%", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

            # Screenshot (Index, Middle, and Ring fingers up)
            elif index_up and middle_up and ring_up and not pinky_up:
                if not screenshot_taken:
                    pyautogui.hotkey("win", "printscreen")
                    screenshot_taken = True
                    cv2.putText(frame, "Screenshot Taken!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            else:
                screenshot_taken = False  # Reset screenshot flag

            # Undo (Index, Middle, Ring, and Pinky fingers up)
            if all(fingers):  # All four fingers up
                if not undo_executed:
                    pyautogui.hotkey("ctrl", "z")
                    undo_executed = True
                    cv2.putText(frame, "Undo (Ctrl + Z) Executed!", (50, 140), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            else:
                undo_executed = False  # Reset undo flag

        # Handle split and merge gestures
        if len(hand_landmarks) == 2:  # Ensure two hands are detected
            left_hand = hand_landmarks[0][9]  # Middle finger MCP
            right_hand = hand_landmarks[1][9]  # Middle finger MCP
            frame_buffer.append((left_hand, right_hand))

            # Smooth hand positions using the buffer
            avg_left_hand = np.mean([pos[0] for pos in frame_buffer], axis=0)
            avg_right_hand = np.mean([pos[1] for pos in frame_buffer], axis=0)
            avg_distance = calculate_distance(avg_left_hand, avg_right_hand)

            # Check gesture stability
            if len(frame_buffer) == frame_buffer.maxlen:
                distances = [calculate_distance(pair[0], pair[1]) for pair in frame_buffer]
                gesture_stable = max(distances) - min(distances) < stability_threshold

            # Visual feedback
            cv2.circle(frame, (int(avg_left_hand[0]), int(avg_left_hand[1])), 10, (255, 0, 0), -1)  # Left hand
            cv2.circle(frame, (int(avg_right_hand[0]), int(avg_right_hand[1])), 10, (0, 255, 0), -1)  # Right hand
            cv2.putText(frame, f"Distance: {avg_distance:.2f}", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            # Execute split/merge commands
            if gesture_stable:
                if avg_distance > 0.7 and last_action != 'split':  # Hands far apart
                    pyautogui.hotkey('win', 'left')
                    pyautogui.press('enter')
                    print("Screen split!")
                    last_action = 'split'
                elif avg_distance < 0.1 and last_action != 'merge':  # Hands close together
                    pyautogui.hotkey('alt', 'space')
                    for _ in range(5):
                        pyautogui.press('down')
                    pyautogui.press('enter')
                    print("Screen merged!")
                    last_action = 'merge'

        cv2.imshow("Gesture Control", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def run_IOTAPP():
    # Configure serial communication
    try:
        ser = serial.Serial('COM3', 115200, timeout=0.1)  # Replace 'COM3' with your Arduino port
    except Exception as e:
        print(f"Error opening serial port: {e}")
        ser = None

    # Initialize MediaPipe Hands
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.8,
        min_tracking_confidence=0.8
    )
    mp_drawing = mp.solutions.drawing_utils

    # Smoothing buffer for finger count
    finger_count_buffer = collections.deque(maxlen=5)

    def count_fingers(hand_landmarks):
        finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky
        thumb_tip = 4

        fingers = []

        # Thumb
        if hand_landmarks.landmark[thumb_tip].x < hand_landmarks.landmark[thumb_tip - 2].x:
            fingers.append(1)  # Thumb is up
        else:
            fingers.append(0)

        # Other fingers
        for tip in finger_tips:
            if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
                fingers.append(1)  # Finger is up
            else:
                fingers.append(0)

        return sum(fingers)

    def detect_fingers(frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Count fingers
                finger_count = count_fingers(hand_landmarks)

                # Add the current count to the buffer
                finger_count_buffer.append(finger_count)

                # Calculate the average count for smoothing
                smoothed_count = sum(finger_count_buffer) / len(finger_count_buffer)
                return round(smoothed_count)  # Return the rounded average count

        return 0  # Return 0 if no hands are detected

    # Function to send data to Arduino
    def send_data(mode, value):
        if ser and ser.isOpen():
            command = f"{mode}{value}\n"
            ser.write(command.encode())

    # Camera-based intensity control
    def intensity_control():
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "Could not access the camera!")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            finger_count = detect_fingers(frame)

            # Display the detected finger count
            cv2.putText(frame, f"Fingers: {finger_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Intensity Control", frame)

            # Send data to Arduino
            send_data('I', finger_count)  # 'I' indicates intensity control mode

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    # Camera-based single light control
    def single_light_control():
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "Could not access the camera!")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            finger_count = detect_fingers(frame)

            # Display the detected finger count
            cv2.putText(frame, f"Fingers: {finger_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Single Light Control", frame)

            # Send data to Arduino
            send_data('L', finger_count)  # 'L' indicates single light control mode

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    # GUI for mode selection
    def show_option_window():
        def on_intensity_mode():
            messagebox.showinfo("Mode Selected", "Intensity Control Mode Activated")
            intensity_control()

        def on_single_light_mode():
            messagebox.showinfo("Mode Selected", "Single Light Control Mode Activated")
            single_light_control()

        window = tk.Tk()
        window.title("LED Control Options")

        intensity_button = tk.Button(window, text="Intensity Control", command=on_intensity_mode, bg="green", fg="white")
        intensity_button.pack(pady=10)

        light_button = tk.Button(window, text="Single Light Control", command=on_single_light_mode, bg="blue", fg="white")
        light_button.pack(pady=10)

        window.mainloop()
    # Start the GUI
    show_option_window()
    # Close the serial port on exit
    if ser and ser.isOpen():
        ser.close()

main()







