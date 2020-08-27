import json

import boto3
from boto3.dynamodb.conditions import Key

print('Loading function')


def validate_request(headers):
    status_code = 200
    try:
        auth_header = headers['authorization'].split()
        try:
            if auth_header[0] != 'Bearer' or len(auth_header) > 2:
                status_code = 400

            if auth_header[0] == 'Bearer' and len(auth_header) < 2:
                status_code = 403

        except IndexError:
            status_code = 400

    except KeyError:
        status_code = 400

    return status_code


def get_user_email(token, table):
    auth_result = table.get_item(
        Key={'token': token},
        ProjectionExpression='email'
    )

    try:
        user_email = auth_result['Item']['email']
        auth_code = 200
    except KeyError:
        user_email = None
        auth_code = 403

    return auth_code, user_email


def get_data(user_email, table):
    result_code = 200
    query_result = table.query(
        ScanIndexForward=False,
        KeyConditionExpression=Key('user').eq(user_email),
        ProjectionExpression="create_date, #txt",
        ExpressionAttributeNames={"#txt": "text"},
        Limit=10
    )

    try:
        notes = query_result['Items']
    except KeyError:
        notes = None

    return result_code, notes


def lambda_handler(event, context):
    headers = event['headers']
    client = boto3.resource('dynamodb')
    auth_table = client.Table('token-email-lookup')
    data_table = client.Table('user-notes')
    response_code = None
    response_body = ''

    validation_code = validate_request(headers)

    if validation_code == 200:
        auth_header = headers['authorization'].split()
        token = auth_header[1]
        auth_code, user_email = get_user_email(token, auth_table)

        if auth_code == 200:
            result_code, notes = get_data(user_email, data_table)

            if result_code == 200:
                if notes:
                    response_code = result_code
                    response_body = notes
                else:
                    response_code = result_code
        else:
            response_code = auth_code
    else:
        response_code = validation_code

    return {
        'statusCode': response_code,
        'body': json.dumps(response_body)
    }
