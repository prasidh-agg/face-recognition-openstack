import boto3
import json
import time

sqs = boto3.client('sqs')
s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')

function_name = "face-recog-lambda-serverlesspresso"
queue_url = "https://sqs.us-west-1.amazonaws.com/702729433599/cse546-input-queue"

while True:
    response = sqs.receive_message(QueueUrl=queue_url, WaitTimeSeconds=10)

    if 'Messages' not in response.keys():
        print("message not found!")
        continue

    # get the message body
    message = response['Messages'][0]
    body = json.loads(message['Body'])

    # extract the object key name from the message
    s3_key_name = body['Records'][0]['s3']['object']['key']

    event = {
        "Records": [
            {
                "s3": {
                    "bucket": {
                        "name": input_bucket_name
                    },
                    "object": {
                        "key": s3_key_name
                    }
                }
            }
        ]
    }

    event_payload = json.dumps(event)

    # invoke lambda function with the event payload
    lambda_client.invoke(FunctionName=function_name,
                         InvocationType='Event', Payload=event_payload)

    print("Video name: ", s3_key_name)
    s3_key_name = s3_key_name.split('.')[0] + '.csv'
    # checking if file in s3 bucket
    while True:
        try:
            s3.get_object(Bucket=output_bucket_name, Key=s3_key_name)

            # if the file exists, print
            obj = s3.get_object(Bucket=output_bucket_name, Key=s3_key_name)
            file_content = obj['Body'].read().decode('utf-8')
            print(file_content)

            # exit the loop once the file has been found
            break

        except s3.exceptions.NoSuchKey:
            # if the file does not exist yet, wait for some time before checking again
            print(f"{s3_key_name} not found in {output_bucket_name}, waiting...")
            time.sleep(1)

    sqs.delete_message(QueueUrl=queue_url,
                       ReceiptHandle=message['ReceiptHandle'])
