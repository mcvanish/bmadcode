# Client Onboarding Workflow v1

**Status:** eerste opzet, ter bespreking tussen Menno en Peter
**Datum:** 2026-09-23
**Doel van dit document:** een herbruikbaar proces om bij een nieuwe klantaanvraag met de juiste vragen, doorvragen en samenvatten tot een scherp beeld van het werkelijke probleem te komen, voordat er over AI-tooling of automatisering wordt nagedacht.

---

## 1. Uitgangspunt

Het risico bij een AI-consultancy is dat je (of de klant) meteen in oplossingen denkt. "We hebben AI nodig" of "kunnen jullie iets met LinkedIn/een chatbot/automatisering bouwen" is een symptoom, geen diagnose. Dit proces is bewust zo ingericht dat oplossingsdenken pas in de laatste fase mag beginnen. Alles daarvoor is diagnose.

Twee ontwerpprincipes staan daarom vast, ongeacht welke methode je erbij pakt.

1. **Diagnose voor therapie.** Eerst het probleem, de context en het werkelijke doel van de klant scherp krijgen. Pas daarna oplossingsrichtingen verkennen.
2. **Elke fase levert een tastbaar tussenresultaat op** dat je aan de klant kunt teruggeven ter bevestiging. Geen fase eindigt in "we hebben een goed gesprek gehad", maar in een kort document waar de klant ja of nee op kan zeggen.

## 2. Waarom deze mix, en niet één methode

Jullie noemden al BMad, Getting Shit Done en Shape Up ("Git Ships Done"). Geen van drieën is op zichzelf een intake-methode, dus hieronder een bewuste selectie van wat elk goed doet, aangevuld met een paar frameworks die specifiek voor het probleem "wat wil de klant nou ECHT" zijn gebouwd.

| Methode | Waar sterk in | Waar gebruikt in dit proces |
|---|---|---|
| **BMad Method** | Gestructureerde elicitatie, brainstorm-technieken, expliciete overdracht van context tussen rollen/fases | Open verkenningsvragen in Fase 1, en het principe dat elke fase een document oplevert dat de volgende fase ingaat |
| **Getting Shit Done (GSD)** | Actiegerichtheid, niet blijven hangen in analyse, prioriteren op wat écht impact heeft | Prioritering in Fase 2, en het voorstel in Fase 4 eindigt altijd in een concrete eerste stap |
| **Shape Up** | "Appetite" (hoeveel tijd/budget past bij dit probleem, in plaats van eindeloos scopen), pitch-format, expliciete "rabbit holes" en "no-gos" | Triage-vraag in Fase 0, en de vorm van het voorstel in Fase 4 |
| **Jobs-to-be-Done (JTBD)** *(nieuw voorstel)* | Herformuleert "ik wil tool X" naar "ik wil resultaat Y bereiken", losse van een vooraf bedachte oplossing | Kern van Fase 2, elk pijnpunt wordt een JTBD-statement |
| **Five Whys (Toyota)** *(nieuw voorstel)* | Snelle, gestructureerde manier om van symptoom naar wortelprobleem door te vragen | Doorvraagtechniek in Fase 2 |
| **SPIN Selling** *(nieuw voorstel)* | Vragenstructuur voor een verkoop-/intakegesprek: Situatie, Probleem, Implicatie, Need-payoff. Precies het "doorvragen" dat je zoekt | Ruggengraat van het gesprek in Fase 1 en 2 |
| **Double Diamond (Design Council)** *(nieuw voorstel)* | Divergeren voor je convergeert, twee keer: eerst het probleem breed verkennen en dan scherpstellen, dan de oplossing breed verkennen en dan kiezen | De hoofdstructuur van dit hele document (Fase 1-2 = eerste diamant, Fase 3-4 = tweede diamant) |
| **Value Proposition Canvas (Strategyzer)** *(nieuw voorstel)* | Compact sjabloon om Jobs / Pains / Gains van een klant te ordenen | Synthese-tool in Fase 2 |
| **Design Sprint "How Might We"** *(nieuw voorstel)* | Vraagvorm om van een probleem naar meerdere oplossingsrichtingen te gaan zonder er meteen één te kiezen | Openingstechniek van Fase 3 |

De rode draad: BMad en GSD geven jullie de manier van werken (structuur, elicitatie, actiegerichtheid). JTBD, Five Whys, SPIN en de Value Proposition Canvas geven jullie de vragen. Double Diamond geeft de vorm die garandeert dat oplossingsdenken pas als laatste komt. Shape Up geeft de vorm van het uiteindelijke voorstel.

