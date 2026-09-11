import pandas as pd
import os


# Load network analysis results
input_file = "output/network_analysis.csv"

df = pd.read_csv(input_file)


print("\n==========================================")
print(" SUSPICIOUS HUB DETECTION")
print("==========================================")


# Calculate dynamic thresholds
degree_threshold = df["degree_centrality"].quantile(0.90)
betweenness_threshold = df["betweenness_centrality"].quantile(0.90)
influence_threshold = df["influence_score"].quantile(0.90)


# Flag entities for review
df["high_connectivity"] = (
    df["degree_centrality"] >= degree_threshold
)

df["bridge_entity"] = (
    df["betweenness_centrality"] >= betweenness_threshold
)

df["high_influence"] = (
    df["influence_score"] >= influence_threshold
)


# Calculate number of flags
df["risk_flags"] = (
    df["high_connectivity"].astype(int)
    + df["bridge_entity"].astype(int)
    + df["high_influence"].astype(int)
)


# Risk category
def classify_risk(flags):

    if flags >= 3:
        return "HIGH PRIORITY REVIEW"
    elif flags == 2:
        return "MEDIUM PRIORITY REVIEW"
    elif flags == 1:
        return "LOW PRIORITY REVIEW"
    else:
        return "NO FLAG"


df["review_priority"] = df["risk_flags"].apply(classify_risk)


# Sort highest priority first
df = df.sort_values(
    by=["risk_flags", "influence_score"],
    ascending=False
)


# Create output folder
os.makedirs("output", exist_ok=True)


# Save flagged entities
output_file = "output/suspicious_entities.csv"

df.to_csv(output_file, index=False)


# Display flagged entities
flagged = df[df["risk_flags"] > 0]

print("\nENTITIES FLAGGED FOR ANALYST REVIEW:\n")

if len(flagged) > 0:
    print(
        flagged[
            [
                "entity",
                "degree_centrality",
                "betweenness_centrality",
                "influence_score",
                "risk_flags",
                "review_priority"
            ]
        ].head(15).to_string(index=False)
    )
else:
    print("No entities crossed the current review thresholds.")


print("\n==========================================")
print(" HUB DETECTION COMPLETED SUCCESSFULLY")
print("==========================================")

print("Output file:", output_file)