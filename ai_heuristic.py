from transformers import BertTokenizer, BertModel
import torch
import torch.nn.functional as F

from transformers import logging
logging.set_verbosity_error()


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu') #I HATE MACBOOKS I HATE MACBOOKS

tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
model = BertModel.from_pretrained("bert-base-uncased")
model.to(device)
model.eval()

embedding_layer = model.get_input_embeddings()

def embed_word(word):

    token_ids = tokenizer.encode(word, add_special_tokens=False)
    token_tensor = torch.tensor(token_ids)
    # print(word,token_tensor)

    token_embeddings = embedding_layer(token_tensor)

    word_embedding = torch.mean(token_embeddings, dim=0)
    return word_embedding

def score_word_similarity(word1, word2):
    if word1 == '':
        return 0
    embed1 = embed_word(word1)
    embed2 = embed_word(word2)
    # return torch.norm(embed1 - embed2)
    return F.cosine_similarity(embed1, embed2, dim=-1).item()
    