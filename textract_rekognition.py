import boto3
import json

s3 = boto3.client('s3')  # Create an S3 client
def lambda_handler(event, context):
    
    # Document
    s3BucketName = "<YOUR_BUCKET_NAME_HERE>"
    documentName = "images/resume.png"
    
    s3_output = boto3.resource('s3').Bucket(s3BucketName)
    input_obj = s3.get_object(Bucket=s3BucketName, Key=documentName)
    input_stream = input_obj['Body'].read()
    
    if len(input_stream) == 0:
        return {
            'statusCode': 400,
            'body': 'Error: The input stream is empty.'
        }
        
    # Use the Rekognition service to detect text in the image
    rekognition = boto3.client('rekognition')
    response = rekognition.detect_text(
        Image={
            'Bytes': input_stream
        }
    )
    
    folder_name = 'RekognitionOutput/'
    json_response = json.dumps(response)
    output_obj = s3_output.Object(bucket_name=s3BucketName, key=f'{folder_name}{documentName}.json')
    output_obj.put(Body=json.dumps(response, indent=2))

    # Amazon Textract client
    textract = boto3.client('textract')
   
    # Call Amazon Textract
    response = textract.detect_document_text(
        Document={
            'S3Object': {
                'Bucket': s3BucketName,
                'Name': documentName
            }
        })

    # Process the detected text
    detected_text = ""
    for item in response["Blocks"]:
        if item["BlockType"] == "LINE":
            detected_text += item["Text"] + '\n'

    # Define the key for the new S3 object
    new_object_key = "TextractOutput/Resume.txt"

    # Upload the extracted text as a new S3 object
    s3.put_object(
        Bucket=s3BucketName,
        Key=new_object_key,
        Body=detected_text,
        ContentType='text/plain'  
    )

    response = {
        
        'statusCode': 200,
        'body': json.dumps({"message": "This is a JSON response."}, indent=2),
        's3Response': "Extracted text has been written to S3: s3://{}/{}".format(s3BucketName, new_object_key)
    }

    return response