## 3. Het proces in één oogopslag

```
Fase 0  TRIAGE          (async, voor het gesprek)
   |
Fase 1  DISCOVER         )
   |                     )  eerste diamant: probleem breed verkennen, dan scherpstellen
Fase 2  DEFINE           )
   |
   ---  Samenvatten & Valideren bij de klant  ---
   |
Fase 3  DEVELOP          )
   |                     )  tweede diamant: oplossingen breed verkennen, dan kiezen
Fase 4  DELIVER          )
```

Elke fase heeft: (a) een doel, (b) concrete vragen/technieken, (c) een tastbaar output-document.

---

## Fase 0 - Triage (async, voor het gesprek)

**Doel:** voorkomen dat je een uur intakegesprek voert met een klant waar geen fit of budget is, en een eerste hypothese vormen over wie de stakeholders zijn.

**Kort intakeformulier (5-7 vragen), bijvoorbeeld:**
- Wat is de aanleiding om nu contact te zoeken? Waarom niet drie maanden geleden of over drie maanden?
- Wie vraagt dit aan, en wie beslist uiteindelijk (kan dezelfde persoon zijn)?
- Hoeveel mensen/tijd raakt dit probleem op dit moment, ruwe schatting?
- Appetite-vraag (Shape Up): als jullie dit zouden oplossen, hoeveel tijd/budget past daar realistisch bij? Dagen, weken, een kleine of grote investering?
- Is er al iets geprobeerd? Wat werkte niet?

**Output:** go/no-go voor een intakegesprek, plus een eerste (interne, niet gedeelde) hypothese over stakeholders en waarschijnlijke urgentie.

**Privacy-noot:** vanaf dit formulier verzamel je bedrijfsgevoelige informatie, en soms persoonsgegevens van derden (zoals in de recruiter-case). Spreek nu al af waar intake-notities worden opgeslagen, wie er toegang toe heeft, en hoe lang je ze bewaart als er geen opdracht uit volgt. Dat hoeft geen bureaucratisch privacybeleid te zijn, wel een bewuste afspraak tussen jullie twee.

---

## Fase 1 - Discover (het gesprek, deel 1: breed verkennen)

**Doel:** het huidige proces en de pijn ervan volledig in kaart brengen, zonder dat er nog één oplossing valt.

**Techniek 1, SPIN "Situatie":** laat de klant het huidige proces stap voor stap doorlopen, alsof jij er nooit bij bent geweest. "Loop met me mee vanaf het moment dat X gebeurt tot het moment dat Y klaar is." Dit dwingt een concrete procesbeschrijving af in plaats van een abstracte klacht, en levert meteen een as-is procesoverzicht op.

**Techniek 2, SPIN "Probleem":** waar loopt dit vast? Wat kost het meeste tijd, geld of energie? Wat frustreert het meest, elke keer opnieuw?

**Techniek 3, BMad-stijl divergentie:** "Als tijd en geld geen rol zouden spelen, hoe zou dit er dan uitzien?" Dit haalt de werkelijke ambitie naar boven, los van de huidige beperkingen (zoals een duur abonnement).

**Techniek 4, parking lot:** zodra de klant zelf met een oplossing komt ("misschien een chatbot", "misschien die API"), schrijf je die op een aparte lijst en zeg je expliciet: "Goed idee, die bewaar ik, daar komen we in de laatste fase op terug." Dit houdt het gesprek gedisciplineerd zonder ideeën van de klant af te wijzen.

**Output:** as-is procesbeschrijving (stappen, wie doet wat, welke tools), een ruwe lijst pijnpunten, en de parking lot met premature oplossingen.

---

## Fase 2 - Define (het gesprek, deel 2: scherpstellen)

**Doel:** van een lijst symptomen naar twee of drie wortelproblemen, geformuleerd als het werkelijke resultaat dat de klant wil bereiken.

**Techniek 1, Five Whys:** pak de twee of drie grootste pijnpunten uit Fase 1 en vraag vier of vijf keer door. "Waarom is dat een probleem? En waarom is dát een probleem?" Stop zodra je bij iets zit dat de klant zelf niet meer verder kan verklaren, dat is meestal het wortelprobleem.

