const firebaseConfig = {
    apiKey: "AIzaSyBV-vv02SgZoRzpp0my4niXX-2P-7QngOY",
    authDomain: "syntatic-1.firebaseapp.com",
    projectId: "syntatic-1",
    storageBucket: "syntatic-1.firebasestorage.app",
    messagingSenderId: "419146724095",
    appId: "1:419146724095:web:06b144293b101518c4d2ca",
    measurementId: "G-7N2BG3Z5Y5"
};

firebase.initializeApp(firebaseConfig);

const db = firebase.firestore();

console.log("Firebase initialized successfully");
