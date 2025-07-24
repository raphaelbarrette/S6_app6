const express = require('express');
const path = require('path');
const bodyParser = require('body-parser');
const fs = require('fs');
const axios = require('axios');

const app = express();
const PORT = 3000;

// Middleware
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

const LED_API_URL = 'http://172.16.11.117:8000/led';
const EVENTS_FILE = path.join(__dirname, '../backend/data/events.json');

app.get('/', async (req, res) => {
    let ledState = 'off';
    let events = [];

    try {
        const response = await axios.get(LED_API_URL);
        ledState = response.data.state;
    } catch (err) {
        console.error('Erreur lecture LED:', err.message);
    }

    try {
        const responseEvents = await axios.get('http://172.16.11.117:8000/events');

        events = responseEvents.data.reverse();
    } catch (err) {
        console.error('Erreur lecture événements:', err.message);
    }

    res.render('admin', { ledState, events });
});

// Route pour changer l'état de la LED
app.post('/led', async (req, res) => {
    const newState = req.body.state;
    try {
        await axios.post(LED_API_URL, { state: newState });
    } catch (err) {
        console.error('Erreur modification LED:', err.message);
    }
    res.redirect('/');
});

app.listen(PORT, () => {
    console.log(`Interface Admin disponible sur http://localhost:${PORT}`);
});
