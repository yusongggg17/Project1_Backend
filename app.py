from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
# Enable CORS to allow your React frontend to connect
CORS(app) 

def load_graph_data():
    """
    Reads the processed nodes and links CSV files, formats them into 
    the D3-compatible { "nodes": [...], "links": [...] } dictionary,
    and returns the result.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, 'data')
    
    nodes_path = os.path.join(data_dir, 'backend_nodes.csv')
    links_path = os.path.join(data_dir, 'backend_citation_links.csv')

    # --- 1. Load and Format Nodes ---
    try:
        nodes_df = pd.read_csv(nodes_path)
    except FileNotFoundError:
        print("CRITICAL ERROR: Node file not found! Check 'data/backend_nodes.csv'.")
        return {"nodes": [], "links": []}

    # CRITICAL: Rename columns for D3 (id, title, year)
    nodes_df = nodes_df.rename(columns={
        "PaperID": "id",
        "Title": "title",  # Used for tooltip
        "Year": "year"      # Used for tooltip
    })
    
    # Select only the necessary columns and convert to list of dictionaries
    nodes = nodes_df[["id", "title", "year"]].to_dict(orient="records")


    # --- 2. Load and Format Links ---
    try:
        links_df = pd.read_csv(links_path)
    except FileNotFoundError:
        print("CRITICAL ERROR: Links file not found! Check 'data/backend_citation_links.csv'.")
        # Return what we have, even if links are empty
        return {"nodes": nodes, "links": []}

    # CRITICAL: Rename columns for D3 (source, target)
    links_df = links_df.rename(columns={
        "CitingPaperID": "source",
        "CitedPaperID": "target"
    })
    
    # Convert to list of dictionaries
    links = links_df[["source", "target"]].to_dict(orient="records")

    print(f"Server Startup: Loaded {len(nodes)} nodes and {len(links)} links successfully.")
    
    # --- 3. Return the final D3-compatible structure ---
    return {
        "nodes": nodes,
        "links": links
    }

# Load the data once when the server starts, making API calls fast
GLOBAL_GRAPH_DATA = load_graph_data()

@app.route("/citation-network")
def citation_network():
    """Returns the pre-loaded citation network data in D3-compatible JSON format."""
    # Flask's jsonify converts the Python dictionary to a JSON response string
    return jsonify(GLOBAL_GRAPH_DATA)

@app.route("/paper-count")
def paper_count():
    """Returns a status message with the count of loaded papers."""
    return jsonify({"message": f"Total papers loaded: {len(GLOBAL_GRAPH_DATA['nodes'])}"})

if __name__ == "__main__":
    app.run(debug=True)