from unicodedata import name
import boto3
import botocore
import json
import datetime

def assume_role(account_id, account_role):
    sts_client = boto3.client('sts')
    role_arn = 'arn:aws:iam::' + account_id + ':role/' + account_role
    try:
        assumedRoleObject = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName="LambdaAssumeRole"
        )
        return assumedRoleObject['Credentials']
    except botocore.exceptions.ClientError as e:
        pass

def lambda_handler(event, context):
    #Get event
    list = event['invokingEvent']
    print(list)
    jsonlist = json.loads(list)
    print(jsonlist)
    accountId = jsonlist['configurationItem']['awsAccountId']
    print(accountId)
    #Assume role
    credentials = assume_role(accountId, 'tagging-role')   
    client = boto3.client('elbv2', aws_access_key_id=credentials['AccessKeyId'], aws_secret_access_key=credentials['SecretAccessKey'], aws_session_token=credentials['SessionToken'])
    #Json with list of elbv2 
    response = client.describe_load_balancers(
        LoadBalancerArns=[]
    )
    print(response)

    #Convert JSON to count all ALB    
    def defaultconverter(o):
        if isinstance(o, datetime.datetime):
            return o.__str__()
    json.dumps(response, default = defaultconverter)

    li = [item.get('Scheme') for item in response["LoadBalancers"]]
    name_length = len(li)
    print(name_length)

    #Make a list of elbv2 with scheme internet-facing or internal    
    client = boto3.client('elbv2', aws_access_key_id=credentials['AccessKeyId'], aws_secret_access_key=credentials['SecretAccessKey'], aws_session_token=credentials['SessionToken'])
    response = client.describe_load_balancers(
        LoadBalancerArns=[]
    )

    counter=0    
    elbv2i = []
    elbv2e = []
    while True:
        if name_length == 0:
            break        
        if response["LoadBalancers"][counter]['Scheme'] == 'internet-facing':
            elbv2e.append(response["LoadBalancers"][counter]['LoadBalancerArn'])
        elif response["LoadBalancers"][counter]['Scheme'] == 'internal':
            elbv2i.append(response["LoadBalancers"][counter]['LoadBalancerArn'])
        counter= counter+1        
        name_length=name_length-1

    #Tag apply internal    
        for a in elbv2i:

            response = client.add_tags(
            ResourceArns=[a],
            Tags=[
                    {
                    'Key': 'Type',
                    'Value': 'internal'                },
            ]
        )  
            print("Tag added to ELB: " + a)
