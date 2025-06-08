from typing import TypedDict, Any


class Taetigkeitsbereich(TypedDict):
    id: int
    version: int
    domain: str
    code: str
    textDe: str
    textFr: str
    textIt: str
    sort: int


# PF = Pflichtenheft
class PHSearchItem(TypedDict):
    pflichtenheftId: int
    pflichtenheftTitel: str
    pflichtenheftNummer: int
    taetigkeitsbereich: Taetigkeitsbereich
    aufgabenbereiche: list[Any]
    bemerkungEinsatzadresse: str
    eibName: str
    eibId: int
    merkliste: bool


# --- not 1:1 from API ---


class Einsatzbetrieb(TypedDict):
    id: int
    name: str


class SearchResults(TypedDict):
    DE: list[PHSearchItem]
    FR: list[PHSearchItem]
    IT: list[PHSearchItem]
