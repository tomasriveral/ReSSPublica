from SPARQLWrapper import SPARQLWrapper, JSON
from feedgen.feed import FeedGenerator

def generateFederalFeed():
    sparql = SPARQLWrapper("https://cached.lindas.admin.ch/sparql")
    sparql.setQuery(open("../queries/popular_initiatives.sparql").read())
    sparql.setReturnFormat(JSON)

    results = sparql.query().convert()
    print(results)

def main():
    generateFederalFeed()
