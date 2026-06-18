### Why

The Swiss governement publishes daily lots of information scattered on the internet (newsletters, sparql endpoints, RTS/SSR/RSI, APIs, ...).
We aim to make it more accessible with RSS (and Atom).

[RSS](https://en.wikipedia.org/wiki/RSS) is a standard web feed (compatible with blogs, journals, YouTube and much more!) that you can access on a multitude of rss readers on all your device. For more information, see [All about RSS](https://github.com/AboutRSS/ALL-about-RSS).

### Feeds

| Title | Description | Source | de | fr | it  | rm | en |
|-------|-------------|--------|----|----|-----|----|----|
| Federal initiatives | New federal popular initiatives in the signature stage. | [LINDAS](https://cached.lindas.admin.ch/) (See [query](https://github.com/tomasriveral/ReSSPublica/blob/main/resspublica/queries/federalPopularInitiatives.sparql)) | [RSS](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/rss/de/eidgenossischVolksinitiativen.xml) [Atom](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/atom/de/eidgenossischVolksinitiativen.atom) | [RSS](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/rss/fr/initiativesPopulairesFederales.xml) [Atom](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/atom/fr/initiativesPopulairesFederales.atom) | [RSS](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/rss/it/iniziativePopolariFederali.xml) [Atom](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/atom/it/iniziativePopolariFederali.atom) |
| Asian hornet sightings in Bern | Weekly map of the sightings of the Asian Hornet (an invasive species see [frelonasiatique.ch](https://frelonasiatique.ch/)) in the Canton of Bern| [opendata.swiss](https://opendata.swiss/en/dataset/asiatische-hornisse) | [RSS](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/rss/de/sichtungenAsiatischerHornissenBern.xml) [Atom](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/atom/de/sichtungenAsiatischerHornissenBern.atom) | [RSS](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/rss/fr/observationsFrelonsAsiatiquesBerne.xml) [Atom](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/atom/fr/observationsFrelonsAsiatiquesBerne.atom) | [RSS](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/rss/it/avvistamentiCalabroniAsiaticiBerna.xml) [Atom](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/atom/it/avvistamentiCalabroniAsiaticiBerna.atom) | [RSS](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/rss/rm/observaziunsVesprasAsiaticasBerna.xml) [Atom](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/atom/rm/observaziunsVesprasAsiaticasBerna.atom) | [RSS](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/rss/en/asianHornetSightingsInBern.xml) [Atom](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/atom/en/asianHornetSightingsInBern.atom) |
| Places of worship in Bern[^1]| Trimestrial map update of places of worship per religion in Bern | [opendata.swiss](https://opendata.swiss/en/dataset/religionslandkarte) | [RSS](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/rss/de/gotteshauserNachReligionImKantonBern.xml) [Atom](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/atom/de/gotteshauserNachReligionImKantonBern.atom) | [RSS](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/rss/fr/lieuDeCulteParReligionDansLeCantonDeBerne.xml) [Atom](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/atom/fr/lieuDeCulteParReligionDansLeCantonDeBerne.atom) |

[^1]: I hate needing to say this, but this feed is provided solely for transparency and informational purposes. It must not be used for harassment, discrimination, radicalization, or any other harmful activity. If you are triggered by a rss feed, please remove it from your feed reader and go consult a psychiatrist.

All the data is already public. We gather it with the following methods :
* SPARQL requests
* opendata.swiss API

## AI Disclaimer

AI (ChatGPT 5.5 and Deepl) was used in this project for :
* crafting the SPARQL requests (a language I had never heard of before this project)
* minor debugging when alternative methods did not solve the problems.
* German, Italian and Romansh translations.
* help with Python libraries (that I did not knew/used before)

All code, text and files in this repo was reviewed by a human ([me](https://github.com/tomasriveral)).
