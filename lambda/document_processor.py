"""
Document Processing Worker Lambda Function

This Lambda function handles the actual document processing tasks.
It receives events from the orchestrator and processes individual documents.
"""

import json
import boto3
import os
import io
import hashlib
from datetime import datetime
from typing import Dict, Any, List
import logging
import PyPDF2
from bs4 import BeautifulSoup

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS services
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
textract = boto3.client('textract')
bedrock = boto3.client('bedrock-runtime')
eventbridge = boto3.client('events')

# Environment variables
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev').lower()
S3_BUCKET = os.environ.get('S3_BUCKET', 'emergency-docs-bucket-us-east-1')
DOCUMENT_JOBS_TABLE = f"agent2_ingestor_jobs_{ENVIRONMENT}"
EVENT_BUS_NAME = os.environ.get('EVENT_BUS_NAME', 'emergency-docs-events')

def lambda_handler(event, context):
    """
    Main Lambda handler for document processing tasks
    """
    try:
        logger.info(f"Processing document task: {json.dumps(event, default=str)}")
        
        # Extract task details from event
        detail = event.get('detail', {})
        task_type = detail.get('type', 'unknown')
        job_id = detail.get('job_id', '')
        
        if task_type == 'file':
            return process_file_task(detail, context)
        elif task_type == 'url':
            return process_url_task(detail, context)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
            
    except Exception as e:
        logger.error(f"Error processing document task: {str(e)}")
        
        # Send failure event
        send_processing_event(detail.get('job_id', ''), 'processing_failed', {
            'error': str(e),
            'task_type': detail.get('type', 'unknown')
        })
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'event_id': context.aws_request_id
            })
        }

