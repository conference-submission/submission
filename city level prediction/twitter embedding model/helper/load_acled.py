import json
import requests

def load_acled_riots(country, city, start_date, end_date):
	params = (
	    ('country', country),
	    ('country_where', '='),
	    ('event_date', start_date+'|'+end_date),
	    ('event_date_where', 'BETWEEN'),
	    ('location', city),
	    ('event_type', 'Riots'),
	    ('event_type_where', '='),
	    ('terms', 'accept'),
	)

	r = requests.get('https://api.acleddata.com/acled/read', params=params)
	response = r.json()
	return response['data']

def load_acled_protests(country, city, start_date, end_date):
	params = (
	    ('country', country),
	    ('country_where', '='),
	    ('event_date', start_date+'|'+end_date),
	    ('event_date_where', 'BETWEEN'),
	    ('location', city),
	    ('event_type', 'Protests'),
	    ('event_type_where', '='),
	    ('terms', 'accept'),
	)

	r = requests.get('https://api.acleddata.com/acled/read', params=params)
	response = r.json()
	return response['data']

################################################################################

country = 'Egypt'
city = 'Cairo'
start_date = '2019-01-01'
end_date = '2019-04-06'
riots = load_acled_riots(country, city, start_date, end_date)
protests = load_acled_protests(country, city, start_date, end_date)
ids = []
ids += riots
ids += protests


with open('', 'w') as f:
	json.dump(ids, f)













