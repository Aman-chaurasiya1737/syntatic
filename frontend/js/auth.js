window.Auth = {
    init() {
        this.setupEventListeners();
        this.checkAuthState();
    },

    setupEventListeners() {
        // Tab switching
        document.getElementById('tab-login')?.addEventListener('click', () => this.switchTab('login'));
        document.getElementById('tab-register')?.addEventListener('click', () => this.switchTab('register'));

        // Toggle password visibility
        document.querySelectorAll('.toggle-password').forEach(icon => {
            icon.addEventListener('click', (e) => {
                const targetId = e.target.getAttribute('data-target');
                const input = document.getElementById(targetId);
                if (input.type === 'password') {
                    input.type = 'text';
                    e.target.classList.replace('fa-eye', 'fa-eye-slash');
                } else {
                    input.type = 'password';
                    e.target.classList.replace('fa-eye-slash', 'fa-eye');
                }
            });
        });

        // Form submissions
        document.getElementById('login-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        document.getElementById('register-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleRegister();
        });

        // Google Auth
        document.getElementById('google-auth-btn')?.addEventListener('click', () => {
            this.handleGoogleAuth();
        });

        // Logout
        document.getElementById('logout-btn')?.addEventListener('click', () => {
            this.handleLogout();
        });
    },

    switchTab(tab) {
        document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.auth-form').forEach(f => f.classList.add('hidden'));

        if (tab === 'login') {
            document.getElementById('tab-login').classList.add('active');
            document.getElementById('login-form').classList.remove('hidden');
        } else {
            document.getElementById('tab-register').classList.add('active');
            document.getElementById('register-form').classList.remove('hidden');
        }
    },

    checkAuthState() {
        App.showLoading('Checking authentication...');
        firebase.auth().onAuthStateChanged(async (user) => {
            if (user) {
                console.log("User is signed in:", user.uid);
                let nameValue = user.displayName;
                try {
                    const userDoc = await db.collection('users').doc(user.uid).get();
                    if (userDoc.exists) {
                        nameValue = userDoc.data().fullName || userDoc.data().username;
                    }
                } catch (e) {
                    console.error("Error fetching user data:", e);
                }
                
                window.AppState.name = nameValue || user.email?.split('@')[0] || 'Candidate';
                
                App.switchView('home');
                HistoryManager.renderHistory();
            } else {
                console.log("No user is signed in.");
                App.switchView('auth');
            }
            App.hideLoading();
        });
    },

    async handleRegister() {
        const fullName = document.getElementById('reg-fullname').value.trim();
        const username = document.getElementById('reg-username').value.trim();
        const email = document.getElementById('reg-email').value.trim();
        const password = document.getElementById('reg-password').value;

        if (!fullName || !username || !email || !password) return;

        App.showLoading('Creating account...');
        try {
            // Check if username is already taken
            const userSnapshot = await db.collection('users').where('username', '==', username).get();
            if (!userSnapshot.empty) {
                alert('Username is already taken. Please choose another one.');
                App.hideLoading();
                return;
            }

            // Create user
            const userCredential = await firebase.auth().createUserWithEmailAndPassword(email, password);
            const user = userCredential.user;

            // Update profile and create firestore document
            await user.updateProfile({ displayName: fullName });
            await db.collection('users').doc(user.uid).set({
                fullName: fullName,
                username: username,
                email: email,
                createdAt: firebase.firestore.FieldValue.serverTimestamp()
            });

            console.log("Successfully registered!");
        } catch (error) {
            console.error("Error during registration:", error);
            alert(error.message);
        }
        App.hideLoading();
    },

    async handleLogin() {
        const identifier = document.getElementById('login-identifier').value.trim(); // username or email
        const password = document.getElementById('login-password').value;

        if (!identifier || !password) return;

        App.showLoading('Logging in...');
        try {
            let email = identifier;

            // If identifier does not look like an email, assume it's a username
            if (!identifier.includes('@')) {
                const userSnapshot = await db.collection('users').where('username', '==', identifier).limit(1).get();
                if (userSnapshot.empty) {
                    alert("Username not found.");
                    App.hideLoading();
                    return;
                }
                email = userSnapshot.docs[0].data().email;
            }

            await firebase.auth().signInWithEmailAndPassword(email, password);
            console.log("Successfully logged in!");
        } catch (error) {
            console.error("Error during login:", error);
            alert("Login failed: " + error.message);
        }
        App.hideLoading();
    },

    async handleGoogleAuth() {
        App.showLoading('Redirecting to Google...');
        const provider = new firebase.auth.GoogleAuthProvider();
        try {
            const result = await firebase.auth().signInWithPopup(provider);
            const user = result.user;
            
            // Generate a username from email if setting up for the first time
            const userDoc = await db.collection('users').doc(user.uid).get();
            if (!userDoc.exists) {
                const baseUsername = user.email.split('@')[0];
                let username = baseUsername;
                let counter = 1;
                
                // Keep checking until a unique username is found
                while (true) {
                    const snap = await db.collection('users').where('username', '==', username).get();
                    if (snap.empty) break;
                    username = `${baseUsername}${counter}`;
                    counter++;
                }

                await db.collection('users').doc(user.uid).set({
                    fullName: user.displayName || username,
                    username: username,
                    email: user.email,
                    createdAt: firebase.firestore.FieldValue.serverTimestamp()
                });
            }
        } catch (error) {
            console.error("Error with Google Auth:", error);
            alert("Google Sign-in failed: " + error.message);
        }
        App.hideLoading();
    },

    async handleLogout() {
        try {
            await firebase.auth().signOut();
            App.resetState();
            // Auth observer will handle redirecting to 'auth' view
        } catch (error) {
            console.error("Error during logout:", error);
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // Only init inside app.js or let auth check it separately
    // We will initialize it from app.js so it controls flow better.
});
