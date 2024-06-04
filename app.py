import os
import time
import numpy as np
import cv2
import pyautogui
from flask import Flask, Response, render_template, request

app = Flask(__name__)
active = True
# Original screen resolution
original_width, original_height = pyautogui.size()

# Target resolution (480p)
target_width, target_height = 854, 480

# Maximum number of video chunks to keep
max_chunks = 10

# Function to capture screen and record video in chunks
def capture_screen():
    global active
    frame_duration = 1.0 / 120  # Duration for each frame to maintain 30 FPS
    chunk_duration = 30  # Duration of each video chunk (in seconds)
    
    # Define the codec
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # You can change the codec as per your preference
    
    # Directory to store video chunks
    video_dir = 'video_chunks'
    os.makedirs(video_dir, exist_ok=True)
    
    # Counter for chunk naming
    chunk_counter = 0
    
    while True:
        start_time = time.time()
        
        # Create a new video writer for each chunk
        out = cv2.VideoWriter(f'{video_dir}/output_{chunk_counter}.mp4', fourcc, 30, (target_width, target_height))
        
        # Counter for frames in the current chunk
        frame_counter = 0
        
        prev_frame = None
        while frame_counter < chunk_duration * 30:  # Multiply by 30 to get the number of frames
            # Capture raw pixels from the entire screen
            screen = pyautogui.screenshot()
            
            # Resize the screen image to the target resolution
            screen = screen.resize((target_width, target_height))
            
            # Convert the screenshot to a format suitable for OpenCV
            current_frame = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
            
            # Blend current frame with previous frame
            if prev_frame is not None:
                alpha = 0.1
                current_frame = cv2.addWeighted(prev_frame, alpha, current_frame, 1 - alpha, 0)
            
            # Get the current mouse cursor position
            mouse_x, mouse_y = pyautogui.position()
            
            # Scale the mouse cursor position to match the target resolution
            scaled_mouse_x = int(mouse_x * target_width / original_width)
            scaled_mouse_y = int(mouse_y * target_height / original_height)
            
            # Draw a small red circle to represent the mouse cursor
            if active:
                cv2.circle(current_frame, (scaled_mouse_x, scaled_mouse_y), 5, (0, 0, 255), -1)
            
            # Write the frame to the video file
            out.write(current_frame)
            
            # Encode the image as JPEG with 75% quality (for streaming)
            _, jpeg = cv2.imencode('.jpg', current_frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            
            # Yield the encoded frame for streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            
            prev_frame = current_frame
            frame_counter += 1
        
        # Release the VideoWriter object for the current chunk
        out.release()
        
        # Increment the chunk counter
        chunk_counter += 1
        
        # Delete old video chunks if the maximum number of chunks is reached
        if chunk_counter > max_chunks:
            oldest_chunk = f'{video_dir}/output_{chunk_counter - max_chunks - 1}.mp4'
            if os.path.exists(oldest_chunk):
                os.remove(oldest_chunk)
    
        # Calculate the time taken to process the chunk
        processing_time = time.time() - start_time
        
        # Sleep for any remaining time to maintain 30 FPS
        if processing_time < chunk_duration:
            time.sleep(chunk_duration - processing_time)

# Route to toggle cursor
@app.route('/toggle_cursor', methods=['POST'])
def toggle_cursor():
    global active
    if active:
        active = False
    else:
        active = True
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
