import yelpapi
from yelpapi import YelpAPI
import json
import boto3
from decimal import Decimal
import requests
import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table("yelp-restaurants")

region = 'us-east-1'
service = 'es'

host = 'https://search-restaurants-7d2j6iva6cvr7kor5tbu4oe6p4.us-east-1.es.amazonaws.com/'

index = 'restaurants'
type = 'Restaurant'

url = host + '/' + index + '/' + type + '/'

headers = { "Content-Type": "application/json" }

# write private api_key to access yelp here
api_key = 'JEzsqyMQ8D2xY1-FlCDni5xs8Z3hu7ChI3XxK32n5i4bbdRUvIOOi744xh5WtpfYG_TL-uWhuZWDGl8jUkA3h--d9RrwDRbfEqhK0V4-Y9S2HXkJuJ-mLTtPtJ2QX3Yx'

yelp_api = YelpAPI(api_key)

data = ['id', 'name', 'review_count', 'rating', 'coordinates', 'address1', 'zip_code', 'phone']
es_data = ['id']

# cuisines = ["thai", "chinese", "mexican"]
cuisines = ["mexican"]


def populate_database(response, cuisine):
    json_response = json.loads(json.dumps(response), parse_float=Decimal)
    for t in json_response["businesses"]:
        dict1 = { key:value for (key,value) in t.items() if key in data}
        dict2 = {key:value for (key,value) in t["location"].items() if key in data}
        dict1.update(dict2)
        dict1.update(cuisine=cuisine)
        final_dict = {key: value for key, value in dict1.items() if value}
        timeStamp = str(datetime.datetime.now())
        final_dict.update(insertedAtTimestamp=timeStamp)
        
        my_es_id  = final_dict['id']
        es_dict = {key: final_dict[key] for key in final_dict.keys() & {'id', 'cuisine'}} 
        docs = json.loads(json.dumps(es_dict))
        
        r = requests.put(url+str(my_es_id), json=docs, headers=headers)
        print(r)
        table.put_item(Item=final_dict)
        

def lambda_handler(event=None, context=None):
    for cuisine in cuisines:
        for x in range(0, 1000, 50):
            response = yelp_api.search_query(term=cuisine, location='Manhattan', limit=50, offset=x)
            populate_database(response, cuisine)