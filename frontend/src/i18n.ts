import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
    en: {
        translation: {
            "Dashboard": "Dashboard",
            "Map": "Interactive Map",
            "Status": "Service Status",
            "Chat": "AI Assistant",
            "Login": "Login",
            "Good Service": "Good Service",
            "Delays": "Delays",
            "Welcome": "Welcome to NYC Transit Hub"
        }
    },
    es: {
        translation: {
            "Dashboard": "Tablero",
            "Map": "Mapa Interactivo",
            "Status": "Estado del Servicio",
            "Chat": "Asistente IA",
            "Login": "Iniciar Sesión",
            "Good Service": "Buen Servicio",
            "Delays": "Retrasos",
            "Welcome": "Bienvenido al Centro de Tránsito de NYC"
        }
    }
};

i18n
    .use(initReactI18next)
    .init({
        resources,
        lng: "en",
        interpolation: {
            escapeValue: false
        }
    });

export default i18n;
