document.addEventListener("DOMContentLoaded", function () {
    const submitButton = document.getElementById('submit-job');
    const cvInput = document.getElementById('cv');

    // Új kulcsszavak hozzáadása
    document.querySelector('.add-keyword').addEventListener('click', function () {
        const keywordsContainer = document.querySelector('.keywords');
        const line = document.createElement('div');
        line.className = 'line';

        // Új input mezők a kulcsszavakhoz
        line.innerHTML = `
            <input type="text" placeholder="Skill/attribute">
            <input type="text" placeholder="Weight" oninput="this.value = this.value.replace(/[^0-9]/g, '')"><span>%</span>
        `;

        keywordsContainer.appendChild(line);
    });

    // Submit esemény figyelése
    submitButton.addEventListener('click', function () {
        const formData = new FormData();
        const industry = document.getElementById('industry').value;
        const jobDescription = document.getElementById('job-description').value;
        const cvFile = cvInput.files[0];  // Ha van feltöltött fájl

        // Hozzáadjuk az Industry és a jobDescription mezőket
        formData.append('industry', industry);
        formData.append('jobDescription', jobDescription);

        // Ha van csatolt dokumentum, azt is hozzáadjuk
        if (cvFile) {
            formData.append('cv', cvFile);
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
