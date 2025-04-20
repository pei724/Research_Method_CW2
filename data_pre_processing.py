import pandas as pd

#reading data
df = pd.read_csv("Results_21Mar2022.csv")

#indicator
columns = [
    'diet_group', 'n_participants', 'mean_ghgs', 'mean_land', 'mean_watscar',
    'mean_eut', 'mean_ghgs_ch4', 'mean_ghgs_n2o', 'mean_bio',
    'mean_watuse', 'mean_acid'
]
df_filtered = df[columns]


#STEP 1: Original dietary structure data

#After aggregation, divide by 1000 to stably obtain the number of participants
original = df_filtered.groupby('diet_group').agg({
    'n_participants': 'sum',   # 1000 times
    'mean_ghgs': 'mean',
    'mean_land': 'mean',
    'mean_watscar': 'mean',
    'mean_eut': 'mean',
    'mean_ghgs_ch4': 'mean',
    'mean_ghgs_n2o': 'mean',
    'mean_bio': 'mean',
    'mean_watuse': 'mean',
    'mean_acid': 'mean'
}).reset_index()

#Correct the number of people
original['n_participants'] = (original['n_participants'] / 1000).round().astype(int)

#Calculate the total environmental impact of each group
for col in original.columns[2:]:
    if col.startswith("mean_"):
        original[f"total_{col}"] = original[col] * original['n_participants']


#STEP 2: Simulate a 30% meat diet conversion

meat_groups = ['meat100', 'meat', 'meat50']
existing_groups = original['diet_group'].unique().tolist()

#Obtain the current number of people in each group
def get_value_safe(group, default=0):
    if group in existing_groups:
        return original.loc[original['diet_group'] == group, 'n_participants'].values[0]
    return default

conversion_target = original[original['diet_group'].isin(meat_groups)].copy()
#Take out 30% of the number of people
conversion_target['to_convert'] = conversion_target['n_participants'] * 0.30
#The total number of people who converted from three types of meat to non-meat
conversion_total = conversion_target['to_convert'].sum()

#Allocate the conversion population according to the Finder.com ratio
new_veggie = int(conversion_total * 0.43)
new_vegan = int(conversion_total * 0.30)
new_fish = int(conversion_total * 0.27)

#Update the number of people in the diet structure
participant_updates = {}
for group in meat_groups:
    if group in existing_groups:
        participant_updates[group] = (get_value_safe(group) * 0.70).round().astype(int)

participant_updates['veggie'] = get_value_safe('veggie') + new_veggie
participant_updates['vegan'] = get_value_safe('vegan') + new_vegan
participant_updates['fish'] = get_value_safe('fish') + new_fish

#Applied to the simulation structure
simulated = original.copy()
simulated['n_participants'] = simulated['diet_group'].apply(
    lambda x: participant_updates.get(x, get_value_safe(x))
)

#Recalculate the total environmental impact
for col in [
    'mean_ghgs', 'mean_land', 'mean_watscar', 'mean_eut',
    'mean_ghgs_ch4', 'mean_ghgs_n2o', 'mean_bio',
    'mean_watuse', 'mean_acid'
]:
    simulated[f'total_{col}'] = simulated[col] * simulated['n_participants']


#STEP 3: Original vs simulation comparative analysis
env_cols = [c for c in original.columns if c.startswith("total_")]
original_totals = original[env_cols].sum().rename("original_total")
simulated_totals = simulated[env_cols].sum().rename("simulated_total")

comparison = pd.concat([original_totals, simulated_totals], axis=1)
comparison['difference'] = comparison['original_total'] - comparison['simulated_total']
comparison['percent_reduction'] = (comparison['difference'] / comparison['original_total']) * 100

#Add the "index" column (environmental indicator name)
comparison = comparison.reset_index().rename(columns={"index": "indicator"})


# STEP 4: save (for Tableau)
original.to_csv("original_diet_impact_summary.csv", index=False)
simulated.to_csv("simulated_policy_diet_impact.csv", index=False)
comparison.to_csv("comparison_original_vs_simulated.csv", index=False)

# Read two data
original = pd.read_csv("original_diet_impact_summary.csv")
simulated = pd.read_csv("simulated_policy_diet_impact.csv")

# Add version tags
original['version'] = 'original'
simulated['version'] = 'simulated'

# Merge into one long table
combined = pd.concat([original, simulated], ignore_index=True)

# Only retain the required fields
plot_df = combined[['diet_group', 'n_participants', 'version']]

# Rename the field
plot_df.columns = ['Diet Group', 'Participants', 'Version']

#save
plot_df.to_csv("diet_participant_comparison.csv", index=False)
#print("diet_participant_comparison.csv")
