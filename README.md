# Bygge, publisere og kjøre et Docker-image

Dette repoet er en del av prosjektheftet til læreverket **Smidig IT-2** i faget **Informasjonsteknologi 2** i videregående skole.

Et Docker-image er en pakke som inneholder applikasjonen med alt den trenger for å kjøre, slik at den kan startes likt på ulike operativsystemer, både lokalt og i skyen.

Målet med dette eksempelet er å vise hvordan vi kan kjøre et Docker-image på tre forskjellige måter:

1. Kjøre et ferdig image i skyen på Render  
2. Kjøre et ferdig image lokalt fra Docker Hub  
3. Bygge og kjøre et image lokalt fra kildekoden i dette repoet

Applikasjonen er laget med Flask, Dash og SQLite, og gir et enkelt eksempel på et API med tilhørende webgrensesnitt. Den er hentet fra *Smidig IT-2* kapittel 5.11, API for web og mobil med Flask og Dash.

---

## 1 Kjøre et image i skyen på Render

Applikasjonen kjøres i en container på Render med et image som ligger på Docker Hub. Du kan åpne den her:

https://flask-dash-sqlite-app.onrender.com

Mer informasjon om Render:

https://render.com/

Merk at gratisversjonen av Render setter applikasjonen i dvale når den ikke er i bruk. Siden databasen ligger inne i containeren, vil dataene forsvinne når containeren stoppes. Dette kan løses ved å bruke en egen databasetjeneste, for eksempel PostgreSQL, eller ved å bruke fast lagring i en betalt plan.

---

## 2 Kjøre et ferdig image lokalt fra Docker Hub  

For å kjøre applikasjonen lokalt må Docker være installert.

Last ned Docker Desktop fra:

https://www.docker.com/products/docker-desktop/

Når Docker Desktop er installert og startet, kan du kjøre applikasjonen i terminalvinduet med kommandoen:

    docker run -p 5000:5000 --name demo  smidigit2/flask-dash-sqlite-app

Port 5000 i containeren kobles da til port 5000 på maskinen din.

Åpne i nettleseren:

http://localhost:5000

Du kan se images og containere i terminalviduet med kommandoene:

    docker images
    docker ps -a

Stoppe og slette containeren:

    docker rm -f demo

Slette imaget:

    docker rmi smidigit2/flask-dash-sqlite-app

---

## 3 Bygge og kjøre et image lokalt fra kildekoden i dette repoet
Du må først kopiere filene som følger med prosjektheftet til din maskin, eller laste dem ned fra GitHub.

Hvis du har installert Git, kan du åpne et terminalvindu, gå til mappen der du vil lagre repoet, og skrive:

    git clone https://github.com/smidig-it2/docker-demo.git

Da opprettes det en ny mappe med samme navn som repoet. Gå inn i denne mappen.

Hvis du ikke har Git, kan du gå til GitHub-siden for repoet, velge **Code** og deretter **Download ZIP**. Pakk ut ZIP-filen.

Når du står i mappen som inneholder `app.py` og `Dockerfile`, kan du bygge imaget med følgende kommando i terminalvinduet:

    docker build -t flask-dash-sqlite-app .

-t gir imaget et navn og en tag. Når vi ikke oppgir noen egen tag, brukes `latest` som standard, for eksempel `flask-dash-sqlite-app:latest`.

Punktumet betyr at Docker skal bygge imaget basert på filene i denne mappen.

Kjør imaget i en container med:

    docker run -p 5000:5000 --name demo flask-dash-sqlite-app

Åpne i nettleseren:

http://localhost:5000

Hvis port 5000 allerede er i bruk, må du stoppe den containeren, eller velge en annen port, for eksempel

    docker run -p 5001:5000 --name demo flask-dash-sqlite-app

Hvis du vil rydde opp, kan du stoppe og slette containeren og imaget på samme måte som under 2 Kjøre et ferdig image lokalt fra Docker Hub.

---

## Dockerfile, .dockerignore og Compose

Instruksjonene for hvordan imaget bygges, ligger i `Dockerfile`.

Når Docker bygger et image, sendes hele prosjektmappen til Docker som `build context`. Med `.dockerignore` kan du velge bort filer og mapper som ikke skal være med i build context. Dette gjør imaget mindre og bygger raskere.

Hvis du vil samle innstillinger som porter, volumes og miljøvariabler i én fil, kan du bruke `compose.yaml` og starte med:

    docker compose up

## Lisens

Dette prosjektet er lisensiert under MIT-lisensen. Se `LICENSE` for mer informasjon.