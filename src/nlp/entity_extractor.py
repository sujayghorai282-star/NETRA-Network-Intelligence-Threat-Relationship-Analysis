import spacy
import re

# Load spaCy English NLP model
nlp = spacy.load("en_core_web_sm")


def extract_custom_entities(text):
    """
    Extract custom entities using Regular Expressions.
    """

    custom_entities = []

    # Phone numbers - Indian 10 digit numbers
    phone_pattern = r'\b[6-9]\d{9}\b'

    # Vehicle numbers - Example: WB12AB1234
    vehicle_pattern = r'\b[A-Z]{2}\d{2}[A-Z]{2}\d{4}\b'

    # Bank accounts - Example: ACC1001
    account_pattern = r'\bACC\d+\b'

    # Money amounts
    money_pattern = r'(?:Rs\.?|₹)\s?\d+(?:,\d+)*'

    for match in re.findall(phone_pattern, text):
        custom_entities.append({
            "text": match,
            "label": "PHONE"
        })

    for match in re.findall(vehicle_pattern, text):
        custom_entities.append({
            "text": match,
            "label": "VEHICLE"
        })

    for match in re.findall(account_pattern, text):
        custom_entities.append({
            "text": match,
            "label": "BANK_ACCOUNT"
        })

    for match in re.findall(money_pattern, text):
        custom_entities.append({
            "text": match,
            "label": "MONEY"
        })

    return custom_entities


def extract_entities(text):
    """
    Combine spaCy NLP entities and custom Regex entities.
    """

    doc = nlp(text)

    entities = []

    # Extract spaCy entities
    for ent in doc.ents:
        entities.append({
            "text": ent.text,
            "label": ent.label_
        })

    # Extract custom entities
    custom_entities = extract_custom_entities(text)

    entities.extend(custom_entities)

    return entities


# Test
if __name__ == "__main__":

    sample_text = """
    Rahul Sharma met Amit Das near Durgapur Railway Station.
    Rahul contacted Suresh Roy using phone number 9876543210.
    A transaction of Rs 250000 was made using account ACC1001.
    Vehicle WB12AB1234 was seen near City Centre.
    """

    entities = extract_entities(sample_text)

    print("\n===== EXTRACTED ENTITIES =====\n")

    for entity in entities:
        print(f"{entity['text']} --> {entity['label']}")