"""Offline checks for the documented mini-contract. Does not verify travel facts or AI quality."""
import argparse
import json
import math
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

BASIS = {'per_person', 'room_night', 'vehicle', 'vehicle_day', 'group'}


def aware(value):
    dt = datetime.fromisoformat(value)
    if dt.utcoffset() is None:
        raise ValueError('timestamp needs UTC offset')
    return dt


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def check(data):
    out = {'issues': [], 'known_subtotal': 0, 'per_person_known': None,
           'target_arrival': None, 'latest_leave': None, 'budget_complete': True}
    def add(code, detail):
        out['issues'].append({'code': code, 'detail': detail})
    if not isinstance(data, dict):
        add('ROOT', 'Expected a JSON object.'); return out
    people = data.get('travelers')
    if not isinstance(people, int) or isinstance(people, bool) or people < 1:
        add('TRAVELERS', 'travelers must be a positive integer.')
    ready = data.get('recommendation') == 'ready'
    for item in data.get('conditions', []):
        if ready and item.get('status') not in ('verified', 'user_provided'):
            add('CONDITIONAL_REQUIRED', str(item.get('id')))
    for item in data.get('evidence', []):
        if item.get('status') == 'verified' and not all(item.get(k) for k in ('source', 'checked_at', 'valid_for')):
            add('EVIDENCE_SOURCE', str(item.get('id')))
    for item in data.get('bookings', []):
        if item.get('display_as_booked') and item.get('state') != 'booked':
            add('BOOKING_CLAIM', str(item.get('id')))
    for item in data.get('luggage', []):
        if not item.get('stored_at') or item.get('stored_at') != item.get('retrieve_at'):
            add('LUGGAGE_LOOP', str(item.get('day')))
        if ready and not item.get('confirmed'):
            add('LUGGAGE_UNCONFIRMED', str(item.get('day')))
    leg = data.get('return_leg')
    if leg:
        try:
            event = aware(leg['event'])
            values = [leg[k] for k in ('arrival_buffer_min', 'ride_min', 'wait_min', 'pickup_min')]
            if not all(number(x) for x in values):
                raise ValueError('invalid time budget')
            arrival = event - timedelta(minutes=values[0])
            leave = event - timedelta(minutes=sum(values))
            out.update(target_arrival=arrival.isoformat(), latest_leave=leave.isoformat())
            if aware(leg['planned_leave']) > leave:
                add('RETURN_BUFFER', 'Planned departure consumes the stated return buffer.')
        except (KeyError, ValueError, TypeError, OverflowError):
            add('RETURN_INVALID', 'Return times need offset-aware ISO dates and nonnegative minutes.')
    intervals = []
    for item in data.get('schedule', []):
        try:
            start, end = aware(item['start']), aware(item['end'])
            if end <= start:
                raise ValueError('nonpositive interval')
            intervals.append((start, end))
        except (KeyError, ValueError, TypeError):
            add('SCHEDULE_INVALID', 'Invalid schedule interval.')
    intervals.sort()
    latest_end = None
    for start, end in intervals:
        if latest_end is not None and start < latest_end:
            add('SCHEDULE_OVERLAP', start.isoformat())
        latest_end = max(latest_end, end) if latest_end else end
    costs = data.get('costs', [])
    ids = [c.get('id') for c in costs]
    if len(ids) != len(set(ids)) or any(not isinstance(i, str) or not i for i in ids):
        add('COST_ID', 'Cost IDs must be unique, nonempty strings.')
    indexed = {c.get('id'): c for c in costs}
    total = Decimal(0)
    for cost in costs:
        label = str(cost.get('id'))
        if cost.get('basis') not in BASIS:
            add('COST_BASIS', label)
        if cost.get('currency', data.get('currency')) != data.get('currency'):
            add('CURRENCY', label); out['budget_complete'] = False; continue
        owner = cost.get('included_in')
        if owner:
            seen = {cost.get('id')}
            while owner:
                if owner not in indexed or owner in seen:
                    add('COST_BUNDLE', label); out['budget_complete'] = False; break
                seen.add(owner); owner = indexed[owner].get('included_in')
            continue
        price, qty = cost.get('unit_price'), cost.get('quantity')
        if price is None:
            add('COST_UNKNOWN', label); out['budget_complete'] = False; continue
        if not number(price) or not number(qty):
            add('COST_INVALID', label); out['budget_complete'] = False; continue
        total += Decimal(str(price)) * Decimal(str(qty))
    out['known_subtotal'] = float(total)
    if isinstance(people, int) and not isinstance(people, bool) and people > 0:
        out['per_person_known'] = float(total / people)
    weather = data.get('weather', {})
    if weather.get('state') == 'failed' and weather.get('fetched_at') != weather.get('previous_fetched_at'):
        add('WEATHER_TIMESTAMP', 'Failed refresh must keep the last data timestamp.')
    if weather.get('assessment') == 'low_risk' and any(weather.get(k) is None for k in ('wind_kmh', 'rain_probability')):
        add('WEATHER_MISSING', 'Missing inputs cannot establish low risk.')
    pub = data.get('publication', {})
    if pub.get('claims_public_access') and any(pub.get(k) != 'passed' for k in ('artifact', 'anonymous_page', 'interaction')):
        add('PUBLICATION_CLAIM', 'Public access claim requires separate artifact, anonymous-page and interaction evidence.')
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    args = parser.parse_args()
    try:
        result = check(json.loads(args.file.read_text(encoding='utf-8')))
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        parser.exit(2, f'Invalid input: {exc}\n')
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 1 if result['issues'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
