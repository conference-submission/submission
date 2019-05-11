# This script is to anonymize Twitter data in purpose of not violating Twitter policy. 
# https://developer.twitter.com/en/developer-terms/agreement-and-policy#id34
# User data and original posts are removed for submission purpose. 
# Output only contains Tweet IDs.

import pandas as pd
from langdetect import detect
import json
import preprocessor as p
from datetime import datetime, timedelta
import os
import io

def parseInput(folder_path, filename):
	converter = {'Date (EST)':str, 'URL':str}
	df = pd.read_excel(folder_path+filename, converters=converter, skiprows=[0], encoding='utf-8')
	url = []
	for i in df.index:
		url.append(df['URL'][i].split('/')[-1])
	return url


folder_path = ''
files = os.listdir(folder_path)

res = []
for filename in files:
	if filename.endswith('.xls') and filename.startswith('Posts'):
		url = parseInput(folder_path, filename)
		res += url
with open('', 'w') as f:
	for id in res:
		f.write("%s\n" % id)



