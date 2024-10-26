document.addEventListener('DOMContentLoaded', function() {

    setTimeout(() => {
        document.querySelector('body').style.opacity = 1;
    }, 100);

    gsap.from('#triangle', {
        width: "0%",
        height: "0%",
        duration: 1.25,
        ease: 'power3.out',
        delay: 0.15
    });

    gsap.from('h2', {
        y: 80,
        opacity: 0,
        duration: 1.25,
        ease: 'power3.out',
        delay: 0.25
    });

    anime({
        targets: '#triangle path',
        strokeDashoffset: [anime.setDashoffset, 0],
        easing: 'easeInOutQuint',
        duration: 1900,
    });

    anime({
        targets: '#triangle path',
        fill: '#009abc',
        duration: 500,
        delay: 1500,
        easing: 'easeOutCubic'
    });

});