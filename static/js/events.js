document.addEventListener('DOMContentLoaded', function() {
    let mainLeft = document.querySelector('.main-page .left');
    let mainRight = document.querySelector('.main-page .right');
    let fileSelector = document.querySelector('.file-selector');
    let cv = document.querySelector('#cv');

    mainLeft.addEventListener('click', function() {

        mainLeft.classList.add('active');
        mainRight.classList.remove('active');

        gsap.to(mainLeft.querySelector('h2'), {
            y: 80,
            opacity: 0,
            duration: 1.25,
            ease: 'power3.out'
        });

        gsap.to(mainLeft, {
            width: "100vw",
            duration: 0.85,
            ease: 'power3.out',
        });

        gsap.to("#triangle", {
            y: 80,
            opacity: 0,
            duration: 1,
            ease: 'power3.out'
        });

        // gsap.to(mainLeft.querySelector('.card'), {
        //     opacity: 1,
        //     duration: 0.85,
        //     ease: 'power2.out'
        // });

    });

    mainRight.addEventListener('click', function() {

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
            duration: 1,
            ease: 'power3.out',
        });

        gsap.to("#triangle", {
            y: 80,
            opacity: 0,
            duration: 1,
            ease: 'power3.out'
        });
    });

    fileSelector.addEventListener('click', function() {
        document.querySelector('#cv').click();
    });

    cv.addEventListener('change', function() {
        let file = cv.files[0];
        let reader = new FileReader();

        reader.onload = function(e) {
            document.querySelector('.file-selector p').innerHTML = file.name;
        }

        reader.readAsDataURL(file);
    });


});