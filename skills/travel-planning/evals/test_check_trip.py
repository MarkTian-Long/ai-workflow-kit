"""Deterministic data checks, NOT an LLM/agent effectiveness evaluation."""
import copy,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('check_trip',ROOT/'scripts/check_trip.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ContractTests(unittest.TestCase):
 def setUp(self):self.p=json.loads((ROOT/'assets/synthetic-trip.json').read_text())
 def codes(self):return {i['code'] for i in m.check(self.p)['issues']}
 def test_01_valid_example(self):self.assertEqual(self.codes(),set())
 def test_02_known_sum(self):self.assertEqual(m.check(self.p)['known_subtotal'],2160)
 def test_03_per_person(self):self.assertEqual(m.check(self.p)['per_person_known'],1080)
 def test_04_arrival(self):self.assertEqual(m.check(self.p)['target_arrival'],'2030-05-12T16:40:00+08:00')
 def test_05_leave(self):self.assertEqual(m.check(self.p)['latest_leave'],'2030-05-12T15:20:00+08:00')
 def test_06_unknown_cost_not_zero_total(self):
  self.p['costs'][0]['unit_price']=None;self.assertFalse(m.check(self.p)['budget_complete']);self.assertIn('COST_UNKNOWN',self.codes())
 def test_07_negative_cost(self):self.p['costs'][0]['unit_price']=-1;self.assertIn('COST_INVALID',self.codes())
 def test_08_nonfinite_cost(self):self.p['costs'][0]['unit_price']=float('inf');self.assertIn('COST_INVALID',self.codes())
 def test_09_bundle_not_double_counted(self):
  self.p['costs'].append({'id':'spa','unit_price':200,'quantity':2,'basis':'per_person','included_in':'hotel'});self.assertEqual(m.check(self.p)['known_subtotal'],2160)
 def test_10_missing_bundle(self):self.p['costs'][0]['included_in']='absent';self.assertIn('COST_BUNDLE',self.codes())
 def test_11_unknown_condition(self):self.p['conditions'][0]['status']='unknown';self.assertIn('CONDITIONAL_REQUIRED',self.codes())
 def test_12_ready_with_uncertainty(self):self.p['conditions'][0]['status']='conflict';self.assertIn('CONDITIONAL_REQUIRED',self.codes())
 def test_13_candidate_not_booked(self):
  self.p['bookings'][0]['state']='candidate';self.p['bookings'][0]['display_as_booked']=True;self.assertIn('BOOKING_CLAIM',self.codes())
 def test_14_verified_needs_source(self):self.p['evidence'][0]['source']=None;self.assertIn('EVIDENCE_SOURCE',self.codes())
 def test_15_luggage_return(self):self.p['luggage'][0]['retrieve_at']='station';self.assertIn('LUGGAGE_LOOP',self.codes())
 def test_16_missing_luggage_confirmation(self):self.p['luggage'][0]['confirmed']=False;self.assertIn('LUGGAGE_UNCONFIRMED',self.codes())
 def test_17_late_departure(self):self.p['return_leg']['planned_leave']='2030-05-12T15:30:00+08:00';self.assertIn('RETURN_BUFFER',self.codes())
 def test_18_missing_timezone(self):self.p['return_leg']['event']='2030-05-12T17:20:00';self.assertIn('RETURN_INVALID',self.codes())
 def test_19_overlap(self):self.p['schedule'][1]['start']='2030-05-12T11:00:00+08:00';self.assertIn('SCHEDULE_OVERLAP',self.codes())
 def test_20_failed_weather_timestamp(self):self.p['weather'].update(state='failed',fetched_at='new');self.assertIn('WEATHER_TIMESTAMP',self.codes())
 def test_21_missing_weather_no_low_risk(self):self.p['weather'].update(wind_kmh=None,assessment='low_risk');self.assertIn('WEATHER_MISSING',self.codes())
 def test_22_public_access_needs_verification(self):self.p['publication']['claims_public_access']=True;self.assertIn('PUBLICATION_CLAIM',self.codes())
 def test_23_zero_travelers(self):self.p['travelers']=0;self.assertIn('TRAVELERS',self.codes())
 def test_24_unknown_cost_basis(self):self.p['costs'][0]['basis']='each';self.assertIn('COST_BASIS',self.codes())
 def test_25_bad_root(self):self.assertIn('ROOT',{i['code'] for i in m.check([])['issues']})
 def test_26_duplicate_ids(self):self.p['costs'].append(copy.deepcopy(self.p['costs'][0]));self.assertIn('COST_ID',self.codes())
 def test_27_bundle_cycle(self):self.p['costs'][0]['included_in']='hotel';self.p['costs'][1]['included_in']='rail';self.assertIn('COST_BUNDLE',self.codes())
 def test_28_multi_currency(self):self.p['costs'][0]['currency']='USD';self.assertIn('CURRENCY',self.codes())
 def test_29_negative_buffer(self):self.p['return_leg']['ride_min']=-1;self.assertIn('RETURN_INVALID',self.codes())
 def test_30_preserved_failure(self):self.p['weather']['state']='failed';self.assertNotIn('WEATHER_TIMESTAMP',self.codes())
if __name__=='__main__':unittest.main(verbosity=2)
