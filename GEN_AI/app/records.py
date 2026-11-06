
# ArduinoMate Record Functions

from data.sample_records import records


def load_records():
    """Load all Arduino function records."""
    return records


def search(keyword):
    """Search records using a keyword."""
    results = []

    for record in load_records():
        searchable_text = " ".join(str(value) for value in record.values())

        if keyword.lower() in searchable_text.lower():
            results.append(record)

    return results


def count_by(category_field="category"):
    """Count records grouped by category."""
    counts = {}

    for record in load_records():
        category = record[category_field]
        counts[category] = counts.get(category, 0) + 1

    return counts


def get_by_id(record_id):
    """Get a record using its ID."""

    for index, record in enumerate(load_records(), start=1):
        if index == record_id:
            return record

    return None
