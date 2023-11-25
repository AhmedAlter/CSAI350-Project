from sentence_transformers import models, SentenceTransformer
from datasets import load_dataset
import pinecone
import pandas as pd
from tqdm import tqdm

class QueryLoader:
    def __init__(self):
        self.model = self.initialize_model()
        self.index = self.initialize_index()
    def initialize_model(self):
        bert = models.Transformer('model')
        pooler = models.Pooling(
            bert.get_word_embedding_dimension(),
            pooling_mode_mean_tokens=True
        )
        return SentenceTransformer(modules=[bert, pooler])

    def initialize_index(self):
        API_KEY = '759bee88-8398-4829-b8e9-981ee7ad0160'
        pinecone.init(api_key=API_KEY, environment='gcp-starter')
        if 'squad-index' not in pinecone.list_indexes():
            pinecone.create_index(
                name='squad-index', dimension=self.model.get_sentence_embedding_dimension(), metric='cosine'
            )

    def load_data(self):
        squad_dev = load_dataset('squad_v2', split='validation')

        squad_data = []

        for row in tqdm(squad_dev, desc="Processing rows"):
            squad_data.append({
                'question': row['question'],
                'context': row['context'],
                'id': row['id']
            })

        squad_df = pd.DataFrame(squad_data)
        no_dupe = squad_df.drop_duplicates(
            subset='context',
            keep='first'
        )
        no_dupe = no_dupe.drop(columns=['question'])
        no_dupe['id'] = no_dupe['id'] + 'con'
        squad_df = squad_df.merge(no_dupe, how='inner', on='context')
        ir_queries = {
            row['id_x']: row['question'] for i, row in squad_df.iterrows()
        }
        ir_corpus = {
            row['id_y']: row['context'] for i, row in squad_df.iterrows()
        }
        ir_relevant_docs = {key: [] for key in squad_df['id_x'].unique()}
        for i, row in squad_df.iterrows():
            ir_relevant_docs[row['id_x']].append(row['id_y'])
        ir_relevant_docs = {key: set(values) for key, values in ir_relevant_docs.items()}

        unique_contexts = []
        unique_ids = []

        for row in squad_dev:
            if row['context'] not in unique_contexts:
                unique_contexts.append(row['context'])
                unique_ids.append(row['id'])

        squad_dev = squad_dev.filter(lambda x: True if x['id'] in unique_ids else False)
        squad_dev = squad_dev.map(lambda x: {
            'encoding': self.model.encode(x['context']).tolist()
        }, batched=True, batch_size=4)

        upserts = [(v['id'], v['encoding'], {'text': v['context']}) for v in squad_dev]

        for i in tqdm(range(0, len(upserts), 50)):
            i_end = i + 50
            if i_end > len(upserts): i_end = len(upserts)
            self.index.upsert(vectors=upserts[i:i_end])

    def query(self, input_query, top_k=3):
        query_encoding = self.model.encode([input_query]).tolist()
        query_result = self.index.query(query_encoding, top_k=top_k, include_metadata=True)
        highest_score_match = max(query_result['matches'], key=lambda x: x['score'])
        highest_score_text = highest_score_match['metadata']['text']

        if highest_score_match['score'] < 0.44:
            highest_score_text = "I'm afraid I don't have much information on that topic at the moment."

        return highest_score_text


# Example usage in Streamlit app:
# (assuming this class is saved in a file called query_loader.py)

# app.py
# import streamlit as st
# from query_loader import QueryLoader

# query_loader = QueryLoader()
# query_loader.load_data()

# st.title("Streamlet Chat App")

# user_question = st.text_input("Ask a question:")
# if user_question:
#     result = query_loader.query(user_question)
#     st.text(result)
