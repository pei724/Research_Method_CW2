import pandas as pd
import numpy as np

# Step 1: read
df = pd.read_csv("Results_21Mar2022.csv")

# Step 2: Define the environmental indicator column
env_columns = [
    "mean_acid", "mean_bio", "mean_eut","mean_ghgs","mean_ghgs_ch4", 
    "mean_ghgs_n2o","mean_land", "mean_watscar",
    "mean_watuse",
   
]

# Step 3: Statistics of the original diet population
original_distribution = df.groupby("diet_group")["n_participants"].sum()

# Correct the number of people
original_distribution = (original_distribution / 1000).round().astype(int)

# Step 4: Set scenario transitions (reduce 30% for each of the three types of meat eaters)
meat_types = ['meat', 'meat50', 'meat100']
converted_total = original_distribution[meat_types].sum() * 0.30

# Transform the target distribution（vegan、veggie、fish）
conversion_ratios = {
    "vegan": 0.30,
    "veggie": 0.43,
    "fish": 0.27
}

# Construction of simulated scenario distribution
scenario_distribution = original_distribution.copy()
for meat_type in meat_types:
    scenario_distribution[meat_type] *= 0.70  # reduce 30%

# Increase the number of non-meat eaters
for group, ratio in conversion_ratios.items():
    scenario_distribution[group] += converted_total * ratio

# Step 5: Define the environmental impact calculation function
def compute_totals(distribution):
    results = {}
    group_means = df.groupby("diet_group")[env_columns].mean()
    for col in env_columns:
        total = sum(distribution.get(group, 0) * group_means.loc[group, col] for group in distribution.index if group in group_means.index)
        results[f"total_{col}"] = total
    return results

# Step 6: Calculate the total value of the two scenarios
original_totals = compute_totals(original_distribution)
scenario_totals = compute_totals(scenario_distribution)

# DataFrame
original_df = pd.DataFrame.from_dict(original_totals, orient='index', columns=["value"]).reset_index()
original_df["version"] = "original"

scenario_df = pd.DataFrame.from_dict(scenario_totals, orient='index', columns=["value"]).reset_index()
scenario_df["version"] = "scenario"

# Merge the two scenes
combined_df = pd.concat([original_df, scenario_df], ignore_index=True)
combined_df.rename(columns={"index": "indicator"}, inplace=True)

# Step 7: Logarithmic transformation + normalization
combined_df["log_value"] = np.log10(combined_df["value"])
min_log = combined_df["log_value"].min()
max_log = combined_df["log_value"].max()
combined_df["log_normalized"] = (combined_df["log_value"] - min_log) / (max_log - min_log)

# Step 8: Allocate the angles in the order of env_columns
indicators_order = [f"total_{col}" for col in env_columns]
n_indicators = len(indicators_order)
angles = np.linspace(0, 2 * np.pi, n_indicators, endpoint=False)
angle_map = dict(zip(indicators_order, angles))

combined_df["angle"] = combined_df["indicator"].map(angle_map)
combined_df["x"] = combined_df["log_normalized"] * np.cos(combined_df["angle"])
combined_df["y"] = combined_df["log_normalized"] * np.sin(combined_df["angle"])

# Step 9: add label indicator_label
label_mapping = {
    "total_mean_acid": "Acidification",
    "total_mean_bio": "Biodiversity Loss",
    "total_mean_eut": "Eutrophication",
    "total_mean_ghgs": "Greenhouse Gas Emissions",
    "total_mean_ghgs_ch4": "Methane Emissions (CH₄)",
    "total_mean_ghgs_n2o": "Nitrous Oxide Emissions (N₂O)",
    "total_mean_land": "Land Use",
    "total_mean_watscar": "Water Scarcity Impact",
    "total_mean_watuse": "Water Use"
}
combined_df["indicator_label"] = combined_df["indicator"].map(label_mapping)

# Step 10: save
combined_df.to_csv("radar_chart_log_normalized_labeled.csv", index=False)