def process_file_task(detail, context):
    """Process a file processing task"""
    try:
        job_id = detail.get('job_id')
        filename = detail.get('filename')
        
        logger.info(f"Processing file: {filename} for job {job_id}")
        
        # Get file from S3 (assuming it was uploaded there)
        file_key = f"uploads/{job_id}/{filename}"
        
        try:
            response = s3_client.get_object(Bucket=S3_BUCKET, Key=file_key)
            file_content = response['Body'].read()
        except s3_client.exceptions.NoSuchKey:
            raise Exception(f"File not found in S3: {file_key}")
        
        # Process the file based on type
        if filename.lower().endswith('.pdf'):
            result = process_pdf_content(file_content, filename, job_id)
        else:
            raise Exception(f"Unsupported file type: {filename}")
        
        # Upload results to S3
        upload_results = upload_processing_results(result, job_id, filename)
        
        # Send success event
        send_processing_event(job_id, 'document_processed', {
            'filename': filename,
            'word_count': result.get('metadata', {}).get('word_count', 0),
            'processing_method': result.get('metadata', {}).get('processing_method', 'unknown'),
            's3_locations': upload_results
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'File processed successfully',
                'filename': filename,
                'job_id': job_id,
                'results': upload_results
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing file task: {str(e)}")
        raise

def process_url_task(detail, context):
    """Process a URL processing task"""
    try:
        job_id = detail.get('job_id')
        url = detail.get('url')
        
        logger.info(f"Processing URL: {url} for job {job_id}")
        
        # Fetch URL content
        url_content = fetch_url_content(url)
        
        # Process the URL content
        result = process_url_content(url_content, url, job_id)
        
        # Upload results to S3
        upload_results = upload_processing_results(result, job_id, url)
        
        # Send success event
        send_processing_event(job_id, 'url_processed', {
            'url': url,
            'word_count': result.get('metadata', {}).get('word_count', 0),
            'processing_method': result.get('metadata', {}).get('processing_method', 'web_scraping'),
            's3_locations': upload_results
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'URL processed successfully',
                'url': url,
                'job_id': job_id,
                'results': upload_results
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing URL task: {str(e)}")
        raise

def process_pdf_content(file_content: bytes, filename: str, job_id: str) -> Dict[str, Any]:
    """Process PDF file content"""
    try:
        # Calculate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Extract text using PyPDF2
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text_content = ""
        page_count = len(pdf_reader.pages)
        processing_method = "PyPDF2"
        
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            if page_text.strip():
                text_content += f"\n\n--- Page {page_num + 1} ---\n\n"
                text_content += page_text
        
        # Check if OCR is needed
        word_count = len(text_content.split())
        if word_count < 50:
            logger.info(f"PDF {filename} has only {word_count} words, attempting OCR...")
            try:
                ocr_text = perform_textract_ocr(file_content)
                if len(ocr_text.split()) > word_count:
                    text_content = ocr_text
                    processing_method = "PyPDF2 + Textract OCR"
                    logger.info(f"OCR improved text extraction: {len(ocr_text.split())} words")
            except Exception as e:
                logger.warning(f"OCR failed: {str(e)}")
        
        if not text_content.strip():
            raise Exception("No text could be extracted from PDF")
        
        # Convert to markdown
        markdown_content = text_to_markdown(text_content, filename)
        
        # Generate embeddings
        vector_sidecar = generate_vector_sidecar(text_content, filename)
        
        return {
            "markdown": markdown_content,
            "sidecar": vector_sidecar,
            "metadata": {
                "source_type": "pdf",
                "filename": filename,
                "file_hash": file_hash,
                "page_count": page_count,
                "processed_at": datetime.utcnow().isoformat(),
                "word_count": len(text_content.split()),
                "character_count": len(text_content),
                "processing_method": processing_method,
                "job_id": job_id
            }
        }
        
    except Exception as e:
        raise Exception(f"Error processing PDF {filename}: {str(e)}")

def fetch_url_content(url: str) -> str:
    """Fetch content from URL"""
    try:
        import requests
        
        headers = {
            'User-Agent': 'Emergency Document Processor 1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.text
        
    except Exception as e:
        raise Exception(f"Error fetching URL {url}: {str(e)}")

def process_url_content(html_content: str, url: str, job_id: str) -> Dict[str, Any]:
    """Process URL content"""
    try:
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract text content
        text_content = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text_content = ' '.join(chunk for chunk in chunks if chunk)
        
        if not text_content.strip():
            raise Exception("No text content extracted from URL")
        
        # Convert to markdown
        markdown_content = text_to_markdown(text_content, url)
        
        # Generate embeddings
        vector_sidecar = generate_vector_sidecar(text_content, url)
        
        return {
            "markdown": markdown_content,
            "sidecar": vector_sidecar,
            "metadata": {
                "source_type": "url",
                "source_url": url,
                "processed_at": datetime.utcnow().isoformat(),
                "word_count": len(text_content.split()),
                "character_count": len(text_content),
                "processing_method": "web_scraping",
                "job_id": job_id
            }
        }
        
    except Exception as e:
        raise Exception(f"Error processing URL {url}: {str(e)}")

def perform_textract_ocr(file_content: bytes) -> str:
    """Perform OCR using AWS Textract"""
    try:
        if len(file_content) > 10 * 1024 * 1024:  # 10MB limit
            raise Exception("File too large for Textract OCR")
        
        response = textract.detect_document_text(
            Document={'Bytes': file_content}
        )
        
        text_content = ""
        current_page = 1
        
        for block in response['Blocks']:
            if block['BlockType'] == 'PAGE':
                if current_page > 1:
                    text_content += f"\n\n--- Page {current_page} ---\n\n"
                current_page += 1
            elif block['BlockType'] == 'LINE':
                confidence = block.get('Confidence', 0)
                if confidence > 80:
                    text_content += block['Text'] + "\n"
        
        return text_content.strip()
        
    except Exception as e:
        raise Exception(f"Textract OCR failed: {str(e)}")

def text_to_markdown(text: str, source_identifier: str) -> str:
    """Convert text to markdown format"""
    try:
        # Basic markdown conversion
        markdown_lines = [
            f"# {source_identifier}",
            "",
            f"*Processed on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*",
            "",
            "---",
            "",
            text
        ]
        
        return '\n'.join(markdown_lines)
        
    except Exception as e:
        return f"# {source_identifier}\n\nError converting to markdown: {str(e)}\n\n{text}"

def generate_vector_sidecar(text_content: str, source_identifier: str) -> Dict[str, Any]:
    """Generate vector embeddings sidecar"""
    try:
        # Chunk text
        chunks = chunk_text_intelligently(text_content, chunk_size=1024)
        
        if not chunks:
            raise Exception("No valid text chunks created for embedding")
        
        embeddings = []
        failed_chunks = 0
        
        for i, chunk in enumerate(chunks):
            try:
                embedding = get_titan_embedding(chunk)
                chunk_hash = hashlib.sha256(chunk.encode()).hexdigest()[:16]
                
                embeddings.append({
                    "chunk_id": f"{source_identifier}_{i:04d}_{chunk_hash}",
                    "chunk_index": i,
                    "text": chunk,
                    "embedding": embedding,
                    "metadata": {
                        "source": source_identifier,
                        "chunk_index": i,
                        "word_count": len(chunk.split()),
                        "character_count": len(chunk),
                        "chunk_hash": chunk_hash,
                        "embedding_timestamp": datetime.utcnow().isoformat()
                    }
                })
                
            except Exception as e:
                logger.error(f"Failed to generate embedding for chunk {i}: {str(e)}")
                failed_chunks += 1
                continue
        
        if not embeddings:
            raise Exception("Failed to generate any embeddings")
        
        return {
            "source": source_identifier,
            "created_at": datetime.utcnow().isoformat(),
            "embedding_model": "amazon.titan-embed-text-v1",
            "total_chunks": len(chunks),
            "successful_chunks": len(embeddings),
            "failed_chunks": failed_chunks,
            "chunk_size": 1024,
            "overlap_size": 100,
            "chunks": embeddings
        }
        
    except Exception as e:
        raise Exception(f"Error generating vector sidecar: {str(e)}")

def chunk_text_intelligently(text: str, chunk_size: int = 1024, overlap: int = 100) -> List[str]:
    """Chunk text intelligently preserving boundaries"""
    try:
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        current_size = 0
        
        for paragraph in paragraphs:
            paragraph_words = paragraph.split()
            paragraph_size = len(paragraph_words)
            
            if current_size + paragraph_size <= chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + paragraph
                current_size += paragraph_size
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    
                # Start new chunk with overlap
                overlap_words = current_chunk.split()[-overlap:] if overlap > 0 else []
                current_chunk = ' '.join(overlap_words) + ("\n\n" if overlap_words else "") + paragraph
                current_size = len(overlap_words) + paragraph_size
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
        
    except Exception as e:
        logger.error(f"Error chunking text: {str(e)}")
        return [text]  # Return original text as single chunk if chunking fails

def get_titan_embedding(text: str) -> List[float]:
    """Get embeddings from AWS Bedrock Titan"""
    try:
        # Ensure text is not too long
        if len(text.split()) > 2000:
            text = ' '.join(text.split()[:2000])
        
        response = bedrock.invoke_model(
            modelId="amazon.titan-embed-text-v1",
            body=json.dumps({
                "inputText": text
            }),
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        embedding = response_body.get('embedding')
        
        if not embedding:
            raise Exception("No embedding returned from Bedrock")
        
        return embedding
        
    except Exception as e:
        raise Exception(f"Failed to get Titan embedding: {str(e)}")

def upload_processing_results(result: Dict[str, Any], job_id: str, source_identifier: str) -> Dict[str, str]:
    """Upload processing results to S3"""
    try:
        # Generate S3 keys
        safe_identifier = source_identifier.replace('/', '_').replace(':', '_')
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        markdown_key = f"processed/{job_id}/{safe_identifier}_{timestamp}.md"
        sidecar_key = f"sidecars/{job_id}/{safe_identifier}_{timestamp}_sidecar.json"
        
        # Upload markdown
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=markdown_key,
            Body=result['markdown'].encode('utf-8'),
            ContentType='text/markdown',
            Metadata=result['metadata']
        )
        
        # Upload sidecar
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=sidecar_key,
            Body=json.dumps(result['sidecar'], indent=2).encode('utf-8'),
            ContentType='application/json'
        )
        
        # Update manifest
        update_manifest(result, markdown_key, sidecar_key, job_id)
        
        return {
            'markdown_s3_uri': f"s3://{S3_BUCKET}/{markdown_key}",
            'sidecar_s3_uri': f"s3://{S3_BUCKET}/{sidecar_key}",
            'markdown_key': markdown_key,
            'sidecar_key': sidecar_key
        }
        
    except Exception as e:
        raise Exception(f"Error uploading results: {str(e)}")

def update_manifest(result: Dict[str, Any], markdown_key: str, sidecar_key: str, job_id: str):
    """Update the manifest with new document entry"""
    try:
        manifest_key = 'manifest.json'
        
        # Get existing manifest
        try:
            response = s3_client.get_object(Bucket=S3_BUCKET, Key=manifest_key)
            manifest = json.loads(response['Body'].read().decode('utf-8'))
        except s3_client.exceptions.NoSuchKey:
            manifest = {
                "version": "1.0",
                "created_at": datetime.utcnow().isoformat(),
                "document_count": 0,
                "documents": []
            }
        
        # Add new document entry
        document_entry = {
            "id": str(len(manifest["documents"]) + 1),
            "job_id": job_id,
            "source_type": result['metadata'].get('source_type', 'unknown'),
            "source_url": result['metadata'].get('source_url', result['metadata'].get('filename', 'unknown')),
            "markdown_s3_key": markdown_key,
            "sidecar_s3_key": sidecar_key,
            "processed_at": result['metadata']['processed_at'],
            "word_count": result['metadata']['word_count'],
            "chunk_count": result['sidecar']['successful_chunks'],
            "processing_method": result['metadata']['processing_method']
        }
        
        manifest["documents"].append(document_entry)
        manifest["document_count"] = len(manifest["documents"])
        manifest["last_updated"] = datetime.utcnow().isoformat()
        
        # Upload updated manifest
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=manifest_key,
            Body=json.dumps(manifest, indent=2).encode('utf-8'),
            ContentType='application/json'
        )
        
        logger.info(f"Manifest updated with new document: {document_entry['id']}")
        
    except Exception as e:
        logger.error(f"Error updating manifest: {str(e)}")
        # Don't raise exception - manifest update failure shouldn't fail the entire process

def send_processing_event(job_id: str, event_type: str, detail: Dict[str, Any]):
    """Send processing event to EventBridge"""
    try:
        event_data = {
            'Source': 'emergency.docs',
            'DetailType': f'Document {event_type.replace("_", " ").title()}',
            'Detail': json.dumps({
                'job_id': job_id,
                'timestamp': datetime.utcnow().isoformat(),
                **detail
            }),
            'EventBusName': EVENT_BUS_NAME
        }
        
        eventbridge.put_events(Entries=[event_data])
        logger.info(f"Sent {event_type} event for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error sending processing event: {str(e)}")
        # Don't raise - event sending failure shouldn't fail processing