from collections import Counter

def extract_entities(doc):
    """
    Extracts named entities from a spaCy Doc, maps standard labels to user-friendly categories,
    and returns:
      - grouped: Dictionary mapping category -> list of {"name": text, "count": count}
      - flat: List of {"name": text, "type": category, "count": count} sorted by frequency.
    """
    label_map = {
        "PERSON": "Person",
        "ORG": "Organization",
        "GPE": "Location",
        "LOC": "Location",
        "DATE": "Date",
        "MONEY": "Money",
        "EVENT": "Event",
        "PRODUCT": "Product",
        "LAW": "Law",
        "FAC": "Facility"
    }
    
    entity_counts = Counter()
    
    for ent in doc.ents:
        label = ent.label_
        if label in label_map:
            # Clean up entity text (whitespace normalization)
            text = " ".join(ent.text.strip().split())
            if text:
                category = label_map[label]
                entity_counts[(text, category)] += 1

    flat_entities = []
    grouped_entities = {category: [] for category in set(label_map.values())}
    
    # Sort from most frequent to least frequent
    for (text, category), count in entity_counts.most_common():
        flat_entities.append({
            "name": text,
            "type": category,
            "count": count
        })
        grouped_entities[category].append({
            "name": text,
            "count": count
        })
        
    # Remove categories that don't have any entities
    grouped_entities = {k: v for k, v in grouped_entities.items() if v}
    
    return {
        "flat": flat_entities,
        "grouped": grouped_entities
    }
