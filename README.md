# Julefrokost på Amager: spillet

Et lille 16-bit browserspil som opvarmning til julefrokosten 27. december 2026. Man vælger sin fisker, løber ti baner på Amager med en kæmpe pokal over hovedet, og til sidst får man hemmeligheden og en nedtælling.

Status: **grundarkitektur (v0.4)**. Spillet kan spilles fra start til slut, men al grafik er pladsholdere, og banerne er kun groft afstemt.

## Sådan køres det

Spillet er ren HTML, JavaScript og PNG. Der er intet build-trin.

```
python3 -m http.server 8080
```

Åbn derefter `http://localhost:8080`. Filen kan ikke åbnes direkte fra disken, fordi browseren kræver en webserver til JavaScript-moduler.

Genvej: `?scene=Scores` åbner topscorerlisten direkte. Testgenvejene (`?level`, `?alle`, `?fisher`, `?scene=Secret`) er fjernet i den udgivne version (24/11) for at undgå snyd.

## Styring

| Mobil | Tastatur | Handling |
| --- | --- | --- |
| Swipe op | Pil op, W, mellemrum | Hop |
| Swipe ned | Pil ned, S | Slide (i luften: hurtigt ned) |
| Tap | X, Enter, pil til højre | Slå med pokalen |

Fiskeren løber selv. Fuld ølmåler (10 bajere) gør næste slag til et superslag. Et shot er valgfrit: alt giver dobbelt point i 6 sekunder, men op og ned bytter plads, og man er ikke usårlig.

Første gang man har valgt fisker, kommer en kort øvebane. Den stopper spillet tre gange og venter på hop, slide og slag. Den kan springes over og findes igen på kortet under ØV STYRINGEN.

Forsiden viser nedtællingen til julefrokosten søndag 27/12 kl. 13.00. Samtidig lukker highscoren.

Banerne: Dragør Havn, Lufthavnen (droner), Den Blå Planet (under vand med hajer: swipe op og ned skifter svømmebane), Sundby Idrætspark (bolde og Sunnyside), Amager Fælled (bulldozere og køer), DR Byen (kameraer og ledninger), Søndre Campus, Amager Centret, Jaguaren (rockere) og CopenHill (Kæmpeduen).

## Mapper

```
index.html              siden, der starter det hele
vendor/phaser.min.js    spilmotoren Phaser 4.2.1 (ligger i repoet, så intet hentes udefra)
src/
  main.js               opsætning af Phaser og listen af scener
  config.js             opløsning, fysik, point, dato for julefrokosten
  data/
    levels.js           BANERNE. Skrives som rækker af tegn, se toppen af filen
    entities.js         alt, der kan stå i en bane, og hvad der er særligt pr. bane
    fishers.js          de syv fiskere (navn og erhverv)
    quiz.js             spørgsmål til quizkasserne
  game/
    Player.js           fiskeren: hop, slide, slag og kollisionskasser
    Boss.js             Kæmpeduen
    ui.js               tekst, paneler og knapper
  scenes/               én fil pr. skærm: Boot, Title, Select, Map, Level, Hud, Quiz, Result, Secret, Scores
  systems/
    input.js            swipe og tap
    save.js             gemmer fremskridt på telefonen
    scores.js           topscorerlisten
    audio.js            lydeffekter (lavet i kode, ingen lydfiler)
assets/                 færdig grafik. Bygges af tools/build_assets.py. Ret ikke i filerne i hånden
tools/
  build_assets.py       tegner al grafik og pakker atlas, baggrunde, kort og fonte
  pixlib.py             pixel-tegnebibliotek og sprites
  test_play.cjs         en robot spiller alle baner igennem
  test_flow.cjs         tester menuer og styring med rigtige berøringer
  make_artifact.py      laver testversionen til Claude
```

## Sådan ændrer man tingene

- **En bane:** ret `layout` i `src/data/levels.js`. Hver byggeklods er fire rækker tegn (`hi`, `mid`, `lo`, `fl`), og tegnene står forklaret øverst i filen.
- **En ny fjende eller ting:** tilføj et bogstav i `ENTITIES` i `src/data/entities.js`, og brug bogstavet i en bane. `THEMES` bestemmer, hvordan en ting ser ud på en bestemt bane (fx er `x` en ko på Fælleden og en rocker på Jaguaren).
- **Spilfølelsen:** `TUNING` i `src/config.js` (hophøjde, slidetid, slag, usårlighed).
- **Sværhedsgrad:** hver bane har `speed: [start, slut]` og en række bølger (`waves`), der trækker byggeklodser fra puljerne `easy`, `med` og `hard`. Flere eller sværere bølger gør banen længere og hårdere. `spaceOut()` i `levels.js` indsætter selv luft, hvis to ting kommer for tæt ved banens topfart, så banerne altid kan klares. Robotten i `tools/test_play.cjs` viser, om det holder (`ONLY=3,5` kører kun bane 3 og 5).
- **Grafik:** ret tegnefunktionerne i `tools/build_assets.py` og kør `python3 tools/build_assets.py`. Framenavnene i atlasset (`fisher/kasper/run0`, `due/walk0`, `obst/cow` osv.) er aftalen med koden. Behold dem.
- **Quiz:** `src/data/quiz.js`. Første svar er det rigtige.

Grafikken er tegnet i 320x180 og skaleret 2x til spillets 640x360. Når den tegnes om i fuld opløsning, sættes `ART = 1` i `build_assets.py`.

## Test

```
npm install
npm test
```

Kræver en Chrome. Sæt `CHROME=/sti/til/chrome`, hvis den ikke ligger i `/usr/bin/google-chrome`. Skærmbilleder havner i `tools/shots/`.

## Online

Spillet skal kunne spilles af alle med linket, uden login.

1. **Spillet:** mappen lægges i et offentligt GitHub-repo med GitHub Pages slået til (Settings, Pages, Deploy from branch, main, /root). Der er intet build.
2. **Fælles highscore:** `server/worker.js` er en lille Cloudflare Worker med et KV-lager. Opret et KV-namespace, sæt dets id i `server/wrangler.toml`, og deploy med `npx wrangler deploy` fra mappen `server/` (eller indsæt koden i Cloudflares dashboard og bind KV-lageret som `SCORES`). Sæt derefter `SCORES_URL` i `src/config.js` til Workerens adresse.
3. Test serveren lokalt med `node tools/test_worker.mjs`.

Der er intet login. Man spiller under det navn, man vælger, og serveren gemmer kun hver fiskers bedste point pr. bane. Efter søndag 27/12 kl. 13.00 afviser serveren nye point.

## Mangler

- Rigtig 16-bit grafik i fuld opløsning (alt er pladsholdere).
- De rigtige quizspørgsmål.
- Fælles topscorerliste er skrevet og testet lokalt (`server/`), men ikke sat online endnu.
- Musik.
- Flere banespecifikke fjender (bibliotekaren, jetstråle, rulletrapper).
- Test på rigtige telefoner. Spillet er kun testet i en hovedløs Chrome.

## Kreditering

- [Phaser 4](https://phaser.io) (MIT).
- Fontene VT323, Jersey 10 og Silkscreen (SIL Open Font License, se `tools/fonts/`). De er bagt ind i `assets/fonts/` som bitmapfonte.
