from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# OpenAlex IDs for FSU and Computer Science
InstitutionID = "I103163165"  
FieldID = "C41008148"         
StartYear_T1 = 2020           

FULL_PAPER_DATA_T1 = None # Stores raw data for T1 (5-year scope)

# Data Fetching Logic (Pagination) ---

def fetch_all_from_openAlex(institution_id, field_id, start_year):
    """
    Fetches all papers from OpenAlex using the cursor for pagination.
    Returns: (list of paper dicts, total count)
    """
    all_papers = []
    cursor = '*'
    per_page = 200 # Max per_page is 200

    print(f"Fetching data from {start_year} for {institution_id} in {field_id}")

    while cursor is not None:
        url = (
            "https://api.openalex.org/works?"
            f"filter=institutions.id:{institution_id},"
            f"concepts.id:{field_id},"
            f"from_publication_date:{start_year}-01-01&"
            f"per_page={per_page}&"
            f"cursor={cursor}"
        )
        
        try:
            resp = requests.get(url)
            resp.raise_for_status() # Raise an HTTPError for bad responses
            data = resp.json()
            
            # Add the results and get the next cursor
            results = data.get("results", [])
            all_papers.extend(results)
            cursor = data.get("meta", {}).get("next_cursor")
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return None, 0
            
    return all_papers, data.get("meta", {}).get("count", 0)

# -----Data Processing Logic-----

def create_citation_network_data(papers):
    #Creates node-link data for the paper citation network (T1).
    paper_ids_set = {p['id'] for p in papers}
    paper_nodes = []    # list of all papers
    for p in papers:
        short_id = p['id'].split('/')[-1]
        paper_nodes.append({
            "id": short_id,
            "title": p['title'],
            "year": p['publication_year'],
            "cited_by_count": p['cited_by_count']
        })
        
    citation_edges = []     #list of edges that stores a source paper id and cited paper id
    for paper in papers:    #iterates through every inputed paper
        citing_short_id = paper['id'].split('/')[-1]
        for cited_work_id in paper.get('referenced_works', []): #for each paper, iterates through its reference lists
            if cited_work_id in paper_ids_set:  #check if the citation of this paper is also in the input paper list
                cited_short_id = cited_work_id.split('/')[-1]
                citation_edges.append({"source": citing_short_id, "target": cited_short_id}) #if the citation machines another paper in the list, add it to edge[]
    
    return {"nodes": paper_nodes, "links": citation_edges}

def create_collaboration_network_data(papers):
    """Creates node-link data for the author collaboration network (T1)."""
    # ... (rest of function is fine)
    author_nodes = {}
    collaboration_edges = {} 
    
    for paper in papers:
        author_ids = [
            a['author']['id'] 
            for a in paper.get('authorships', []) 
            if a.get('author') and a['author'].get('id')
        ]
        
        # 1. Create/Update Author Nodes
        for authorship in paper.get('authorships', []):
            author_data = authorship.get('author')
            if author_data and author_data.get('id'):
                author_id = author_data['id']
                if author_id not in author_nodes:
                    short_id = author_id.split('/')[-1]
                    author_nodes[author_id] = {
                        "id": short_id, 
                        "display_name": author_data.get('display_name', 'Unknown Author'),
                        "works_count": author_data.get('works_count') 
                    }
                
        # 2. Create Collaboration Edges (between every pair of authors)
        for i in range(len(author_ids)):
            for j in range(i + 1, len(author_ids)):
                author_a = author_ids[i]
                author_b = author_ids[j]
                
                key = tuple(sorted((author_a, author_b)))
                collaboration_edges[key] = collaboration_edges.get(key, 0) + 1 
    
    # 3. Convert collaboration_edges dictionary to a list of links
    collaboration_links = []
    for (author_a, author_b), count in collaboration_edges.items():
        collaboration_links.append({
            "source": author_a.split('/')[-1],
            "target": author_b.split('/')[-1],
            "weight": count
        })
    
    return {"nodes": list(author_nodes.values()), "links": collaboration_links}


@app.route("/load-data")
def load_data():
    #Initializes the global data by fetching from OpenAlex.
    global FULL_PAPER_DATA_T1
    #fetching 
    papers_t1, count_t1 = fetch_all_from_openAlex(InstitutionID, FieldID, StartYear_T1)
    if papers_t1 is None:
        return jsonify({"message": "Failed to load T1 data"}), 500
    FULL_PAPER_DATA_T1 = papers_t1
    
    return jsonify({
        "message": f"Data loaded successfully.",
        "T1_papers_count": count_t1
    })

# --- T1: Graph Endpoints ---

@app.route("/citation-network")
def citation_network():
    #Returns data for the Paper Citation Network graph (T1).
    if FULL_PAPER_DATA_T1 is None:
        return jsonify({"message": "Data not loaded."}), 503
    
    graph_data = create_citation_network_data(FULL_PAPER_DATA_T1)
    return jsonify(graph_data)

@app.route("/collaboration-network")
def collaboration_network():
    """Returns data for the Author Collaboration Network graph (T1)."""
    if FULL_PAPER_DATA_T1 is None:
        return jsonify({"message": "Data not loaded."}), 503

    graph_data = create_collaboration_network_data(FULL_PAPER_DATA_T1)
    return jsonify(graph_data)


if __name__ == '__main__':
    print("Starting Flask app...")
    print("Access the API endpoints at http://127.0.0.1:5000/")
    with app.app_context():
        load_data()
        
    app.run(debug=True)