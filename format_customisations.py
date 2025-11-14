import pandas as pd
import os

# Get the directory of the current Python script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the file path
file_path = os.path.join(script_dir, "data", "Product Customisations Report (System).csv")


data_frame = pd.read_csv(file_path,skiprows=3)

level_strings = data_frame['customisation_value'].unique()

# Read ability mapping from CSV file
ability_mapping_path = os.path.join(script_dir, "data", "ability_mapping.csv")
ability_mapping_df = pd.read_csv(ability_mapping_path)
ability_mapping = dict(zip(ability_mapping_df['customisation_value'], ability_mapping_df['ability']))

# Validate that all customisation values in the data have a mapping
if set(level_strings) != set(ability_mapping.keys()):
    raise ValueError("Error: The unique customisation values do not match the ability mapping.")



data_frame = data_frame.rename(columns={'textbox16': 'Name'})

# Map 'customisation_value' to its corresponding integer
data_frame['ability'] = data_frame['customisation_value'].map(ability_mapping)

# Ensure 'attendance' column is set to False
data_frame['attendance'] = False

# Check for duplicate names
duplicate_names = data_frame['Name'].duplicated(keep=False)
if duplicate_names.any():
    duplicates = data_frame[duplicate_names].sort_values('Name')
    print(f"Found {len(duplicates) // 2} duplicate entries:")
    for name, group in duplicates.groupby('Name'):
        print(f"  • {name} appears {len(group)} times with abilities: {', '.join(map(str, group['ability']))}")
    
    # Keep the entry with the highest ability (lowest integer value) for each name
    # First, sort by Name and ability
    data_frame = data_frame.sort_values(['Name', 'ability'])
    # Then drop duplicates, keeping the first occurrence (which will be the one with lowest ability integer)
    num_before = len(data_frame)
    data_frame = data_frame.drop_duplicates(subset=['Name'], keep='first')
    num_removed = num_before - len(data_frame)
    print(f"Removed {num_removed} duplicate entries, keeping the highest ability for each player.")


# Sort by 'Name'
data_frame = data_frame.sort_values(by='Name')

# Select only necessary columns
data_frame = data_frame[['Name', 'ability', 'attendance']]

# Read manual additions from CSV file
manual_additions_path = os.path.join(script_dir, "data", "manual_additions.csv")
manual_df = pd.read_csv(manual_additions_path)

# Ensure 'attendance' column is set to False for manual additions
manual_df['attendance'] = False

print(f"Adding {len(manual_df)} manual entries.")

# print all names in the dataframe before concatenation
# print("Names before concatenation:")
# print(len(data_frame))
# print(data_frame['Name'].tolist())

# Concatenate with existing data and sort
data_frame = pd.concat([data_frame, manual_df], ignore_index=True)
data_frame = data_frame.sort_values(by='Name').reset_index(drop=True)

# print("Names after concatenation:")
# print(len(data_frame))
# print(data_frame['Name'].tolist())

# Check that all names from "charity signups.csv" are present in attendance
charity_signups_path = os.path.join(script_dir, "data", "charity-signups.csv")
if os.path.exists(charity_signups_path):
    charity_df = pd.read_csv(charity_signups_path)
    # Get names from the second column (index 1)
    charity_names = set(charity_df.iloc[:, 1].dropna())
    attendance_names = set(data_frame['Name'])
    
    missing_from_attendance = charity_names - attendance_names
    if missing_from_attendance:
        raise ValueError(f"Error: The following names from 'charity signups.csv' are missing from attendance: {', '.join(sorted(missing_from_attendance))}")
    print(f"Verified: All {len(charity_names)} names from 'charity signups.csv' are present in attendance.")
else:
    print("Warning: 'charity signups.csv' not found. Skipping charity signups verification.")


# Read ability changes from CSV file
ability_changes_path = os.path.join(script_dir, "data", "ability_changes.csv")
if os.path.exists(ability_changes_path):
    changes_df = pd.read_csv(ability_changes_path)
    changes = dict(zip(changes_df['Name'], changes_df['ability']))
    
    missing_names = set(changes.keys()) - set(data_frame['Name'])
    if missing_names:
        raise ValueError(f"Warning: The following names are missing from the data: {', '.join(missing_names)}")
    
    # Apply changes to the 'ability' column based on 'Name'
    data_frame.loc[data_frame['Name'].isin(changes.keys()), 'ability'] = data_frame['Name'].map(changes)
else:
    print("Warning: 'ability_changes.csv' not found. Skipping ability changes.")

# Write to 'attendance.csv'
data_frame.to_csv("attendance.csv", index=False)

print("Processed data saved to 'attendance.csv'.")