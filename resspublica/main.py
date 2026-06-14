from SPARQLWrapper import SPARQLWrapper, JSON
from feedgen.feed import FeedGenerator
from importlib.resources import files

def generateFederalFeed():
    sparql = SPARQLWrapper("https://cached.lindas.admin.ch/query")
    query = files("resspublica.queries").joinpath("federalPopularInitiatives.sparql").read_text()
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    results = sparql.query().convert()
    print(results)

def main():
    generateFederalFeed()
