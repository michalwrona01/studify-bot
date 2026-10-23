"""Cached, single-machine Nominatim client for public institution addresses."""

import fcntl
import json
import math
import os
import re
import time
from pathlib import Path

import requests

from logger import logger


def select_result(results, address):
    """Require the requested house number; prefer a named healthcare facility."""
    numbers = re.findall(r"\b\d+(?:[-/]\d+)?[a-z]?\b", address.casefold())
    house = numbers[-1] if numbers else None
    candidates = []
    for result in results:
        details = result.get('address', {})
        if not house or str(details.get('house_number', '')).casefold() != house:
            continue
        try:
            lat, lng = float(result['lat']), float(result['lon'])
            if not (math.isfinite(lat) and math.isfinite(lng) and -90 <= lat <= 90 and -180 <= lng <= 180):
                continue
        except (KeyError, TypeError, ValueError):
            continue
        healthcare = result.get('type') in {'hospital', 'clinic', 'doctors'}
        candidates.append((healthcare, result, lat, lng))
    if not candidates:
        return None
    preferred = [entry for entry in candidates if entry[0]] or candidates
    if len(preferred) != 1:
        return None
    _, result, lat, lng = preferred[0]
    return {'lat': lat, 'lng': lng, 'display_name': result.get('display_name', ''),
            'osm_type': result.get('osm_type'), 'osm_id': result.get('osm_id')}


class Geocoder:
    def __init__(self, cache_path, seed=()):
        self.path = Path(cache_path)
        self.seed = {row['address']: {'lat': row['lat'], 'lng': row['lng'],
                                     'source': row.get('coordinate_source')} for row in seed}
        self.url = os.getenv('NOMINATIM_URL', 'https://nominatim.openstreetmap.org/search')
        self.user_agent = os.getenv('NOMINATIM_USER_AGENT', 'StudifyScheduleBot/1.0 (classroom address geocoding)')
        self.session = requests.Session()

    def lookup(self, address):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                state = json.loads(self.path.read_text()) if self.path.exists() else {}
            except (ValueError, OSError):
                logger.warning('Invalid geocoding cache; rebuilding it')
                state = {}
            entries = state.setdefault('entries', {})
            # Cache is keyed by full address and provider, never just by subject.
            key = self.url + '|' + ' '.join(address.casefold().split())
            cached = entries.get(key)
            now = time.time()
            if cached and (cached.get('point') or cached.get('retry_after', 0) > now):
                return cached.get('point')
            if address in self.seed:
                point = self.seed[address]
            else:
                if state.get('blocked_until', 0) > now:
                    return None
                delay = max(0, state.get('next_request_at', 0) - now)
                if delay:
                    time.sleep(delay)
                # Periodic scripts on the public server: at most four requests/minute.
                state['next_request_at'] = time.time() + 15.1
                self._save(state)
                try:
                    response = self.session.get(
                        self.url, params={'q': address, 'countrycodes': 'pl', 'format': 'jsonv2',
                                          'addressdetails': 1, 'limit': 10},
                        headers={'User-Agent': self.user_agent}, timeout=15,
                    )
                    if response.status_code in {403, 429}:
                        state['blocked_until'] = time.time() + 86400
                    response.raise_for_status()
                    results = response.json()
                    point = select_result(results, address) if isinstance(results, list) else None
                except (requests.RequestException, ValueError, TypeError):
                    logger.warning('Geocoding unavailable for address: %s', address)
                    point = None
                if point is None:
                    logger.warning('No unambiguous coordinates for address: %s', address)
            entries[key] = {'point': point, 'retry_after': time.time() + 86400}
            self._save(state)
            return point

    def _save(self, state):
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(self.path)
