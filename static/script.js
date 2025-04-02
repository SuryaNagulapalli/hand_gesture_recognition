document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const videoFeed = document.getElementById('videoFeed');
    const uploadForm = document.getElementById('uploadForm');
    const uploadResult = document.getElementById('uploadResult');

    // Start camera
    startBtn.addEventListener('click', () => {
        fetch('/start_camera', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                console.log(data.message);
                if (data.status === 'success') {
                    videoFeed.src = '/video_feed';
                }
            })
            .catch(error => console.error('Error starting camera:', error));
    });

    // Stop camera
    stopBtn.addEventListener('click', () => {
        fetch('/stop_camera', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                console.log(data.message);
                if (data.status === 'success') {
                    videoFeed.src = '';
                }
            })
            .catch(error => console.error('Error stopping camera:', error));
    });

    // Handle image upload
    uploadForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(uploadForm);
        
        uploadResult.innerHTML = '<p>Processing...</p>'; // Show processing status
        
        fetch('/upload_image', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                uploadResult.innerHTML = `<img src="${data.image_url}" alt="Processed Image" style="max-width: 660px;">`;
            } else {
                uploadResult.innerHTML = `<p style="color: red;">Error: ${data.message}</p>`;
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
            uploadResult.innerHTML = `<p style="color: red;">Upload failed: ${error.message}</p>`;
        });
    });
});