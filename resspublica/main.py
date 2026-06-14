from SPARQLWrapper import SPARQLWrapper, JSON
from feedgen.feed import FeedGenerator
from importlib.resources import files

def getValue(row, key):
    return row.get(key, {}).get("value") or None

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

    for entry in data:
        for lang in ["fr", "de", "it"]:
            item = {
                "id": getValue(entry, "id"),
                "date": getValue(entry, "date"),
                "title": getValue(entry, "title_" + lang),
                "article": getValue(entry, "artikel_" + lang),
                "text": getValue(entry, "text_" + lang)
            }
            feeds[lang].append(item)
    print(feeds["fr"])
def main():
    generateFederalFeed()
