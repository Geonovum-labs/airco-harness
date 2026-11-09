"""Optioneel — bronnencontrole: bereikbaarheid van alle URI's + host op de bekende bronnenlijst.

Gebruik: python bronnencontrole.py uit/kader.ttl reports/bronnencontrole.tsv \
             [--skosmos https://definities.geostandaarden.nl/rest/v1/<kader>] [--bronnenlijst pad/bronnenlijst.md]

Controleert dct:source-objecten, harmonisatiedoelen, het kader, begrippen en collecties.
--skosmos: begrippen binnen het kader via de REST-API controleren (`label?uri=`), veel sneller
dan de HTML-pagina's. Bij HTTP 429 (rate limiting) wordt rustig opnieuw geprobeerd.
Interpretatie (NL-SBB-skill): 4xx/5xx = waarschuwing; blokkade door de omgeving
(x-deny-reason / 'Host not in allowlist') = niet getest; timeout/DNS = onzeker.
"""
import argparse
import collections
import concurrent.futures as cf
import csv
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rdflib  # noqa: E402
from rdflib import RDF  # noqa: E402
from rdflib.namespace import DCTERMS, SKOS  # noqa: E402

from kern import curl_status  # noqa: E402


def check(url):
    code, deny = curl_status(url, accept="text/html,*/*")
    if deny:
        return "geblokkeerd"
    return code if code != "000" else "timeout/DNS"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kader")
    ap.add_argument("uit")
    ap.add_argument("--skosmos")
    ap.add_argument("--bronnenlijst")
    ap.add_argument("--parallel", type=int, default=3)
    a = ap.parse_args()

    g = rdflib.Graph().parse(a.kader)
    scheme = next(g.subjects(RDF.type, SKOS.ConceptScheme))
    items = [("kader", str(scheme))]
    items += [("bron", str(o)) for o in sorted(set(g.objects(None, DCTERMS.source)))]
    items += [("match", str(o)) for p in ("exactMatch", "closeMatch", "broadMatch", "narrowMatch", "relatedMatch")
              for o in sorted(set(g.objects(None, SKOS[p])))]
    items += [("begrip", str(c)) for c in sorted(set(g.subjects(RDF.type, SKOS.Concept)))]
    items += [("collectie", str(c)) for c in sorted(set(g.subjects(RDF.type, SKOS.Collection)))]

    def url_voor(soort, u):
        if soort == "begrip" and a.skosmos:
            return a.skosmos.rstrip("/") + "/label?uri=" + urllib.parse.quote(u, safe="")
        return u

    with cf.ThreadPoolExecutor(a.parallel) as ex:
        res = list(ex.map(lambda it: check(url_voor(*it)), items))

    bekend = set()
    if a.bronnenlijst:
        bekend = set(re.findall(r"^\|\s*`([^`]+)`", open(a.bronnenlijst, encoding="utf-8").read(), re.M))
    with open(a.uit, "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["soort", "uri", "http", "host", "bekende_bron"])
        tel = collections.Counter()
        for (soort, u), r in zip(items, res):
            host = urllib.parse.urlparse(u).hostname or ""
            bk = "ja" if host in bekend else ("nee" if bekend else "")
            w.writerow([soort, u, r, host, bk])
            tel[(soort, host, bk, r)] += 1
    print("soort      host                                   bekend  http    aantal")
    for (s, h, bk, r), n in sorted(tel.items()):
        print(f"{s:10} {h:38} {bk:7} {r:7} {n}")
    print(f"-> {a.uit}")


if __name__ == "__main__":
    main()
