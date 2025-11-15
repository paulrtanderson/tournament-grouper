import pandas as pd
import numpy as np
import os
from math import ceil

def create_tournament_groups(attendance_file='build/attendance.csv', pairs_file='data/paired.csv', output_file='build/tournament_groups.csv'):
    """
    Create tournament groups from attendance data and optional pairs information.
    
    Args:
        attendance_file (str): Path to the attendance CSV file
        must have formatted with columns: 'Name': string, 'ability': string, 'attendance': boolean
        
        pairs_file (str, optional): Path to predefined pairs CSV file
        must have columns: 'person1': string, 'person2': string
        
        output_file (str): Path to save the output groups CSV file
    """
    print(f"Loading attendance data from {attendance_file}...")
    
    # Load attendance data
    attendance_df = pd.read_csv(attendance_file)
    
    REQUIRE_ATTENDENCE = True  # TESTING ONLY SET TO TRUE WHEN ACTUALLY USING THIS
    
    # Filter to only include players who are attending
    
    players = attendance_df.copy()
    
    if REQUIRE_ATTENDENCE:
        players = attendance_df[attendance_df['attendance'] == True].copy()
    
    if len(players) == 0:
        print("No attending players found. Please update attendance in the CSV file.")
        return
    
    print(f"Found {len(players)} attending players")
    
    # Sort players by ability level (lower number = higher ability)
    players = players.sort_values(by='ability')
    print(f"Players sorted by ability level {players['ability'].values}")
    # Create pairs
    pairs = []
    manually_paired = set()
    
    # Load manual pairs if provided
    if pairs_file and os.path.exists(pairs_file):
        print(f"Loading manual pairs from {pairs_file}...")
        # Use quotechar and escapechar parameters to handle names with commas
        pairs_override = pd.read_csv(pairs_file, quotechar='"', escapechar='\\')
        print(f"Loaded {len(pairs_override)} manual pairs")
        print(f"Pairs data columns: {pairs_override.columns.tolist()}")
        
        # Debugging: print the first few rows to see what was actually loaded
        print("First few rows of pairs file:")
        print(pairs_override.head())
        
        # Check for required columns
        if not {'person1', 'person2'}.issubset(pairs_override.columns):
            raise ValueError("Pairs file must contain 'person1' and 'person2' columns")
        
        # Check for players not in attendance data
        all_players = set(players['Name'])
        print(f"Available players: {all_players}")
        missing_players = []
        
        for _, row in pairs_override.iterrows():
            # Trim whitespace to handle potential formatting issues
            person1 = row['person1'].strip() if isinstance(row['person1'], str) else row['person1']
            person2 = row['person2'].strip() if isinstance(row['person2'], str) else row['person2']
            
            if person1 not in all_players:
                missing_players.append(f"{person1} (not found in attendance)")
            if person2 not in all_players:
                missing_players.append(f"{person2} (not found in attendance)")
        
        if missing_players:
            raise ValueError(f"The following players in the pairs file are not in attendance data: {', '.join(set(missing_players))}")
        
        # Now process the valid pairs
        for _, row in pairs_override.iterrows():
            if (row['person1'] in players['Name'].values and 
                row['person2'] in players['Name'].values):
                pairs.append((row['person1'], row['person2']))
                manually_paired.add(row['person1'])
                manually_paired.add(row['person2'])
    
    # Filter out manually paired players
    unpaired_players = players[~players['Name'].isin(manually_paired)]
    
    # Dynamically pair remaining players - pair highest with lowest ability for balance
    # This creates balanced pairs by pairing strongest with weakest players
    while len(unpaired_players) > 1:
        player1 = unpaired_players.iloc[0]  # Highest skill (lowest number)
        player2 = unpaired_players.iloc[-1]  # Lowest skill (highest number)
        print(f"pairing player1: {player1['Name']} ({player1['ability']}) with player2: {player2['Name']} ({player2['ability']})")
        pairs.append((player1['Name'], player2['Name']))
        unpaired_players = unpaired_players.iloc[1:-1]  # Remove the paired players
    
    # Handle odd number of players
    if len(unpaired_players) == 1:
        pairs.append((unpaired_players.iloc[0]['Name'], "NO PARTNER"))
        print(f"Warning: Odd number of players. {unpaired_players.iloc[0]['Name']} has no partner.")
    
    # Calculate number of groups needed
    # Aim for 4 teams per group, but allow flexibility
    teams_per_group = 4
    num_teams = len(pairs)
    num_groups = max(2, ceil(num_teams / teams_per_group))  # Ensure at least 2 groups
    
    # Adjust teams_per_group if needed
    teams_per_group = ceil(num_teams / num_groups)
    
    print(f"Creating {num_groups} groups with approximately {teams_per_group} teams each")
    
    # Assign teams to groups using a snake pattern for balanced distribution
    # This ensures groups are balanced in terms of skill level
    groups = {}
    for i in range(num_groups):
        group_name = chr(65 + i)  # A, B, C, ...
        groups[group_name] = []
    
    # Sort pairs by average skill level
    pair_skills = []
    for i, (player1, player2) in enumerate(pairs):
        if player2 == "NO PARTNER":
            avg_skill = players[players['Name'] == player1]['ability'].values[0]
        else:
            skill1 = players[players['Name'] == player1]['ability'].values[0]
            skill2 = players[players['Name'] == player2]['ability'].values[0]
            avg_skill = (skill1 + skill2) / 2
        pair_skills.append((i, avg_skill))
    
    # Sort pairs by skill (ascending)
    pair_skills.sort(key=lambda x: x[1])
    
    # Distribute in snake pattern (1,2,3,3,2,1,1,2,...)
    group_indices = []
    direction = 1
    current = 0
    
    for _ in range(len(pairs)):
        group_indices.append(current)
        current += direction
        
        # Change direction when reaching the end or beginning
        if current >= num_groups:
            current = num_groups - 1
            direction = -1
        elif current < 0:
            current = 0
            direction = 1
    
    # Assign teams to groups
    for i, (pair_idx, _) in enumerate(pair_skills):
        group_key = chr(65 + group_indices[i])
        groups[group_key].append(pairs[pair_idx])
    
    # Prepare output data
    output_data = []
    for group, team_list in groups.items():
        for i, (player1, player2) in enumerate(team_list):
            # Get ability level for player1
            player1_ability = players[players['Name'] == player1]['ability'].values[0]
            player1_with_level = f"{player1} ({player1_ability})"
            
            # Get ability level for player2 if not "NO PARTNER"
            if player2 == "NO PARTNER":
                player2_with_level = player2
            else:
                player2_ability = players[players['Name'] == player2]['ability'].values[0]
                player2_with_level = f"{player2} ({player2_ability})"
            
            output_data.append({
                'Group': f"{group}{i+1}", 
                'Person 1': player1_with_level, 
                'Person 2': player2_with_level
            })
    
    # Create DataFrame and save to CSV
    output_df = pd.DataFrame(output_data)
    output_df.to_csv(output_file, index=False)
    
    print(f"Tournament groups have been created and saved to '{output_file}'")
    
    # Print group summary
    print("\nGroup Summary:")
    for group, team_list in groups.items():
        print(f"Group {group}: {len(team_list)} teams")

if __name__ == "__main__":
    create_tournament_groups()