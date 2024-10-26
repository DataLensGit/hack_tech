document.addEventListener('DOMContentLoaded', function() {
    document.querySelector('#triangle path').style.stroke = '#008bad';

    gsap.from('#triangle', {
        scale: 0,
        duration: 1.25,
        ease: 'power3.out',
        delay: 0.25
    });

    anime({
        targets: '#triangle path',
        strokeDashoffset: [anime.setDashoffset, 0],
        easing: 'easeInOutQuint',
        duration: 2000,
        complete: function() {
            anime({
                targets: '#triangle path',
                fill: '#008bad',
                duration: 800,
                easing: 'easeOutCubic'
            });
        }
    });
});