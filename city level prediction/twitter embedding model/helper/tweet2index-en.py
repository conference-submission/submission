# -*- coding: utf8 -*-
import gensim
import re
import numpy as np
from nltk import ngrams
import pickle
import os
import json
import io

# =========================
# ==== Helper Methods =====

# Clean/Normalize Arabic Text
def clean_str(text):
    #trim    
    text = text.strip()

    return text


def get_all_tokens(text):
    text = re.sub(r'[\,\.\;\(\)\[\]\_\+\#\@\!\?\؟\^]', ' ', text)
    tokens = [token for token in text.split(" ") if token.strip() != ""]
    return tokens


def convert_data_to_index(string_data, wv):
    index_data = []
    for word in string_data:
        if word in wv:
            index_data.append(wv.vocab[word].index)
    return index_data


# =========================
t_model = gensim.models.KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin', binary=True)
with open('impact-amman.pickle', 'rb') as f:
  score = pickle.load(f)

folder_path = ''
files = os.listdir(folder_path)
output_path = ''


for filename in files:
    if filename.endswith('-en.json') and filename.startswith('2'):
        print(filename)
        res = []
        with open(folder_path+filename) as f:
            data = json.load(f)
            for record in data:
                dic = {}
                dic['Date'] = record['Date']
                dic['Author'] = record['Author']
                dic['Impact'] = score[record['Author']+record['Date']]
                dic['Post Type'] = record['Post Type']

                tweet = record['Contents']
                print(tweet)
                normalized = clean_str(tweet)
                tokens = get_all_tokens(normalized)
                dic['Contents_idx'] = convert_data_to_index(tokens, t_model.wv)
                print(dic['Contents_idx'])
                res.append(dic)
        with io.open(output_path+filename, 'w') as out_file:
            json.dump(res, out_file, ensure_ascii=False)

