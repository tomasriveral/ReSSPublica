Project curently in devellopment.

### Why

The Swiss governement publishes daily lots of information scattered on the internet (newsletters, sparql endpoints, RTS/SSR/RSI, ...).
We aim to make it more accessible with RSS (and Atom).

[RSS](https://en.wikipedia.org/wiki/RSS) is a standard web feed that you can access on a multitude of application on all your device. For more information, see [All about RSS](https://github.com/AboutRSS/ALL-about-RSS).

### Feeds

| Title | Description | Source | de | fr | it  |
|-------|-------------|--------|----|----|-----|
| Federal initiatives | New federal popular initiatives in the signature stage. | [LINDAS](https://cached.lindas.admin.ch/) (See [query](https://github.com/tomasriveral/ReSSPublica/blob/main/resspublica/queries/federalPopularInitiatives.sparql)) | [RSS](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/rss/de/eidgenossischVolksinitiativen.xml) [Atom](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/atom/de/eidgenossischVolksinitiativen.atom) | [RSS](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/rss/fr/initiativesPopulairesFederales.xml) [Atom](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/atom/fr/initiativesPopulairesFederales.atom) | [RSS](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/rss/it/iniziativePopolariFederali.xml) [Atom](https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/atom/it/iniziativePopolariFederali.atom) |


All the is already public. We gather it with the following methods :
* SPARQL requests

## AI Disclaimer

AI (ChatGPT 5.5 and Deepl) was used in this project for :
* crafting the SPARQL requests (a language I had never heard of before this project)
* minor debugging when alternative methods did not solve the problems.
* German, Italian and Romansh translations.

## Contributing

If you want to help this project, you can :
* find new, open and interesting data for a new feed. (You can open an issue to request a feed). [awesome-ogd-switzerland](https://github.com/rnckp/awesome-ogd-switzerland) is a good start if you want to see which data is available.
* create new feeds.
* help with the translations. The goal would be to have feeds in English, French, German, Italian and Romansh. However, some data is only available in French, German and Italian. You are welcome to translate and/or verify translations. (See `./resspublica/translations.py`.
* help popularize RSS by talking to friends, family and more, opening blogs and requesting news outlets or other entities to have an rss option. Besides this project, I truely think RSS is a standard that could resolve multiples current issues (such as the problems of algorithimic social media).
