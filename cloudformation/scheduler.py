import boto3


def handle_stack_creation(event, context):
    client = boto3.client('cloudformation')

    STACK_NAME = "investing-scrapping-stack"
    # CLOUDFORMATION_FILE = "./cloudformation/investingscrapping_aws.yaml"
    CLOUDFORMATION_FILE = './investingscrapping_aws.yaml'

    template_body = ""
    with open(CLOUDFORMATION_FILE, mode='r') as template_file:
        template_body = template_file.read()

    parameters = [
        {'ParameterKey': 'ProjectName', 'ParameterValue':' Investing Scrapping'},
        {'ParameterKey': 'NeedsEBSVolume', 'ParameterValue': 'true'},
        {'ParameterKey': 'EC2MarketType', 'ParameterValue': 'On-demand'},
        {'ParameterKey': 'EC2KeyName', 'ParameterValue': 'pytradejobs'},
        {'ParameterKey': 'EBSVolumeId', 'ParameterValue': 'vol-0720dcb52f88d1c3e'},
        {'ParameterKey': 'NetworkStack', 'ParameterValue': 'InvestingScrappingNetwork'}
    ]
    client.create_stack(StackName=STACK_NAME, TemplateBody=template_body, Parameters=parameters)
    waiter = client.get_waiter('stack_create_complete')
    waiter.wait()

    stack_description = client.describe_stacks(StackName=STACK_NAME)
    stack_id = stack_description['Stacks'][0]['StackId']
    ec2_instance_id = [x['OutputValue'] for x in stack_description['Stacks'][0]['Outputs'] if x['OutputKey']=='Ec2InstanceId'][0]
    ec2_instance_public_ip = [x['OutputValue'] for x in stack_description['Stacks'][0]['Outputs'] if x['OutputKey']=='Ec2InstancePublicIp'][0]

    return {'stack_id': stack_id, 'ec2_id': ec2_instance_id, 'ec2_public_ip': ec2_instance_public_ip}


def handle_stack_removal(event, context):
    client = boto3.client('cloudformation')

    stack_name = "investing-scrapping-stack"
    stack_description = client.describe_stacks(StackName=stack_name)
    stack_id = stack_description['Stacks'][0]['StackId']
    ec2_instance_id = [x['OutputValue'] for x in stack_description['Stacks'][0]['Outputs'] if x['OutputKey'] == 'Ec2InstanceId'][0]
    ec2_instance_public_ip = [x['OutputValue'] for x in stack_description['Stacks'][0]['Outputs'] if x['OutputKey'] == 'Ec2InstancePublicIp'][0]

    client.delete_stack(StackName=stack_id)
    return {'stack_id': stack_id, 'ec2_id': ec2_instance_id, 'ec2_public_ip': ec2_instance_public_ip}