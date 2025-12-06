import pandas as pd

# --- CONFIGURATION ---
MY_UNI_NAME = "Florida State University"
MY_FIELD_NAME = "Computer Science"
MIN_YEAR = 2020

def optimize_data():
    print("Step 1: Getting IDs for University and Field...")
    
    # 1. Find FieldID of computer science
    field_id = 41008148
    print(f" FieldID: {field_id}")

    # 2. Find affiliation id of Florida state university
    uni_id=103163165
    print(f"University ID: {uni_id}")

    print("Step 2: Filtering Papers by Year (Chunking)...")
    # 3. Get Recent PaperIDs
    # Only load PaperID and Year, store it in recent_paper_ids
    recent_paper_ids = set()
    for chunk in pd.read_csv("data/SciSciNet_Papers.tsv", sep="\t", usecols=['PaperID', 'Year'], chunksize=100000):
        chunk = chunk.dropna(subset=['Year'])
        filtered = chunk[chunk['Year'] >= MIN_YEAR]
        recent_paper_ids.update(filtered['PaperID'])
    print(f"Found {len(recent_paper_ids)} papers from {MIN_YEAR}+")

    print("Step 3: Finding CS Papers (Intersection)...")
    # 4. Within the recent_paper_ids, filter for specific CS field ID
    recent_cs_paper_ids = set()
    for chunk in pd.read_csv("data/SciSciNet_PaperFields.tsv", sep="\t", usecols=['PaperID', 'FieldID'], chunksize=100000):
        # Keep rows where FieldID matches AND PaperID is in our recent list
        matches = chunk[(chunk['FieldID'] == field_id) & (chunk['PaperID'].isin(recent_paper_ids))]
        recent_cs_paper_ids.update(matches['PaperID'])
    print(f"Reduced to {len(recent_cs_paper_ids)} recent CS papers.")

    print("Step 4: Finding University Papers (Final Intersection)...")

    # 5. Filter for University Affiliation
    # This is the heavy one, checks links between papers and authors/affiliations
    recent_cs_FSU_paper_ids = set()
    # We also need to save author info for the Collaboration Network later
    final_author_affiliations = []

    for chunk in pd.read_csv("data/SciSciNet_PaperAuthorAffiliations.tsv", sep="\t", chunksize=100000):
        # Check if AffiliationID is in our University list
        uni_matches = chunk[chunk['AffiliationID']== uni_id]
        
        # Check if those papers are also in our Recent CS list
        valid_rows = uni_matches[uni_matches['PaperID'].isin(recent_cs_FSU_paper_ids)]
    print(f"FINAL COUNT: {len(recent_cs_FSU_paper_ids)} papers found for {MY_UNI_NAME} (CS, >{MIN_YEAR}).")

    # --- SAVE NODES ---
    # Now we grab the DOIs for these specific papers
    print("Step 5: Saving Nodes...")
    # We iterate papers one last time to get DOIs for only the final IDs
    node_data = []
    for chunk in pd.read_csv("data/SciSciNet_Papers.tsv", sep="\t", usecols=['PaperID', 'DOI', 'Year'], chunksize=100000):
        found = chunk[chunk['PaperID'].isin(recent_cs_FSU_paper_ids)]
        node_data.append(found)
    
    nodes_df = pd.concat(node_data)
    nodes_df.to_csv("data/backend_nodes.csv", index=False)

    # --- SAVE LINKS (Citation Network) ---
    print("Step 6: Saving Citation Links...")
    link_data = []
    for chunk in pd.read_csv("data/SciSciNet_PaperReferences.tsv", sep="\t", chunksize=100000):
        # Only keep links where BOTH source and target are in our final set (Internal network)
        # OR keep links where just the source is in our set (External references) - usually internal is better for viz
        internal_links = chunk[chunk['Citing_PaperID'].isin(recent_cs_FSU_paper_ids) & chunk['Cited_PaperID'].isin(recent_cs_FSU_paper_ids)]
        link_data.append(internal_links)
    
    if link_data:
        links_df = pd.concat(link_data)
        links_df.to_csv("data/backend_citation_links.csv", index=False)

    # --- SAVE AUTHOR LINKS (Collaboration Network) ---
    print("Step 7: Saving Author Data...")
    if final_author_affiliations:
        # Concatenate the author data we found in Step 4
        auth_df = pd.concat(final_author_affiliations)
        auth_df.to_csv("data/backend_author_links.csv", index=False)

if __name__ == "__main__":
    optimize_data()