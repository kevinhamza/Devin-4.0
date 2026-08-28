# services/s3_service.py
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import boto3

app = FastAPI()

# Assuming AWS credentials are configured in the environment
s3_client = boto3.client('s3')

@app.get("/download/{file_name}")
def download_file(file_name: str):
    bucket_name = 'your-bucket-name'  # Replace with your actual S3 bucket name
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_name)
        return StreamingResponse(
            response['Body'].iter_chunks(),
            media_type=response['ContentType'],
            headers={'Content-Disposition': f'attachment;filename="{file_name}"'}
        )
    except s3_client.exceptions.NoSuchKey:
        return {"error": "File not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
