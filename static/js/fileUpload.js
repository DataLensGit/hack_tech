document.addEventListener('DOMContentLoaded', () => {
    const jobDescriptionTextarea = document.getElementById('job-description');
    const submitButton = document.getElementById('submit-job');
    const cvInput = document.getElementById('cv');
    let attachedFile = null;  // Változó a hozzáadott fájl tárolására

    // Drag and drop események kezelése
    jobDescriptionTextarea.addEventListener('dragover', (event) => {
        event.preventDefault(); // Alapértelmezett viselkedés megakadályozása
        jobDescriptionTextarea.style.border = "2px dashed #4CAF50"; // Vizualis visszajelzés
    });

    jobDescriptionTextarea.addEventListener('dragleave', () => {
        jobDescriptionTextarea.style.border = ""; // Eredeti stílus visszaállítása
    });

    jobDescriptionTextarea.addEventListener('drop', (event) => {
        event.preventDefault();
        jobDescriptionTextarea.style.border = ""; // Eredeti stílus visszaállítása

        const file = event.dataTransfer.files[0];
        if (file && file.type === 'application/pdf') {
            // A fájlt eltároljuk a változóban
            attachedFile = file;

            // Vizualis visszajelzés a felhasználónak
            jobDescriptionTextarea.value = `Fájl hozzáadva: ${file.name}`;
        } else {
            alert('Csak PDF fájlokat lehet ide húzni.');
        }
    });

});