**Techniek 2, JTBD-herformulering:** herschrijf elk wortelprobleem als "Wanneer [situatie], wil ik [motivatie], zodat ik [gewenst resultaat]." Dit dwingt je weg van "ik wil tool X" naar "ik wil resultaat Y", en voorkomt dat je (of de klant) later een oplossing kiest die het eigenlijke doel mist.

**Techniek 3, Value Proposition Canvas (klantzijde):** orden wat je gehoord hebt in Jobs (wat probeert de klant voor elkaar te krijgen), Pains (wat frustreert, kost tijd/geld) en Gains (wat zou het opleveren als het goed gaat). Dit is een goede check of je iets gemist hebt.

**Techniek 4, prioriteren (GSD):** niet alles is even belangrijk. Scoor de wortelproblemen kort op impact x frequentie: wat kost structureel het meeste, in plaats van wat het laatst genoemd is of het meest opvalt.

**Output:** top 2-3 wortelproblemen als JTBD-statements, geprioriteerd.

---

## Tussenstap - Samenvatten & Valideren

**Doel:** bevestigen dat je het probleem goed begrepen hebt, voordat er tijd in oplossingen gaat zitten. Dit is het scharniermoment van het hele proces.

**Vorm:** een kort document (maximaal 1 A4), terug naar de klant, met:
- Situatie (2-3 zinnen)
- Top pijnpunten, als JTBD-statements
- Wat expliciet **niet** in scope zit (voorkomt scope-verwarring later)
- Een concrete vraag: "Klopt dit? Mist er iets?"

Pas na akkoord van de klant ga je door naar Fase 3. Dit is bewust een harde stop, niet een formaliteit.

---

## Fase 3 - Develop (oplossingen breed verkennen, nog geen keuze)

**Doel:** meerdere oplossingsrichtingen verkennen voor elk JTBD-statement, inclusief richtingen die geen nieuwe tooling vereisen. Nu, en pas nu, mag oplossingsdenken beginnen.

**Techniek 1, Design Sprint "How Might We":** herschrijf elk JTBD-statement als een "Hoe zouden we..." vraag, en genereer minimaal drie richtingen per vraag. Voorbeeld: niet "hoe bouwen we een LinkedIn-integratie" maar "hoe zorgen we dat kandidaten sneller reageren", wat tot heel andere opties leidt.

**Techniek 2, Double Diamond breed verkennen:** dwing jezelf om per probleem minstens drie soorten opties te overwegen, niet alleen de technische.
- (a) **Technisch:** een AI-tool, integratie of automatisering
- (b) **Proces:** het huidige proces anders inrichten, zonder nieuwe tooling
- (c) **Anders:** uitbesteden, anders inkopen, of iets stoppen in plaats van iets toevoegen

**Techniek 3, parking lot terugkoppelen:** kijk nu pas naar de oplossingen die de klant in Fase 1 zelf al aandroeg. Passen ze bij het wortelprobleem, of waren het aannames?

**Output:** per prioritair JTBD-statement drie tot vijf richtingen, ruw geschetst met verwachte impact en relatieve inspanning. Nog geen volledige uitwerking of business case.

---

## Fase 4 - Deliver (concreet voorstel)

**Doel:** één voorstel, in een vorm die de klant kan beoordelen en waar een concrete eerste stap uit volgt.

