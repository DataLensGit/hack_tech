document.addEventListener('DOMContentLoaded', () => {
    const jobDescriptionTextarea = document.getElementById('job-description');

    // Drag and drop események kezelése
    jobDescriptionTextarea.addEventListener('dragover', (event) => {
        event.preventDefault(); // Alapértelmezett viselkedés megakadályozása
        jobDescriptionTextarea.style.border = "2px dashed #4CAF50"; // Vizualis visszajelzés
    });

    jobDescriptionTextarea.addEventListener('dragleave', () => {
        jobDescriptionTextarea.style.border = ""; // Eredeti stílus visszaállítása
    });

    jobDescriptionTextarea.addEventListener('drop', async (event) => {
        event.preventDefault();
        jobDescriptionTextarea.style.border = ""; // Eredeti stílus visszaállítása

        const file = event.dataTransfer.files[0];
        if (file && file.type === 'application/pdf') {
            // A PDF fájl küldése a backendre
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('http://localhost:8000/upload-pdf', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    window.location.href = '/results?param1=Candidate&param2=Vagyamitakarsz';
                } else {
                    window.location.href = '/results?param1=Candidate&param2=Vagyamitakarsz';
                }
            } catch (error) {
                console.error('Hiba a fájl feltöltése közben:', error);
            }
        } else {
            alert('Csak PDF fájlokat lehet ide húzni.');
        }
    });
});
