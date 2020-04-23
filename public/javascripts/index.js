document.addEventListener("DOMContentLoaded", function() {
    const cards = document.querySelectorAll('.card');

    function transition() {
    if (this.classList.contains('active')) {
        this.classList.remove('active');
    } else {
        this.classList.add('active');
    }
    }

    cards.forEach(card => card.addEventListener('click', transition));

    Vue.config.silent = false;
    vue = new Vue({
        el: '#iacon-vue',
        data: {
            services: [{
                name: "",
                path: "",
                command: "",
                title: "Título",
                description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
                pid: 0,
                restart: true,
                status: "running",
                startat: "",
                stopat: ""
            }],
        }
    });

    requestStatus = function() {
        var xhr = new XMLHttpRequest();
        xhr.onload = function () {
            if (xhr.status >= 200 && xhr.status < 300) {
                vue.services = JSON.parse(xhr.response);
            } else {
                console.log('The request failed!');
            }
        };
        xhr.open('GET', 'detalhes');
        xhr.send();
    }

    monitorStatus = function() {
        requestStatus();
        setTimeout(monitorStatus, 1000);
    }
    monitorStatus();
});