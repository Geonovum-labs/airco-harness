"""Stap 1 (alternatief) — Enterprise Architect-repository (.eap/.eapx of .qea/.qeax) -> inventaris.json.

Gebruik: python inventaris_eap.py model.eap werk/inventaris.json --package IMGEO [--package ...] [--zonder deprecated]

Een EA-repository bevat vaak meer dan het model zelf (bv. CityGML, GML, NEN 3610). Kies daarom
met --package welke package(s) (inclusief subpackages) worden omgezet. Een naam mag een pad zijn
(`IMEV-conceptueel/Waardelijsten`) als dezelfde naam vaker voorkomt; --zonder sluit subpackages uit. Zonder --package toont
het script de packageboom en stopt (exitcode 1): leg de keuze dan voor aan de gebruiker.
Klassen buiten de gekozen packages tellen als externe klassen (bv. superklassen).

Uitvoer heeft dezelfde vorm en dezelfde id's (EAID_<guid>) als inventaris.py op een XMI-export.
.eap/.eapx = Access-database (gelezen met access-parser, pure Python);
.qea/.qeax = SQLite (standaardbibliotheek).
"""
import argparse
import json
import logging
import re
import sqlite3
import sys
from collections import Counter

TABELLEN = ["t_package", "t_object", "t_objectproperties", "t_attribute", "t_attributetag", "t_connector"]
UMLTYPE = {"Class": "uml:Class", "Enumeration": "uml:Enumeration", "DataType": "uml:DataType",
           "Interface": "uml:Interface"}


def lees_access(pad):
    logging.disable(logging.CRITICAL)  # access-parser logt veel ruis over systeemtabellen
    from access_parser import AccessParser
    import access_parser.access_parser as ap

    verloren, huidig = Counter(), [""]

    def overflow(self, ptr):
        """Vervangt AccessTable._get_overflow_record (access-parser 0.0.6).
        Het origineel maskeert de vlagbits van de recordgrens niet (`end & 0xff != 0` is door de
        operatorvolgorde `end & True`) en leest dan door tot het einde van de pagina, waardoor
        teksten van volgende records aan een memo worden geplakt. Ontbrekende pagina's worden
        geteld in plaats van te crashen."""
        offset, page = ptr & 0xFF, ptr >> 8
        rec = self._data_pages.get(page * self.page_size)
        if not rec:
            verloren[huidig[0]] += 1
            return b"\0\0\0\0"
        offs = ap.parse_data_page_header(rec, version=self.version).record_offsets
        if offset >= len(offs):
            verloren[huidig[0]] += 1
            return b"\0\0\0\0"
        start = offs[offset] & 0x1FFF
        return rec[start:] if offset == 0 else rec[start:offs[offset - 1] & 0x1FFF]
    ap.AccessTable._get_overflow_record = overflow

    orig_parse_type = ap.parse_type

    def parse_type(data_type, buffer, length=None, version=3, props=None):
        """Vervangt parse_type voor tekst met 'compressed unicode' (Jet 4, begint met FF FE).
        access-parser 0.0.6 decodeert dat als UTF-8/Latin-1 en gooit NUL-bytes weg, waardoor
        tekens buiten Latin-1 (bv. '–' U+2013) als losse lage byte (\\x13) overblijven.
        Algoritme zoals mdbtools: byte 0x00 wisselt tussen 1-byte- en 2-bytemodus."""
        if data_type == ap.TYPE_TEXT and version > 3 and buffer[:2] == b"\xff\xfe":
            out, comp, i, src = bytearray(), True, 2, bytes(buffer)
            while i < len(src):
                if src[i] == 0:
                    comp, i = not comp, i + 1
                elif comp:
                    out += bytes((src[i], 0))
                    i += 1
                elif i + 1 < len(src):
                    out += src[i:i + 2]
                    i += 2
                else:
                    break
            return out.decode("utf-16-le", errors="replace")
        return orig_parse_type(data_type, buffer, length, version=version, props=props)
    ap.parse_type = parse_type

    db = AccessParser(pad)
    data = {}
    for t in TABELLEN:
        huidig[0] = t
        d = db.parse_table(t)
        ks = list(d)
        data[t] = [dict(zip(ks, v)) for v in zip(*d.values())]
    return data, verloren


