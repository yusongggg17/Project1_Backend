# import pandas as pd
# import os
# #load preprocessed papers
# def load_papers():
#     current_dir = os.path.dirname(os.path.abspath(__file__))
    
#     # Path to the file created by the preprocessing script
#     path = os.path.join(current_dir, 'data', 'backend_nodes.csv')
#     try:
#         # Load the small CSV file
#         df = pd.read_csv(path) 
#         print(f"Successfully loaded {len(df)} papers from processed file.")
#         return df
#     except FileNotFoundError:
#         print("ERROR: Processed file not found! Please run 'preprocess_efficient.py' first.")
#         # Return an empty DataFrame to prevent the server from crashing
#         return pd.DataFrame()
#     except Exception as e:
#         print(f"An error occurred while loading the file: {e}")
#         return pd.DataFrame()