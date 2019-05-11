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
	matrix_full = [[x/longitude for x in y] for y in res]
	return matrix_full[:30]


def getCounts(date, lap):
	with open('') as f:
		data = json.load(f)
		x = datetime.strptime(date, '%Y-%m-%d')+timedelta(days=lap)
		day = x.strftime('%Y-%m-%d')
		return data[day]


longitude = 60
lap = 7

# start_date = '2015-05-01'
start_date = '2016-01-01'
end_date = '2019-01-01'

days_min = datetime.strptime(start_date, '%Y-%m-%d')
days_max = datetime.strptime(end_date, '%Y-%m-%d')
days = [days_min + timedelta(days=x) for x in range((days_max-days_min).days + 2)]
days1 = [x.strftime('%Y-%m-%d') for x in days]

with open('tweet-matrix-amman-en.pickle', 'rb') as f:
	daily_matrix = pickle.load(f)

data_0 = []
data_1 = []
data_2 = []

for i in range(len(days1)-1):
	date = days1[i]
	res = {}
	indic = getTweetsAvg(date, longitude, daily_matrix)
	res['date'] = (datetime.strptime(date, '%Y-%m-%d')+timedelta(days=lap)).strftime('%Y-%m-%d')
	c = getCounts(date, lap)
	res['counts'] = c
	res['indicators'] = indic
	if c<=0:
		data_0.append(res)
	elif c<=1:
		data_1.append(res)
	else:
		data_2.append(res)
	print(date + ' done')

data = [data_0, data_1, data_2]
for i in range(3):
	with open('', 'w') as f:
		ndjson.dump(data[i], f)
	print(len(data[i]))






	












