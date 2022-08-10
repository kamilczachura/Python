import boto3
client = boto3.client('dynamodb')

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

#Name of DynamoDB table
table = dynamodb.Table('aws-accounts')

#Scan all items in table
response = table.scan()
data = response['Items']

a=0
tabela=[]
while True:
    tabela.append(response["Items"][a]['id'])
    a=a+1
    if a==1536:
        break




table = boto3.resource('dynamodb').Table('aws-accounts')

# get item
response = table.get_item(Key={'id': '1'})
item = response['Item']

# update
item['splunkpush'] = 'this tag should be removed'

# put (idempotent)
table.put_item(Item=item)


