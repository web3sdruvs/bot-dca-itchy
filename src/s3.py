 #register order in csv
import boto3

def s3():
    """
    Retrieves data from an AWS S3 bucket, specifically a CSV file containing
    token-related information. If the file does not exist, it initializes the file
    with a header and returns a 500 status code.

    Returns:
    - dict: A dictionary containing the response status code.

    Note: Make sure to replace 'YOUR BUCKET NAME' with the actual S3 bucket name.
    """
    bucket_name = 'YOUR BUCKET NAME'
    file_name = 'token/token.csv'
    s3 = boto3.client('s3')
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_name)
        csv_data = response['Body'].read().decode('utf-8')
    except s3.exceptions.NoSuchKey:
        csv_data = 'symbol,quantity,timestamp,index_current,index_class,dominance_btc_global,percent_1h_token,percent_24h_token,percent_7d_token,rsi_value,intensity\n'
        s3.put_object(Bucket=bucket_name, Key=file_name, Body=csv_data)
        return {
            'statusCode': 500,
        }
s3()