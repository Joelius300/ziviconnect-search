from typing import TypedDict, Any, NotRequired


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
    # custom
    sprache: str
    ausland: NotRequired[bool]
    lager: NotRequired[bool]


# --- not 1:1 from API ---


class Einsatzbetrieb(TypedDict):
    id: int
    name: str
