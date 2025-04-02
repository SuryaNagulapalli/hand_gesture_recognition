from flask import Flask, render_template, Response, jsonify, request
import cv2 as cv
import numpy as np
from gesture_recognition import process_frame
import threading
import time
import os

app = Flask(__name__)

# Global variables for camera control
camera_running = False
cap = None
frame = None
lock = threading.Lock()

def init_camera():
    """Initialize the camera."""
    global cap
    cap = cv.VideoCapture(0)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, 660)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, 540)
    cap.set(cv.CAP_PROP_FPS, 30)
    return cap.isOpened()

def release_camera():
    """Release the camera."""
    global cap
    if cap is not None:
        cap.release()
        cap = None

def capture_frames():
    """Background task to capture frames."""
    global camera_running, frame, cap
    while True:
        if camera_running and cap is not None:
            success, img = cap.read()
            if success:
                processed_frame = process_frame(img)
                with lock:
                    frame = processed_frame
            else:
                time.sleep(0.01)
        else:
            time.sleep(0.1)

def gen_frames():
    """Generate video frames for streaming."""
    global frame
    while True:
        with lock:
            if frame is not None and camera_running:
                ret, buffer = cv.imencode('.jpg', frame, [int(cv.IMWRITE_JPEG_QUALITY), 85])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.033)

@app.route('/')
def index():
    """Render the frontend HTML page."""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Stream the video feed."""
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_camera', methods=['POST'])
def start_camera():
    """Start the camera."""
    global camera_running
    if not camera_running:
        if init_camera():
            camera_running = True
            return jsonify({'status': 'success', 'message': 'Camera started'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to start camera'})
    return jsonify({'status': 'success', 'message': 'Camera already running'})

@app.route('/stop_camera', methods=['POST'])
def stop_camera():
    """Stop the camera."""
    global camera_running, frame
    if camera_running:
        camera_running = False
        with lock:
            frame = None
        release_camera()
        return jsonify({'status': 'success', 'message': 'Camera stopped'})
    return jsonify({'status': 'success', 'message': 'Camera already stopped'})

@app.route('/upload_image', methods=['POST'])
def upload_image():
    """Handle image upload and process it for gesture recognition."""
    if 'image' not in request.files:
        return jsonify({'status': 'error', 'message': 'No image file provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400
    
    try:
        # Read the image file into a numpy array
        filestr = file.read()
        npimg = np.frombuffer(filestr, np.uint8)
        image = cv.imdecode(npimg, cv.IMREAD_COLOR)

        if image is None:
            return jsonify({'status': 'error', 'message': 'Invalid image format'}), 400

        # Process the image for gesture recognition
        processed_image = process_frame(image)
        
        # Ensure the static folder exists
        if not os.path.exists('static'):
            os.makedirs('static')
        
        # Save the processed image
        temp_path = os.path.join('static', 'processed_image.jpg')
        success = cv.imwrite(temp_path, processed_image)
        
        if not success:
            return jsonify({'status': 'error', 'message': 'Failed to save processed image'}), 500
        
        # Return the URL of the processed image
        image_url = f'/static/processed_image.jpg?{int(time.time())}'  # Cache busting
        return jsonify({
            'status': 'success',
            'message': 'Image processed successfully',
            'image_url': image_url
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Processing failed: {str(e)}'}), 500

if __name__ == '__main__':
    # Start the frame capture thread
    threading.Thread(target=capture_frames, daemon=True).start()
    try:
        app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)  # Debug=True for better error logging
    finally:
        release_camera()