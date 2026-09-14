document.addEventListener("DOMContentLoaded", () => {
    const flashes = document.querySelectorAll(".flash");
    flashes.forEach((item) => {
        setTimeout(() => {
            item.style.opacity = "0";
            item.style.transition = "opacity .5s";
        }, 4500);
    });
});
