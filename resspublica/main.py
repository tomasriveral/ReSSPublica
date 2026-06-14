from SPARQLWrapper import SPARQLWrapper, JSON
from feedgen.feed import FeedGenerator
from importlib.resources import files
from datetime import datetime


def getValue(row, key):
    return row.get(key, {}).get("value") or None
def generateFeed(title, description, fileName, language, standards, entries):
    time = datetime.now()
    fg = FeedGenerator()
    fg.title(title)
    fg.link("https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/" + standard + "/" + language  + "/" + fileName)
    fg.description(description)
    fg.language(language)
    fg.updated(time)
    fg.author({'name': 'ReSSPublica'})
    fg.docs("https://github.com/tomasriveral/ReSSPublica")

    for item in entries:
        fe = fg.add_entry()
        fe.title(item["title"])
        fe.guid(f"initiative-{item['id']}", permalink=False)
        fe.updated(time)
        fe.source({'url': item["url"], 'title': item["source"]})
        fe.link(url)
        fe.description(item["article")
        fe.summary(item["article")
        fe.content(item["text"])
    
    fg.rss_file("./feed/rss/" + language + "/" + fileName + ".xml", pretty=True)
    fg.atom_file("./feed/atom/" + language + "/" + fileName + ".atom", pretty=True)

def generateFederalFeed():
    sparql = SPARQLWrapper("https://cached.lindas.admin.ch/query")
    query = files("resspublica.queries").joinpath("federalPopularInitiatives.sparql").read_text()
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    results = sparql.query().convert()

    # remove some of useless json data such as "head": {"vars": [...]}
    data = results["results"]["bindings"]

    feeds = {
      "fr": [],
      "de": [],
      "it": []
    }

    BASE_URLS = {
        "fr": "https://www.bk.admin.ch/fr/details-initiatives-populaires/?initiative=",
        "de": "https://www.bk.admin.ch/de/details-volksinitiativen/?initiative=",
        "it": "https://www.bk.admin.ch/it/dettagli-iniziative-popolari/?initiative="
    }
    BASE_SOURCE = {
        "fr": "Chancellerie fédérale ChF",
        "de": "Bundeskanzlei BK",
        "it": "Cancelleria federale CaF"
    }

    for entry in data:
        for lang in ["fr", "de", "it"]:
            item = {
                "id": getValue(entry, "id"),
                "date": getValue(entry, "date"),
                "title": getValue(entry, "title_" + lang),
                "article": getValue(entry, "artikel_" + lang),
                "text": getValue(entry, "text_" + lang),
                "url": BASE_URLS.get(lang, BASE_URLS["de"]) + str(getValue(entry, "id")),
                "source": BASE_SOURCE[lang]
            }
            feeds[lang].append(item)
    print(feeds["fr"])
    generateFeed("Initiatives populaires fédérales", "RSS feed des Initiatives populaires fédérales", "initiativesPopulairesFederales", "fr", [ "rss" "atom"], feeds[fr]);
def main():
    generateFederalFeed()
