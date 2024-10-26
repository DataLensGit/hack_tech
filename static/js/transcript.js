const transcriptButtons = document.querySelectorAll('.transcript-button');
const jobDescriptionTextarea = document.getElementById('job-description');

let mediaRecorder;
let audioChunks = [];

// Minden transcript gombhoz eseményfigyelő hozzáadása
transcriptButtons.forEach(button => {
    button.addEventListener('click', async () => {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            // Ha a felvétel folyamatban van, állítsuk le
            mediaRecorder.stop();
            transcriptButtons.forEach(btn => btn.textContent = 'use voice transcription');
            return;
        }

        // Mikrofon hozzáférés kérése
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            // Felvétel végén az audio adat feltöltése a szerverre
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            audioChunks = [];

            const formData = new FormData();
            formData.append('file', audioBlob, 'recording.wav');

            try {
                const response = await fetch('http://localhost:8000/upload-audio', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    jobDescriptionTextarea.value += data.transcription; // Transzkripció hozzáadása a textarea-hoz
                } else {
                    const errorData = await response.json();
                    alert('Hiba történt: ' + errorData.detail);
                }
            } catch (error) {
                console.error('Hiba a fájl feltöltése közben:', error);
            }
        };

        // Felvétel indítása
        mediaRecorder.start();
        transcriptButtons.forEach(btn => btn.textContent = 'Stop transcription');
    });
});
