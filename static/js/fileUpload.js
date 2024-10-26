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

    // Submit esemény figyelése
    submitButton.addEventListener('click', () => {
        const formData = new FormData();
        const industry = document.getElementById('industry').value;
        const jobDescription = jobDescriptionTextarea.value;

        // Hozzáadjuk az Industry és a jobDescription mezőket
        formData.append('industry', industry);
        formData.append('jobDescription', jobDescription);

        // Ha van csatolt fájl, azt is hozzáadjuk
        if (attachedFile) {
            formData.append('cv', attachedFile);
        }

        // Kulcsszavak összegyűjtése
        document.querySelectorAll('.keywords .line').forEach((line, index) => {
            const skill = line.querySelector('input[type="text"]:first-child').value;
            const weight = line.querySelector('input[type="text"]:nth-child(2)').value;
            if (skill && weight) {
                formData.append(`keywords[${index}][skill]`, skill);
                formData.append(`keywords[${index}][weight]`, weight);
            }
        });

        // POST kérés küldése a backendnek
        fetch('/submit-job', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log('Válasz a szervertől:', data);
            // Ide jöhet a további feldolgozás
        })
        .catch(error => {
            console.error('Hiba történt az adatok küldése közben:', error);
        });
    });
});
