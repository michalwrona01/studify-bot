import unittest

from locations import CATALOG, resolve_location
from parser import ScheduleParser


class LocationTests(unittest.TestCase):
    def test_every_catalog_row_resolves(self):
        self.assertEqual(len(CATALOG), 20)
        for row in CATALOG:
            with self.subTest(subject=row['subjects'][0], address=row['address']):
                result = resolve_location(row['subjects'][0] + ' zajęcia kliniczne ' + row['facilities'][0])
                self.assertEqual(result, {key: row[key] for key in ('address', 'lat', 'lng')})
                self.assertTrue(-90 <= result['lat'] <= 90)
                self.assertTrue(-180 <= result['lng'] <= 180)

    def test_same_hospital_name_uses_subject_to_choose_address(self):
        facility = 'Zespół Szpitali Miejskich w Chorzowie'
        self.assertIn('Truchana 7', resolve_location('Chirurgia dziecięca ' + facility)['address'])
        self.assertIn('Strzelców Bytomskich 11', resolve_location('Neurologia ' + facility)['address'])

    def test_unknown_online_and_other_campus_stay_unlocated(self):
        for name, mode in [
            ('Neurologia', ''), ('Nieznane zajęcia', ''),
            ('Pediatria - Kardiologia wykład Zabrze sala 404', ''),
            ('Neurologia Zespół Szpitali Miejskich w Chorzowie online', ''),
            ('Neurologia Zespół Szpitali Miejskich w Chorzowie', 'Zdalnie'),
        ]:
            with self.subTest(name=name, mode=mode):
                self.assertEqual(resolve_location(name, mode), {})

    def test_whitespace_typo_and_paks_aliases(self):
        self.assertTrue(resolve_location('TORAKOCHIRURGIA\nCentrum  Pulmunologii i Tarakochirurgii w Bystrej'))
        self.assertTrue(resolve_location('Podstawy echokardiografii ćwiczenia PAKS Bielsko-Biała'))

    def test_parser_includes_coordinates_and_preserves_lesson_name(self):
        name = 'Neurologia (IX-X) zajęcia kliniczne Zespół Szpitali Miejskich w Chorzowie'
        day = {'DATA': '2026-10-23', 'SEKCJA': '1', 'TRYB': 'Stacjonarne', '08:00-09:00': name}
        result = ScheduleParser._normalize_hours([day])[0]
        lesson = result['hours']['08:00-09:00']
        self.assertEqual(lesson['name'], name)
        self.assertIn('Strzelców Bytomskich 11', lesson['location'])
        self.assertIsInstance(lesson['lat'], float)
        self.assertIsInstance(lesson['lng'], float)
        day['TRYB'] = 'ONLINE'
        self.assertIsNone(ScheduleParser._normalize_hours([day])[0]['hours']['08:00-09:00']['lat'])
