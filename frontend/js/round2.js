window.Round2 = {
    stream: null,
    recognition: null,
    mediaRecorder: null,
    audioChunks: [],
    eyeTrackingInterval: null,
    currentQuestionIndex: 0,
    questions: [],
    answers: [],
    isRecording: false,
    useServerTranscription: false,
    warningCount: 0,
    canvas: null,

    async init() {
        this.currentQuestionIndex = 0;
        this.questions = [];
        this.answers = [];
        this.warningCount = 0;
        this.useServerTranscription = false;

        document.getElementById('start-answer-btn').addEventListener('click', () => this.toggleRecording());
        document.getElementById('submit-answer-btn').addEventListener('click', () => this.submitAnswer());
        document.getElementById('replay-question-btn').addEventListener('click', () => this.replayQuestion());

        await this.setupMedia();

        await this.loadQuestions();

        this.startEyeTracking();
    },

    async setupMedia() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480, facingMode: 'user' },
                audio: true
            });

            const videoEl = document.getElementById('webcam-feed');
            videoEl.srcObject = this.stream;
            document.getElementById('video-overlay').classList.add('hidden');

            this.canvas = document.getElementById('eye-canvas');
            this.canvas.width = 640;
            this.canvas.height = 480;

            this.setupSpeechRecognition();

            document.getElementById('mic-status').innerHTML = '<i class="fas fa-microphone"></i><span>Microphone Ready</span>';

        } catch (error) {
            console.error('Media access error:', error);
            document.getElementById('video-overlay').innerHTML =
                '<i class="fas fa-exclamation-triangle" style="color: var(--accent-red)"></i>' +
                '<p style="color: var(--accent-red)">Camera/Mic access denied</p>' +
                '<p style="font-size:0.8rem; margin-top:8px;">Please allow camera and microphone access to proceed.</p>';
        }
    },

    setupSpeechRecognition() {
        this._setupMediaRecorder();

        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            this._SpeechRecognition = SpeechRecognition;
            this._initWebSpeechRecognition();
        } else {
            console.warn('Web Speech API not available, using server transcription');
            this.useServerTranscription = true;
        }
    },

    _setupMediaRecorder() {
        if (!this.stream) return;

        var audioTracks = this.stream.getAudioTracks();
        if (audioTracks.length === 0) return;

        var audioStream = new MediaStream(audioTracks);

        var mimeTypes = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4'];
        var selectedMime = '';
        for (var i = 0; i < mimeTypes.length; i++) {
            if (MediaRecorder.isTypeSupported(mimeTypes[i])) {
                selectedMime = mimeTypes[i];
                break;
            }
        }

        try {
            this.mediaRecorder = new MediaRecorder(audioStream, selectedMime ? { mimeType: selectedMime } : {});
            this._recorderMimeType = this.mediaRecorder.mimeType || 'audio/webm';
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            console.log('MediaRecorder ready with mime:', this._recorderMimeType);
        } catch (e) {
            console.warn('MediaRecorder setup failed:', e);
            this.mediaRecorder = null;
        }
    },

    _initWebSpeechRecognition() {
        var SpeechRecognition = this._SpeechRecognition;
        if (!SpeechRecognition) return;

        if (this.recognition) {
            try { this.recognition.abort(); } catch (e) { }
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
        this.recognition.maxAlternatives = 1;

        var finalTranscript = '';
        var networkErrors = 0;
        var self = this;

        this.recognition.onresult = function (event) {
            networkErrors = 0;
            var interim = '';
            for (var i = event.resultIndex; i < event.results.length; i++) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript + ' ';
                } else {
                    interim += event.results[i][0].transcript;
                }
            }
            var ta = document.getElementById('answer-textarea');
            if (ta) {
                ta.value = finalTranscript + interim;
                ta.style.height = 'auto';
                ta.style.height = ta.scrollHeight + 'px';
                document.getElementById('submit-answer-btn').disabled = false;
            }
        };

        this.recognition.onerror = function (event) {
            console.warn('Web Speech API error:', event.error);

            if (event.error === 'no-speech') {
                if (self.isRecording) {
                    setTimeout(function () { try { self.recognition.start(); } catch (e) { } }, 100);
                }
            } else if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
                console.warn('Mic permission denied for Web Speech API');
                self.recognition = null;
                self.useServerTranscription = true;
            } else if (event.error === 'network' || event.error === 'audio-capture' || event.error === 'aborted') {
                networkErrors++;
                if (networkErrors >= 2) {
                    console.log('Web Speech API failed, switching to server transcription');
                    self.useServerTranscription = true;
                    self.recognition = null;
                    if (self.isRecording) {
                        document.getElementById('mic-status').innerHTML =
                            '<i class="fas fa-microphone"></i><span>Recording...</span>';
                    }
                } else if (self.isRecording) {
                    setTimeout(function () { try { self.recognition.start(); } catch (e) { } }, 500);
                }
            }
        };

        this.recognition.onend = function () {
            if (self.isRecording && !self.useServerTranscription) {
                console.log('Web Speech API ended, restarting...');
                try {
                    self.recognition.start();
                } catch (e) {
                    console.log('Restart failed:', e);
                }
            }
        };

        this._getWebSpeechTranscript = function () { return finalTranscript; };
        this._resetWebSpeechTranscript = function () { finalTranscript = ''; };
    },

    async _transcribeViaServer() {
        if (this.audioChunks.length === 0) return '';

        var audioBlob = new Blob(this.audioChunks, { type: this._recorderMimeType || 'audio/webm' });

        document.getElementById('mic-status').innerHTML =
            '<i class="fas fa-spinner fa-spin"></i><span>Transcribing...</span>';

        var notice = document.getElementById('transcribing-notice');
        if (notice) {
            notice.innerHTML = '<i class="fas fa-spinner fa-spin" style="margin-right:6px;"></i>Transcribing your speech...';
            notice.classList.remove('hidden');
        }

        try {
            var base64Audio = await this._blobToBase64(audioBlob);

            var response = await fetch(window.API_BASE + '/api/transcribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    audio: base64Audio,
                    mime_type: this._recorderMimeType || 'audio/webm'
                })
            });

            var data = await response.json();
            var text = (data.text || '').trim();

            if (notice) notice.classList.add('hidden');

            if (text) {
                var ta = document.getElementById('answer-textarea');
                if (ta) {
                    var existing = ta.value.trim();
                    ta.value = existing ? existing + ' ' + text : text;
                    ta.style.height = 'auto';
                    ta.style.height = ta.scrollHeight + 'px';
                    document.getElementById('submit-answer-btn').disabled = false;
                }
            } else {
                if (notice) {
                    notice.innerHTML = '<i class="fas fa-info-circle" style="margin-right:6px; color: var(--accent-amber);"></i>No speech detected. You can type your answer or try recording again.';
                    notice.classList.remove('hidden');
                    setTimeout(function () { notice.classList.add('hidden'); }, 4000);
                }
            }

            document.getElementById('mic-status').innerHTML =
                '<i class="fas fa-microphone"></i><span>Microphone Ready</span>';
            return text;
        } catch (error) {
            console.error('Server transcription error:', error);
            if (notice) {
                notice.innerHTML = '<i class="fas fa-exclamation-triangle" style="margin-right:6px; color: var(--accent-red);"></i>Transcription failed. Please type your answer.';
                notice.classList.remove('hidden');
                setTimeout(function () { notice.classList.add('hidden'); }, 4000);
            }
            document.getElementById('mic-status').innerHTML =
                '<i class="fas fa-microphone"></i><span>Microphone Ready</span>';
            return '';
        }
    },

    _blobToBase64(blob) {
        return new Promise(function (resolve, reject) {
            var reader = new FileReader();
            reader.onloadend = function () {
                var base64 = reader.result.split(',')[1];
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    },

    async loadQuestions() {
        var state = window.AppState;

        try {
            // Fetch pre-generated sessions from Firebase for the selected company
            const companyId = state.companyMode ? state.companyMode.toUpperCase() : '';
            const doc = await db.collection('interview_sessions').doc(companyId).get();
            
            if (!doc.exists) {
                throw new Error('No interview sessions found for ' + state.companyMode);
            }
            
            const data = doc.data();
            const allSessions = data.sessions || [];
            
            if (allSessions.length === 0) {
                throw new Error('Interview sessions are empty for ' + state.companyMode);
            }
            
            // Flatten all questions from all sessions
            let allQuestions = [];
            allSessions.forEach(session => {
                allQuestions = allQuestions.concat(session.questions || []);
            });

            // Deduplicate questions by their exact text to remove the repetitive static seed questions
            const uniqueQuestionsMap = new Map();
            allQuestions.forEach(q => {
                if (q && q.question) {
                    uniqueQuestionsMap.set(q.question, q);
                }
            });
            
            let uniqueQuestions = Array.from(uniqueQuestionsMap.values());
            
            // Shuffle the unique questions
            for (let i = uniqueQuestions.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [uniqueQuestions[i], uniqueQuestions[j]] = [uniqueQuestions[j], uniqueQuestions[i]];
            }

            // Pick 5 truly random questions for the interview
            this.questions = uniqueQuestions.slice(0, 5);

            if (this.questions.length > 0) {
                this.presentQuestion(0);
            }
        } catch (error) {
            console.error('Error loading interview questions:', error);
            document.getElementById('current-question-text').textContent =
                'Error loading questions. Please ensure the backend is running and Firebase is seeded.';
        }
    },

    async presentQuestion(index) {
        if (index >= this.questions.length) return;

        this.currentQuestionIndex = index;
        var question = this.questions[index];

        document.getElementById('current-question-text').textContent = question.question;
        document.getElementById('r2-progress-text').textContent = 'Question ' + (index + 1) + ' of ' + this.questions.length;
        document.getElementById('r2-progress-fill').style.width = (((index + 1) / this.questions.length) * 100) + '%';

        this._showAnswerArea();

        document.getElementById('submit-answer-btn').disabled = true;
        document.getElementById('start-answer-btn').innerHTML = '<i class="fas fa-microphone"></i> Start Answering';
        document.getElementById('start-answer-btn').classList.add('btn-success');
        document.getElementById('start-answer-btn').classList.remove('btn-outline');
        document.getElementById('start-answer-btn').style.borderColor = '';
        document.getElementById('start-answer-btn').style.color = '';
        this.isRecording = false;

        await this.speakQuestion(question.question);
    },

    _showAnswerArea() {
        var answerEl = document.getElementById('answer-text');
        answerEl.innerHTML =
            '<div id="transcribing-notice" class="transcribing-notice hidden"></div>' +
            '<textarea id="answer-textarea" class="answer-textarea" rows="4" ' +
            'placeholder="Click Start Answering to record, or just type here..."></textarea>';

        setTimeout(function () {
            var ta = document.getElementById('answer-textarea');
            if (ta) {
                ta.addEventListener('input', function () {
                    document.getElementById('submit-answer-btn').disabled = !ta.value.trim();
                    ta.style.height = 'auto';
                    ta.style.height = ta.scrollHeight + 'px';
                });
            }
        }, 30);
    },

    async speakQuestion(text) {
        try {
            var response = await fetch(window.API_BASE + '/api/tts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });

            if (response.ok) {
                var blob = await response.blob();
                var audioUrl = URL.createObjectURL(blob);
                var audio = new Audio(audioUrl);
                audio.play();
            } else {
                throw new Error('Server TTS failed with status ' + response.status);
            }
        } catch (error) {
            console.error('TTS error:', error);
            if ('speechSynthesis' in window) {
                var utterance = new SpeechSynthesisUtterance(text);
                utterance.rate = 0.9;
                speechSynthesis.speak(utterance);
            }
        }
    },

    toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            this.startRecording();
        }
    },

    startRecording() {
        this.isRecording = true;
        this.audioChunks = [];
        if (this._resetWebSpeechTranscript) this._resetWebSpeechTranscript();

        if (this.mediaRecorder && this.mediaRecorder.state === 'inactive') {
            try { this.mediaRecorder.start(1000); } catch (e) { console.warn('MediaRecorder start error:', e); }
        }

        if (this.recognition && !this.useServerTranscription) {
            try { this.recognition.start(); } catch (e) { }
        }

        document.getElementById('start-answer-btn').innerHTML = '<i class="fas fa-stop"></i> Stop Recording';
        document.getElementById('start-answer-btn').classList.remove('btn-success');
        document.getElementById('start-answer-btn').classList.add('btn-outline');
        document.getElementById('start-answer-btn').style.borderColor = 'var(--accent-red)';
        document.getElementById('start-answer-btn').style.color = 'var(--accent-red)';
        document.getElementById('recording-indicator').classList.remove('hidden');
        document.getElementById('mic-status').classList.add('recording');
        document.getElementById('mic-status').innerHTML = '<i class="fas fa-microphone"></i><span>Recording...</span>';

        var ta = document.getElementById('answer-textarea');
        if (ta) {
            ta.placeholder = this.useServerTranscription
                ? 'Recording... Speak your answer. It will be transcribed when you stop. You can also type here.'
                : 'Listening... Speak your answer (or type here)...';
        }
    },

    async stopRecording() {
        this.isRecording = false;

        if (this.recognition) {
            try { this.recognition.stop(); } catch (e) { }
        }

        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
            await new Promise(function (resolve) {
                this.mediaRecorder.onstop = resolve;
                setTimeout(resolve, 500);
            }.bind(this));
        }

        document.getElementById('recording-indicator').classList.add('hidden');
        document.getElementById('mic-status').classList.remove('recording');

        var ta = document.getElementById('answer-textarea');
        var hasWebSpeechText = ta && ta.value.trim().length > 0;

        if ((this.useServerTranscription || !hasWebSpeechText) && this.audioChunks.length > 0) {
            await this._transcribeViaServer();
        }

        document.getElementById('start-answer-btn').innerHTML = '<i class="fas fa-microphone"></i> Start Answering';
        document.getElementById('start-answer-btn').classList.add('btn-success');
        document.getElementById('start-answer-btn').classList.remove('btn-outline');
        document.getElementById('start-answer-btn').style.borderColor = '';
        document.getElementById('start-answer-btn').style.color = '';
        document.getElementById('mic-status').innerHTML =
            '<i class="fas fa-microphone"></i><span>Microphone Ready</span>';

        if (ta && ta.value.trim()) {
            document.getElementById('submit-answer-btn').disabled = false;
        }

        if (ta) {
            ta.placeholder = 'Click "Start Answering" to record, or just type here...';
        }
    },

    async submitAnswer() {
        if (this.isRecording) {
            await this.stopRecording();
        }

        var ta = document.getElementById('answer-textarea');
        var answerText = ta ? ta.value.trim() : '';

        if (!answerText) {
            alert('Please record or type your answer before submitting.');
            return;
        }

        this.answers.push({
            question: this.questions[this.currentQuestionIndex].question,
            answer: answerText
        });

        var nextIndex = this.currentQuestionIndex + 1;

        if (nextIndex < this.questions.length) {
            await this.presentQuestion(nextIndex);
        } else {
            await this.evaluateInterview();
        }
    },

    async evaluateInterview() {
        this.stopEyeTracking();
        this.stopMedia();

        window.App.showLoading('Evaluating your interview performance...');

        var state = window.AppState;

        try {
            var response = await fetch(window.API_BASE + '/api/evaluate-interview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    questions_answers: this.answers,
                    domain: state.domain
                })
            });

            var result = await response.json();

            state.round2.questions = this.answers.map(function (qa, i) {
                return {
                    question: qa.question,
                    answer: qa.answer,
                    score: result.per_question && result.per_question[i] ? result.per_question[i].score : 0,
                    remarks: result.per_question && result.per_question[i] ? result.per_question[i].remarks : ''
                };
            });
            state.round2.overallScore = result.overall_score || 0;
            state.round2.overallRemarks = result.overall_remarks || '';
            state.round2.strengths = result.strengths || '';
            state.round2.improvements = result.improvements || '';

            window.App.hideLoading();
            window.App.showRound2Results(result);

        } catch (error) {
            console.error('Error evaluating interview:', error);
            window.App.hideLoading();
            alert('Error connecting to server. Please ensure the backend is running.');
        }
    },

    async replayQuestion() {
        if (this.questions[this.currentQuestionIndex]) {
            await this.speakQuestion(this.questions[this.currentQuestionIndex].question);
        }
    },

    startEyeTracking() {
        var videoEl = document.getElementById('webcam-feed');
        var canvas = this.canvas;
        var ctx = canvas ? canvas.getContext('2d') : null;
        var self = this;

        if (!ctx) return;

        this.eyeTrackingInterval = setInterval(async function () {
            if (!self.stream) return;

            try {
                ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);
                var imageData = canvas.toDataURL('image/jpeg', 0.7);

                var response = await fetch(window.API_BASE + '/api/analyze-eyes', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image: imageData })
                });

                var result = await response.json();
                var eyeStatusEl = document.getElementById('eye-status');
                var warningOverlay = document.getElementById('eye-warning-overlay');
                var warningIcon = document.getElementById('eye-warning-icon');
                var warningText = document.getElementById('eye-warning-text');

                if (result.looking_at_screen) {
                    eyeStatusEl.classList.remove('warning');
                    eyeStatusEl.innerHTML = '<i class="fas fa-eye"></i> <span>Tracking</span>';
                    if (warningOverlay) warningOverlay.classList.add('hidden');
                } else {
                    eyeStatusEl.classList.add('warning');
                    self.warningCount++;

                    // Set icon and status text based on warning type
                    var wType = result.warning_type || 'not_focused';
                    if (wType === 'no_face') {
                        eyeStatusEl.innerHTML = '<i class="fas fa-user-slash"></i> <span>No Face</span>';
                        if (warningIcon) warningIcon.className = 'fas fa-user-slash';
                    } else if (wType === 'multiple_faces') {
                        eyeStatusEl.innerHTML = '<i class="fas fa-users"></i> <span>Multiple Faces</span>';
                        if (warningIcon) warningIcon.className = 'fas fa-users';
                    } else {
                        eyeStatusEl.innerHTML = '<i class="fas fa-eye-slash"></i> <span>Not Focused</span>';
                        if (warningIcon) warningIcon.className = 'fas fa-eye-slash';
                    }

                    if (warningText) warningText.textContent = result.warning || 'Please look at the screen!';
                    if (warningOverlay) {
                        warningOverlay.classList.remove('hidden');
                        setTimeout(function () {
                            warningOverlay.classList.add('hidden');
                        }, 2500);
                    }
                }
            } catch (error) {
            }
        }, 3000);
    },

    stopEyeTracking() {
        if (this.eyeTrackingInterval) {
            clearInterval(this.eyeTrackingInterval);
            this.eyeTrackingInterval = null;
        }
        var overlay = document.getElementById('eye-warning-overlay');
        if (overlay) overlay.classList.add('hidden');
    },

    stopMedia() {
        if (this.stream) {
            this.stream.getTracks().forEach(function (track) { track.stop(); });
            this.stream = null;
        }
        if (this.recognition) {
            try { this.recognition.stop(); } catch (e) { }
        }
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            try { this.mediaRecorder.stop(); } catch (e) { }
        }
    },

    cleanup() {
        this.stopEyeTracking();
        this.stopMedia();
        this.isRecording = false;
    }
};
