document.addEventListener("DOMContentLoaded", () => {
    const generatorForm = document.getElementById("generator-form");
    const topicInput = document.getElementById("topic");
    const generateBtn = document.getElementById("generate-btn");
    const trendBtn = document.getElementById("trend-btn");
    
    // View Panels
    const inputView = document.getElementById("input-view");
    const loadingView = document.getElementById("loading-view");
    const resultView = document.getElementById("result-view");
    
    // Loading State elements
    const loadingStatus = document.getElementById("loading-status");
    const stepScript = document.getElementById("step-script");
    const stepVoice = document.getElementById("step-voice");
    const stepStock = document.getElementById("step-stock");
    const stepMerge = document.getElementById("step-merge");
    
    // Result elements
    const videoPreview = document.getElementById("video-preview");
    const downloadBtn = document.getElementById("download-btn");
    const resetBtn = document.getElementById("reset-btn");

    // Campaign Optimizer Elements
    const scoreBadge = document.getElementById("score-badge");
    const metaTitle = document.getElementById("meta-title");
    const metaTags = document.getElementById("meta-tags");
    const metaScript = document.getElementById("meta-script");
    
    // YouTube Uploader UI Elements
    const youtubeSetupGuide = document.getElementById("youtube-setup-guide");
    const youtubeUploadForm = document.getElementById("youtube-upload-form");
    const ytTitle = document.getElementById("yt-title");
    const ytPrivacy = document.getElementById("yt-privacy");
    const ytDesc = document.getElementById("yt-desc");
    const ytUploadBtn = document.getElementById("yt-upload-btn");
    const youtubeUploadProgress = document.getElementById("youtube-upload-progress");
    const ytProgressStatus = document.getElementById("yt-progress-status");
    const ytProgressPercent = document.getElementById("yt-progress-percent");
    const ytProgressFill = document.getElementById("yt-progress-fill");
    const youtubeUploadSuccess = document.getElementById("youtube-upload-success");
    const ytVideoLink = document.getElementById("yt-video-link");
    
    let ytPollInterval = null;
    
    // Timer handles
    let statusInterval = null;
    let stepTimeout1 = null;
    let stepTimeout2 = null;
    let stepTimeout3 = null;

    // Creative status sentences to cycle through
    const statusMessages = [
        "Designing high-retention hook variations...",
        "Evaluating script hooks with scoring engine...",
        "Analyzing topic context with LLaMA 3...",
        "Generating three script variations...",
        "Running viral scorer to pick the best script...",
        "Synthesizing high-quality neural voiceover...",
        "Sourcing vertical portrait video clips...",
        "Generating procedural canvas background...",
        "Formatting subtitles into kinetic captions...",
        "Adding neon yellow uppercase subtitles...",
        "Rendering audio and video sync in MoviePy...",
        "Merging MP4 visual containers...",
        "Exporting production-ready YouTube Short..."
    ];

    // Transition Helper
    function showPanel(panelToShow) {
        [inputView, loadingView, resultView].forEach(panel => {
            panel.classList.remove("active");
        });
        panelToShow.classList.add("active");
    }

    // Set active step in the loading UI
    function setStepState(stepElement, state) {
        stepElement.classList.remove("pending", "current", "completed");
        stepElement.classList.add(state);
    }

    // Displays an error message banner inside the card
    function showErrorMessage(message) {
        const existingError = document.querySelector(".error-banner");
        if (existingError) {
            existingError.remove();
        }

        const errorBanner = document.createElement("div");
        errorBanner.className = "error-banner";
        errorBanner.innerHTML = `
            <i class="fa-solid fa-triangle-exclamation"></i>
            <span>${message}</span>
        `;
        
        const card = document.querySelector(".card-container");
        card.insertBefore(errorBanner, card.firstChild);

        setTimeout(() => {
            errorBanner.style.opacity = '0';
            setTimeout(() => errorBanner.remove(), 400);
        }, 8000);
    }

    // Reset pipeline checklists to pending
    function resetPipelineChecklist() {
        setStepState(stepScript, "pending");
        setStepState(stepVoice, "pending");
        setStepState(stepStock, "pending");
        setStepState(stepMerge, "pending");
    }

    // Fetch and fill trending topic
    trendBtn.addEventListener("click", async () => {
        try {
            trendBtn.disabled = true;
            const originalHTML = trendBtn.innerHTML;
            trendBtn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Sourcing...`;
            
            const response = await fetch("/trend");
            if (response.ok) {
                const data = await response.json();
                if (data && data.topic) {
                    topicInput.value = data.topic;
                    // Trigger dynamic styling if any
                    topicInput.focus();
                }
            }
            trendBtn.innerHTML = originalHTML;
        } catch (error) {
            console.error("Error fetching trend:", error);
        } finally {
            trendBtn.disabled = false;
        }
    });

    // Handle Form submission
    generatorForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const topic = topicInput.value.trim();
        if (!topic) return;

        const existingError = document.querySelector(".error-banner");
        if (existingError) existingError.remove();

        // 1. Enter Loading State
        resetPipelineChecklist();
        showPanel(loadingView);
        setStepState(stepScript, "current");
        loadingStatus.textContent = "Generating 3 viral script variations...";

        // 2. Start progress step timeline simulation
        stepTimeout1 = setTimeout(() => {
            setStepState(stepScript, "completed");
            setStepState(stepVoice, "current");
            loadingStatus.textContent = "Synthesizing natural voiceover...";
        }, 7000); // 7s multi-script

        stepTimeout2 = setTimeout(() => {
            setStepState(stepVoice, "completed");
            setStepState(stepStock, "current");
            loadingStatus.textContent = "Fetching high-retention stock clips...";
        }, 13000); // 6s voice

        stepTimeout3 = setTimeout(() => {
            setStepState(stepStock, "completed");
            setStepState(stepMerge, "current");
            loadingStatus.textContent = "Syncing video streams, captions, and rendering...";
        }, 21000); // 8s stock

        let messageIdx = 0;
        statusInterval = setInterval(() => {
            const activeStep = document.querySelector(".step.current");
            if (activeStep) {
                const stepLabel = activeStep.querySelector(".step-label").textContent;
                loadingStatus.textContent = `${statusMessages[messageIdx]} (${stepLabel.split(" ")[0]})`;
            } else {
                loadingStatus.textContent = statusMessages[messageIdx];
            }
            messageIdx = (messageIdx + 1) % statusMessages.length;
        }, 3000);

        try {
            const response = await fetch("/generate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ topic: topic })
            });

            const data = await response.json();

            clearInterval(statusInterval);
            clearTimeout(stepTimeout1);
            clearTimeout(stepTimeout2);
            clearTimeout(stepTimeout3);

            if (response.ok && data.status === "success") {
                setStepState(stepScript, "completed");
                setStepState(stepVoice, "completed");
                setStepState(stepStock, "completed");
                setStepState(stepMerge, "completed");
                
                setTimeout(() => {
                    const timestamp = new Date().getTime();
                    
                    // Bind video preview player source
                    videoPreview.src = `/download?t=${timestamp}`;
                    videoPreview.load();
                    
                    // Bind download button
                    downloadBtn.href = `/download?t=${timestamp}`;
                    
                    // Bind Campaign Optimizer metadata fields
                    metaTitle.value = data.title || "";
                    metaTags.value = data.hashtags || "";
                    metaScript.value = data.script || "";
                    scoreBadge.textContent = `Viral Index: ${data.score || 0}%`;
                    
                    // Populate YouTube upload form fields
                    ytTitle.value = (data.title || "").substring(0, 100);
                    ytDesc.value = `${data.script || ""}\n\n${data.hashtags || ""}`;
                    
                    // Reset YouTube status views
                    youtubeUploadProgress.style.display = "none";
                    youtubeUploadSuccess.style.display = "none";
                    ytUploadBtn.disabled = false;
                    
                    // Check if credentials exist and update view accordingly
                    checkYoutubeAvailability();
                    
                    showPanel(resultView);
                    
                    videoPreview.play().catch(err => {
                        console.log("Autoplay blocked, waiting for user click.", err);
                    });
                }, 1000);
            } else {
                showPanel(inputView);
                showErrorMessage(data.message || "Failed to generate video. Please try again.");
            }
        } catch (error) {
            console.error("Fetch request error:", error);
            clearInterval(statusInterval);
            clearTimeout(stepTimeout1);
            clearTimeout(stepTimeout2);
            clearTimeout(stepTimeout3);
            
            showPanel(inputView);
            showErrorMessage("Could not connect to the backend server. Make sure Flask is running.");
        }
    });

    // Copy to clipboard actions
    document.querySelectorAll(".copy-action-trigger").forEach(btn => {
        btn.addEventListener("click", async () => {
            const targetId = btn.getAttribute("data-target");
            const targetEl = document.getElementById(targetId);
            if (!targetEl) return;

            try {
                const textToCopy = targetEl.value;
                await navigator.clipboard.writeText(textToCopy);
                
                // Visual feedback checkmark
                btn.classList.add("copied");
                const originalHTML = btn.innerHTML;
                btn.innerHTML = `<i class="fa-solid fa-check"></i> <span>Copied!</span>`;
                
                setTimeout(() => {
                    btn.classList.remove("copied");
                    btn.innerHTML = originalHTML;
                }, 2000);
            } catch (err) {
                console.error("Failed to copy content:", err);
            }
        });
    });

    // Handle create another video
    resetBtn.addEventListener("click", () => {
        topicInput.value = "";
        videoPreview.pause();
        videoPreview.src = "";
        
        // Reset optimizer fields
        metaTitle.value = "";
        metaTags.value = "";
        metaScript.value = "";
        scoreBadge.textContent = "Viral Index: 0%";
        
        // Reset YouTube fields and states
        ytTitle.value = "";
        ytDesc.value = "";
        youtubeUploadProgress.style.display = "none";
        youtubeUploadSuccess.style.display = "none";
        if (ytPollInterval) {
            clearInterval(ytPollInterval);
            ytPollInterval = null;
        }
        
        showPanel(inputView);
    });

    async function checkYoutubeAvailability() {
        try {
            const response = await fetch("/upload_status");
            if (response.ok) {
                const data = await response.json();
                if (data.client_secrets_exist) {
                    youtubeSetupGuide.style.display = "none";
                    youtubeUploadForm.style.display = "grid";
                } else {
                    youtubeSetupGuide.style.display = "block";
                    youtubeUploadForm.style.display = "none";
                }
            }
        } catch (error) {
            console.error("Error checking YouTube capability:", error);
        }
    }

    ytUploadBtn.addEventListener("click", async () => {
        const title = ytTitle.value.trim();
        const description = ytDesc.value.trim();
        const privacy = ytPrivacy.value;
        
        if (!title) {
            alert("Please provide a title for the YouTube upload.");
            return;
        }
        
        ytUploadBtn.disabled = true;
        youtubeUploadProgress.style.display = "block";
        youtubeUploadSuccess.style.display = "none";
        
        ytProgressStatus.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Initializing upload stream...`;
        ytProgressPercent.textContent = "0%";
        ytProgressFill.style.width = "0%";
        
        try {
            const response = await fetch("/upload_youtube", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    title: title,
                    description: description,
                    privacy: privacy,
                    tags: metaTags.value
                })
            });
            
            const data = await response.json();
            if (response.ok && data.status === "success") {
                if (ytPollInterval) clearInterval(ytPollInterval);
                ytPollInterval = setInterval(pollUploadStatus, 1500);
            } else {
                ytProgressStatus.innerHTML = `<span style="color: var(--system-rose-alert);"><i class="fa-solid fa-triangle-exclamation"></i> ${data.message || "Failed to start upload."}</span>`;
                ytUploadBtn.disabled = false;
            }
        } catch (error) {
            console.error("YouTube upload initiation failed:", error);
            ytProgressStatus.innerHTML = `<span style="color: var(--system-rose-alert);"><i class="fa-solid fa-triangle-exclamation"></i> Could not connect to server.</span>`;
            ytUploadBtn.disabled = false;
        }
    });

    async function pollUploadStatus() {
        try {
            const response = await fetch("/upload_status");
            if (!response.ok) return;
            
            const data = await response.json();
            
            if (data.status === "authenticating") {
                ytProgressStatus.innerHTML = `<i class="fa-solid fa-key fa-bounce" style="color: #fca5a5;"></i> Authentication required! Sign in using the browser pop-up.`;
                ytProgressPercent.textContent = "0%";
                ytProgressFill.style.width = "0%";
            } else if (data.status === "uploading") {
                const progress = data.progress || 0;
                ytProgressStatus.innerHTML = `<i class="fa-solid fa-cloud-arrow-up fa-fade"></i> ${data.message || "Uploading chunks..."}`;
                ytProgressPercent.textContent = `${progress}%`;
                ytProgressFill.style.width = `${progress}%`;
            } else if (data.status === "success") {
                clearInterval(ytPollInterval);
                youtubeUploadProgress.style.display = "none";
                youtubeUploadSuccess.style.display = "flex";
                ytVideoLink.href = `https://studio.youtube.com/video/${data.video_id}/edit`;
            } else if (data.status === "error") {
                clearInterval(ytPollInterval);
                ytProgressStatus.innerHTML = `<span style="color: var(--system-rose-alert);"><i class="fa-solid fa-circle-exclamation"></i> ${data.message || "Upload failed."}</span>`;
                ytUploadBtn.disabled = false;
            }
        } catch (error) {
            console.error("Polling error:", error);
        }
    }
});