**Vorm, Shape Up pitch-format:**
- **Probleem** (uit Fase 2, het JTBD-statement)
- **Appetite** (uit Fase 0, hoeveel tijd/budget past hierbij)
- **Oplossing** (de gekozen richting uit Fase 3, met een korte onderbouwing waarom deze en niet de andere twee)
- **Rabbit holes** (bekende risico's of valkuilen, expliciet benoemd zodat niemand er later door verrast wordt)
- **No-gos** (wat je bewust niet doet in deze versie)

**GSD-principe:** het voorstel eindigt altijd in een concrete eerste stap die deze week of komende twee weken gezet kan worden, niet in een compleet ontwerp voor alles ineens.

**Output:** voorstel-document ter akkoord, plus eerste vervolgstap.

---

## 4. Praktijkcase: de recruiter

Ter illustratie, toegepast op de casus die jullie al hebben: een recruiter die zowel voor haar eigen bedrijf als voor klanten via LinkedIn naar kandidaten zoekt, met een duur LinkedIn-abonnement en veel handmatig werk.

**Fase 0, triage (voorbeeld):** aanleiding is waarschijnlijk de kosten van het abonnement of de tijdsdruk. Appetite-vraag onthult of dit een "we willen dit deze maand opgelost hebben" is, of een "we zijn benieuwd wat er kan" verkenning. Stakeholder is de recruiter zelf, mogelijk ook een manager die het abonnement betaalt.

**Fase 1, discover (voorbeeld vragen):**
- "Loop met me mee vanaf het moment dat je een vacature krijgt tot het moment dat er een kandidaat op gesprek komt."
- "Wat kost op dit moment de meeste tijd: het zoeken, het benaderen, of het opvolgen van reacties?"
- "Als geld geen rol speelde, hoe zou jouw ideale zoekdag eruitzien?"
- Parking lot: als de klant meteen zegt "kunnen jullie iets met de LinkedIn API bouwen", noteer je dat en gaat het gesprek door.

**Fase 2, define (voorbeeld):**
Five Whys op "het kost te veel tijd" kan uitkomen bij heel verschillende wortelproblemen, bijvoorbeeld:
- Wortelprobleem A: te veel tijd kwijt aan het handmatig doorzoeken van profielen die niet passen (een zoek/filterprobleem)
- Wortelprobleem B: kandidaten reageren traag of niet op eerste berichten (een opvolgprobleem, geen zoekprobleem)
- Wortelprobleem C: dezelfde kandidaten worden voor meerdere vacatures opnieuw vanaf nul gezocht (een hergebruik/CRM-probleem)

Dit zijn drie totaal verschillende JTBD-statements, en dus drie verschillende oplossingsrichtingen. Zonder deze fase zou je zomaar bij "we bouwen een LinkedIn-scraper" uitkomen terwijl het eigenlijke probleem opvolging of hergebruik van eerdere kandidaten is.

**Fase 3, develop (voorbeeld richtingen per wortelprobleem):**
- Voor A (zoeken/filteren): geautomatiseerde profielscreening op de bestaande zoekresultaten, óf een scherpere zoekstrategie zonder nieuwe tooling
- Voor B (opvolging): een geautomatiseerde, persoonlijke follow-up sequentie, óf simpelweg een vast opvolgmoment inplannen (procesoplossing, geen tooling nodig)
- Voor C (hergebruik): een lichte CRM/kandidatendatabase zodat eerder gevonden kandidaten doorzoekbaar blijven voor nieuwe vacatures

**Belangrijke kanttekening bij de LinkedIn API/MCP-route, die pas hier relevant wordt:** LinkedIn staat in de gebruikersvoorwaarden geautomatiseerde data-extractie en scraping niet toe, ook niet via een eigen MCP-server die achter de schermen scraped. Er bestaat een officiële LinkedIn Talent Solutions API, maar die is beperkt toegankelijk (partnerschap, geen vrije publieke toegang) en kent eigen voorwaarden. Daarnaast zijn de profielgegevens van kandidaten persoonsgegevens, wat een eigen AVG-grondslag vereist zodra je ze buiten LinkedIn opslaat of verwerkt. Dit is precies waarom dit soort afwegingen in Fase 3/4 thuishoren, en niet als eerste aanname aan het begin: het bepaalt sterk welke oplossingsrichting haalbaar is, en had het gesprek over "wat wil de klant echt" onnodig vernauwd als het vanaf het begin het uitgangspunt was geweest.

---

## 5. Sjablonen (kort, om direct te gebruiken)

**Triage-formulier:** aanleiding / wie vraagt aan + wie beslist / geschatte impact / appetite / al iets geprobeerd

**Samenvatting na Fase 2 (max 1 A4):** situatie / top pijnpunten als JTBD / expliciet buiten scope / akkoord-vraag

**Voorstel (Fase 4, Shape Up-vorm):** probleem / appetite / oplossing / rabbit holes / no-gos / eerste concrete stap

## 6. Open vragen voor Peter (dit is bewust v1)

- Past de appetite-vraag in Fase 0 bij hoe we willen binnenkomen bij een klant, of voelt dat te vroeg te transactioneel?
- Willen we de samenvatting na Fase 2 altijd schriftelijk (document/mail), of volstaat soms een mondelinge check?
- Hoeveel tijd willen we standaard reserveren voor Fase 1-2 samen (één gesprek, of bewust twee losse sessies met denktijd ertussen)?
- Testen we dit proces eerst live op de recruiter-casus voordat we het op andere klanten loslaten?

## 7. Volgende stap

Dit proces piloten op de recruiter-casus, en op basis daarvan een v2 maken met de sjablonen verder uitgewerkt (bijvoorbeeld als losse, invulbare documenten).
