import pandas as pd
from langdetect import detect
import json
import preprocessor as p
from datetime import datetime, timedelta
import os
import io

def parseInput(filename):
	# given raw tweets spreadsheet return in json format, detect language
	converter = {'Date (EST)':str, 'Author':str, 'Posts':int, 'Followers':int, 'Following':int, 'Post Type':str}
	df = pd.read_excel(filename, sheet_name='Social unrest events prediction', converters=converter, skiprows=[0], encoding='utf-8')
	arabic = {}
	english = {}
	p.set_options(p.OPT.URL, p.OPT.MENTION, p.OPT.EMOJI, p.OPT.SMILEY, p.OPT.RESERVED)
	for i in df.index:
		# try:
		if df['Source'][i] != 'Twitter':
			continue
		dic = {}
		date = df['Date (EST)'][i].split(' ')
		dic['Date'] = date[0]
		tweet = df['Contents'][i]
		try:
			dic['lang'] = detect(tweet)
			dic['Posts'] = int(df['Posts'][i])
			dic['Followers'] = int(df['Followers'][i])
			dic['Following'] = int(df['Following'][i])
		except:
			continue
		tweet =  tweet.replace('#', '')
		dic['Contents'] = p.clean(tweet)
		dic['Author'] = df['Author'][i]
		dic['Post Type'] = df['Post Type'][i]
		if dic['lang']=='ar':
			if date[0] not in arabic:
				arabic[date[0]] = []
			arabic[date[0]].append(dic)
		else:
			if date[0] not in english:
				english[date[0]] = []
			english[date[0]].append(dic)		
	return arabic, english


folder_path = ''
files = os.listdir(folder_path)

for filename in files:
	if filename.endswith('.xls') and filename.startswith('Posts'):
		print(filename)
		arabic, english = parseInput(folder_path+filename)
		for key, value in arabic.items():
			with io.open('', 'w') as f:
				json.dump(value, f, ensure_ascii=False)
		for key, value in english.items():
			with io.open('', 'w') as f:
				json.dump(value, f, ensure_ascii=False)


































