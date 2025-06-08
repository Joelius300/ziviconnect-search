from concurrent.futures import ProcessPoolExecutor

import fire
import requests

from api_types import PHSearchItem


def main(workers: int = 32):
    # since a lot of network stuff is happening, I think more workers than cores works?
    with ProcessPoolExecutor(max_workers=workers) as executor:
        
    pass

def augment_ph(ph: PHSearchItem) -> Pflichtenheft:
    pass

# FYI, you can access hidden/deleted(?) PHs if you just do random numbers here. They aren't shown in ZiviConnect
# when their contact info are null (phone and mail), maybe that's their way of deleting things?
# Anyway, after you've fetched all the ones that you grabbed from the searches, you can start iterating over the
# remaining (seemingly) consecutive ids to get more (current, but mostly inactive) PHs.
def _fetch_ph(requests: requests.Session, ph_id: int) -> dict:
    return requests.get(
        f"https://ziviconnect.admin.ch/web-zdp/api/pflichtenheft/{ph_id}",
    ).json()

if __name__ == '__main__':
    fire.Fire(main)