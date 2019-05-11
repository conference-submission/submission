# -*- coding: utf8 -*-
import gensim
import pandas as pd
from datetime import datetime, timedelta
import json
import ndjson
import os
import math
import pickle


def addM(a, b):
    res = []
    for i in range(len(a)):
        row = []
        for j in range(len(a[0])):
            row.append(a[i][j]+b[i][j])
        res.append(row)
    return res

def getTweetsAvg(d, wv_en):
	res = [[0 for col in range(300)] for row in range(62)]
	num = 0
	path = ''
	with open(path+d+'-en.json') as f:
		data = json.load(f)
		for record in data:
			cur = [[0 for col in range(300)] for row in range(62)]
			for c, idx in enumerate(record['Contents_idx']):
				word = wv_en.index2word[idx]
				word_vector = wv_en[word]
				cur[c] = word_vector
			cur_weighted = [[x*record['Impact'] for x in y] for y in cur]
			res = addM(res, cur_weighted)
			num += 1
	return [[x/num for x in y] for y in res]



start_date = '2015-04-01'
end_date = '2019-02-25'

days_min = datetime.strptime(start_date, '%Y-%m-%d')
days_max = datetime.strptime(end_date, '%Y-%m-%d')
days = [days_min + timedelta(days=x) for x in range((days_max-days_min).days + 1)]
days1 = [x.strftime('%Y-%m-%d') for x in days]

model_en = gensim.models.KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin', binary=True)

dic = {}

for date in days1:
	matrix = getTweetsAvg(date, model_en.wv)
	dic[date] = matrix
	print(date + ' done')


with open('tweet-matrix-amman-en.pickle', 'wb') as output_file:
	pickle.dump(dic, output_file)


