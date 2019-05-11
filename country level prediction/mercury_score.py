import pandas as pd
from datetime import datetime, timedelta
import json
import ndjson


def quality_score(predicted, actual):
    """
    Computes quality score on a scale of 0.0 to 1.0
    :param predicted: The predicted value
    :param actual: The actual value
    :param accuracy_denominator: The minimum value for scaling differences
    :return: Quality score value
    """
    if predicted <0 or actual<0:
        print("Negative case counts are not allowed")
        return
    numerator = abs(predicted-actual)
    denominator = max(predicted, actual, 4)
    qs = 1 - 1.*numerator/denominator
    return qs


def getCounts(date):
	with open('') as f:
		data = json.load(f)
		x = datetime.strptime(date, '%Y-%m-%d')
		day = x.strftime('%Y-%m-%d')
		return data[day]


total  = 0

with open('prediction.json') as f:
	d = json.load(f)
	data = d['payload']
	for entry in data:
		predicted = float(entry['Case_Count'])
		actual = getCounts(entry['Event_Date'])
		total = total + quality_score(predicted, actual)

	q_score = total/len(data)
	m_score = 1000000 * q_score
	print('quality_score: ' + str(q_score))
	print('mercury_score: ' + str(m_score))
		








	












