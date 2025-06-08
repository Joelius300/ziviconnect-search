import itertools
import json
import math
import string
from typing import Optional

import fire
import requests
from tqdm import tqdm

from api_types import PHSearchItem
from auth import auth_session
from consts import LANG_CODES, SPECIAL_AUSLAND, MAX_SEARCH_LEN, TKB_CODES


def main(bearer_token: str, raw_cookie: str, *, max_perm_len=2, allow_partial: Optional[list[str]] = None):
    res = search(bearer_token, raw_cookie, max_perm_len, allow_partial)

    with open("data/phs.json", "wt", encoding="utf-8") as file:
        json.dump(res, file, indent=2, ensure_ascii=False)

    print(f"Fetched {len(res)} Pflichtenhefte")


def search(
    bearer_token: str, raw_cookie: str, max_perm_len: int, allow_partial: Optional[list[str]]
) -> list[PHSearchItem]:
    # muss speziell gesucht werden, weil es in der API response nicht vorkommt (weder search noch PH selbst)
    #  - Sprache
    #  - Spezial Ausland
    #  - Spezial Lager
    #  - Umkreissuche theoretisch -> ableitbar von Adresse
    phs: list[PHSearchItem] = []
    with auth_session(bearer_token, raw_cookie) as s:
        with tqdm() as t:
            t.set_description("Fetching Ausland PHs")
            ausland = get_ausland(s)
            phs.extend(ausland)
            t.update(len(ausland))

            t.set_description("Fetching Lager PHs")
            lager = get_lager(s)
            phs.extend(lager)
            t.update(len(lager))

            for taetigkeit, taetigkeit_id in TKB_CODES.items():
                # no need to augment response, already contains taetigkeit
                t.set_description(f"Fetching {taetigkeit} PHs")

                # these are just too big, cannot guarantee that we get everything with this brute-force technique,
                # so just return what we can get in the best effort.
                return_part = allow_partial is not None and ("all" in allow_partial or taetigkeit in allow_partial)

                taet = search_over_lang(s, taetigkeit=taetigkeit_id, return_part=return_part, max_perm_len=max_perm_len)
                phs.extend(taet)
                t.update(len(taet))

    return deduplicate(phs)


# neither special code should need brute forcing, not many of them
def get_ausland(rq_ses: requests.Session) -> list[PHSearchItem]:
    l = search_over_lang(rq_ses, special_code=SPECIAL_AUSLAND, max_perm_len=0)
    return [ph | dict(ausland=True) for ph in l]


def get_lager(rq_ses: requests.Session) -> list[PHSearchItem]:
    l = search_over_lang(rq_ses, special_code=SPECIAL_AUSLAND, max_perm_len=0)
    return [ph | dict(lager=True) for ph in l]


def fetch_ph(requests: requests.Session, ph_id: int) -> dict:
    return requests.get(
        f"https://ziviconnect.admin.ch/web-zdp/api/pflichtenheft/{ph_id}",
    ).json()


def search_over_lang(
    requests: requests.Session,
    *,
    taetigkeit: Optional[int] = None,
    special_code: Optional[str] = None,
    min_perm_len=1,
    max_perm_len=4,
    return_part=False,
) -> list[PHSearchItem]:
    out: list[PHSearchItem] = []
    for lang, lang_id in LANG_CODES.items():
        part = search_with_brute_force(
            requests,
            lang_id=lang_id,
            taetigkeit=taetigkeit,
            special_code=special_code,
            min_perm_len=min_perm_len,
            max_perm_len=max_perm_len,
            return_part=return_part,
        )
        out.extend(ph | dict(sprache=lang) for ph in part)

    # TODO this doesn't work when brute-forcing of course
    #  Instead create a set of ids and a set of (id, lang) tuples and compare length; can also be done at end
    # assert not has_duplicates(out), "Duplicates when varying just the language = multi-language PH found"

    return out


