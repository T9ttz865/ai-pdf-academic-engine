document.addEventListener("submit", async function(e) {

    if (e.target.id !== "pdfForm") return;

    e.preventDefault();

    const formData = new FormData(e.target);

    document.getElementById("resultBox").innerText = "⏳ جاري التحليل...";

    const response = await fetch("/analyze", {
        method: "POST",
        body: formData
    });

    const data = await response.json();

    document.getElementById("resultBox").innerText =
        data.result || data.error;
});