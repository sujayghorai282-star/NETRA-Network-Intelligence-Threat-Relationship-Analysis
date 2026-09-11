import re


def clean_value(value):
    """Clean extracted field values."""
    if not value:
        return ""

    value = value.strip()
    value = re.sub(r"\s+", " ", value)

    return value


def is_unknown(value):
    """Check whether a field contains an unusable unknown value."""
    if not value:
        return True

    unknown_values = {
        "unknown",
        "unknown / unidentified",
        "unidentified",
        "not known",
        "n/a",
        "na",
        "none"
    }

    return value.lower().strip() in unknown_values


def extract_field(text, field_name, next_field=None):
    """
    Extract a labeled field from the standardized FIR report.
    Example:
    Complainant: Rahul Sharma. Accused: Amit Das.
    """

    if next_field:
        pattern = rf"{re.escape(field_name)}:\s*(.*?)(?=\.\s*{re.escape(next_field)}:)"
    else:
        pattern = rf"{re.escape(field_name)}:\s*(.*?)(?=\.\s*Case Status:)"

    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        return clean_value(match.group(1))

    return ""


def extract_relationships(text):
    """
    Extract relationships from both traditional FIR reports
    and universal person/case datasets.
    """

    relationships = []

    if not isinstance(text, str):
        return relationships

    def get_field(field_name):
        pattern = rf"{re.escape(field_name)}:\s*(.*?)(?=\.\s*[A-Za-z_][A-Za-z0-9 _]*:|$)"
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return clean_value(match.group(1))

        return ""

    # ============================================================
    # TRADITIONAL FIR FIELDS
    # ============================================================

    complainant = get_field("Complainant")
    accused = get_field("Accused")
    legal_section = get_field("Legal Section")
    crime_category = get_field("Crime Category")
    state = get_field("State")
    district = get_field("District")
    police_station = get_field("Police Station")

    # Complainant -> Accused
    if not is_unknown(complainant) and not is_unknown(accused):
        relationships.append({
            "source": complainant,
            "target": accused,
            "relationship": "REPORTED_AGAINST"
        })

    # Accused -> State
    if not is_unknown(accused) and not is_unknown(state):
        relationships.append({
            "source": accused,
            "target": state,
            "relationship": "LOCATED_IN_STATE"
        })

    # Accused -> District
    if not is_unknown(accused) and not is_unknown(district):
        relationships.append({
            "source": accused,
            "target": district,
            "relationship": "LOCATED_IN_DISTRICT"
        })

    # Accused -> Police Station
    if not is_unknown(accused) and not is_unknown(police_station):
        relationships.append({
            "source": accused,
            "target": police_station,
            "relationship": "CASE_REGISTERED_AT"
        })

    # Accused -> Crime Category
    if not is_unknown(accused) and not is_unknown(crime_category):
        relationships.append({
            "source": accused,
            "target": crime_category,
            "relationship": "INVOLVED_IN_CRIME"
        })

    # Accused -> Legal Section
    if not is_unknown(accused) and not is_unknown(legal_section):
        relationships.append({
            "source": accused,
            "target": legal_section,
            "relationship": "CHARGED_UNDER"
        })

    # ============================================================
    # UNIVERSAL PERSON / CASE DATASET
    # ============================================================

    person_name = get_field("Person Name")
    person_id = get_field("Person ID")
    crime_type = get_field("Crime Type")
    city = get_field("City")
    case_id = get_field("Case ID")
    severity = get_field("Severity")
    prior_cases = get_field("Prior Cases")
    incident_year = get_field("Incident Year")

    # Person -> Crime
    if not is_unknown(person_name) and not is_unknown(crime_type):
        relationships.append({
            "source": person_name,
            "target": crime_type,
            "relationship": "INVOLVED_IN_CRIME"
        })

    # Person -> State
    if not is_unknown(person_name) and not is_unknown(state):
        relationships.append({
            "source": person_name,
            "target": state,
            "relationship": "LOCATED_IN_STATE"
        })

    # Person -> City
    if not is_unknown(person_name) and not is_unknown(city):
        relationships.append({
            "source": person_name,
            "target": city,
            "relationship": "LOCATED_IN_CITY"
        })

    # Person -> Case
    if not is_unknown(person_name) and not is_unknown(case_id):
        relationships.append({
            "source": person_name,
            "target": case_id,
            "relationship": "LINKED_TO_CASE"
        })

    # Person -> Person ID
    if not is_unknown(person_name) and not is_unknown(person_id):
        relationships.append({
            "source": person_name,
            "target": person_id,
            "relationship": "IDENTIFIED_AS"
        })

    # Person -> Severity
    if not is_unknown(person_name) and not is_unknown(severity):
        relationships.append({
            "source": person_name,
            "target": severity,
            "relationship": "HAS_SEVERITY"
        })

    # Person -> Prior Cases
    if not is_unknown(person_name) and not is_unknown(prior_cases):
        relationships.append({
            "source": person_name,
            "target": prior_cases,
            "relationship": "HAS_PRIOR_CASE_COUNT"
        })

    # Person -> Incident Year
    if not is_unknown(person_name) and not is_unknown(incident_year):
        relationships.append({
            "source": person_name,
            "target": incident_year,
            "relationship": "INVOLVED_IN_YEAR"
        })

    return relationships

    # ==========================================
    # EXTRACT FIR FIELDS
    # ==========================================

    complainant = extract_field(
        text,
        "Complainant",
        "Accused"
    )

    accused = extract_field(
        text,
        "Accused",
        "Legal Section"
    )

    legal_section = extract_field(
        text,
        "Legal Section",
        "Crime Category"
    )

    crime_category = extract_field(
        text,
        "Crime Category",
        "Incident Description"
    )

    state = extract_field(
        text,
        "State",
        "District"
    )

    district = extract_field(
        text,
        "District",
        "Police Station"
    )

    police_station = extract_field(
        text,
        "Police Station",
        "Complainant"
    )

    # ==========================================
    # COMPLAINANT -> ACCUSED
    # ==========================================

    if not is_unknown(complainant) and not is_unknown(accused):

        relationships.append({
            "source": complainant,
            "target": accused,
            "relationship": "REPORTED_AGAINST"
        })

    # ==========================================
    # ACCUSED -> STATE
    # ==========================================

    if not is_unknown(accused) and not is_unknown(state):

        relationships.append({
            "source": accused,
            "target": state,
            "relationship": "LOCATED_IN_STATE"
        })

    # ==========================================
    # ACCUSED -> DISTRICT
    # ==========================================

    if not is_unknown(accused) and not is_unknown(district):

        relationships.append({
            "source": accused,
            "target": district,
            "relationship": "LOCATED_IN_DISTRICT"
        })

    # ==========================================
    # ACCUSED -> POLICE STATION
    # ==========================================

    if not is_unknown(accused) and not is_unknown(police_station):

        relationships.append({
            "source": accused,
            "target": police_station,
            "relationship": "CASE_REGISTERED_AT"
        })

    # ==========================================
    # ACCUSED -> CRIME CATEGORY
    # ==========================================

    if not is_unknown(accused) and not is_unknown(crime_category):

        relationships.append({
            "source": accused,
            "target": crime_category,
            "relationship": "INVOLVED_IN_CRIME"
        })

    # ==========================================
    # ACCUSED -> LEGAL SECTION
    # ==========================================

    if not is_unknown(accused) and not is_unknown(legal_section):

        relationships.append({
            "source": accused,
            "target": legal_section,
            "relationship": "CHARGED_UNDER"
        })
        if not is_unknown(accused) and not is_unknown(legal_section):
                relationships.append({
                    "source": accused,
                    "target": legal_section,
                    "relationship": "CHARGED_UNDER"
                })

                return relationships
    


# ==========================================
# TEST
# ==========================================

if __name__ == "__main__":

    sample_text = """
    FIR FIR/2023/00001.
    Filed on 2023-11-29.
    State: Gujarat.
    District: Vadodara.
    Police Station: Vadodara West PS.
    Complainant: Aryan Maharaj.
    Accused: Rahul Sharma.
    Legal Section: BNS 301.
    Crime Category: Violent Crime.
    Incident Description: Violent incident.
    Case Status: Pending Trial.
    """

    relationships = extract_relationships(sample_text)

    print("\n===== EXTRACTED RELATIONSHIPS =====\n")

    for relation in relationships:

        print(
            f"{relation['source']} "
            f"--- {relation['relationship']} ---> "
            f"{relation['target']}"
        )