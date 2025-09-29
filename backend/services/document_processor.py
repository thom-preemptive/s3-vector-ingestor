import boto3
import PyPDF2
import io
import json
from typing import List, Dict, Any, Tuple
from datetime import datetime
import markdown
import requests
from bs4 import BeautifulSoup
import uuid
import hashlib
import os
from urllib.parse import urlparse
import asyncio
import aiofiles
import re

class DocumentProcessor:
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name='us-east-1')
        self.textract_client = boto3.client('textract', region_name='us-east-1')
        self.bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.bucket_name = os.getenv('S3_BUCKET', 'agent2-ingestor-bucket-us-east-1')
    
    async def process_job(self, job_id: str, files: List[bytes] = None, 
                         filenames: List[str] = None, urls: List[str] = None,
                         user_id: str = None, job_name: str = None) -> Dict[str, Any]:
        """Complete job processing pipeline"""
        try:
            results = {
                'job_id': job_id,
                'processed_documents': [],
                'failed_documents': [],
                'total_documents': 0,
                'successful_documents': 0,
                'failed_documents_count': 0
            }
            
            # Process PDF files
            if files and filenames:
                results['total_documents'] += len(files)
                for i, (file_content, filename) in enumerate(zip(files, filenames)):
                    try:
                        doc_result = await self.process_pdf(file_content, filename)
                        doc_result['job_id'] = job_id
                        doc_result['user_id'] = user_id
                        doc_result['job_name'] = job_name
                        
                        # Upload to S3 and update manifest
                        s3_result = await self._upload_document_to_s3(doc_result, job_id)
                        results['processed_documents'].append(s3_result)
                        results['successful_documents'] += 1
                        
                    except Exception as e:
                        error_doc = {
                            'filename': filename,
                            'error': str(e),
                            'type': 'pdf'
                        }
                        results['failed_documents'].append(error_doc)
                        results['failed_documents_count'] += 1
            
            # Process URLs
            if urls:
                results['total_documents'] += len(urls)
                for url in urls:
                    try:
                        doc_result = await self.process_url(url)
                        doc_result['job_id'] = job_id
                        doc_result['user_id'] = user_id
                        doc_result['job_name'] = job_name
                        
                        # Upload to S3 and update manifest
                        s3_result = await self._upload_document_to_s3(doc_result, job_id)
                        results['processed_documents'].append(s3_result)
                        results['successful_documents'] += 1
                        
                    except Exception as e:
                        error_doc = {
                            'url': url,
                            'error': str(e),
                            'type': 'url'
                        }
                        results['failed_documents'].append(error_doc)
                        results['failed_documents_count'] += 1
            
            return results
            
        except Exception as e:
            raise Exception(f"Job processing failed: {str(e)}")
    
    async def _upload_document_to_s3(self, doc_result: Dict[str, Any], job_id: str) -> Dict[str, Any]:
        """Upload processed document and sidecar to S3, update manifest"""
        try:
            # Generate unique identifiers
            doc_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            
            # Create S3 keys
            if doc_result['metadata']['source_type'] == 'pdf':
                base_name = doc_result['metadata']['filename'].replace('.pdf', '')
            else:
                base_name = urlparse(doc_result['metadata'].get('source_url', 'unknown')).netloc
            
            markdown_key = f"documents/{job_id}/{timestamp}_{base_name}.md"
            sidecar_key = f"sidecars/{job_id}/{timestamp}_{base_name}.sidecar.json"
            
            # Upload markdown file
            markdown_s3_url = await self._upload_to_s3(
                content=doc_result['markdown'],
                key=markdown_key,
                content_type='text/markdown'
            )
            
            # Upload sidecar file
            sidecar_s3_url = await self._upload_to_s3(
                content=json.dumps(doc_result['sidecar'], indent=2),
                key=sidecar_key,
                content_type='application/json'
            )
            
            # Create manifest entry
            manifest_entry = {
                'document_id': doc_id,
                'job_id': job_id,
                'user_id': doc_result.get('user_id'),
                'job_name': doc_result.get('job_name'),
                'source_type': doc_result['metadata']['source_type'],
                'filename': doc_result['metadata'].get('filename'),
                'source_url': doc_result['metadata'].get('source_url'),
                'processed_at': doc_result['metadata']['processed_at'],
                'word_count': doc_result['metadata']['word_count'],
                'chunk_count': doc_result['sidecar']['total_chunks'],
                'markdown_s3_key': markdown_key,
                'sidecar_s3_key': sidecar_key,
                'markdown_s3_url': markdown_s3_url,
                'sidecar_s3_url': sidecar_s3_url,
                'file_size': len(doc_result['markdown'].encode('utf-8')),
                'embedding_model': doc_result['sidecar']['embedding_model']
            }
            
            # Update manifest
            await self._update_manifest(manifest_entry)
            
            return {
                'document_id': doc_id,
                'markdown_s3_url': markdown_s3_url,
                'sidecar_s3_url': sidecar_s3_url,
                'manifest_entry': manifest_entry
            }
            
        except Exception as e:
            raise Exception(f"Failed to upload document to S3: {str(e)}")
    
    async def _upload_to_s3(self, content: str, key: str, content_type: str) -> str:
        """Upload content to S3 and return the S3 URL"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content.encode('utf-8'),
                ContentType=content_type,
                Metadata={
                    'uploaded_at': datetime.utcnow().isoformat(),
                    'processor_version': '1.0'
                }
            )
            return f"s3://{self.bucket_name}/{key}"
        except Exception as e:
            raise Exception(f"S3 upload failed for {key}: {str(e)}")
    
    async def _update_manifest(self, manifest_entry: Dict[str, Any]) -> None:
        """Update the manifest file with new document entry"""
        try:
            # Get current manifest
            try:
                response = self.s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key='manifest.json'
                )
                manifest = json.loads(response['Body'].read().decode('utf-8'))
            except self.s3_client.exceptions.NoSuchKey:
                manifest = {
                    "version": "1.0",
                    "created_at": datetime.utcnow().isoformat(),
                    "documents": []
                }
            
            # Add new document
            manifest["documents"].append(manifest_entry)
            manifest["updated_at"] = datetime.utcnow().isoformat()
            manifest["document_count"] = len(manifest["documents"])
            
            # Upload updated manifest
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key='manifest.json',
                Body=json.dumps(manifest, indent=2).encode('utf-8'),
                ContentType='application/json'
            )
            
        except Exception as e:
            raise Exception(f"Failed to update manifest: {str(e)}")
    
    async def process_pdf(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process PDF file and return markdown + vector sidecar"""
        try:
            # Calculate file hash for deduplication
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Extract text using PyPDF2 first
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text_content = ""
            page_count = len(pdf_reader.pages)
            processing_method = "PyPDF2"
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text.strip():
                    text_content += f"\n\n--- Page {page_num + 1} ---\n\n"
                    text_content += page_text
            
            # Check if text extraction was successful
            word_count = len(text_content.split())
            ocr_data = None
            
            if word_count < 50:  # If too few words, likely needs OCR
                print(f"PDF {filename} has only {word_count} words, attempting advanced OCR...")
                
                try:
                    # Try advanced Textract with tables and forms
                    ocr_data = await self._ocr_with_textract_advanced(file_content)
                    
                    if ocr_data and len(ocr_data['text'].split()) > word_count:
                        text_content = ocr_data['text']
                        processing_method = "PyPDF2 + Textract Advanced OCR"
                        print(f"Advanced OCR improved text extraction: {len(ocr_data['text'].split())} words")
                        print(f"OCR confidence: {ocr_data.get('average_confidence', 0):.2f}%")
                        
                        # Add structured data to text if available
                        if ocr_data.get('tables'):
                            text_content += "\n\n## Extracted Tables\n\n"
                            for i, table in enumerate(ocr_data['tables']):
                                text_content += f"### Table {i + 1}\n\n"
                                text_content += self._format_table_as_markdown(table)
                                text_content += "\n\n"
                        
                        if ocr_data.get('forms'):
                            text_content += "\n\n## Extracted Form Data\n\n"
                            for form_item in ocr_data['forms']:
                                if form_item['key'] and form_item['value']:
                                    text_content += f"**{form_item['key']}:** {form_item['value']}\n\n"
                    
                except Exception as e:
                    print(f"Advanced OCR failed, trying basic OCR: {str(e)}")
                    # Fallback to basic OCR
                    try:
                        basic_ocr_text = await self._ocr_with_textract(file_content)
                        if len(basic_ocr_text.split()) > word_count:
                            text_content = basic_ocr_text
                            processing_method = "PyPDF2 + Textract Basic OCR"
                            print(f"Basic OCR improved text extraction: {len(basic_ocr_text.split())} words")
                    except Exception as basic_e:
                        print(f"Basic OCR also failed: {str(basic_e)}")
            
            if not text_content.strip():
                raise Exception("No text could be extracted from PDF")
            
            # Convert to markdown
            markdown_content = self._text_to_markdown(text_content, filename)
            
            # Generate embeddings for vector sidecar
            vector_sidecar = await self._generate_vector_sidecar(text_content, filename)
            
            # Prepare metadata
            metadata = {
                "source_type": "pdf",
                "filename": filename,
                "file_hash": file_hash,
                "page_count": page_count,
                "processed_at": datetime.utcnow().isoformat(),
                "word_count": len(text_content.split()),
                "character_count": len(text_content),
                "processing_method": processing_method
            }
            
            # Add OCR-specific metadata if available
            if ocr_data:
                metadata.update({
                    "ocr_confidence": ocr_data.get('average_confidence', 0),
                    "tables_extracted": len(ocr_data.get('tables', [])),
                    "forms_extracted": len(ocr_data.get('forms', [])),
                    "textract_features": ["TABLES", "FORMS"] if ocr_data.get('tables') or ocr_data.get('forms') else []
                })
            
            return {
                "markdown": markdown_content,
                "sidecar": vector_sidecar,
                "metadata": metadata
            }
            
        except Exception as e:
            raise Exception(f"Error processing PDF {filename}: {str(e)}")
    
    def _format_table_as_markdown(self, table_data: Dict[str, Any]) -> str:
        """Convert extracted table data to markdown format"""
        try:
            if not table_data.get('rows'):
                return ""
            
            rows = table_data['rows']
            if not rows:
                return ""
            
            markdown_lines = []
            
            # Add header row
            if len(rows) > 0:
                header_row = "| " + " | ".join(str(cell).strip() for cell in rows[0]) + " |"
                markdown_lines.append(header_row)
                
                # Add separator
                separator = "| " + " | ".join("---" for _ in rows[0]) + " |"
                markdown_lines.append(separator)
                
                # Add data rows
                for row in rows[1:]:
                    data_row = "| " + " | ".join(str(cell).strip() for cell in row) + " |"
                    markdown_lines.append(data_row)
            
            return "\n".join(markdown_lines)
            
        except Exception as e:
            return f"Table extraction error: {str(e)}"
    
    async def process_url(self, url: str) -> Dict[str, Any]:
        """Process URL and return markdown + vector sidecar"""
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise Exception(f"Invalid URL format: {url}")
            
            # Set user agent to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; EmergencyDocProcessor/1.0)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            # Scrape URL content with timeout
            response = requests.get(url, timeout=30, headers=headers)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type and 'application/xml' not in content_type:
                raise Exception(f"Unsupported content type: {content_type}")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract metadata
            title = soup.find('title')
            title_text = title.get_text().strip() if title else parsed_url.netloc
            
            # Extract meaningful content
            text_content = self._extract_text_from_html(soup)
            
            if not text_content.strip():
                raise Exception("No meaningful text content found on the page")
            
            # Create URL hash for deduplication
            url_hash = hashlib.sha256(url.encode()).hexdigest()
            
            # Convert to markdown
            markdown_content = self._text_to_markdown(text_content, url, title_text)
            
            # Generate embeddings for vector sidecar
            vector_sidecar = await self._generate_vector_sidecar(text_content, url)
            
            return {
                "markdown": markdown_content,
                "sidecar": vector_sidecar,
                "metadata": {
                    "source_type": "url",
                    "source_url": url,
                    "title": title_text,
                    "domain": parsed_url.netloc,
                    "url_hash": url_hash,
                    "content_type": content_type,
                    "processed_at": datetime.utcnow().isoformat(),
                    "word_count": len(text_content.split()),
                    "character_count": len(text_content),
                    "status_code": response.status_code
                }
            }
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch URL {url}: {str(e)}")
        except Exception as e:
            raise Exception(f"Error processing URL {url}: {str(e)}")
    
    async def _ocr_with_textract(self, file_content: bytes) -> str:
        """Use AWS Textract for OCR when PDF text extraction fails"""
        try:
            response = self.textract_client.detect_document_text(
                Document={'Bytes': file_content}
            )
            
            text_content = ""
            for block in response['Blocks']:
                if block['BlockType'] == 'LINE':
                    text_content += block['Text'] + "\n"
            
            return text_content
        except Exception as e:
            raise Exception(f"Textract OCR failed: {str(e)}")
    
    def _extract_text_from_html(self, soup: BeautifulSoup) -> str:
        """Extract meaningful text content from HTML"""
        try:
            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "header", "footer", 
                               "aside", "form", "button", "input", "select", 
                               "textarea", "noscript", "iframe"]):
                element.decompose()
            
            # Try to find main content areas first
            main_content = None
            for selector in ['main', 'article', '.content', '.main-content', 
                           '#content', '#main', '.post-content', '.entry-content']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            # If no main content found, use body
            if not main_content:
                main_content = soup.find('body') or soup
            
            # Extract text with structure preservation
            text_parts = []
            
            # Get headings and paragraphs with structure
            for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'li']):
                text = element.get_text(strip=True)
                if text and len(text) > 10:  # Only include substantial text
                    if element.name.startswith('h'):
                        # Add heading markers
                        level = int(element.name[1])
                        text_parts.append('\n' + '#' * level + ' ' + text + '\n')
                    elif element.name == 'li':
                        text_parts.append('- ' + text)
                    else:
                        text_parts.append(text)
            
            # If structured extraction didn't work well, fall back to simple text
            if len(' '.join(text_parts).split()) < 50:
                text = main_content.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)
                return text
            
            return '\n\n'.join(text_parts)
            
        except Exception as e:
            # Fallback to simple text extraction
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            return '\n'.join(chunk for chunk in chunks if chunk)
    
    def _text_to_markdown(self, text_content: str, source_identifier: str, title: str = None) -> str:
        """Convert text content to markdown format"""
        try:
            # Create markdown header
            markdown_lines = []
            
            # Add title
            if title and title != source_identifier:
                markdown_lines.append(f"# {title}")
                markdown_lines.append("")
            
            # Add metadata section
            markdown_lines.append("## Document Information")
            markdown_lines.append("")
            markdown_lines.append(f"**Source:** {source_identifier}")
            markdown_lines.append(f"**Processed:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
            markdown_lines.append(f"**Word Count:** {len(text_content.split())} words")
            markdown_lines.append("")
            markdown_lines.append("---")
            markdown_lines.append("")
            
            # Add main content
            markdown_lines.append("## Content")
            markdown_lines.append("")
            
            # Clean and format the text content
            cleaned_content = self._clean_text_content(text_content)
            markdown_lines.append(cleaned_content)
            
            return '\n'.join(markdown_lines)
            
        except Exception as e:
            # Fallback to simple format
            return f"# Document: {source_identifier}\n\n*Processed on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*\n\n---\n\n{text_content}"
    
    def _clean_text_content(self, text: str) -> str:
        """Clean and normalize text content"""
        try:
            # Remove excessive whitespace
            lines = text.split('\n')
            cleaned_lines = []
            
            for line in lines:
                line = line.strip()
                if line:
                    # Remove excessive spaces
                    line = ' '.join(line.split())
                    cleaned_lines.append(line)
                elif cleaned_lines and cleaned_lines[-1]:  # Add blank line only if last line wasn't blank
                    cleaned_lines.append('')
            
            # Remove trailing blank lines
            while cleaned_lines and not cleaned_lines[-1]:
                cleaned_lines.pop()
            
            return '\n'.join(cleaned_lines)
            
        except Exception:
            return text
    
    async def _generate_vector_sidecar(self, text_content: str, source_identifier: str) -> Dict[str, Any]:
        """Generate optimized vector embeddings sidecar file for AWS Bedrock"""
        try:
            # Analyze text characteristics for optimal chunking
            total_words = len(text_content.split())
            estimated_tokens = total_words * 1.3  # Rough estimation
            
            # Adjust chunk size based on content characteristics
            if total_words < 500:
                chunk_size = 256  # Smaller chunks for short documents
            elif total_words < 2000:
                chunk_size = 512  # Medium chunks for medium documents
            else:
                chunk_size = 1024  # Standard chunks for large documents
                
            overlap = min(100, chunk_size // 10)  # Dynamic overlap based on chunk size
            
            # Chunk text into optimal segments
            chunks = self._chunk_text_intelligently(text_content, chunk_size=chunk_size, overlap=overlap)
            
            if not chunks:
                raise Exception("No valid text chunks created for embedding")
            
            print(f"Generating embeddings for {len(chunks)} chunks from {source_identifier}")
            
            embeddings = []
            failed_chunks = 0
            total_embedding_time = 0
            
            for i, chunk in enumerate(chunks):
                try:
                    start_time = datetime.utcnow()
                    
                    # Generate embeddings using Bedrock Titan
                    embedding = await self._get_titan_embedding(chunk)
                    
                    end_time = datetime.utcnow()
                    embedding_time = (end_time - start_time).total_seconds()
                    total_embedding_time += embedding_time
                    
                    # Calculate chunk metadata
                    chunk_hash = hashlib.sha256(chunk.encode()).hexdigest()[:16]
                    chunk_words = len(chunk.split())
                    
                    embeddings.append({
                        "chunk_id": f"{source_identifier}_{i:04d}_{chunk_hash}",
                        "chunk_index": i,
                        "text": chunk,
                        "embedding": embedding,
                        "metadata": {
                            "source": source_identifier,
                            "chunk_index": i,
                            "word_count": chunk_words,
                            "character_count": len(chunk),
                            "estimated_tokens": int(chunk_words * 1.3),
                            "chunk_hash": chunk_hash,
                            "embedding_timestamp": end_time.isoformat(),
                            "embedding_generation_time_seconds": round(embedding_time, 3),
                            "embedding_dimensions": len(embedding),
                            "embedding_model_version": "amazon.titan-embed-text-v1"
                        }
                    })
                    
                    if (i + 1) % 10 == 0:
                        print(f"Generated embeddings for {i + 1}/{len(chunks)} chunks")
                    
                except Exception as e:
                    print(f"Failed to generate embedding for chunk {i}: {str(e)}")
                    failed_chunks += 1
                    continue
            
            if not embeddings:
                raise Exception("Failed to generate any embeddings")
            
            # Calculate statistics
            avg_chunk_size = sum(len(emb['text'].split()) for emb in embeddings) / len(embeddings)
            total_embedded_tokens = sum(emb['metadata']['estimated_tokens'] for emb in embeddings)
            
            sidecar_result = {
                "source": source_identifier,
                "created_at": datetime.utcnow().isoformat(),
                "embedding_model": "amazon.titan-embed-text-v1",
                "embedding_dimensions": 1536,
                "total_chunks": len(chunks),
                "successful_chunks": len(embeddings),
                "failed_chunks": failed_chunks,
                "chunking_strategy": {
                    "chunk_size": chunk_size,
                    "overlap_size": overlap,
                    "dynamic_sizing": True,
                    "preserve_boundaries": True
                },
                "processing_statistics": {
                    "original_word_count": total_words,
                    "original_character_count": len(text_content),
                    "estimated_total_tokens": int(estimated_tokens),
                    "embedded_tokens": total_embedded_tokens,
                    "average_chunk_size_words": round(avg_chunk_size, 1),
                    "total_embedding_time_seconds": round(total_embedding_time, 2),
                    "average_embedding_time_per_chunk": round(total_embedding_time / len(embeddings), 3) if embeddings else 0
                },
                "quality_metrics": {
                    "success_rate": round((len(embeddings) / len(chunks)) * 100, 2),
                    "chunk_utilization": round((sum(len(emb['text'].split()) for emb in embeddings) / total_words) * 100, 2)
                },
                "chunks": embeddings
            }
            
            print(f"Vector sidecar generation complete: {len(embeddings)} successful embeddings, {failed_chunks} failed")
            return sidecar_result
            
        except Exception as e:
            raise Exception(f"Error generating vector sidecar: {str(e)}")
    
    def _chunk_text_intelligently(self, text: str, chunk_size: int = 1024, overlap: int = 100) -> List[str]:
        """Chunk text intelligently preserving sentence and paragraph boundaries"""
        try:
            # First, split by paragraphs
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            
            chunks = []
            current_chunk = ""
            current_size = 0
            
            for paragraph in paragraphs:
                paragraph_words = paragraph.split()
                paragraph_size = len(paragraph_words)
                
                # If paragraph alone exceeds chunk size, split it by sentences
                if paragraph_size > chunk_size:
                    sentences = self._split_into_sentences(paragraph)
                    for sentence in sentences:
                        sentence_words = sentence.split()
                        sentence_size = len(sentence_words)
                        
                        # If current chunk + sentence exceeds size, save current chunk
                        if current_size + sentence_size > chunk_size and current_chunk:
                            chunks.append(current_chunk.strip())
                            # Start new chunk with overlap from end of previous
                            overlap_words = current_chunk.split()[-overlap:] if overlap > 0 else []
                            current_chunk = ' '.join(overlap_words + sentence_words)
                            current_size = len(overlap_words) + sentence_size
                        else:
                            current_chunk += (" " if current_chunk else "") + sentence
                            current_size += sentence_size
                
                # If paragraph fits in current chunk
                elif current_size + paragraph_size <= chunk_size:
                    current_chunk += ("\n\n" if current_chunk else "") + paragraph
                    current_size += paragraph_size
                
                # Paragraph doesn't fit, save current chunk and start new one
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                    current_size = paragraph_size
            
            # Add remaining content
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            # Filter out very small chunks
            chunks = [chunk for chunk in chunks if len(chunk.split()) >= 10]
            
            return chunks
            
        except Exception as e:
            # Fallback to simple word-based chunking
            return self._chunk_text(text, chunk_size)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        try:
            import re
            # Simple sentence splitting regex
            sentences = re.split(r'(?<=[.!?])\s+', text)
            return [s.strip() for s in sentences if s.strip()]
        except:
            # Fallback to period splitting
            sentences = text.split('. ')
            return [s.strip() + ('.' if not s.endswith('.') else '') for s in sentences if s.strip()]
    
    def _chunk_text(self, text: str, chunk_size: int = 1024) -> List[str]:
        """Chunk text into segments suitable for embeddings"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    async def _get_titan_embedding(self, text: str, max_retries: int = 3) -> List[float]:
        """Get embeddings from AWS Bedrock Titan model with retry logic and optimization"""
        for attempt in range(max_retries):
            try:
                # Clean and prepare text for embedding
                cleaned_text = self._prepare_text_for_embedding(text)
                
                # Ensure text is not too long for Titan (max ~8000 tokens)
                if len(cleaned_text.split()) > 2000:  # Conservative limit
                    cleaned_text = ' '.join(cleaned_text.split()[:2000])
                
                if not cleaned_text.strip():
                    raise Exception("Text is empty after cleaning")
                
                response = self.bedrock_client.invoke_model(
                    modelId="amazon.titan-embed-text-v1",
                    body=json.dumps({
                        "inputText": cleaned_text
                    }),
                    contentType="application/json",
                    accept="application/json"
                )
                
                response_body = json.loads(response['body'].read())
                embedding = response_body.get('embedding')
                
                if not embedding:
                    raise Exception("No embedding returned from Bedrock")
                
                # Validate embedding dimensions (Titan v1 returns 1536 dimensions)
                if len(embedding) != 1536:
                    raise Exception(f"Unexpected embedding dimensions: {len(embedding)}, expected 1536")
                
                return embedding
                
            except Exception as e:
                print(f"Embedding attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to get Titan embedding after {max_retries} attempts: {str(e)}")
                
                # Wait before retry (exponential backoff)
                await asyncio.sleep(2 ** attempt)
                continue
    
    def _prepare_text_for_embedding(self, text: str) -> str:
        """Clean and prepare text for optimal embedding generation"""
        try:
            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Remove very short words (less than 2 characters) that might be noise
            words = text.split()
            meaningful_words = [word for word in words if len(word.strip()) >= 2 or word.strip().isdigit()]
            
            # Rejoin and strip
            cleaned_text = ' '.join(meaningful_words).strip()
            
            # Ensure minimum text length for meaningful embedding
            if len(cleaned_text.split()) < 3:
                return text  # Return original if cleaning removes too much
                
            return cleaned_text
            
        except Exception:
            return text  # Return original text if cleaning fails
    
    async def _ocr_with_textract(self, file_content: bytes) -> str:
        """Use AWS Textract for OCR when PDF text extraction fails"""
        try:
            # Check file size (Textract has limits)
            if len(file_content) > 10 * 1024 * 1024:  # 10MB limit
                raise Exception("File too large for Textract OCR")
            
            # Use synchronous detection for smaller files
            response = self.textract_client.detect_document_text(
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
                    if confidence > 80:  # Only include high-confidence text
                        text_content += block['Text'] + "\n"
            
            return text_content.strip()
            
        except Exception as e:
            raise Exception(f"Textract OCR failed: {str(e)}")
    
    async def _ocr_with_textract_advanced(self, file_content: bytes) -> Dict[str, Any]:
        """Advanced Textract processing with tables and forms analysis"""
        try:
            # Check file size
            if len(file_content) > 10 * 1024 * 1024:
                raise Exception("File too large for Textract advanced analysis")
            
            # Analyze document with tables and forms
            response = self.textract_client.analyze_document(
                Document={'Bytes': file_content},
                FeatureTypes=['TABLES', 'FORMS']
            )
            
            # Extract different types of content
            result = {
                'text': '',
                'tables': [],
                'forms': [],
                'confidence_scores': []
            }
            
            # Process blocks
            blocks = response['Blocks']
            
            # Extract text content
            text_blocks = [block for block in blocks if block['BlockType'] == 'LINE']
            for block in text_blocks:
                confidence = block.get('Confidence', 0)
                result['confidence_scores'].append(confidence)
                if confidence > 75:  # Lower threshold for advanced OCR
                    result['text'] += block['Text'] + "\n"
            
            # Extract tables
            table_blocks = [block for block in blocks if block['BlockType'] == 'TABLE']
            for table_block in table_blocks:
                table_data = self._extract_table_data(blocks, table_block)
                if table_data:
                    result['tables'].append(table_data)
            
            # Extract forms/key-value pairs
            key_blocks = [block for block in blocks if block['BlockType'] == 'KEY_VALUE_SET' and block.get('EntityTypes') == ['KEY']]
            for key_block in key_blocks:
                form_data = self._extract_form_data(blocks, key_block)
                if form_data:
                    result['forms'].append(form_data)
            
            # Calculate average confidence
            if result['confidence_scores']:
                result['average_confidence'] = sum(result['confidence_scores']) / len(result['confidence_scores'])
            else:
                result['average_confidence'] = 0
            
            return result
            
        except Exception as e:
            raise Exception(f"Advanced Textract analysis failed: {str(e)}")
    
    def _extract_table_data(self, blocks: List[Dict], table_block: Dict) -> Dict[str, Any]:
        """Extract structured table data from Textract blocks"""
        try:
            # Get table cells
            cell_blocks = []
            if 'Relationships' in table_block:
                for relationship in table_block['Relationships']:
                    if relationship['Type'] == 'CHILD':
                        for cell_id in relationship['Ids']:
                            cell_block = next((b for b in blocks if b['Id'] == cell_id), None)
                            if cell_block and cell_block['BlockType'] == 'CELL':
                                cell_blocks.append(cell_block)
            
            # Organize cells into rows and columns
            table_data = {
                'rows': [],
                'confidence': table_block.get('Confidence', 0)
            }
            
            # Sort cells by row and column
            cell_blocks.sort(key=lambda x: (x.get('RowIndex', 0), x.get('ColumnIndex', 0)))
            
            current_row = []
            last_row_index = None
            
            for cell in cell_blocks:
                row_index = cell.get('RowIndex')
                
                # If we're on a new row, save the previous row
                if last_row_index is not None and row_index != last_row_index:
                    if current_row:
                        table_data['rows'].append(current_row)
                    current_row = []
                
                # Extract cell text
                cell_text = self._get_cell_text(blocks, cell)
                current_row.append(cell_text)
                last_row_index = row_index
            
            # Add the last row
            if current_row:
                table_data['rows'].append(current_row)
            
            return table_data if table_data['rows'] else None
            
        except Exception as e:
            print(f"Error extracting table data: {str(e)}")
            return None
    
    def _extract_form_data(self, blocks: List[Dict], key_block: Dict) -> Dict[str, Any]:
        """Extract form key-value pairs from Textract blocks"""
        try:
            # Get key text
            key_text = self._get_block_text(blocks, key_block)
            
            # Find associated value
            value_text = ""
            if 'Relationships' in key_block:
                for relationship in key_block['Relationships']:
                    if relationship['Type'] == 'VALUE':
                        for value_id in relationship['Ids']:
                            value_block = next((b for b in blocks if b['Id'] == value_id), None)
                            if value_block:
                                value_text = self._get_block_text(blocks, value_block)
                                break
            
            return {
                'key': key_text.strip(),
                'value': value_text.strip(),
                'confidence': key_block.get('Confidence', 0)
            }
            
        except Exception as e:
            print(f"Error extracting form data: {str(e)}")
            return None
    
    def _get_cell_text(self, blocks: List[Dict], cell_block: Dict) -> str:
        """Get text content from a table cell"""
        try:
            return self._get_block_text(blocks, cell_block)
        except:
            return ""
    
    def _get_block_text(self, blocks: List[Dict], block: Dict) -> str:
        """Get text content from a block and its children"""
        try:
            text_parts = []
            
            if 'Relationships' in block:
                for relationship in block['Relationships']:
                    if relationship['Type'] == 'CHILD':
                        for child_id in relationship['Ids']:
                            child_block = next((b for b in blocks if b['Id'] == child_id), None)
                            if child_block and child_block['BlockType'] == 'WORD':
                                text_parts.append(child_block.get('Text', ''))
            
            return ' '.join(text_parts)
            
        except:
            return ""