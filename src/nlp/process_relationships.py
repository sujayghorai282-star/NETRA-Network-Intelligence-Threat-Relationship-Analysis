import pandas as pd
from relationship_extractor import extract_relationships


# Load intelligence reports
file_path = "output/standardized_fir_data.csv"

df = pd.read_csv(file_path)


# Store all relationships
all_relationships = []


# Process every report
for _, row in df.iterrows():

    report_id = row["report_id"]
    report_text = row["report_text"]

    relationships = extract_relationships(report_text)

    for relation in relationships:

        all_relationships.append({
            "report_id": report_id,
            "source": relation["source"],
            "relationship": relation["relationship"],
            "target": relation["target"]
        })


# Convert to DataFrame
relationships_df = pd.DataFrame(all_relationships)


# Display results
print("\n========================================")
print("RELATIONSHIP EXTRACTION COMPLETE")
print("========================================")

print("\nTotal Reports Processed:", len(df))
print("Total Relationships Extracted:", len(relationships_df))

print("\nExtracted Relationships:\n")

if not relationships_df.empty:
    print(relationships_df.head(20))
else:
    print("No relationships found.")


# Save output
output_file = "output/extracted_relationships.csv"

relationships_df.to_csv(output_file, index=False)


print("\n========================================")
print("RELATIONSHIPS SAVED SUCCESSFULLY")
print("========================================")

print("Output file:", output_file)