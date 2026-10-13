# VoxClarity

Haalt achtergrondgeluid uit audio-opnames zodat alleen stemmen overblijven. Onderdeel van Safe Haven. Bedoeld als stap vóór transcriptie.

Alles draait lokaal. Er gaat geen audio naar een externe dienst, wat bij aangiftemateriaal een harde eis is.

## Gebruik

```bash
pip install -r requirements.txt      # plus ffmpeg op het systeem
python voxclarity.py opname.m4a            # -> opname.schoon.wav + opname.schoon.wav.json
python voxclarity.py map_met_opnames/ -o schoon/   # hele map
```

Vanuit code (bv. in de Safe Haven backend):

```python
from voxclarity import clean_audio, Options
report = clean_audio("in.m4a", "uit.wav", Options())
print(report.speech_ratio, report.segments)
```

Invoer: alles wat ffmpeg leest (wav, mp3, m4a, opus, amr, mp4/mov enz.). Uitvoer: WAV, 16 kHz mono, de standaard voor transcriptiemodellen.

## Wat het doet

1. **RNNoise** (neuraal netwerk) haalt ruis weg, ook onder de spraak.
2. **Silero VAD** bepaalt per 32 ms of er een stem klinkt. Al het andere (deurslag, muziek, verkeer, stilte) wordt volledig gedempt.
3. Loudness-normalisatie op de stemfragmenten.

De tijdlijn blijft intact. Niet-stem wordt gedempt, niet weggeknipt, dus tijdstempels uit de transcriptie kloppen met het origineel. Wil je wel knippen: `--trim-silence` (de segmenten in het rapport laten zien hoe de tijd verschuift).

## Bewijsketen

Het origineel wordt nooit aangepast en de tool weigert het te overschrijven. Naast elke uitvoer staat een `.json`-rapport met SHA-256 van invoer en uitvoer, tijdstip, alle instellingen en de gedetecteerde stemsegmenten. Bewaar het rapport bij het dossier en transcribeer, waar mogelijk, ook het origineel ter controle.

## Afstellen

| Situatie | Optie |
|---|---|
| Zachte of fluisterende stem valt weg | `--threshold 0.35` |
| Muziek/tv wordt als stem meegenomen | `--threshold 0.65` |
| Zeer rumoerige opname | `--passes 2 --extra-denoise` |
| Woordbegin of -einde wordt afgekapt | `--pad-ms 300` |
| Liever geen harde digitale stilte | `--keep-noise-db -55` |

## Beperkingen (lees dit voor je het op echt materiaal inzet)

- **Stemmen op de achtergrond** (tv, radio, mensen in de verte) zijn voor de tool ook stemmen en blijven staan. Stemmen scheiden naar spreker is een ander probleem (diarization/bronscheiding) en zit hier niet in.
- **Geluid dat tegelijk met spraak klinkt** wordt door RNNoise verminderd, niet perfect verwijderd. Zware overlap geeft restanten of lichte vervorming.
- Zang en sommige muziek worden door de VAD soms als spraak gezien.
- Zeer zachte spraak kan wegvallen. Controleer bij belangrijk materiaal altijd luisterend of het resultaat niets weglaat, en kijk in het rapport naar `speech_ratio`.
- Getest op synthetische spraak met ruis. Test dit op een set echte, geanonimiseerde opnames voordat je het in productie neemt.

## Evalueren op echte opnames

Beantwoordt de vraag die telt: helpt VoxClarity, en vallen er geen woorden weg? Draait Whisper lokaal (faster-whisper), er gaat niets naar buiten.

```bash
pip install -r requirements-eval.txt
python evaluate.py opnames/ --refs referenties/ --out resultaat/
```

- `opnames/`: 10 tot 20 geanonimiseerde opnames, een mix van rustig, rumoerig, fluisterend en met tv/muziek.
- `referenties/` (optioneel, maar sterk aangeraden): per opname een handmatige transcriptie `<zelfde naam>.txt`, voor minstens 5 opnames. Zonder referentie wordt alleen origineel met schoon vergeleken.
- Model: standaard `large-v3` (beste, traag op CPU). Snel proberen: `--model small --compute-type int8`. Taal: `--language nl` (standaard) of `auto`.
- Instellingen testen: `--threshold 0.35`, `--passes 2`, `--extra-denoise`, `--pad-ms 300`. Draai meerdere varianten en vergelijk de rapporten.

Uitvoer in `resultaat/`: `report.md` (samenvatting, tabel per opname, weggevallen passages met tijdstip), `results.csv` en `details/<naam>.json`. De schone audio staat in `resultaat/schoon/`.

Zo lees je het resultaat:
1. Kijk eerst naar opnames die **slechter** werden (positieve Δ). Dat is waar VoxClarity schade doet.
2. Luister bij elke weggevallen passage naar het origineel op dat tijdstip. Echte spraak? Dan dempt VoxClarity te hard.
3. Een lagere WER na opschonen komt soms doordat Whisper op ruis woorden verzint. Dat is winst, maar controleer het.
4. Besluit pas na de uitschieters, niet op het gemiddelde alleen.

Privacy: rapport, details en schone audio bevatten aangiftemateriaal. Sla ze op dezelfde beveiligde plek op als de opnames. `--redact` houdt tekst uit `report.md`, maar `details/*.json` bevat de transcripties wel.

## Tests

```bash
python -m unittest discover -s tests
```
