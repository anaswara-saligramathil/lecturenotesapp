let mediaRecorder;
let audioChunks = [];
let timerInterval;
let seconds = 0;

// TIMER
function startTimer() {
    seconds = 0;
    timerInterval = setInterval(() => {
        seconds++;
        const m = String(Math.floor(seconds / 60)).padStart(2, "0");
        const s = String(seconds % 60).padStart(2, "0");
        document.getElementById("timer").innerText = `⏱ ${m}:${s}`;
    }, 1000);
}

function stopTimer() {
    clearInterval(timerInterval);
}

// UPLOAD
function uploadAudio() {
    const file = document.getElementById("audioFile").files[0];
    if (!file) return alert("Select an audio file");

    const fd = new FormData();
    fd.append("audio", file);

    fetch("/upload", { method: "POST", body: fd })
        .then(r => r.json())
        .then(d => document.getElementById("text").value = d.transcript || "");
}

// RECORD
function startRecording() {
    audioChunks = [];
    startTimer();
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.start();
        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
    });
}

function stopRecording() {
    stopTimer();
    mediaRecorder.stop();
    mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunks, { type: "audio/wav" });
        const fd = new FormData();
        fd.append("audio", blob, "recorded.wav");
        fetch("/upload", { method: "POST", body: fd })
            .then(r => r.json())
            .then(d => document.getElementById("text").value = d.transcript || "");
    };
}

// SUMMARY
function summarize() {
    fetch("/summarize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: document.getElementById("text").value })
    })
    .then(r => r.json())
    .then(d => document.getElementById("summary").innerText = d.summary);
}

// KEYWORDS
function keywords() {
    fetch("/keywords", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: document.getElementById("text").value })
    })
    .then(r => r.json())
    .then(d => {
        const ul = document.getElementById("keywords");
        ul.innerHTML = "";
        d.keywords.forEach(k => {
            const li = document.createElement("li");
            li.innerText = k;
            ul.appendChild(li);
        });
    });
}

// FLASHCARDS
function flashcards() {
    fetch("/flashcards", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: document.getElementById("text").value })
    })
    .then(r => r.json())
    .then(d => {
        const container = document.getElementById("flashcards");
        container.innerHTML = "";
        d.flashcards.forEach(card => {
            const div = document.createElement("div");
            div.className = "flashcard";
            div.innerHTML = `<h4>${card.title}</h4><p>${card.content}</p>`;
            container.appendChild(div);
        });
    });
}
