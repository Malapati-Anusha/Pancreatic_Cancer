
document.addEventListener("DOMContentLoaded", () => {
    const inputs = document.querySelectorAll("input");
    inputs.forEach((input) => {
        input.addEventListener("focus", () => {
            input.style.border = "2px solid #6a11cb";
        });
        input.addEventListener("blur", () => {
            input.style.border = "none";
        });
    });

    const uploadInput = document.getElementById("image-upload");
    const preview = document.getElementById("preview-image");
    if (uploadInput && preview) {
        uploadInput.addEventListener("change", (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (event) {
                    preview.src = event.target.result;
                    preview.style.display = "block";
                };
                reader.readAsDataURL(file);
            }
        });
    }
});
