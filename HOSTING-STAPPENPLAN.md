# Tennis Tossen online zetten (PythonAnywhere)

Doel: de app live op internet, zodat je overal via een URL in de browser kunt gebruiken.

## Stap 0 — Bestanden downloaden
Download `tennistoernooi.zip` en pak hem uit op je eigen computer.
Je krijgt de map `tennistoernooi` met daarin: `app.py`, `templates/`, `static/`, `requirements.txt`.

## Stap 1 — Account aanmaken (1 minuut)
1. Ga naar **https://www.pythonanywhere.com**
2. Klik op **Create a beginner account** (gratis)
3. Kies een gebruikersnaam — die komt in je URL: `https://jouwnaam.pythonanywhere.com`

## Stap 2 — Bestanden uploaden (2 minuten)
1. Log in en klik bovenin op het tabje **Files**
2. Klik op **Upload files** (rechts bovenin)
3. Upload **alle losse bestanden en mappen** uit de map `tennistoernooi`:
   - `app.py` en `requirements.txt` rechtstreeks in je home-map
   - de map `templates` (met de 6 .html-bestanden) en de map `static` (met style.css)
   - Tip: je kunt ook de hele `tennistoernooi.zip` uploaden en dan in een Bash-console typen: `unzip tennistoernooi.zip -d tennistoernooi`

## Stap 3 — Flask installeren (1 minuut)
1. Ga naar tabje **Consoles** en klik **Bash** (nieuw console)
2. Typ:
   ```
   cd ~/tennistoernooi
   pip3 install --user flask gunicorn
   ```

## Stap 4 — Web-app aanmaken (3 minuten)
1. Ga naar tabje **Web**
2. Klik **Add a new web app** → **Next** → **Manual configuration** → Python-versie (3.10 of nieuwer) → **Next**
3. Klik op de blauwe link **WSGI configuration file** (bij het kopje Code)
4. Verwijder alles tussen de markers `# +++` en plak in plaats daarvan:
   ```python
   import sys
   path = '/home/JOUWGEBRUIKERSNAAM/tennistoernooi'
   if path not in sys.path:
       sys.path.insert(0, path)
   from app import app as application
   ```
5. Vervang `JOUWGEBRUIKERSNAAM` door je eigen gebruikersnaam en sla op (knop bovenin)

## Stap 5 — Working directory instellen
1. Terug op de Web-pagina, zoek het vak **Code**
2. Zet bij **Working directory**: `/home/JOUWGEBRUIKERSNAAM/tennistoernooi`
3. Zet bij **Source code**: hetzelfde pad (optioneel maar netjes)

## Stap 6 — Live gaan
1. Klik op de groene knop **Reload** (rechts bovenin op de Web-pagina)
2. Open `https://jouwnaam.pythonanywhere.com` — klaar! 🎾

## Fouten oplossen
- **"Application errored"**: controleer of je gebruikersnaam in het WSGI-bestand klopt en of je op Reload hebt gedrukt
- **Stijl doet het niet**: check of de map `static` echt op de juiste plek staat
- **Data verdwijnt niet**: de deelnemers/rondes worden opgeslagen in `tennistoernooi/data/tossen.json` en blijven bewaard
- De app heeft nu een eigen login-scherm. Stel na de eerste keer inloggen direct een wachtwoord in via het menu-item **Wachtwoord**. Daarna kan alleen wie het wachtwoord kent bij het toernooi. Je kunt het wachtwoord later altijd wijzigen via datzelfde menu-item.
- Belangrijk voor PythonAnywhere: de app moet kunnen wegschrijven naar de map `data`. Die maak je zo nodig even aan via de Files-tab (map `tennistoernooi/data`) of via de Bash-console: `mkdir -p ~/tennistoernooi/data`.

## Daarna
- Elke keer als je iets aan de code verandert: knop **Reload** op de Web-pagina
- Gratis accounts: de site blijft gewoon online staan; alleen consoles slapen na lange inactiviteit, de website zelf niet
