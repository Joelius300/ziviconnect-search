from typing import cast

import fire
import requests

from api_types import SearchResults, PHSearchItem
from consts import LANG_CODES


def main(bearer_token: str, raw_cookie: str):
    res = search(bearer_token, raw_cookie)

    print(res)

    ph_ids = {lang: [ph["pflichtenheftId"] for ph in res[lang]] for lang in LANG_CODES.keys()}

    all_ids = [id for ids in ph_ids.values() for id in ids]

    sets = [set(l) for l in ph_ids.values()]

    list_lens = [len(l) for l in ph_ids.values()]
    set_lens = [len(s) for s in sets]

    for i in range(len(list_lens)):
        assert list_lens[i] == set_lens[i], f"Duplicates found in langauge at index {i}"

    # number of unique ph across all searches
    len_all = len(set(all_ids))
    # number of unique ph per language summed up
    len_separate = sum(set_lens)
    if len_separate > len_all:
        print("There are PH with multiple languages!")
    else:
        print("No multi-language PHs")

    print(sorted(all_ids))


def bake_cookies(raw_cookie: str):
    return dict(cookie.split("=", 1) for cookie in raw_cookie.split("; "))


def auth_session(bearer_token: str, raw_cookie: str):
    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {bearer_token}"
    s.headers.update(
        {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-zivi-locale": "de-CH",
        }
    )
    s.cookies.update(bake_cookies(raw_cookie))

    return s


def search(bearer_token: str, raw_cookie: str) -> SearchResults:
    with auth_session(bearer_token, raw_cookie) as s:
        res = {}
        for lang, lang_id in LANG_CODES.items():
            res[lang] = _search(s, lang_id)

    return cast(SearchResults, res)


def fetch_ph(ph_id: int) -> dict:
    return requests.get(
        f"https://ziviconnect.admin.ch/web-zdp/api/pflichtenheft/{ph_id}",
    ).json()


def _search(requests: requests.Session, lang_id: int) -> PHSearchItem:
    # purposeful shadowing
    res = requests.post(
        "https://ziviconnect.admin.ch/web-zdp/api/pflichtenheft/search",
        json={
            "searchText": None,
            "einsatzortId": None,
            "einsatzdauer": None,
            "taetigkeitsbereichId": [],
            "spracheId": [lang_id],
            "pflichtenheftKennzeichnungSpeziellCodeList": [],
        },
    )

    return res.json()


if __name__ == "__main__":
    fire.Fire(main)
