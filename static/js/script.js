// Front-end Interactions for SmartDoc NLP — Intelligent Local System

document.addEventListener("DOMContentLoaded", function() {
    
    const methodTextRadio = document.getElementById("method-text");
    const methodFileRadio = document.getElementById("method-file");
    const btnTextLabel = document.getElementById("btn-text");
    const btnFileLabel = document.getElementById("btn-file");
    
    const textInputSection = document.getElementById("text-input-section");
    const fileInputSection = document.getElementById("file-input-section");
    
    const textarea = document.getElementById("pasted_text");
    const charCounter = document.getElementById("char-counter");
    const wordCounter = document.getElementById("word-counter");
    
    const fileUploadInput = document.getElementById("file_upload");
    const dropZone = document.getElementById("drop-zone");
    const selectedFileName = document.getElementById("selected-file-name");
    const selectedFileSize = document.getElementById("selected-file-size");
    const removeFileBtn = document.getElementById("remove-file");
    
    const clearBtn = document.getElementById("clear-btn");
    const analyzeForm = document.getElementById("analyze-form");
    const loaderModal = document.getElementById("loader-modal");

    function toggleInputMethod(method) {
        if (method === "text") {
            if (methodTextRadio) methodTextRadio.checked = true;
            if (btnTextLabel) btnTextLabel.classList.add("active");
            if (btnFileLabel) btnFileLabel.classList.remove("active");
            if (textInputSection) textInputSection.classList.add("active");
            if (fileInputSection) fileInputSection.classList.remove("active");
        } else {
            if (methodFileRadio) methodFileRadio.checked = true;
            if (btnFileLabel) btnFileLabel.classList.add("active");
            if (btnTextLabel) btnTextLabel.classList.remove("active");
            if (fileInputSection) fileInputSection.classList.add("active");
            if (textInputSection) textInputSection.classList.remove("active");
        }
    }

    if (btnTextLabel) btnTextLabel.addEventListener("click", () => toggleInputMethod("text"));
    if (btnFileLabel) btnFileLabel.addEventListener("click", () => toggleInputMethod("file"));

    function updateCounters() {
        if (!textarea) return;
        const text = textarea.value.trim();
        const charCount = text.length;
        const wordCount = text === "" ? 0 : text.split(/\s+/).filter(w => w.length > 0).length;
        
        if (charCounter) charCounter.innerText = `${charCount.toLocaleString()} character${charCount !== 1 ? 's' : ''}`;
        if (wordCounter) wordCounter.innerText = `${wordCount.toLocaleString()} word${wordCount !== 1 ? 's' : ''}`;
    }

    if (textarea) textarea.addEventListener("input", updateCounters);

    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
    }

    function handleFileSelection(file) {
        if (!file) {
            resetFileDisplay();
            return;
        }

        const ext = file.name.split('.').pop().toLowerCase();
        if (ext !== 'pdf' && ext !== 'docx' && ext !== 'txt') {
            alert("Invalid file format. Only PDF, DOCX, and TXT files are supported.");
            resetFileDisplay();
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            alert("File is too large. Maximum supported file size is 10MB.");
            resetFileDisplay();
            return;
        }

        if (selectedFileName) selectedFileName.innerText = file.name;
        if (selectedFileSize) selectedFileSize.innerText = `(${formatBytes(file.size)})`;
        if (removeFileBtn) removeFileBtn.style.display = "inline-block";
    }

    function resetFileDisplay() {
        if (fileUploadInput) fileUploadInput.value = "";
        if (selectedFileName) selectedFileName.innerText = "No file selected";
        if (selectedFileSize) selectedFileSize.innerText = "";
        if (removeFileBtn) removeFileBtn.style.display = "none";
    }

    if (fileUploadInput) {
        fileUploadInput.addEventListener("change", (e) => {
            if (e.target.files.length > 0) {
                handleFileSelection(e.target.files[0]);
            }
        });
    }

    if (removeFileBtn) {
        removeFileBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            resetFileDisplay();
        });
    }

    if (dropZone) {
        ["dragenter", "dragover"].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.add("dragover");
            }, false);
        });

        ["dragleave", "drop"].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove("dragover");
            }, false);
        });

        dropZone.addEventListener("drop", (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                fileUploadInput.files = files;
                handleFileSelection(files[0]);
            }
        }, false);
    }

    if (clearBtn) {
        clearBtn.addEventListener("click", () => {
            if (textarea) textarea.value = "";
            updateCounters();
            resetFileDisplay();
        });
    }

    if (analyzeForm) {
        analyzeForm.addEventListener("submit", function(e) {
            const isTextMethod = methodTextRadio && methodTextRadio.checked;
            
            if (isTextMethod) {
                const text = textarea ? textarea.value.trim() : "";
                const wordCount = text === "" ? 0 : text.split(/\s+/).filter(w => w.length > 0).length;
                
                if (wordCount < 5) {
                    e.preventDefault();
                    alert("Please enter a longer text to analyze (minimum 5 words).");
                    return;
                }
            } else {
                if (fileUploadInput && fileUploadInput.files.length === 0) {
                    e.preventDefault();
                    alert("Please select or drop a PDF, DOCX, or TXT file to upload.");
                    return;
                }
            }
            
            if (loaderModal) loaderModal.style.display = "flex";
        });
    }

    // Allow Enter key to submit Q&A
    const qaInput = document.getElementById("qa-question-input");
    if (qaInput) {
        qaInput.addEventListener("keypress", function(e) {
            if (e.key === "Enter") {
                e.preventDefault();
                const btn = document.getElementById("qa-submit-btn");
                if (btn) btn.click();
            }
        });
    }

});
