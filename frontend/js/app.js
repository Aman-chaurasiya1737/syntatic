// Auto-detect backend URL: empty when served by Flask, full URL otherwise
window.API_BASE = window.location.port === '5000' ? '' : 'http://localhost:5000';

window.AppState = {
    name: '',
    domain: '',
    difficulty: '',
    companyMode: '',
    resumeFile: null,
    resumeText: '',
    extractedInfo: null,
    round1: {
        question: null,
        code: '',
        score: null,
        remarks: '',
        details: null
    },
    round2: {
        questions: [],
        overallScore: 0,
        overallRemarks: '',
        strengths: '',
        improvements: ''
    },
    currentView: 'home'
};

window.App = {

    init() {
        this.injectSVGGradient();
        this.setupHomeEvents();
        this.setupProctoring();
        // Delay history render until auth check finishes
        if (window.Auth) {
            window.Auth.init();
        } else {
            console.warn("Auth script not loaded.");
            HistoryManager.renderHistory();
        }
        console.log('Syntatic initialized');
    },

    injectSVGGradient() {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '0');
        svg.setAttribute('height', '0');
        svg.style.position = 'absolute';
        svg.innerHTML = `
            <defs>
                <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#0ea5e9;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#06b6d4;stop-opacity:1" />
                </linearGradient>
                <linearGradient id="scoreGradientGreen" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#22c55e;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#06b6d4;stop-opacity:1" />
                </linearGradient>
                <linearGradient id="scoreGradientGold" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#f59e0b;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#ef4444;stop-opacity:1" />
                </linearGradient>
            </defs>
        `;
        document.body.appendChild(svg);
    },

    setupHomeEvents() {
        const form = document.getElementById('interview-form');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.startInterview();
        });

        const uploadArea = document.getElementById('file-upload-area');
        const fileInput = document.getElementById('resume-upload');

        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = 'var(--accent-blue)';
            uploadArea.style.background = 'rgba(59,130,246,0.05)';
        });
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.style.borderColor = '';
            uploadArea.style.background = '';
        });
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '';
            uploadArea.style.background = '';
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                this.handleResumeUpload(e.dataTransfer.files[0]);
            }
        });
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleResumeUpload(e.target.files[0]);
            }
        });

        document.getElementById('remove-resume').addEventListener('click', (e) => {
            e.stopPropagation();
            fileInput.value = '';
            window.AppState.resumeFile = null;
            window.AppState.resumeText = '';
            window.AppState.extractedInfo = null;
            document.getElementById('upload-placeholder').classList.remove('hidden');
            document.getElementById('upload-success').classList.add('hidden');
        });

        document.getElementById('continue-to-round2-btn').addEventListener('click', async () => {
            try {
                await document.documentElement.requestFullscreen();
            } catch (err) {
                console.log("Fullscreen request denied or not supported:", err);
            }
            this.switchView('round2');
            Round2.init();
        });

        document.getElementById('view-final-results-btn').addEventListener('click', () => {
            this.showFinalResults();
        });

        document.getElementById('back-to-home-btn').addEventListener('click', () => {
            this.goHome();
        });
    },

    goHome() {
        this.resetState();
        this.switchView('home');
        if (typeof HistoryManager !== 'undefined') {
            HistoryManager.renderHistory();
        }
    },

    handleResumeUpload(file) {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            alert('Please upload a PDF file.');
            return;
        }

        window.AppState.resumeFile = file;
        window.AppState.resumeText = '';
        window.AppState.extractedInfo = null;

        document.getElementById('upload-placeholder').classList.add('hidden');
        document.getElementById('upload-success').classList.remove('hidden');
        document.getElementById('uploaded-filename').textContent = file.name;
    },


    async startInterview() {
        let domain = document.getElementById('domain-select').value;
        let difficulty = document.getElementById('difficulty-select').value;
        let companyMode = document.getElementById('company-select').value;

        if (window.AppState.resumeFile && !window.AppState.extractedInfo) {
            this.showLoading('Analyzing Resume & Configuring Interview...');
            
            const formData = new FormData();
            formData.append('file', window.AppState.resumeFile);
            
            try {
                const response = await fetch(window.API_BASE + '/api/parse-resume', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                
                if (result.text) {
                    window.AppState.resumeText = result.text;
                    if (result.info) {
                        window.AppState.extractedInfo = result.info;
                    }
                } else {
                    this.hideLoading();
                    alert("Analysis failed: " + (result.error || "Unknown error"));
                    return;
                }
            } catch (error) {
                console.error('Error parsing resume:', error);
                this.hideLoading();
                alert("Upload failed. Please try again or select manually.");
                return;
            }
        }

        if (window.AppState.extractedInfo) {
            domain = window.AppState.extractedInfo.domain || domain;
            difficulty = window.AppState.extractedInfo.difficulty || difficulty;
            companyMode = window.AppState.extractedInfo.company || companyMode;
        }

        if (!domain || !difficulty || !companyMode) {
            this.hideLoading();
            alert('Please select Tech Domain, Difficulty, and Company OR upload a Resume PDF to extract them automatically.');
            return;
        }

        window.AppState.domain = domain;
        window.AppState.difficulty = difficulty;
        window.AppState.companyMode = companyMode;
        window.AppState.cheatWarnings = 0; // Reset just in case

        this.showLoading('Loading your coding challenge...');

        try {
            document.documentElement.requestFullscreen().catch(err => {
                console.warn(`Fullscreen error: ${err.message}`);
            });
        } catch (e) {}

        this.switchView('round1');
        await Round1.init();

        this.hideLoading();
    },

    showRound1Results(result) {
        const score = result.score || 0;
        this.animateScoreCircle('r1-score-circle', 'r1-score-value', score);

        document.getElementById('r1-correctness').textContent = result.correctness || 'N/A';
        document.getElementById('r1-time-complexity').textContent = result.time_complexity || 'N/A';
        document.getElementById('r1-space-complexity').textContent = result.space_complexity || 'N/A';
        document.getElementById('r1-code-quality').textContent = result.code_quality || 'N/A';
        document.getElementById('r1-suggestions').textContent = result.suggestions || 'N/A';

        document.getElementById('r1-remarks').innerHTML = `
            <i class="fas fa-comment-dots"></i>
            <p>${this._escapeHtml(result.remarks || 'No remarks available.')}</p>
        `;

        this.switchView('round1-results');
    },

    showRound2Results(result) {
        const state = window.AppState;

        this.animateScoreCircle('r2-score-circle', 'r2-score-value', result.overall_score || 0);

        const pqContainer = document.getElementById('per-question-results');
        pqContainer.innerHTML = (result.per_question || []).map((pq, i) => {
            const scoreClass = pq.score >= 7 ? 'score-good' : pq.score >= 5 ? 'score-ok' : 'score-low';
            const qa = state.round2.questions[i] || {};
            return `
                <div class="pq-item">
                    <div class="pq-header">
                        <span class="pq-label">Question ${i + 1}</span>
                        <span class="pq-score ${scoreClass}">${pq.score}/10</span>
                    </div>
                    <p class="pq-question">"${this._escapeHtml(qa.question || '')}"</p>
                    <p class="pq-remarks">${this._escapeHtml(pq.remarks || '')}</p>
                </div>
            `;
        }).join('');

        document.getElementById('r2-strengths').textContent = result.strengths || 'N/A';
        document.getElementById('r2-improvements').textContent = result.improvements || 'N/A';

        document.getElementById('r2-remarks').innerHTML = `
            <i class="fas fa-comment-dots"></i>
            <p>${this._escapeHtml(result.overall_remarks || 'No remarks available.')}</p>
        `;

        this.switchView('round2-results');
    },

    async showFinalResults() {
        const state = window.AppState;
        const r1Score = state.round1.score || 0;
        const r2Score = state.round2.overallScore || 0;
        const totalScore = parseFloat(((r1Score + r2Score) / 2).toFixed(1));

        this.switchView('final-results');

        document.getElementById('final-candidate-name').textContent = `Great job, ${state.name}!`;

        setTimeout(() => {
            this.animateScoreCircle('final-r1-circle', 'final-r1-score', r1Score);
            this.animateScoreCircle('final-r2-circle', 'final-r2-score', r2Score);
            this.animateScoreCircle('final-total-circle', 'final-total-score', totalScore);
        }, 300);

        this.launchConfetti();

        await HistoryManager.saveResult({
            name: state.name,
            domain: state.domain,
            difficulty: state.difficulty,
            companyMode: state.companyMode,
            round1: {
                question: JSON.stringify(state.round1.question),
                score: r1Score,
                remarks: state.round1.remarks,
                code: state.round1.code
            },
            round2: {
                questions: state.round2.questions,
                overallScore: r2Score,
                overallRemarks: state.round2.overallRemarks
            },
            totalScore: totalScore
        });

        // Pre-load history so dashboard is ready when user goes home
        HistoryManager.renderHistory();
    },

    animateScoreCircle(circleId, valueId, score) {
        const circle = document.getElementById(circleId);
        const valueEl = document.getElementById(valueId);
        if (!circle || !valueEl) return;

        const circumference = 2 * Math.PI * 54;
        const offset = circumference - (score / 10) * circumference;

        if (score >= 7) {
            circle.style.stroke = 'url(#scoreGradientGreen)';
        } else if (score >= 5) {
            circle.style.stroke = 'url(#scoreGradient)';
        } else {
            circle.style.stroke = 'url(#scoreGradientGold)';
        }

        circle.style.strokeDasharray = circumference;
        circle.style.strokeDashoffset = circumference;

        setTimeout(() => {
            circle.style.transition = 'stroke-dashoffset 1.5s ease';
            circle.style.strokeDashoffset = offset;
        }, 100);

        this.animateNumber(valueEl, 0, score, 1500);
    },

    animateNumber(el, from, to, duration) {
        const start = performance.now();
        const update = (now) => {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = from + (to - from) * eased;
            el.textContent = Number.isInteger(to) ? Math.round(current) : current.toFixed(1);
            if (progress < 1) requestAnimationFrame(update);
        };
        requestAnimationFrame(update);
    },

    launchConfetti() {
        const container = document.getElementById('confetti-container');
        if (!container) return;
        container.innerHTML = '';

        const colors = ['#0ea5e9', '#06b6d4', '#14b8a6', '#38bdf8', '#0284c7', '#10b981', '#67e8f9'];

        for (let i = 0; i < 50; i++) {
            const piece = document.createElement('div');
            piece.className = 'confetti-piece';
            piece.style.left = Math.random() * 100 + '%';
            piece.style.background = colors[Math.floor(Math.random() * colors.length)];
            piece.style.animationDelay = Math.random() * 2 + 's';
            piece.style.animationDuration = (2 + Math.random() * 2) + 's';

            if (Math.random() > 0.5) {
                piece.style.borderRadius = '50%';
            }

            container.appendChild(piece);
        }
    },

    switchView(viewName) {
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));

        const viewId = viewName === 'home' ? 'home-view' :
            viewName === 'auth' ? 'auth-view' :
            viewName === 'round1' ? 'round1-view' :
                viewName === 'round1-results' ? 'round1-results-view' :
                    viewName === 'round2' ? 'round2-view' :
                        viewName === 'round2-results' ? 'round2-results-view' :
                            viewName === 'final-results' ? 'final-results-view' :
                                'home-view';

        const view = document.getElementById(viewId);
        if (view) {
            view.classList.add('active');
            window.scrollTo(0, 0);
        }

        window.AppState.currentView = viewName;
    },

    setupProctoring() {
        window.AppState.cheatWarnings = 0;
        
        const interviewViews = ['round1', 'round1-results', 'round2', 'round2-results', 'final-results'];

        document.addEventListener('visibilitychange', () => {
            if (interviewViews.includes(window.AppState.currentView)) {
                if (document.visibilityState === 'hidden') {
                    this.handleCheatViolation();
                } else if (document.visibilityState === 'visible') {
                    // Auto re-enter fullscreen when the user comes back to this tab
                    if (!document.fullscreenElement) {
                        try {
                            document.documentElement.requestFullscreen().catch(() => {});
                        } catch (e) {}
                    }
                }
            }
        });

        // Fallback: also re-enter fullscreen on click in case the automatic attempt was blocked
        document.addEventListener('click', () => {
            if (interviewViews.includes(window.AppState.currentView)) {
                if (!document.fullscreenElement) {
                    try {
                        document.documentElement.requestFullscreen().catch(() => {});
                    } catch (e) {}
                }
            }
        });

        const closeBtn = document.getElementById('close-cheat-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                document.getElementById('cheat-modal').classList.add('hidden');
            });
        }

        const goHomeBtn = document.getElementById('cheat-go-home-btn');
        if (goHomeBtn) {
            goHomeBtn.addEventListener('click', () => {
                document.getElementById('cheat-modal').classList.add('hidden');
                this.goHome();
            });
        }
    },

    async handleCheatViolation() {
        window.AppState.cheatWarnings = (window.AppState.cheatWarnings || 0) + 1;
        
        if (window.AppState.cheatWarnings < 3) {
            this.showToast(`Warning ${window.AppState.cheatWarnings}/3: You tried to cheat in the interview. Do not switch tabs.`, 'error');
        } else {
            // 3rd violation — terminate interview, calculate & save results
            if (document.fullscreenElement) {
                document.exitFullscreen().catch(err => console.log(err));
            }

            const state = window.AppState;
            const r1Score = state.round1.score || 0;
            const r2Score = state.round2.overallScore || 0;
            const totalScore = parseFloat(((r1Score + r2Score) / 2).toFixed(1));

            // Save partial results to history
            try {
                await HistoryManager.saveResult({
                    name: state.name,
                    domain: state.domain,
                    difficulty: state.difficulty,
                    companyMode: state.companyMode,
                    round1: {
                        question: JSON.stringify(state.round1.question),
                        score: r1Score,
                        remarks: state.round1.remarks || 'Interview terminated — tab switching detected.',
                        code: state.round1.code
                    },
                    round2: {
                        questions: state.round2.questions,
                        overallScore: r2Score,
                        overallRemarks: state.round2.overallRemarks || 'Interview terminated — tab switching detected.'
                    },
                    totalScore: totalScore,
                    terminated: true
                });
            } catch (e) {
                console.error('Failed to save terminated interview result:', e);
            }

            // Update cheat modal with scores
            const scoresDiv = document.getElementById('cheat-modal-scores');
            if (scoresDiv) {
                document.getElementById('cheat-r1-score').textContent = r1Score + '/10';
                document.getElementById('cheat-r2-score').textContent = r2Score + '/10';
                document.getElementById('cheat-total-score').textContent = totalScore + '/10';
                scoresDiv.style.display = 'block';
            }

            // Clean up interview state
            Round1.cleanup();
            Round2.cleanup();
            this.switchView('home');

            // Refresh history dashboard after terminated save
            HistoryManager.renderHistory();

            const modal = document.getElementById('cheat-modal');
            if (modal) modal.classList.remove('hidden');
            window.AppState.cheatWarnings = 0;
        }
    },

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icon = type === 'error' ? '<i class="fas fa-exclamation-triangle"></i>' : '<i class="fas fa-info-circle"></i>';
        
        toast.innerHTML = `
            ${icon}
            <span>${message}</span>
        `;
        
        container.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Remove after 4 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    },

    showLoading(message) {
        document.getElementById('loading-text').textContent = message || 'Loading...';
        document.getElementById('loading-overlay').classList.remove('hidden');
    },

    hideLoading() {
        document.getElementById('loading-overlay').classList.add('hidden');
    },

    goHome() {
        this.resetState();
        this.switchView('home');
        if (window.HistoryManager && window.firebase && window.firebase.auth().currentUser) {
            window.HistoryManager.renderHistory();
        }
    },

    resetState() {
        Round1.cleanup();
        Round2.cleanup();

        window.AppState = {
            name: '',
            domain: '',
            difficulty: '',
            companyMode: '',
            resumeFile: null,
            resumeText: '',
            extractedInfo: null,
            cheatWarnings: 0,
            round1: { question: null, code: '', score: null, remarks: '', details: null },
            round2: { questions: [], overallScore: 0, overallRemarks: '', strengths: '', improvements: '' },
            currentView: 'home'
        };

        document.getElementById('interview-form').reset();
        document.getElementById('upload-placeholder').classList.remove('hidden');
        document.getElementById('upload-success').classList.add('hidden');
    },

    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

document.addEventListener('DOMContentLoaded', () => {
    window.App.init();
});
