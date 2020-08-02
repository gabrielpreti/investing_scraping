import json
import deepdiff
import pprint
from pymongo import MongoClient
import boto3

# dict_1 = {
#     "a": 1,
#     "nested": {
#         "b": 1,
#     }
# }
#
# dict_2 = {
#     "a": 2,
#     "nested": {
#         "b": 2,
#     }
# }
#
# diff = deepdiff.DeepDiff(dict_1, dict_2)
# print(json.dumps(diff, indent=4))

##########################################
# Load mongo data
##########################################
MONGO_HOST = "3.86.47.246"
mongo_client = MongoClient(MONGO_HOST, 27017)
mongo_database = mongo_client.stoch_data_database
investing_data_collection = mongo_database.investing_collection
cursor = investing_data_collection.find({"datetime": {
    "$gte": "2020-07-27",
    "$lte": "2020-08-01"
}})
mongo_data = {}
for document in cursor:
    if 'code' not in document['General-Information'].keys():
        continue
    if '_id' in list(document.keys()):
        del document['_id']
    # pprint.pprint(document)
    day = document['datetime'].split(" ")[0]
    code = document['General-Information']['code']
    print("%s %s" % (day, code))
    if day=='2020-07-30' and code=='BRAP4':
        pprint.pprint(document)
        break
    del document['datetime']
    if day not in mongo_data.keys():
        mongo_data[day] = {}
    mongo_data[day][code] = document


with open('mongo_data.json', 'w') as mongo_data_file:
    json.dump(mongo_data, mongo_data_file, indent=4)

##########################################
# Load s3
##########################################
s3 = boto3.resource('s3')
my_bucket = s3.Bucket('preti-stock-crawling-output')
f = None
s3_data = {}
for file in my_bucket.objects.all():
    print(file.key)
    if not file.key.startswith('2020'):
        print("Skipping ...")
        continue

    content = file.get()['Body'].read()
    json_content =  json.loads(content)
    # pprint.pprint(json_content)

    if 'code' not in json_content['General-Information'].keys():
        continue
    day = file.key.split('/')[0]
    code = json_content['General-Information']['code']
    print("%s %s" % (day, code))
    if day not in s3_data.keys():
        s3_data[day] = {}
    s3_data[day][code] = json_content

with open('s3_data.json', 'w') as s3_data_file:
    json.dump(s3_data, s3_data_file, indent=4)

##########################################
# Compare data
##########################################
mongo_data = None
with open('mongo_data.json', 'r') as mongo_data_file:
    mongo_data = json.load(mongo_data_file)

s3_data = None
with open('s3_data.json', 'r') as s3_data:
    s3_data = json.load(s3_data)

diff = deepdiff.DeepDiff(mongo_data, s3_data)
print(json.dumps(diff, indent=4))
pprint.pprint(diff)

diff = deepdiff.DeepDiff(mongo_data['2020-07-31']['BRAP4']['General-Information'], s3_data['2020-07-31']['BRAP4']['General-Information'])
pprint.pprint(diff)

pprint.pprint(s3_data['2020-07-31']['BRAP4']['General-Information'])

#Compara quantidade de registros
days = ['2020-07-27', '2020-07-28', '2020-07-29', '2020-07-30', '2020-07-31']
    print(d)
    print("S3: %s" % len(s3_data[d].keys()))
    print("Mongo: %s" % len(mongo_data[d].keys()))

#Compara somente os registros encontrandos em ambos os datasets
for d in days:
    for code in s3_data[d].keys():
        if code not in mongo_data[d].keys():
            continue
        print("Comparing code %s in day %s" % (code, d))

        s3_data_to_compare = s3_data[d][code]
        mongo_data_to_compare = mongo_data[d][code]

        if 'datetime' in s3_data_to_compare.keys():
            del s3_data_to_compare['datetime']
        if 'datetime' in mongo_data_to_compare.keys():
            del mongo_data_to_compare['datetime']

        if 'Technical-TechnicalAnalysis' in s3_data_to_compare.keys():
            del  s3_data_to_compare['Technical-TechnicalAnalysis']
        if 'Technical-TechnicalAnalysis' in mongo_data_to_compare.keys():
            del mongo_data_to_compare['Technical-TechnicalAnalysis']

        if 'General-Information' in s3_data_to_compare.keys() and 'Volume Medio (3m)' in s3_data_to_compare['General-Information'].keys():
            del s3_data_to_compare['General-Information']['Volume Medio (3m)']
        if 'General-Information' in mongo_data_to_compare.keys() and 'Volume Medio (3m)' in mongo_data_to_compare['General-Information'].keys():
            del mongo_data_to_compare['General-Information']['Volume Medio (3m)']

        pprint.pprint(deepdiff.DeepDiff(s3_data_to_compare, mongo_data_to_compare))
