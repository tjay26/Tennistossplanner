# Tennis Tossen

Lokale web-app om tennistossen (dubbelspel) te organiseren.

## Starten

```bash
pip install -r requirements.txt
python3 app.py
```

Open daarna `http://127.0.0.1:5000` in je browser. De app luistert alleen op
je eigen machine (127.0.0.1).

## Functionaliteit

- **Deelnemers**: naam, man/vrouw, speelsterkte in 3 niveaus, actief/aanwezig
  toggle, en een teller hoeveel keer iemand is ingedeeld.
- **Instellingen**: aantal rondes en aantal beschikbare banen per ronde.
- **Per ronde indelen**: automatische indeling (spelers die het minst zijn
  ingedeeld gaan eerst, gemengde teams waar mogelijk, teams van gelijke
  totale sterkte tegen elkaar) of volledig handmatig aanpassen.
- **Speelschema per ronde**: overzicht per baan met teams.
- **Stand invoeren**: score (games) per baan, ook achteraf te wijzigen tot de
  ronde geblokkeerd is.
- **Blokkeren**: een gespeelde ronde blokkeren zodat indeling en scores niet
  meer kunnen wijzigen (deblokkeren kan weer).
- **Afdrukken**: printbare versie van het speelschema van een ronde, met
  lege hokken om de stand op het veld in te vullen.

## Opslag

Data wordt opgeslagen in `data/tossen.json` (automatisch aangemaakt).
