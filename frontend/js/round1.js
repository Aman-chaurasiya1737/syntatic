window.Round1 = {
    editor: null,
    timerInterval: null,
    timeRemaining: 45 * 60,

    async init() {
        this.setupEditor();
        this.startTimer();
        await this.loadQuestion();

        document.getElementById('submit-code-btn').addEventListener('click', () => this.submitCode());
        document.getElementById('reset-code-btn').addEventListener('click', () => this.resetCode());
        document.getElementById('language-select').addEventListener('change', (e) => this.changeLanguage(e.target.value));
    },

    setupEditor() {
        const editorEl = document.getElementById('code-editor');
        this.editor = CodeMirror(editorEl, {
            mode: 'python',
            theme: 'dracula',
            lineNumbers: true,
            autoCloseBrackets: true,
            matchBrackets: true,
            indentUnit: 4,
            tabSize: 4,
            lineWrapping: true,
            value: '# Write your solution here\n\ndef solution():\n    pass\n',
            extraKeys: {
                'Tab': function (cm) {
                    cm.replaceSelection('    ', 'end');
                }
            }
        });
    },

    changeLanguage(mode) {
        this.editor.setOption('mode', mode);

        const starters = {
            'python': '# Write your solution here\n\ndef solution():\n    pass\n',
            'javascript': '// Write your solution here\n\nfunction solution() {\n    \n}\n',
            'text/x-java': '// Write your solution here\n\npublic class Solution {\n    public void solve() {\n        \n    }\n}\n',
            'text/x-csrc': '// Write your solution here\n\n#include <stdio.h>\n\nint main() {\n    \n    return 0;\n}\n',
            'text/x-c++src': '// Write your solution here\n\n#include <iostream>\nusing namespace std;\n\nint main() {\n    \n    return 0;\n}\n'
        };

        if (starters[mode]) {
            this.editor.setValue(starters[mode]);
        }
    },

    async loadQuestion() {
        const state = window.AppState;

        try {
            const doc = await db.collection('dsa_questions').doc(state.companyMode).get();

            if (!doc.exists) {
                throw new Error('No questions found for ' + state.companyMode);
            }

            const data = doc.data();
            const allQuestions = data.questions || [];

            const filtered = allQuestions.filter(q => q.difficulty === state.difficulty);

            if (filtered.length === 0) {
                throw new Error('No ' + state.difficulty + ' questions found');
            }

            const question = filtered[Math.floor(Math.random() * filtered.length)];
            state.round1.question = question;
            this.renderQuestion(question);
        } catch (error) {
            console.error('Error loading question:', error);
            document.getElementById('q-title').textContent = 'Error loading question';
            document.getElementById('q-description').innerHTML = '<p>Could not load questions from database. Please make sure questions have been seeded.</p>';
        }
    },

    renderQuestion(q) {
        document.getElementById('q-difficulty').textContent = q.difficulty || 'Medium';
        document.getElementById('q-topic').textContent = q.topic || 'DSA';
        document.getElementById('q-title').textContent = q.title || 'Untitled';
        document.getElementById('q-description').textContent = q.description || '';

        const examplesEl = document.getElementById('q-examples');
        if (q.examples && q.examples.length > 0) {
            examplesEl.innerHTML = q.examples.map((ex, i) => `
                <div class="example-block">
                    <div class="example-label">Example ${i + 1}</div>
                    <div class="example-io"><strong>Input:</strong> ${this._escapeHtml(ex.input)}</div>
                    <div class="example-io"><strong>Output:</strong> ${this._escapeHtml(ex.output)}</div>
                    ${ex.explanation ? `<div class="example-explanation">${this._escapeHtml(ex.explanation)}</div>` : ''}
                </div>
            `).join('');
        }

        const constraintsEl = document.getElementById('q-constraints');
        if (q.constraints && q.constraints.length > 0) {
            constraintsEl.innerHTML = `
                <h3 style="color: var(--text-heading); margin-bottom: 8px; font-size: 1rem;">Constraints</h3>
                <ul class="constraints-list">
                    ${q.constraints.map(c => `<li>${this._escapeHtml(c)}</li>`).join('')}
                </ul>
            `;
        }
    },

    async submitCode() {
        const code = this.editor.getValue();
        const state = window.AppState;

        if (!code.trim() || code.trim() === '# Write your solution here\n\ndef solution():\n    pass') {
            alert('Please write your solution before submitting.');
            return;
        }

        state.round1.code = code;
        this.stopTimer();

        window.App.showLoading('Evaluating your solution...');

        const langSelect = document.getElementById('language-select');
        const langMap = {
            'python': 'Python',
            'javascript': 'JavaScript',
            'text/x-java': 'Java',
            'text/x-csrc': 'C',
            'text/x-c++src': 'C++'
        };

        try {
            const response = await fetch(window.API_BASE + '/api/evaluate-code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: state.round1.question,
                    code: code,
                    language: langMap[langSelect.value] || 'Python'
                })
            });

            const result = await response.json();
            state.round1.score = result.score;
            state.round1.remarks = result.remarks;
            state.round1.details = result;

            window.App.hideLoading();
            window.App.showRound1Results(result);
        } catch (error) {
            console.error('Error evaluating code:', error);
            window.App.hideLoading();
            alert('Error connecting to server. Please ensure the backend is running.');
        }
    },

    resetCode() {
        const langSelect = document.getElementById('language-select');
        this.changeLanguage(langSelect.value);
    },

    startTimer() {
        this.timeRemaining = 45 * 60;
        this.updateTimerDisplay();
        this.timerInterval = setInterval(() => {
            this.timeRemaining--;
            this.updateTimerDisplay();
            if (this.timeRemaining <= 0) {
                this.stopTimer();
                this.submitCode();
            }
        }, 1000);
    },

    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    },

    updateTimerDisplay() {
        const mins = Math.floor(this.timeRemaining / 60);
        const secs = this.timeRemaining % 60;
        const el = document.getElementById('r1-time');
        el.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;

        if (this.timeRemaining < 300) {
            el.parentElement.style.color = 'var(--accent-red)';
            el.parentElement.style.borderColor = 'rgba(239,68,68,0.3)';
            el.parentElement.style.background = 'rgba(239,68,68,0.1)';
        }
    },

    cleanup() {
        this.stopTimer();
    },

    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};
