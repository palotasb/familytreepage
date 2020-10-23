function get_own_families(element) {
    return element
        .getAttribute("data-own-families")
        .split(",")
        .filter((s) => s !== "");
}

function get_parent_families(element) {
    return element
        .getAttribute("data-parent-families")
        .split(",")
        .filter((s) => s !== "");
}

window.addEventListener("load", (event) => {
    for (let box of document.querySelectorAll("#boxes .box")) {
        box.addEventListener("mouseover", (event) => {
            event.target.classList.add("hovered");
            for (let family of get_own_families(event.target)) {
                document
                    .getElementById("g" + family)
                    .classList.add("hovered-own-family");
            }
            for (let family of get_parent_families(event.target)) {
                document
                    .getElementById("g" + family)
                    .classList.add("hovered-parent-family");
            }
        });
        box.addEventListener("mouseout", (event) => {
            event.target.classList.remove("hovered");
            for (let family of get_own_families(event.target)) {
                document
                    .getElementById("g" + family)
                    .classList.remove("hovered-own-family");
            }
            for (let family of get_parent_families(event.target)) {
                document
                    .getElementById("g" + family)
                    .classList.remove("hovered-parent-family");
            }
        });
    }
});
