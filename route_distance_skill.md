# Skill: Beregn afstande på ruter med poster og sløjfer

## Formål

Brug denne skill, når brugeren uploader en CSV-fil med en hovedrute,
poster og én eller flere sløjfer. Udregn den faktiske afstand langs
ruternes geometri mellem posterne, og returnér en overskuelig liste med
afstand fra foregående post.

## Forventet input

En CSV-fil, typisk med: - `WKT`: geometri i WKT-format, fx
`LINESTRING (...)` for ruter og `POINT (...)` for poster. - `navn`: navn
på ruten eller posten. - `beskrivelse`: eventuel supplerende
information.

Kolonnenavne kan variere. Undersøg altid filens kolonner og geometri,
før beregningen begynder. WKT-koordinater er normalt angivet som
længdegrad, breddegrad (x, y).

## Arbejdsgang

### 1. Indlæs og undersøg filen

1.  Læs CSV-filen med korrekt tegnsætning og separator.
2.  Vis kolonnenavne, antal rækker og eksempler på værdier.
3.  Opdel rækker i linjegeometrier (`LINESTRING`/`MULTILINESTRING`) og
    punktgeometrier (`POINT`/`MULTIPOINT`).
4.  Udtræk navnene på hovedruten, sløjferne og posterne. Brug ikke
    rækkefølgen i CSV-filen som eneste indikator for ruteforløbet.

### 2. Beregn afstande korrekt

-   Mål afstand langs rutelinjens faktiske geometri, ikke luftlinje
    mellem poster.
-   Da WKT-koordinater typisk er i længdegrad/breddegrad, skal længder
    beregnes geodætisk eller efter projektion til et passende metrisk
    koordinatsystem.
-   I Danmark kan ETRS89 / UTM zone 32N (EPSG:25832) normalt bruges til
    metriske afstande. Alternativt kan geodætiske afstande beregnes
    segment for segment.
-   Summér længden af de relevante linjesegmenter mellem de punkter, der
    markerer poster eller tilslutninger.
-   Rund som standard til nærmeste hele meter, medmindre brugeren ønsker
    en anden præcision.
-   Kontrollér, at afstandene er ikke-negative, og at delstrækningerne
    følger den tegnede rute.

### 3. Find posternes placering på ruten

1.  Match hvert postpunkt med det relevante sted på hovedruten eller
    sløjfen.
2.  Hvis et punkt ligger lidt ved siden af linjen på grund af
    GPS-/tegnepræcision, find det nærmeste punkt på den relevante
    rutelinje og notér eventuelt usikkerheden.
3.  Hvis samme rute passerer tæt på sig selv, må nærmeste punkt ikke
    vælges blindt. Brug rutens rækkefølge, naboposter og rutens forløb
    til at identificere den korrekte position.
4.  Hvis en post kan knyttes til flere steder, eller rutegeometrien ikke
    giver en entydig fortolkning, bed om afklaring frem for at opfinde
    et præcist resultat.

### 4. Beregn hovedruten

-   Identificér rækkefølgen fra Start til Mål.
-   Beregn hver delstrækning mellem på hinanden følgende poster langs
    hovedrutens geometri.
-   Medtag kun den rute, der faktisk forbinder de to poster; undgå at
    måle en direkte luftlinje.

### 5. Beregn hver sløjfe

For hver sløjfe: 1. Find det sted, hvor sløjfen forlader hovedruten. 2.
Find sløjfens poster i den rækkefølge, de mødes langs sløjfen. 3. Find
det sted, hvor sløjfen vender tilbage til hovedruten. 4. Beregn afstand
fra tilslutningspunktet på hovedruten til første post på sløjfen, mellem
sløjfens poster og videre fra sidste post til **den første efterfølgende
post på hovedruten**. 5. Hvis sløjfen starter ved en navngiven
hovedrutepost, brug den post som start for første delstrækning. 6. Hvis
sløjfen vender tilbage til hovedruten mellem to poster, beregn også
afstanden fra sløjfens afsluttende post til den første efterfølgende
hovedrutepost langs den relevante hovedrutestrækning. 7. Hold sløjfens
afstande adskilt fra hovedrutens almindelige delstrækninger, så der ikke
opstår dobbeltoptælling.

### 6. Kontroller resultatet

-   Kontrollér, at hver post kun forbindes til den korrekte foregående
    post i den viste rute.
-   Sammenlign summen af delstrækninger med længden af den relevante del
    af rutelinjen.
-   Vær opmærksom på, at en post kan være en markør ved siden af ruten,
    og at en sløjfe kan dele et stykke geometri med hovedruten.
-   Skeln mellem målte værdier og antagelser. Angiv ikke afstande som
    præcise, hvis geometrien ikke understøtter det.
-   Hvis data ikke kan læses, eller en rute ikke kan matches entydigt,
    forklar præcist hvad der mangler.

## Outputformat

Returnér resultatet på dansk med én tabel pr. rute/sløjfe:

  Fra post                Til post       Afstand
  ----------------------- ------------ ---------
  Start/foregående post   Næste post      1.4 km

-   Brug de fulde postnavne fra filen, hvis de findes.
-   For hovedruten skal alle delstrækninger fra Start til Mål medtages.
-   For hver sløjfe skal listen gå til og med den første efterfølgende
    post på hovedruten.
-   Angiv afstande i kilometer med to decimaler
-   Angiv sløjfens samlede længde, hvis det er nyttigt, men adskil den
    fra de enkelte delstrækninger.
-   Skriv kort, hvis der er usikkerhed eller behov for manuel kontrol.

## Vigtige regler

-   Brug aldrig luftlinjeafstand som erstatning for rutelængde.
-   Udled ikke sløjfernes tilslutningspunkter alene fra postnumre; brug
    geometrien.
-   Opfind ikke manglende afstande.
-   Kontrollér beregningerne på den aktuelle fil hver gang. Tidligere
    ruter eller tidligere afstandstal må ikke genbruges som om de gjaldt
    for den nye fil.
-   Hvis brugeren beder om kun sløjferne, returnér kun sløjferne.
