import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests
from geocoding import Geocoder, select_result
from locations import read_locations, resolve_location
from parser import ScheduleParser


def workbook(rows, title='ADRESY'):
    return SimpleNamespace(worksheets=[SimpleNamespace(title='PLAN'), SimpleNamespace(
        title=title, iter_rows=lambda **kw: iter(rows))])


def result(lat='50.1', lon='19.2', kind='hospital', house='12'):
    return {'lat': lat, 'lon': lon, 'type': kind, 'address': {'house_number': house}, 'osm_type': 'node', 'osm_id': 1}


class DynamicLocationTests(unittest.TestCase):
    def test_second_sheet_continued_subject_and_new_address(self):
        geo = Mock()
        geo.lookup.return_value = {'lat': 50.1, 'lng': 19.2}
        rows = read_locations(workbook([
            ('PRZEDMIOT', 'ADRES PLACÓWKI'),
            ('Nowy przedmiot', 'Szpital Alfa w Warszawie, ul. Długa 12'),
            (None, 'Szpital Beta w Krakowie ul. Krótka 12'),
        ], title='Lokalizacje'), geo)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]['subjects'], ['Nowy przedmiot'])
        self.assertEqual(resolve_location('Nowy przedmiot Szpital Beta w Krakowie', catalog=rows)['lat'], 50.1)
        normalized = ScheduleParser._normalize_hours([
            {'08:00-09:00': 'Nowy przedmiot Szpital Alfa w Warszawie', 'TRYB': 'stacjonarne'}
        ], catalog=rows)
        self.assertEqual(normalized[0]['hours']['08:00-09:00']['lng'], 19.2)

    def test_changed_address_does_not_reuse_old_coordinates(self):
        geo = Mock()
        geo.lookup.return_value = {'lat': 51, 'lng': 20}
        address = 'Zespół Szpitali Miejskich w Chorzowie ul. Nowa 12'
        rows = read_locations(workbook([('PRZEDMIOT','ADRES PLACÓWKI'),('Neurologia',address)]), geo)
        geo.lookup.assert_called_once_with(address)
        resolved = resolve_location('Neurologia Zespół Szpitali Miejskich w Chorzowie', catalog=rows)
        self.assertEqual(resolved, {'address':address,'lat':51,'lng':20})

    def test_missing_sheet_and_removed_rows_do_not_fall_back(self):
        geo = Mock()
        self.assertEqual(read_locations(SimpleNamespace(worksheets=[]), geo), [])
        self.assertEqual(resolve_location('Neurologia Zespół Szpitali Miejskich w Chorzowie', catalog=[]), {})
        geo.lookup.assert_not_called()

    def test_no_result_preserves_address_without_coordinates(self):
        geo = Mock()
        geo.lookup.return_value = None
        rows = read_locations(workbook([('PRZEDMIOT','ADRES PLACÓWKI'),('Nowy','Szpital Alfa ul. Długa 12')]), geo)
        self.assertEqual(resolve_location('Nowy Szpital Alfa', catalog=rows),
                         {'address':'Szpital Alfa ul. Długa 12','lat':None,'lng':None})


class GeocoderTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name)/'cache.json'
        self.geo = Geocoder(self.path)
        self.geo.session = Mock()
        self.response = Mock(status_code=200)
        self.response.json.return_value = [result()]
        self.geo.session.get.return_value = self.response

    def test_success_is_cached_across_instances(self):
        first = self.geo.lookup('Szpital ul. Długa 12')
        second = Geocoder(self.path)
        second.session = Mock()
        self.assertEqual(second.lookup('Szpital ul. Długa 12'), first)
        second.session.get.assert_not_called()
        self.geo.session.get.assert_called_once()
        self.assertEqual(first['lat'], 50.1)

    def test_seed_avoids_network(self):
        geo = Geocoder(self.path, seed=[{'address':'Długa 12','lat':50,'lng':19}])
        geo.session = Mock()
        self.assertEqual(geo.lookup('Długa 12')['lng'],19)
        geo.session.get.assert_not_called()

    def test_timeout_and_no_result_are_negatively_cached(self):
        self.geo.session.get.side_effect = requests.Timeout()
        self.assertIsNone(self.geo.lookup('Długa 12'))
        self.assertIsNone(self.geo.lookup('Długa 12'))
        self.geo.session.get.assert_called_once()

    def test_rate_limit_is_persistent(self):
        with patch('geocoding.time.time', return_value=100), patch('geocoding.time.sleep') as sleep:
            self.geo.lookup('Długa 12')
            self.geo.lookup('Krótka 12')
        sleep.assert_called_once()
        self.assertAlmostEqual(sleep.call_args.args[0],15.1)
        self.assertEqual(json.loads(self.path.read_text())['next_request_at'],115.1)

    def test_429_stops_requests_to_other_addresses(self):
        self.response.status_code = 429
        self.response.raise_for_status.side_effect = requests.HTTPError()
        self.assertIsNone(self.geo.lookup('Długa 12'))
        self.assertIsNone(self.geo.lookup('Krótka 12'))
        self.geo.session.get.assert_called_once()

    def test_rejects_ambiguous_wrong_number_and_invalid_coordinates(self):
        for values in ([result(),result()], [result(house='99')], [result(lat='nan')], [result(lon='200')]):
            with self.subTest(values=values):
                self.assertIsNone(select_result(values, 'Długa 12'))
        self.assertEqual(select_result([result(kind='restaurant'), result()], 'Długa 12')['lat'], 50.1)
