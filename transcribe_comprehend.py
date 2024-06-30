import boto3
import json
import time
import uuid
import urllib.request
s3 = boto3.client('s3', region_name='us-east-1')
transcribe = boto3.client('transcribe', region_name='us-east-1')
comprehend = boto3.client('comprehend',  region_name='us-east-1')
bucketName='<YOUR_S3_BUCKET>'
def lambda_handler(event, context):
    #Transcription Service
    job_name = f'transcription_job_{int(time.time())}_{uuid.uuid4()}'
    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri':f's3://{bucketName}/AppData/myaudio.wav'},  # Adjust to your S3 bucket
        LanguageCode='en-US'
    )
    while True:
        result = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        if result['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
            break
        elif result['TranscriptionJob']['TranscriptionJobStatus'] == 'FAILED':
            print("Transcription job failed")
            print(result['TranscriptionJob'])
            return
        else:
            time.sleep(5)  # Poll every 5 seconds
    # Retrieve the transcription result when the job is completed
    transcript_file_uri = result['TranscriptionJob']['Transcript']['TranscriptFileUri']
    with urllib.request.urlopen(transcript_file_uri) as response:
        transcript_data = json.loads(response.read().decode('utf-8'))
    transcript = transcript_data['results']['transcripts'][0]['transcript']
    # Comprehend service to detect PII entities
    comprehend = boto3.client('comprehend',
    region_name = 'us-east-1')
    # Text to analyze
    text_to_analyze = transcript
    response = comprehend.detect_pii_entities(Text=text_to_analyze, LanguageCode='en')
    pii_entities = response.get('Entities', [])
    redacted_text = text_to_analyze
    for entity in pii_entities:
        entity_start = entity['BeginOffset']
        entity_end = entity['EndOffset']
        redacted_text = redacted_text[:entity_start] + '*' * (entity_end - entity_start) + redacted_text[entity_end:]
    #Uploading redacted text to S3
    s3 = boto3.client('s3',  region_name='us-east-1')
    bucket_name = bucketName
    s3_object_key = 'AppOutput/redacted_text.txt'
    try:
        response = s3.put_object(
            Bucket=bucket_name,
            Key=s3_object_key,
            Body=redacted_text
        )
        print("Redacted text uploaded successfully to S3. S3 Object URL:", response['ObjectURL'])
    except Exception as e:
        print("Error uploading redacted text to S3:", str(e))
    print("Redacted Text:", redacted_text)