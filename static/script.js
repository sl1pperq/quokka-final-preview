import devtools from "./index";

if ("{{ quiz.protect}}" === "True") {

    document.ondragstart = prohibit;
    document.onselectstart = prohibit;
    document.oncontextmenu = prohibit;

    function prohibit() {
        return false;
    }

    document.querySelector('input').addEventListener('paste', function (e) {
        e.preventDefault();
    });

    document.querySelector('input').addEventListener('copy', function (e) {
        e.preventDefault();
    });

    console.log('Is DevTools open:', devtools.isOpen);

    console.log('DevTools orientation:', devtools.orientation);

    window.addEventListener('devtoolschange', event => {
        console.log('Is DevTools open:', event.detail.isOpen);
        console.log('DevTools orientation:', event.detail.orientation);
        if (event.detail.isOpen) {
            document.location.href = '/error'
        }
    });
}