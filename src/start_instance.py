import boto3

def lambda_handler(event, context):
    region = 'region'
    ec2 = boto3.client('ec2', region_name=region)
    instance_id = 'id-instance'
    response =  str(ec2.describe_instance_status(InstanceIds=[instance_id]))

    if instance_id in response:
        ec2.stop_instances(InstanceIds=[instance_id])
        status = "stop"
    else:
        ec2.start_instances(InstanceIds=[instance_id])
        status = "start"

    return {
        'statusCode': 200,
        'instance': status
    }