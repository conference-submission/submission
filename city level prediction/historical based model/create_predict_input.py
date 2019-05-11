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

longitude = 30
lap = 3

start_date = '2019-01-01'
end_date = '2019-02-23'

days_min = datetime.strptime(start_date, '%Y-%m-%d')
days_max = datetime.strptime(end_date, '%Y-%m-%d')
days = [days_min + timedelta(days=x) for x in range((days_max-days_min).days + 2)]
days1 = [x.strftime('%Y-%m-%d') for x in days]

data = []

for i in range(len(days1)-1):
	date = days1[i]
	res = {}
	indic = []
	indic.append([getHistorical(date, longitude), getHistorical(date, longitude)])
	res['country'] = 'Jordan'
	res['date'] = (datetime.strptime(date, '%Y-%m-%d')+timedelta(days=lap)).strftime('%Y-%m-%d')
	res['indicators'] = indic
	data.append(res)
	print(date + ' done')

with open('', 'w') as f:
	ndjson.dump(data, f)







	












