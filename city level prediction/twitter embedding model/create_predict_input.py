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

def getTweetsAvg(date, longitude, daily_matrix):
	res = [[0 for col in range(300)] for row in range(62)]
	days = [datetime.strptime(date, '%Y-%m-%d') - timedelta(days=x) for x in range(1, longitude+1)]
	days1 = [x.strftime('%Y-%m-%d') for x in days]
	for d in days1:
		res = addM(res, daily_matrix[d])
	full_matrix = [[x/longitude for x in y] for y in res]
	return full_matrix[:30]



longitude = 60
lap = 0

start_date = '2019-01-01'
end_date = '2019-02-25'

days_min = datetime.strptime(start_date, '%Y-%m-%d')
days_max = datetime.strptime(end_date, '%Y-%m-%d')
days = [days_min + timedelta(days=x) for x in range((days_max-days_min).days + 2)]
days1 = [x.strftime('%Y-%m-%d') for x in days]

with open('tweet-matrix-cairo-en.pickle', 'rb') as f:
	daily_matrix = pickle.load(f)

data = []

for i in range(len(days1)-1):
	date = days1[i]
	res = {}
	indic = getTweetsAvg(date, longitude, daily_matrix)
	res['date'] = (datetime.strptime(date, '%Y-%m-%d')+timedelta(days=lap)).strftime('%Y-%m-%d')
	res['indicators'] = indic
	data.append(res)
	print(date + ' done')

with open('cairo.ndjson', 'w') as f:
	ndjson.dump(data, f)







	












