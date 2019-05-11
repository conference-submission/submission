import pandas as pd
from datetime import datetime, timedelta
import json
import ndjson


def getHistorical(date, longitude):
	df = pd.read_excel('', sheet_name='Jordan', converters={'Date':str})
	for i in df.index:
		if(df['Date'][i]==date+' 00:00:00'):
			res = []
			for x in range(longitude):
				res.append(df['ACLED'][i-longitude])
				i += 1
			return res


def getCounts(date, lap):
	with open('') as f:
		data = json.load(f)
		x = datetime.strptime(date, '%Y-%m-%d')+timedelta(days=lap)
		day = x.strftime('%Y-%m-%d')
		return data[day]


longitude = 30
lap = 3

# start_date = '2015-05-01'
start_date = '2016-01-01'
end_date = '2019-01-01'

days_min = datetime.strptime(start_date, '%Y-%m-%d')
days_max = datetime.strptime(end_date, '%Y-%m-%d')
days = [days_min + timedelta(days=x) for x in range((days_max-days_min).days + 2)]
days1 = [x.strftime('%Y-%m-%d') for x in days]

data_0 = []
data_1 = []
data_2 = []


for i in range(len(days1)-1):
	date = days1[i]
	res = {}
	indic = []
	indic.append([getHistorical(date, longitude), getHistorical(date, longitude)])
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






	












