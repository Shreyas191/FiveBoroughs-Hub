import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyDummyKey",
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "transit-hub.firebaseapp.com",
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "transit-hub",
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "transit-hub.appspot.com",
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "123456789",
    appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:123456789:web:abcdef"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
export default app;
