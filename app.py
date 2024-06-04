import time
import numpy as np
import cv2
import pyautogui
from flask import Flask, Response, render_template

# Initialize Flask app
app = Flask(__name__)

# Original screen resolution
original_width, original_height = pyautogui.size()

# Target resolution (480p)
target_width, target_height = 854, 480

# Function to capture screen
def capture_screen():
    frame_duration = 1.0 / 120  # Duration for each frame to maintain FPS
    
    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # You can change the codec as per your preference
    out = cv2.VideoWriter('output.mp4', fourcc, 30, (target_width, target_height))
    
    while True:
        start_time = time.time()
        
        # Capture raw pixels from the entire screen
        screen = pyautogui.screenshot()
        
        # Resize the screen image to the target resolution
        screen = screen.resize((target_width, target_height))
        
        # Convert the screenshot to a format suitable for OpenCV
        img = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
        
        # Get the current mouse cursor position
        mouse_x, mouse_y = pyautogui.position()
        
        # Scale the mouse cursor position to match the target resolution
        scaled_mouse_x = int(mouse_x * target_width / original_width)
        scaled_mouse_y = int(mouse_y * target_height / original_height)
        
        # Draw a small red circle to represent the mouse cursor
        cv2.circle(img, (scaled_mouse_x, scaled_mouse_y), 5, (0, 0, 255), -1)
        
        # Write the frame to the video file
        out.write(img)
        
        # Encode the image as JPEG with 75% quality
        _, jpeg = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 75])
        
        # Yield the encoded frame for streaming
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        
        # Calculate the time taken to process the frame
        processing_time = time.time() - start_time
        
        # Sleep for any remaining time to achieve 30 FPS
        if processing_time < frame_duration:
            time.sleep(frame_duration - processing_time)
    
    # Release the VideoWriter object
    out.release()

# Route for the main page
@app.route('/')
def index():
    return render_template('index.html')

# Route for the video feed
@app.route('/video_feed')
def video_feed():
    return Response(capture_screen(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # Run Flask app with host specified
    app.run(host='0.0.0.0', debug=True)
