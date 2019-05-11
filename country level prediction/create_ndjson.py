import pandas as pd
from datetime import datetime, timedelta
import json
import ndjson


def twitterVolume(date, longitude):
	df = pd.read_excel('', sheet_name='Social unrest events prediction', converters={'Date':str})
	for i in df.index:
		if(df['Date'][i]==date+' 00:00:00'):
			res = []
			for x in range(longitude):
				res.append(df['Relevant Posts'][i-longitude])
				i += 1
			return res


def twitterSentiment(date, longitude):
	df = pd.read_excel('', sheet_name='Social unrest events prediction', converters={'Analysis Date':str})
	for i in df.index:
		if(df['Analysis Date'][i]==date+' 00:00:00'):
			res = []
			for x in range(longitude):
				res.append(df['Anger'][i-longitude])
				i += 1
			return res


def getCounts(date, lap):
	with open('') as f:
		data = json.load(f)
		x = datetime.strptime(date, '%Y-%m-%d')+timedelta(days=lap)
		day = x.strftime('%Y-%m-%d')
		return data[day]


def indicators(date, longitude, indicator):
	df = pd.read_excel('', sheet_name='Jordan', converters={'Date':str})
	start_date = datetime.strptime(date, '%Y-%m-%d')-timedelta(days=longitude)
	end_date = datetime.strptime(date, '%Y-%m-%d')-timedelta(days=1)
	days = [start_date + timedelta(days=x) for x in range((end_date-start_date).days + 2)]
	days1 = [x.strftime('%Y-%m-%d') for x in days]
	res = []
	for x in range(len(days1)-1):
		for i in df.index:
			if(str(df['Date'][i]).startswith(days1[x][0:7])):
				res.append(round(float(df[indicator][i]), 2))
	return res


longitude = 30
lap = 3

start_date = '2015-05-01'
end_date = '2019-01-01'

days_min = datetime.strptime(start_date, '%Y-%m-%d')
days_max = datetime.strptime(end_date, '%Y-%m-%d')
days = [days_min + timedelta(days=x) for x in range((days_max-days_min).days + 2)]
days1 = [x.strftime('%Y-%m-%d') for x in days]

data_0 = []
data_1 = []
data_2 = []
data_3 = []
data_4 = []
data_5 = []
data_6 = []
data_7 = []
data_8 = []
data_9 = []
data_10 = []
data_11 = []

for i in range(len(days1)-1):
	date = days1[i]
	res = {}
	indic = []
	indic.append([twitterVolume(date, longitude), twitterVolume(date, longitude)])
	indic.append([twitterSentiment(date, longitude), twitterSentiment(date, longitude)])
	indic.append([indicators(date, longitude, 'Copper'), indicators(date, longitude, 'Copper')])
	indic.append([indicators(date, longitude, 'Wheat'), indicators(date, longitude, 'Wheat')])
	indic.append([indicators(date, longitude, 'Maize'), indicators(date, longitude, 'Maize')])
	indic.append([indicators(date, longitude, 'Natrual gas'), indicators(date, longitude, 'Natrual gas')])
	indic.append([indicators(date, longitude, 'Iron ore'), indicators(date, longitude, 'Iron ore')])
	res['country'] = 'Jordan'
	res['date'] = (datetime.strptime(date, '%Y-%m-%d')+timedelta(days=lap)).strftime('%Y-%m-%d')
	c = getCounts(date, lap)
	res['counts'] = c
	res['indicators'] = indic
	if c<=0:
		data_0.append(res)
	elif c<=1:
		data_1.append(res)
	elif c<=2:
		data_2.append(res)
	elif c<=3:
		data_3.append(res)
	elif c<=4:
		data_4.append(res)
	elif c<=5:
	    data_5.append(res)
	elif c<=6:
	    data_6.append(res)
	elif c<=7:
		data_7.append(res)
	elif c<=8:
		data_8.append(res)
	elif c<=9:
	    data_9.append(res)
	elif c<=10:
	    data_10.append(res)
	else:
	    data_11.append(res)
	print(date + ' done')

data = [data_0, data_1, data_2, data_3, data_4, data_5, data_6, data_7, data_8, data_9, data_10, data_11]
for i in range(12):
	with open('jordan_'+str(i)+'.ndjson', 'w') as f:
		ndjson.dump(data[i], f)
	print(len(data[i]))






	












