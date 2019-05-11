import os
import json
import math
import pickle

dic = {}

folder_path = ''
files = os.listdir(folder_path)


for filename in files:
	if filename.endswith('.json') and filename.startswith('2'):
		with open(folder_path+filename) as f:
			data = json.load(f)
			for record in data:
				score = math.log((abs(record['Followers'])+1)**2/(abs(record['Following'])+1))
				dic[record['Author']+record['Date']] = score

scores = []
for key, score in dic.items():
	scores.append(score)
max = max(scores)
min = min(scores)

for key, score in dic.items():
	dic[key] = (dic[key]-min)/(max-min)

with open('impact-amman.pickle', 'wb') as output_file:
	pickle.dump(dic, output_file)

