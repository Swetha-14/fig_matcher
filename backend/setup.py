import sys
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from data_loader import users_data

def get_user_text(user):
    bio_text = user.get('bio', '')
    
    domain_expertise_text = " ".join(user.get('domain_expertise', [])) * 5
    
    skill_text = ""
    for skill, level in user.get('skill_levels', {}).items():
        if level == 'expert':
            skill_text += f"{skill} expert " * 3
        elif level == 'intermediate':
            skill_text += f"{skill} intermediate " * 2
        else:
            skill_text += f"{skill} "
    
    role_text = user.get('current_role', '').replace('_', ' ') * 2
    experience_text = user.get('experience_level', '') * 2
    networking_text = user.get('networking_intent', '').replace('_', ' ') * 2
    
    recent_conversations = user.get('conversations', [])[:2]
    conversations_text = " ".join([conv['text'] for conv in recent_conversations])
    
    location_text = user.get('location', '')
    last_active_text = f"Last active on {user.get('last_active', '')}" if user.get('last_active') else ""

    full_text = " ".join([
        bio_text,
        domain_expertise_text,  
        skill_text,            
        role_text,             
        experience_text,       
        networking_text,       
        conversations_text,    
        location_text,
        last_active_text
    ])
    
    return full_text


def get_all_user_texts():
    return [get_user_text(user) for user in users_data]

def create_embeddings():
    model = SentenceTransformer('all-MiniLM-L6-v2')
    user_texts = get_all_user_texts()

    # Create embeddings
    user_embeddings = model.encode(user_texts)
    print(f" Embeddings Shape: {user_embeddings.shape}")

    embeddings_path = "embeddings/user_embeddings.npy"
    np.save(embeddings_path, user_embeddings)
    return user_embeddings

def create_faiss_index(user_embeddings):
    
    dimension = user_embeddings.shape[1]  

    # Normalize embeddings for cosine similarity
    normalized_embeddings = user_embeddings.copy()
    faiss.normalize_L2(normalized_embeddings)

    # Create the index and save it
    index = faiss.IndexFlatIP(dimension) 
    index.add(normalized_embeddings)
    index_path = "embeddings/faiss_index.bin"
    faiss.write_index(index, index_path)

    return index

def verify_embeddings(user_embeddings):
    for i, user in enumerate(users_data):
        embedding = user_embeddings[i]
        print(f"\n{i+1}. {user['name']}:")
        print(f"Shape: {embedding.shape}")
        print(f"Min value: {embedding.min():.4f}")
        print(f"Max value: {embedding.max():.4f}")
        print(f"Mean: {embedding.mean():.4f}")

    # Quality checks
    print(f"Any NaN values? {np.isnan(user_embeddings).any()}")
    print(f"Any infinite values? {np.isinf(user_embeddings).any()}")
    print(f"All embeddings same length? {all(len(emb) == 384 for emb in user_embeddings)}")

def test_index(index):
    user_embeddings = np.load("embeddings/user_embeddings.npy")
    normalized_embeddings = user_embeddings.copy()
    faiss.normalize_L2(normalized_embeddings)
    
    # Find top 3 matches for alex
    test_query = normalized_embeddings[0:1] 
    distances, indices = index.search(test_query, k=3)  

    print(f"Query: {users_data[0]['name']}'s embedding")
    print(f"Top 3 matches:")
    for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
        print(f"{i+1}. {users_data[idx]['name']} - similarity: {distance:.3f}")



def main():
    os.makedirs("embeddings", exist_ok=True)
    

    user_embeddings = create_embeddings()
    verify_embeddings(user_embeddings)
    index = create_faiss_index(user_embeddings)
    
    test_index(index)
    
    print("Setup done")

if __name__ == "__main__":
    main()