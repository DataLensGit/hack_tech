document.addEventListener('DOMContentLoaded', function () {
    let mainLeft = document.querySelector('.main-page .left');
    let mainRight = document.querySelector('.main-page .right');
    let fileSelector = document.querySelector('.file-selector');
    let cv = document.querySelector('#cv');

    if (mainLeft) {

        mainLeft.addEventListener('click', function () {
            mainLeft.classList.add('active');
            mainRight.classList.remove('active');
    
            gsap.to('.main-page h2', {
                y: 80,
                opacity: 0,
                duration: 1.25,
                ease: 'power3.out'
            });
    
            gsap.to(mainLeft, {
                width: "100vw",
                duration: 0.75,
                ease: 'power2.out',
            });
    
            gsap.to(mainRight, {
                width: "20vw",
                duration: 0.75,
                ease: 'power2.out',
            });
    
            gsap.to("#triangle", {
                y: 80,
                opacity: 0,
                duration: 1,
                ease: 'power3.out'
            });
        });
    
        mainRight.addEventListener('click', function () {
            mainRight.classList.add('active');
            mainLeft.classList.remove('active');
    
            gsap.to(mainRight.querySelector('h2'), {
                y: 80,
                opacity: 0,
                duration: 1.25,
                ease: 'power3.out'
            });
    
            gsap.to(mainRight, {
                width: "100vw",
                duration: 0.75,
                ease: 'power2.out',
            });
    
            gsap.to(mainLeft, {
                width: "20vw",
                duration: 0.75,
                ease: 'power2.out',
            });
    
            gsap.to("#triangle", {
                y: 80,
                opacity: 0,
                duration: 1,
                ease: 'power3.out'
            });
        });
    
        // File selector
        fileSelector.addEventListener('click', function () {
            document.querySelector('#cv').click();
        });
    
        cv.addEventListener('change', function () {
            let file = cv.files[0];
            uploadFile(file);
        });
    
        ["dragenter", "dragover", "dragleave", "drop"].forEach(eventName => {
            fileSelector.addEventListener(eventName, preventDefaults, false);
        });
    
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
    
        ["dragenter", "dragover"].forEach(eventName => {
            fileSelector.addEventListener(eventName, () => fileSelector.classList.add("highlight"), false);
        });
        ["dragleave", "drop"].forEach(eventName => {
            fileSelector.addEventListener(eventName, () => fileSelector.classList.remove("highlight"), false);
        });
    
        fileSelector.addEventListener("drop", handleDrop, false);
    
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const file = dt.files[0];
            uploadFile(file);
        }
    
        async function uploadFile(file) {
            const formData = new FormData();
            formData.append('file', file);
    
            try {
                const response = await fetch('http://localhost:8000/upload-pdf', {
                    method: 'POST',
                    body: formData
                });
    
                if (response.ok) {
                    // Ha a feltöltés sikeres, navigáljunk a results.html oldalra
                    window.location.href = '/results';
                } else {
                    window.location.href = '/results';
                    console.error('Hiba a fájl feltöltésekor');
                }
            } catch (error) {
                console.error('Hiba a szerverrel való kapcsolat során:', error);
            }
        }
    
        // Job description send
        let jobDescription = document.querySelector('#job-description');
        let descriptionSubmit = document.querySelector('#submit-job');
    
        descriptionSubmit.addEventListener('click', function () {
            // Itt mehet a küldés a backendnek
            console.log(jobDescription.value);
        });

        
    }
});
