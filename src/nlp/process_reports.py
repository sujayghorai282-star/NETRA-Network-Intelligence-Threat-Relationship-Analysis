import pandas as pd
from entity_extractor import nlp, extract_custom_entities


# ==========================================
# LOAD STANDARDIZED FIR DATASET
# ==========================================

file_path = "output/standardized_fir_data.csv"

df = pd.read_csv(file_path)

print("\n========================================")
print("      ENTITY EXTRACTION STARTED")
print("========================================\n")

print("Total FIR Records:", len(df))


# ==========================================
# STORE EXTRACTED ENTITIES
# ==========================================

all_entities = []

texts = df["report_text"].fillna("").tolist()
report_ids = df["report_id"].tolist()


# ==========================================
# BATCH PROCESS WITH SPACY
# ==========================================

print("\nProcessing FIR records in batches...\n")

for index, (report_id, doc) in enumerate(
    zip(
        report_ids,
        nlp.pipe(texts, batch_size=100)
    ),
    start=1
):

    # --------------------------------------
    # spaCy entities
    # --------------------------------------

    for ent in doc.ents:

        all_entities.append({
            "report_id": report_id,
            "entity": ent.text,
            "entity_type": ent.label_
        })


    # --------------------------------------
    # Custom regex entities
    # --------------------------------------

    custom_entities = extract_custom_entities(doc.text)

    for entity in custom_entities:

        all_entities.append({
            "report_id": report_id,
            "entity": entity["text"],
            "entity_type": entity["label"]
        })


    # --------------------------------------
    # Progress display
    # --------------------------------------

    if index % 1000 == 0:

        print(
            f"Processed {index}/{len(df)} FIR records..."
        )


# ==========================================
# CONVERT TO DATAFRAME
# ==========================================

entities_df = pd.DataFrame(all_entities)


# ==========================================
# DISPLAY RESULTS
# ==========================================

print("\n========================================")
print("ENTITY EXTRACTION COMPLETE")
print("========================================")

print("\nTotal Reports Processed:", len(df))
print("Total Entities Extracted:", len(entities_df))

print("\nExtracted Entity Preview:\n")

print(
    entities_df.head(20)
)


# ==========================================
# SAVE EXTRACTED ENTITIES
# ==========================================

output_file = "output/extracted_entities.csv"

entities_df.to_csv(
    output_file,
    index=False
)


print("\n========================================")
print("ENTITIES SAVED SUCCESSFULLY")
print("========================================")

print("Output file:", output_file)