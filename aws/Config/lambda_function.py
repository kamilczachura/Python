import boto3
import json
import time


def lambda_handler(event, context):
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
            RoleArn="arn:aws:iam::" + a + ":role/cloudops",
            RoleSessionName="cross_acct_lambda"
            )
        
            ACCESS_KEY = account_b['Credentials']['AccessKeyId']
            SECRET_KEY = account_b['Credentials']['SecretAccessKey']
            SESSION_TOKEN = account_b['Credentials']['SessionToken']
            
            #Create new lambda with script to automate tag apply on new ELB
            client = boto3.client('lambda',
                    aws_access_key_id=ACCESS_KEY,
                    aws_secret_access_key=SECRET_KEY,
                    aws_session_token=SESSION_TOKEN
                    )


            response = client.create_function(
                Code={
                    'ZipFile': open('function.zip', 'rb').read()
                },
                Description='Automation for Tagging new ELB on this account, please do not remove it. Contact person kamil.czachura.ext@bayer.com',
                FunctionName='Elbv2-Tagging-Automation-WAF',
                MemorySize=256,
                Publish=True,
                Role='arn:aws:iam::' + a + ':role/cloudops',
                Runtime='python3.9',
                Handler='lambda_function.lambda_handler',
                Timeout=900,
                TracingConfig={
                    'Mode': 'PassThrough',
                },
            )

            #Add permission for lambda to be able invoke lambda directly from config rule
            response = client.add_permission(
                Action='lambda:InvokeFunction',
                FunctionName='Elbv2-Tagging-Automation-WAF',
                Principal='config.amazonaws.com',
                StatementId='config',
        )

            #Wait till lambda will be fully aviaiable.
            time.sleep(20)

            #Create configuration to invoke lambda funtion when new ELBv2 will be created
            client = boto3.client('config',
                    aws_access_key_id=ACCESS_KEY,
                    aws_secret_access_key=SECRET_KEY,
                    aws_session_token=SESSION_TOKEN
                    )
            
            response = client.put_config_rule(
                ConfigRule={
                    'ConfigRuleName': 'Apply-tag-on-new-elb',
                    'Description': 'Please do not remove this rule, its a part of automation. Rule will trigger lambda function when new loadbalancer will be created',
                    'Scope': {
                        'ComplianceResourceTypes': [
                            'AWS::ElasticLoadBalancingV2::LoadBalancer',
                        ]
                    },
                    'Source': {
                        'Owner': 'CUSTOM_LAMBDA',
                        'SourceIdentifier': 'arn:aws:lambda:us-east-1:' + a + ':function:Elbv2-Tagging-Automation-WAF',
                        'SourceDetails': [
                                {'EventSource': 'aws.config', 'MessageType': 'ConfigurationItemChangeNotification'
                                },
                                {'EventSource': 'aws.config', 'MessageType': 'OversizedConfigurationItemChangeNotification'
                                }
                            ]
                    },
                    'ConfigRuleState': 'ACTIVE',
                }
            )