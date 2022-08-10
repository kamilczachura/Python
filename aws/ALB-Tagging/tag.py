import boto3
import json
import datetime
import uuid

###List of Accounts
f = open("accounts.txt","r")
accounts=[]
for line in f:
        line=line.strip()
        accounts.append(line)
f.close()


###auth part, assume role on different account
for a in accounts:
        sts_connection = boto3.client('sts')
        account_b = sts_connection.assume_role(
        RoleArn="arn:aws:iam::" + a + ":role/tag-role",
        RoleSessionName="cross_acct_lambda"
        )
    
        ACCESS_KEY = account_b['Credentials']['AccessKeyId']
        SECRET_KEY = account_b['Credentials']['SecretAccessKey']
        SESSION_TOKEN = account_b['Credentials']['SessionToken']

        #Json with list of elbv2
        client = boto3.client('elbv2',
                aws_access_key_id=ACCESS_KEY,
                aws_secret_access_key=SECRET_KEY,
                aws_session_token=SESSION_TOKEN
                )
        response = client.describe_load_balancers(
                LoadBalancerArns=[]
        )
        

        #Convert JSON to count all ALB
        def defaultconverter(o):
                if isinstance(o, datetime.datetime):
                        return o.__str__()
        json.dumps(response, default = defaultconverter)

        li = [item.get('Scheme') for item in response["LoadBalancers"]]
        name_length = len(li)

        #Make a list of elbv2 with scheme internet-facing or internal
        client = boto3.client('elbv2',
                aws_access_key_id=ACCESS_KEY,
                aws_secret_access_key=SECRET_KEY,
                aws_session_token=SESSION_TOKEN
                )
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
                        'Key': 'bayer:privileged:fw-mgr:exception',
                        'Value': 'internal'
                        },
                ]
        )
        #Tag apply external
        for a in elbv2e:
                response = client.remove_tags(
                ResourceArns=[a],
                Tags=[
                        {
                        'Key': 'bayer:privileged:fw-mgr:exception',
                        'Value': ''
                        },
                ]
                )