def search_with_brute_force(
    requests: requests.Session,
    *,
    lang_id: Optional[int] = None,
    taetigkeit: Optional[int] = None,
    special_code: Optional[str] = None,
    min_perm_len=1,
    max_perm_len=4,
    return_part=False,
) -> list[PHSearchItem]:
    out = _search(requests, lang_id=lang_id, taetigkeit=taetigkeit, special_code=special_code)
    if len(out) < MAX_SEARCH_LEN:
        return out

    if min_perm_len <= 0 or max_perm_len <= 0:
        raise ValueError(f"Disabled brute forcing but got more than {MAX_SEARCH_LEN} items.")

    assert max_perm_len >= min_perm_len, "Invalid min/max perm_len config"

    # there are probably more results, so initiate brute force search
    for perm_len in range(min_perm_len, max_perm_len + 1):
        # if return_part is True, and we're in the last iteration,
        # don't check the length, just do the perm and return what you got
        check_len = (not return_part) or perm_len < max_perm_len
        part, search_aborted = search_perm(
            requests,
            perm_len,
            lang_id=lang_id,
            taetigkeit=taetigkeit,
            special_code=special_code,
            check_len=check_len,
        )
        
        out.extend(part)

        if not search_aborted:
            return deduplicate(out)

    raise ValueError(f"Even after extensively searching with perms of len {max_perm_len}, it found huge chunks; abort")


def search_perm(
    requests: requests.Session,
    perm_len: int,
    *,
    lang_id: Optional[int] = None,
    taetigkeit: Optional[int] = None,
    special_code: Optional[str] = None,
    check_len=True,
) -> tuple[list[PHSearchItem], bool]:
    """
    Returns a list of search results and a flag whether the process was aborted because a search resulted in more items than 150.
    """
    out = []
    perm_set = string.ascii_lowercase
    set_len = len(perm_set)
    for s in tqdm(
        itertools.combinations(perm_set, perm_len),
        # itertools.product(perm_set, repeat=perm_len),
        # itertools.permutations(perm_set, perm_len),
        desc=f"Brute-forcing with perm-len {perm_len}",
        total=math.comb(set_len, perm_len),
        # total=set_len**perm_len,
        # total=math.factorial(set_len) // math.factorial(set_len - perm_len),
    ):
        term = "".join(s)
        part = _search(requests, lang_id=lang_id, text=term, taetigkeit=taetigkeit, special_code=special_code)
        out.extend(part)
        
        if check_len and len(part) >= MAX_SEARCH_LEN:
            if len(out) > MAX_SEARCH_LEN:
                # no need to deduplicate if it was just one search result and then it ended
                out = deduplicate(out)

            return out, True

    return deduplicate(out), False


def deduplicate(phs: list[PHSearchItem]):
    out = []
    ids = set()
    for ph in phs:
        id = ph["pflichtenheftId"]
        if id in ids:
            continue
        ids.add(id)
        out.append(ph)

    return out


def has_duplicates(phs: list[PHSearchItem]):
    ids = [ph["pflichtenheftId"] for ph in phs]
    return len(set(ids)) != len(ids)


def _search(
    requests: requests.Session,
    *,
    lang_id: Optional[int] = None,
    text: Optional[str] = None,
    taetigkeit: Optional[int] = None,
    special_code: Optional[str] = None,
) -> list[PHSearchItem]:
    # purposeful shadowing
    res = requests.post(
        "https://ziviconnect.admin.ch/web-zdp/api/pflichtenheft/search",
        json={
            "searchText": text,
            "einsatzortId": None,
            "einsatzdauer": None,
            "taetigkeitsbereichId": [taetigkeit] if taetigkeit is not None else [],
            "spracheId": [lang_id] if lang_id is not None else [],
            "pflichtenheftKennzeichnungSpeziellCodeList": [special_code] if special_code is not None else [],
        },
    )

    res.raise_for_status()

    return res.json()


if __name__ == "__main__":
    fire.Fire(main)
