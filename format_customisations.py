import pandas as pd
import os
from typing import Dict, Set


def get_script_directory() -> str:
    """Get the directory of the current Python script."""
    return os.path.dirname(os.path.abspath(__file__))


def load_ability_mapping(script_dir: str) -> Dict[str, int]:
    """Load ability mapping from CSV file."""
    ability_mapping_path = os.path.join(script_dir, "data", "ability_mapping.csv")
    ability_mapping_df = pd.read_csv(ability_mapping_path)
    return dict(zip(ability_mapping_df['customisation_value'], ability_mapping_df['ability']))


def load_product_customisations(script_dir: str, ability_mapping: Dict[str, int]) -> pd.DataFrame:
    """Load and process product customisations data."""
    file_path = os.path.join(script_dir, "data", "Product Customisations Report (System).csv")
    df = pd.read_csv(file_path, skiprows=3)
    
    # Validate that all customisation values have a mapping
    level_strings = df['customisation_value'].unique()
    if set(level_strings) != set(ability_mapping.keys()):
        raise ValueError("Error: The unique customisation values do not match the ability mapping.")
    
    # Rename column and map abilities
    df = df.rename(columns={'textbox16': 'Name'})
    df['ability'] = df['customisation_value'].map(ability_mapping)
    df['attendance'] = False
    
    return df


def handle_duplicate_names(df: pd.DataFrame) -> pd.DataFrame:
    """Handle duplicate names by keeping the entry with the highest ability."""
    duplicate_names = df['Name'].duplicated(keep=False)
    if duplicate_names.any():
        duplicates = df[duplicate_names].sort_values('Name')
        print(f"Found {len(duplicates) // 2} duplicate entries:")
        for name, group in duplicates.groupby('Name'):
            print(f"  • {name} appears {len(group)} times with abilities: {', '.join(map(str, group['ability']))}")
        
        # Keep the entry with the highest ability (lowest integer value)
        df = df.sort_values(['Name', 'ability'])
        num_before = len(df)
        df = df.drop_duplicates(subset=['Name'], keep='first')
        num_removed = num_before - len(df)
        print(f"Removed {num_removed} duplicate entries, keeping the highest ability for each player.")
    
    return df


def load_manual_additions(script_dir: str) -> pd.DataFrame:
    """Load manual additions from CSV file."""
    manual_additions_path = os.path.join(script_dir, "data", "manual_additions.csv")
    manual_df = pd.read_csv(manual_additions_path)
    manual_df['attendance'] = False
    print(f"Adding {len(manual_df)} manual entries.")
    return manual_df


def verify_charity_signups(script_dir: str, attendance_names: Set[str]) -> None:
    """Verify that all charity signup names are present in attendance."""
    charity_signups_path = os.path.join(script_dir, "data", "charity-signups.csv")
    if os.path.exists(charity_signups_path):
        charity_df = pd.read_csv(charity_signups_path)
        charity_names = set(charity_df.iloc[:, 1].dropna())
        
        missing_from_attendance = charity_names - attendance_names
        if missing_from_attendance:
            raise ValueError(
                f"Error: The following names from 'charity-signups.csv' are missing from attendance: "
                f"{', '.join(sorted(missing_from_attendance))}"
            )
        print(f"Verified: All {len(charity_names)} names from 'charity-signups.csv' are present in attendance.")
    else:
        print("Warning: 'charity-signups.csv' not found. Skipping charity signups verification.")


def apply_ability_changes(script_dir: str, df: pd.DataFrame) -> pd.DataFrame:
    """Apply ability changes from CSV file if it exists."""
    ability_changes_path = os.path.join(script_dir, "data", "ability_changes.csv")
    if os.path.exists(ability_changes_path):
        changes_df = pd.read_csv(ability_changes_path)
        changes = dict(zip(changes_df['Name'], changes_df['ability']))
        
        missing_names = set(changes.keys()) - set(df['Name'])
        if missing_names:
            raise ValueError(f"Warning: The following names are missing from the data: {', '.join(missing_names)}")
        
        # Apply changes to the 'ability' column based on 'Name'
        df.loc[df['Name'].isin(changes.keys()), 'ability'] = df['Name'].map(changes)
    else:
        print("Warning: 'ability_changes.csv' not found. Skipping ability changes.")
    
    return df


def save_attendance_data(df: pd.DataFrame, output_path: str = "attendance.csv") -> None:
    """Save the processed data to CSV file."""
    df.to_csv(output_path, index=False)
    print(f"Processed data saved to '{output_path}'.")


def main() -> None:
    """Main function to process tournament customisations."""
    script_dir = get_script_directory()
    
    # Load ability mapping
    ability_mapping = load_ability_mapping(script_dir)
    
    # Load and process product customisations
    data_frame = load_product_customisations(script_dir, ability_mapping)
    
    # Handle duplicate names
    data_frame = handle_duplicate_names(data_frame)
    
    # Sort and select only necessary columns
    data_frame = data_frame.sort_values(by='Name')
    data_frame = data_frame[['Name', 'ability', 'attendance']]
    
    # Load and add manual additions
    manual_df = load_manual_additions(script_dir)
    data_frame = pd.concat([data_frame, manual_df], ignore_index=True)
    data_frame = data_frame.sort_values(by='Name').reset_index(drop=True)
    
    # Verify charity signups
    verify_charity_signups(script_dir, set(data_frame['Name']))
    
    # Apply ability changes
    data_frame = apply_ability_changes(script_dir, data_frame)
    
    # Save to CSV
    save_attendance_data(data_frame)


if __name__ == "__main__":
    main()