def lees_sqlite(pad):
    con = sqlite3.connect(f"file:{pad}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return {t: [dict(r) for r in con.execute(f"select * from {t}")] for t in TABELLEN}, Counter()


def eaid(guid):
    return "EAID_" + (guid or "").strip("{}").replace("-", "_")


ZONDER_GUID = {"t_object": set(), "t_attribute": set()}


def oid_id(o):
    """Id van een object; zonder leesbare ea_guid (komt voor bij access-parser) een id op Object_ID,
    zodat objecten niet samenvallen. Zulke id's wijken af van een XMI-export (alleen intern gebruikt)."""
    g = (ci(o, "ea_guid") or "").strip()
    if g:
        return eaid(g)
    ZONDER_GUID["t_object"].add(ci(o, "Object_ID"))
    return f"EAOBJ_{ci(o, 'Object_ID')}"


def att_id(at):
    g = (ci(at, "ea_guid") or "").strip()
    if g:
        return eaid(g)
    ZONDER_GUID["t_attribute"].add(ci(at, "ID"))
    return f"EAATT_{ci(at, 'ID')}"


ONLEESBAAR = []


def s(v, wat=None):
    """Tekst; Windows-regeleinden (\r\n) zoals in de XMI-export naar \n. access-parser geeft bij een
    onleesbaar memoveld bytes terug; dat wordt lege tekst en gemeld (wat = beschrijving voor de melding)."""
    if isinstance(v, (bytes, bytearray)):
        if wat:
            ONLEESBAAR.append(wat)
        return ""
    return "" if v is None else str(v).replace("\r\n", "\n")


def past(pad, naam):
    """Package-pad eindigt op 'naam' (een naam of een pad als 'Ouder/Kind')."""
    delen = naam.strip("/").split("/")
    return pad[-len(delen):] == delen


def ci(row, key):
    """Kolommen hebben per EA-versie/database soms andere hoofdletters (VALUE/Value)."""
    for k in row:
        if k.lower() == key.lower():
            return row[k]
    return None


def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("bron")
    ap_.add_argument("uit")
    ap_.add_argument("--package", action="append", default=[])
    ap_.add_argument("--zonder", action="append", default=[])
    a = ap_.parse_args()

    if a.bron.lower().endswith((".qea", ".qeax")):
        data, verloren = lees_sqlite(a.bron)
    else:
        data, verloren = lees_access(a.bron)

    pk = {int(ci(p, "Package_ID")): p for p in data["t_package"]}
    kinderen = {}
    for p in pk.values():
        kinderen.setdefault(int(ci(p, "Parent_ID") or 0), []).append(int(ci(p, "Package_ID")))

    def pad(pid):
        uit = []
        while pid in pk:
            uit.insert(0, s(ci(pk[pid], "Name")))
            pid = int(ci(pk[pid], "Parent_ID") or 0)
        return uit

    objs = data["t_object"]
    tel = Counter(int(ci(o, "Package_ID") or 0) for o in objs if ci(o, "Object_Type") in UMLTYPE)
    if not a.package:
        print("Kies met --package welke package(s) worden omgezet. Packageboom (aantal klassen):")

        def toon(pid, d):
            print(f"{'  ' * d}{ci(pk[pid], 'Name')} ({tel.get(pid, 0)})")
            for k in sorted(kinderen.get(pid, []), key=lambda x: s(ci(pk[x], "Name"))):
                toon(k, d + 1)
        for r in sorted(kinderen.get(0, [])):
            toon(r, 0)
        sys.exit(1)

    def zoek(naam):
        ids = [pid for pid in pk if past(pad(pid), naam)]
        if not ids:
            sys.exit(f"Package '{naam}' niet gevonden")
        return ids

    gekozen, uit = set(), {pid for n in a.zonder for pid in zoek(n)}
    for naam in a.package:
        stack = zoek(naam)
        while stack:
            pid = stack.pop()
            if pid in uit:
                continue
            gekozen.add(pid)
            stack += kinderen.get(pid, [])

    by_oid = {int(ci(o, "Object_ID")): o for o in objs}
    elems, oid2id = {}, {}
    # volgorde zoals de XMI-export van EA: per package (boomvolgorde), dan TPos en naam
    volg = []

    def boom(pid):
        volg.append(pid)
        for k in sorted(kinderen.get(pid, []), key=lambda x: (int(ci(pk[x], "TPos") or 0), s(ci(pk[x], "Name")))):
            boom(k)
    for r in sorted(kinderen.get(0, [])):
        boom(r)
    rang = {pid: n for n, pid in enumerate(volg)}
    for o in sorted(objs, key=lambda o: (rang.get(int(ci(o, "Package_ID") or 0), 1e9),
                                         int(ci(o, "TPos") or 0), s(ci(o, "Name")))):
        if ci(o, "Object_Type") not in UMLTYPE or not ci(o, "Name"):
            continue
        if int(ci(o, "Package_ID") or 0) not in gekozen:
            continue
        i = oid_id(o)
        oid2id[int(ci(o, "Object_ID"))] = i
        ppath = pad(int(ci(o, "Package_ID")))
        elems[i] = dict(name=s(ci(o, "Name")), type=UMLTYPE[ci(o, "Object_Type")],
                        doc=s(ci(o, "Note"), f"definitie van {s(ci(o, 'Name'))}"),
                        alias=ci(o, "Alias") or None, stereo=ci(o, "Stereotype") or None,
                        pkg=ppath[-1] if ppath else None, pkg_path=ppath,
                        abstract=s(ci(o, "Abstract")) == "1", tags={}, attrs=[], gens=[])

    def tagwaarde(t, kol, notes):
        """Memo-tags: waarde '<memo>', de tekst staat in de notitiekolom."""
        v, n = s(ci(t, kol)), s(ci(t, notes)).strip()
        # 'Default: ...' / 'Description: ...' is de beschrijving van de tag, geen inhoud
        return n if v == "<memo>" and n and not re.match(r"(Default|Description):", n) else v

    for t in data["t_objectproperties"]:
        i = oid2id.get(int(ci(t, "Object_ID") or 0))
        if i:
            elems[i]["tags"][s(ci(t, "Property"))] = tagwaarde(t, "Value", "Notes")

    atags = {}
    for t in data["t_attributetag"]:
        atags.setdefault(int(ci(t, "ElementID") or 0), {})[s(ci(t, "Property"))] = tagwaarde(t, "VALUE", "NOTES")
    for at in sorted(data["t_attribute"], key=lambda r: (int(ci(r, "Object_ID") or 0), int(ci(r, "Pos") or 0),
                                                         s(ci(r, "Name")))):
        i = oid2id.get(int(ci(at, "Object_ID") or 0))
        if not i:
            continue
        cl = ci(at, "Classifier")
        cl = int(cl) if cl not in (None, "", "0") else None
        tid = (oid2id.get(cl) or (oid_id(by_oid[cl]) if cl in by_oid else None)) if cl else None
        elems[i]["attrs"].append(dict(
            id=att_id(at), name=s(ci(at, "Name")),
            doc=s(ci(at, "Notes"), f"definitie van {elems[i]['name']}.{s(ci(at, 'Name'))}"),
            type_id=tid, type=ci(at, "Type") or None, stereo=ci(at, "Stereotype") or None,
            lower=ci(at, "LowerBound"), upper=ci(at, "UpperBound"),
            tags=atags.get(int(ci(at, "ID")), {}), alias=ci(at, "Style") or None))

    externe = {}
    for c in data["t_connector"]:
        if ci(c, "Connector_Type") != "Generalization":
            continue
        src, dst = int(ci(c, "Start_Object_ID") or 0), int(ci(c, "End_Object_ID") or 0)
        if src in oid2id and dst in by_oid:
            gid = oid2id.get(dst) or oid_id(by_oid[dst])
            elems[oid2id[src]]["gens"].append(gid)
            if dst not in oid2id:
                externe[gid] = s(ci(by_oid[dst], "Name"))
    # namen van overige klassen buiten de selectie waarnaar attributen verwijzen
    for c in elems.values():
        for at in c["attrs"]:
            if at["type_id"] and at["type_id"] not in elems:
                o = next((o for o in objs if oid_id(o) == at["type_id"]), None)
                if o is not None and ci(o, "Object_Type") in UMLTYPE:
                    externe.setdefault(at["type_id"], s(ci(o, "Name")))

    json.dump(dict(bron=a.bron, elementen=elems, externe_klassen=externe),
              open(a.uit, "w"), ensure_ascii=False, indent=1)
    print(f"{len(elems)} elementen, {sum(len(c['attrs']) for c in elems.values())} attributen/waarden, "
          f"{len(externe)} externe klassen")
    for (t, st), n in sorted(Counter((c["type"], c["stereo"]) for c in elems.values()).items(), key=str):
        print(f"  {t:16} {str(st):20} {n}")
    if ONLEESBAAR:
        print(f"LET OP: {len(ONLEESBAAR)} memovelden onleesbaar (access-parser), als leeg behandeld: "
              + "; ".join(ONLEESBAAR) + ". Controleer deze in EA of gebruik een XMI-export.")
    if any(ZONDER_GUID.values()):
        print(f"LET OP: ea_guid niet leesbaar ({ {k: len(v) for k, v in ZONDER_GUID.items() if v} }); id op Object_ID/ID gebruikt "
              "(EAOBJ_/EAATT_). Begrippen zijn correct, maar id's wijken af van een XMI-export.")
    if verloren:
        print(f"LET OP: memovelden niet leesbaar per tabel {dict(verloren)} (overflowpagina ontbreekt). "
              "In t_connector is dat onschuldig (alleen opmaak/notities); in t_object of t_attribute "
              "kunnen definities ontbreken: vergelijk dan met een XMI-export.")
        print(f"  {verloren} memovelden niet leesbaar (overflowpagina ontbreekt); "
              "controleer definities of exporteer naar XMI")


if __name__ == "__main__":
    main()
