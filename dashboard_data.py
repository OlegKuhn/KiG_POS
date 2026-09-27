"""Lesende Zusammenfassung vorhandener Daten für die Startseite."""
from datetime import date
from decimal import Decimal
import config


def dashboard_snapshot(db, today=None):
    today = today or date.today()
    iso = today.isoformat()
    events = sorted((dict(row) for row in db.get_events()
                     if row['entry_type'] == 'EVENT' and row['start_date']
                     and (row['end_date'] or row['start_date'])[:10] >= iso),
                    key=lambda row: (row['start_date'], row['id']))
    by_id = {row['id']: row for row in events}
    shifts = []
    for plan in db.get_shift_plans():
        event = by_id.get(plan['event_id'])
        if event is None:
            continue
        for row in db.get_shifts(plan['id']):
            missing = max(0, row['needed'] - row['besetzt'])
            if missing:
                shifts.append(dict(row, event_name=event['name'],
                                   event_date=event['start_date'], missing=missing))
    shifts.sort(key=lambda row: (row['event_date'], row['start_time'] or '', row['id']))
    tasks = [dict(item, checklist_name=checklist['name'])
             for checklist in db.get_checklists()
             for item in db.get_checklist_items(checklist['id']) if not item['done']]
    tasks.sort(key=lambda row: (not bool(row['deadline']), row['deadline'] or '',
                               row['checklist_name'], row['position'], row['id']))
    entries, findings = db.get_cash_book_entries_checked(today.year, today.month)
    days = {}
    for entry in entries:
        row = days.setdefault(entry['entry_date'], {'date': entry['entry_date'],
                                                   'income': Decimal('0'), 'expenses': Decimal('0')})
        for key in ('income', 'expenses'):
            row[key] += Decimal(str(entry[key] or 0))
    monthly = sorted(days.values(), key=lambda row: row['date'])
    return dict(events=events[:3], shifts=shifts, tasks=tasks, monthly=monthly,
                income=sum((r['income'] for r in monthly), Decimal('0')),
                expenses=sum((r['expenses'] for r in monthly), Decimal('0')),
                invalid_entries=sum(bool(messages) for messages in findings.values()),
                daily_revenue=db.get_daily_revenue(today.strftime(config.DATE_FORMAT)), today=today)
