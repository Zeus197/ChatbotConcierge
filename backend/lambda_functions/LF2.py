import json
import boto3
import sys
import requests
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

sns = boto3.client('sns')
sqs = boto3.resource('sqs')
dynamodb = boto3.resource('dynamodb')
table_name = "yelp-restaurants"
region = 'us-east-1'
service = 'es'
index = 'restaurants'

host = 'https://search-restaurants-7d2j6iva6cvr7kor5tbu4oe6p4.us-east-1.es.amazonaws.com/'
url = host + '/' + index + '/_search?'
queue = sqs.get_queue_by_name(QueueName='RestaurantQueue')


def get_recommendations(request):
    table = dynamodb.Table(table_name)

    headers = headers = {
        'Content-Type': "application/json",
        'Accept': "/",
        'Cache-Control': "no-cache",
        'Host': "search-restaurants-7d2j6iva6cvr7kor5tbu4oe6p4.us-east-1.es.amazonaws.com",
        'Accept-Encoding': "gzip, deflate",
        'Content-Length': "335",
        'Connection': "keep-alive",
        'cache-control': "no-cache"
    }

    cuisine = request['Cuisine']

    # search_params = """{"query":{"bool":{"must":[{"match":{"cuisine":\"""" + cuisine + \
        # """\"}}],"must_not":[],"should":[]}},"from":0,"size":3,"sort":[],"aggs":{}}"""
    search_params = {
        "from": 0,
        "size": 3,
        "query": {
            "function_score": {
                "query": {
                    "match": {
                        "cuisine": cuisine
                    }
                },
                "random_score": {}
            }
        }
    }
    response = requests.get(url=url, data=json.dumps(search_params), headers=headers)
    print(response.text, '\n')
    response_dict = json.loads(response.text)
    recommendations = []
    for i in response_dict.get("hits").get("hits"):
        x = table.query(KeyConditionExpression=Key('restaurant_id').eq(i.get("_id")))
        res_name = x['Items'][0]['name']

        res_address = " ".join(x['Items'][0]['display_address'])
        recommendations.append({'name': res_name, 'address': res_address})
    return recommendations


def message_template(request, msg_content):
    c_data_cuisine = request['Cuisine']
    c_data_people = request['NumberPeople']
    c_data_time = request['DiningTime']

    content = 'Hello! Here are my ' + c_data_cuisine + ' restaurant suggestions for ' + \
        c_data_people + ' people, on ' + ' at ' + c_data_time + '.\n\n'
    for i in range(len(msg_content)):
        content += (str(i+1) + '. ' +
                    msg_content[i]['name'] + ', located at ' + msg_content[i]['address'])
        content += '\n'
    print(content)
    return content


def send_to_sns(common_data, raw_data):

    msg = message_template(common_data, raw_data)
    c_data_phone = "+1" + common_data['PhoneNumber']

    sns.publish(
        PhoneNumber=c_data_phone,
        Message=msg)

def delete_message(message):
    """
    Delete a message from a queue. Clients must delete messages after they
    are received and processed to remove them from the queue.

    Usage is shown in usage_demo at the end of this module.

    :param message: The message to delete. The message's queue URL is contained in
                    the message's metadata.
    :return: None
    """
    try:
        message.delete()
        logger.info("Deleted message: %s", message.message_id)
    except ClientError as error:
        logger.exception("Couldn't delete message: %s", message.message_id)
        raise error


def delete_messages(queue, messages):
    """
    Delete a batch of messages from a queue in a single request.

    Usage is shown in usage_demo at the end of this module.

    :param queue: The queue from which to delete the messages.
    :param messages: The list of messages to delete.
    :return: The response from SQS that contains the list of successful and failed
             message deletions.
    """
    try:
        entries = [{
            'Id': str(ind),
            'ReceiptHandle': msg.receipt_handle
        } for ind, msg in enumerate(messages)]
        response = queue.delete_messages(Entries=entries)
        if 'Successful' in response:
            for msg_meta in response['Successful']:
                logger.info("Deleted %s", messages[int(
                    msg_meta['Id'])].receipt_handle)
        if 'Failed' in response:
            for msg_meta in response['Failed']:
                logger.warning(
                    "Could not delete %s",
                    messages[int(msg_meta['Id'])].receipt_handle
                )
    except ClientError:
        logger.exception("Couldn't delete messages from queue %s", queue)
    else:
        return response


def receive_messages(queue, max_number, wait_time):
    """
    Receive a batch of messages in a single request from an SQS queue.

    Usage is shown in usage_demo at the end of this module.

    :param queue: The queue from which to receive messages.
    :param max_number: The maximum number of messages to receive. The actual number
                       of messages received might be less.
    :param wait_time: The maximum time to wait (in seconds) before returning. When
                      this number is greater than zero, long polling is used. This
                      can result in reduced costs and fewer false empty responses.
    :return: The list of Message objects received. These each contain the body
             of the message and metadata and custom attributes.
    """
    try:
        messages = queue.receive_messages(
            MessageAttributeNames=['All'],
            MaxNumberOfMessages=max_number,
            WaitTimeSeconds=wait_time
        )
        for msg in messages:
            logger.info("Received message: %s: %s", msg.message_id, msg.body)
            request = extract_request(msg.message_attributes)
            recommendations = get_recommendations(request)
            send_to_sns(request, recommendations)

    except ClientError as error:
        logger.exception("Couldn't receive messages from queue: %s", queue)
        raise error
    else:
        return messages


def extract_request(message):
    request = {}
    request['Cuisine'] = message.get('Cuisine').get('StringValue')
    request['Location'] = message.get('Location').get('StringValue')
    request['NumberPeople'] = message.get('People').get('StringValue')
    request['DiningTime'] = message.get('Time').get('StringValue')
    request['PhoneNumber'] = message.get('PhoneNumber').get('StringValue')

    return request


def lambda_handler(event, context):
    batch_size = 5
    more_messages = True
    while more_messages:
        received_messages = receive_messages(queue, batch_size, 2)
        if received_messages:
            delete_messages(queue, received_messages)
            print("Messages deleted from queue")
        else:
            more_messages = False
    print('Done!!')

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }