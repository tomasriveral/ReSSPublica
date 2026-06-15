from SPARQLWrapper import SPARQLWrapper, JSON
from feedgen.feed import FeedGenerator
from importlib.resources import files
from datetime import datetime
from dateutil.relativedelta import relativedelta
from zoneinfo import ZoneInfo

def getSignatureInfo(start_date, lang="fr"):
    MONTHS = {
        "fr": ["janvier","février","mars","avril","mai","juin",
               "juillet","août","septembre","octobre","novembre","décembre"],
        "de": ["Januar","Februar","März","April","Mai","Juni",
               "Juli","August","September","Oktober","November","Dezember"],
        "it": ["gennaio","febbraio","marzo","aprile","maggio","giugno",
               "luglio","agosto","settembre","ottobre","novembre","dicembre"]
    }

    texts = {
        "fr": ("La collecte des signatures a commencé le", "et se terminera vers"),
        "de": ("Die Unterschriftensammlung begann am", "und endet ungefähr im"),
        "it": ("La raccolta delle firme è iniziata il", "e terminerà circa nel"),
    }

    end_date = start_date + relativedelta(months=18)

    def format_full(d):
        if lang == "de":
            return f"{d.day}. {MONTHS[lang][d.month - 1]} {d.year}"
        return f"{d.day} {MONTHS[lang][d.month - 1]} {d.year}"

    def format_month_year(d):
        return f"{MONTHS[lang][d.month - 1]} {d.year}"

    start = format_full(start_date)
    end = format_month_year(end_date)

    return f"""
    <p>
        {texts[lang][0]} {start} {texts[lang][1]} {end}.
    </p>
    """.strip()
def getValue(row, key):
    return row.get(key, {}).get("value") or None
def generateFeed(title, description, fileName, language, standards, entries):
    time = datetime.now(ZoneInfo("Europe/Zurich"))
    fg = FeedGenerator()
    fg.title(title)
    # We need to set a different link between atom and rss. As rss links are easier with feedgen we set fg.link for atom and fg.__rss_link for rss
    # See https://github.com/lkiesow/python-feedgen/blob/main/feedgen/feed.py#L542
    fg.link(href="https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/atom/" + language  + "/" + fileName, rel='self')
    fg.__rss_link = "https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/rss/" + language  + "/" + fileName
    fg.id("https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/atom/" + language  + "/" + fileName)
    fg.description(description)
    fg.language(language)
    fg.updated(time)
    fg.author({'name': 'ReSSPublica'})
    fg.docs("https://github.com/tomasriveral/ReSSPublica")

    for item in entries:
        fe = fg.add_entry()
        fe.title(item["title"])
        fe.guid(f"initiative-{item['id']}", permalink=False)
        fe.pubDate(item["date"])
        fe.source({'url': item["url"], 'title': item["source"]})
        fe.content(item["text"], type="html")
    if "rss" in standards:
        fg.rss_file("./feed/rss/" + language + "/" + fileName + ".xml", pretty=True)
    if "atom" in standards:
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
    BASE_PAGE = {
        "fr": "Page officielle",
        "de": "Offizielle Seite",
        "it": "Pagina ufficiale"
    }

    for entry in data:
        for lang in ["fr", "de", "it"]:
            item = {
                "id": getValue(entry, "id"),
                "date": datetime.strptime(getValue(entry, "date"), "%Y-%m-%d").replace(tzinfo=ZoneInfo("Europe/Zurich")),
                "title": getValue(entry, "title_" + lang),
                "text": getValue(entry, "text_" + lang),
                "url": BASE_URLS.get(lang, BASE_URLS["de"]) + str(getValue(entry, "id")),
                "source": BASE_SOURCE[lang]
            }
            item["text"] = "<p><a href=\""+item["url"]+"\">" + BASE_PAGE[lang] +"</a></p>" +  getSignatureInfo(item["date"], lang) + item["text"]
            feeds[lang].append(item)
    generateFeed(
        "Initiatives populaires fédérales",
        "Flux RSS des initiatives populaires fédérales",
        "initiativesPopulairesFederales",
        "fr",
        ["rss", "atom"],
        feeds["fr"]
    )
    
    generateFeed(
        "Eidgenössisch Volksinitiativen",
        "RSS-Feed der föderalen Volksinitiativen",
        "eidgenossischVolksinitiativen",
        "de",
        ["rss", "atom"],
        feeds["de"]
    )
    
    generateFeed(
        "Iniziative popolari federali",
        "Feed RSS delle iniziative popolari federali",
        "iniziativePopolariFederali",
        "it",
        ["rss", "atom"],
        feeds["it"]
    )
def main():
    generateFederalFeed()
