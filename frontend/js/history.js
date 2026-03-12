window.HistoryManager = {

    async saveResult(data) {
        try {
            const user = firebase.auth().currentUser;
            if (!user) {
                console.error("Cannot save interview: No user is signed in.");
                return null;
            }

            const docRef = await db.collection('interviews').add({
                userId: user.uid,
                name: data.name,
                dateTime: firebase.firestore.FieldValue.serverTimestamp(),
                dateString: new Date().toLocaleString(),
                domain: data.domain,
                difficulty: data.difficulty,
                companyMode: data.companyMode,
                round1: {
                    question: data.round1.question || '',
                    score: data.round1.score || 0,
                    remarks: data.round1.remarks || '',
                    code: data.round1.code || ''
                },
                round2: {
                    questions: data.round2.questions || [],
                    overallScore: data.round2.overallScore || 0,
                    overallRemarks: data.round2.overallRemarks || ''
                },
                totalScore: data.totalScore || 0,
                terminated: data.terminated || false
            });
            console.log("Interview saved with ID:", docRef.id);
            return docRef.id;
        } catch (error) {
            console.error("Error saving interview:", error);
            return null;
        }
    },

    async loadHistory() {
        try {
            const user = firebase.auth().currentUser;
            if (!user) return [];

            // Query without orderBy to avoid composite index requirement
            const snapshot = await db.collection('interviews')
                .where('userId', '==', user.uid)
                .get();

            const interviews = [];
            snapshot.forEach(doc => {
                interviews.push({ id: doc.id, ...doc.data() });
            });

            // Sort client-side by dateTime descending
            interviews.sort((a, b) => {
                const aTime = a.dateTime ? a.dateTime.toMillis() : 0;
                const bTime = b.dateTime ? b.dateTime.toMillis() : 0;
                return bTime - aTime;
            });

            return interviews.slice(0, 20);
        } catch (error) {
            console.error("Error loading history:", error.message || error);
            return [];
        }
    },

    async renderHistory() {
        const interviews = await this.loadHistory();
        const listEl = document.getElementById('history-list');
        const avgTotalEl = document.getElementById('avg-total-score');
        const avgR1El = document.getElementById('avg-round1-score');
        const avgR2El = document.getElementById('avg-round2-score');
        const totalCountEl = document.getElementById('total-interviews');

        if (interviews.length === 0) {
            listEl.innerHTML = `
                <div class="history-empty">
                    <i class="fas fa-inbox"></i>
                    <p>No interviews yet</p>
                    <span>Start your first mock interview!</span>
                </div>`;
            avgTotalEl.textContent = '--';
            avgR1El.textContent = '--';
            avgR2El.textContent = '--';
            totalCountEl.textContent = '0';
            return;
        }

        let totalR1 = 0, totalR2 = 0, totalOverall = 0;
        interviews.forEach(i => {
            const r1 = i.round1?.score || 0;
            const r2 = i.round2?.overallScore || 0;
            totalR1 += r1;
            totalR2 += r2;
            totalOverall += i.totalScore || ((r1 + r2) / 2);
        });

        const count = interviews.length;
        avgTotalEl.textContent = (totalOverall / count).toFixed(1);
        avgR1El.textContent = (totalR1 / count).toFixed(1);
        avgR2El.textContent = (totalR2 / count).toFixed(1);
        totalCountEl.textContent = count;

        listEl.innerHTML = interviews.map(interview => {
            const r1Score = interview.round1?.score || 0;
            const r2Score = interview.round2?.overallScore || 0;
            const total = interview.totalScore || ((r1Score + r2Score) / 2);
            const scoreClass = total >= 7 ? 'score-good' : total >= 5 ? 'score-ok' : 'score-low';
            const dateStr = interview.dateString || 'N/A';
            const terminated = interview.terminated ? '<span class="history-terminated-badge"><i class="fas fa-ban"></i> Terminated</span>' : '';

            return `
                <div class="history-item">
                    <div class="history-item-header">
                        <span class="history-item-name">${this._escapeHtml(interview.name || 'Unknown')}</span>
                        <span class="history-item-date">${dateStr}</span>
                    </div>
                    <div class="history-item-meta">
                        <span class="history-meta-tag"><i class="fas fa-code"></i> ${this._escapeHtml(interview.domain || 'N/A')}</span>
                        <span class="history-meta-tag"><i class="fas fa-signal"></i> ${this._escapeHtml(interview.difficulty || 'N/A')}</span>
                        <span class="history-meta-tag"><i class="fas fa-building"></i> ${this._escapeHtml(interview.companyMode || 'N/A')}</span>
                        ${terminated}
                    </div>
                    <div class="history-item-scores">
                        <span class="history-score-badge ${r1Score >= 7 ? 'score-good' : r1Score >= 5 ? 'score-ok' : 'score-low'}">R1: ${r1Score}/10</span>
                        <span class="history-score-badge ${r2Score >= 7 ? 'score-good' : r2Score >= 5 ? 'score-ok' : 'score-low'}">R2: ${r2Score}/10</span>
                        <span class="history-score-badge total ${scoreClass}">Total: ${total.toFixed(1)}/10</span>
                    </div>
                </div>`;
        }).join('');
    },

    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};
