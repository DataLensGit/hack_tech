document.addEventListener('DOMContentLoaded', function () {
    let mainLeft = document.querySelector('.main-page .left');
    
    if (mainLeft) {
        let mainRight = document.querySelector('.main-page .right');
        let fileSelector = document.querySelector('.file-selector');
        let cv = document.querySelector('#cv');
        let loader = document.querySelector('.loader');
        let microphone = document.querySelector('.microphone');

        mainLeft.addEventListener('click', function () {
            mainLeft.classList.add('active');
            mainRight.classList.remove('active');
            mainLeft.classList.add('clicked');
            mainRight.classList.add('clicked');

            mainLeft.style.zIndex = mainLeft.style.zIndex + 2;

            setTimeout(() => {

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
        });

        mainRight.addEventListener('click', function () {
            mainRight.classList.add('active');
            mainLeft.classList.remove('active');
            mainLeft.classList.add('clicked');
            mainRight.classList.add('clicked');

            mainRight.style.zIndex = mainLeft.style.zIndex + 1;

            setTimeout(() => {
    
                gsap.to('.main-page h2', {
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
            }, 30);
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
            loader.style.display = 'flex';
            setTimeout(() => {
                loader.style.opacity = '1';
            }, 20);
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('http://localhost:8000/upload-pdf', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    window.location.href = '/results?param1=Job&param2=you';
                } else {
                    window.location.href = '/results?param1=Job&param2=you';
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
            console.log(jobDescription.value);
        });

        // Transcript handling
        let transcriptButtons = document.querySelectorAll('.transcript-button');

        transcriptButtons.forEach(button => {
            button.addEventListener('click', function () {
                if (microphone) {
                    microphone.style.display = 'flex';
                    setTimeout(() => {
                        microphone.style.opacity = '1';
                    }, 20);
                }
            });
        });

        if (microphone) {
            microphone.querySelector('.primary-link').addEventListener('click', function () {
                microphone.style.opacity = '0';
                setTimeout(() => {
                    microphone.style.display = 'none';
                }, 500);
            });
        }

        // Adding keywords

        let addKeyword = document.querySelector('.add-keyword');

        if (addKeyword) {
            let keywords = document.querySelector('.keywords');

            addKeyword.addEventListener('click', function () {
                let id = keywords.children.length + 1;
                let keyword = document.createElement('div');
                keyword.classList.add('keyword');
                keyword.innerHTML = `
                    <div class="line">
                        <input type="text" id="keyword-${id}" name="keyword-${id}" placeholder="Skill/attribute">
                        <input type="text" id="weight-${id}" name="weight-${id}" placeholder="Weight" oninput="this.value = this.value.replace(/[^0-9]/g, '')"><span>%</span>
                    </div>
                `
                keywords.appendChild(keyword);
            });
        }
    }
});
