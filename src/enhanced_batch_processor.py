"""
Enhanced Batch Processor for Gemini AI
Provides advanced batch processing with retry logic, error handling, and validation
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import traceback

try:
    from .gemini_client import GeminiClient
    from .system_instructions import SystemInstructions
    from .reference_validator import ReferenceValidator
    from .logger_config import LoggerConfig
    from .json_combiner import JSONCombiner
except ImportError:
    from gemini_client import GeminiClient
    from system_instructions import SystemInstructions
    from reference_validator import ReferenceValidator
    from logger_config import LoggerConfig
    from json_combiner import JSONCombiner

logger = LoggerConfig.get_logger(__name__)

@dataclass
class BatchResult:
    """Result of processing a batch"""
    batch_index: int
    status: 'BatchStatus'
    items_processed: int
    items_found: int
    items_not_found: int
    results: List[Dict[str, Any]]
    errors: List[str]
    processing_time: float
    retry_count: int
    confidence_score: float

class BatchStatus(Enum):
    """Status of batch processing"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class EnhancedBatchProcessor:
    """Enhanced batch processor with retry logic and error handling"""
    
    def __init__(self, gemini_client, config):  # Accept parameters instead of creating new instances
        self.gemini_client = gemini_client
        self.config = config
        self.system_instructions = SystemInstructions()
        self.reference_validator = ReferenceValidator()
        self.json_combiner = JSONCombiner()
        self.max_concurrent_batches = config.MAX_CONCURRENT_BATCHES if hasattr(config, 'MAX_CONCURRENT_BATCHES') else 3  # Use config value
        
        # Retry configuration
        self.max_retries = config.MAX_RETRIES if hasattr(config, 'MAX_RETRIES') else 3
        self.batch_size = config.BATCH_SIZE if hasattr(config, 'BATCH_SIZE') else 50  # Use config batch size
        self.retry_delay = config.BATCH_RETRY_DELAY if hasattr(config, 'BATCH_RETRY_DELAY') else 5.0  # Use config
        self.backoff_factor = config.BATCH_BACKOFF_FACTOR if hasattr(config, 'BATCH_BACKOFF_FACTOR') else 3.0  # Use config
        
        logger.info(f"EnhancedBatchProcessor initialized with max_retries={self.max_retries}, batch_size={self.batch_size}, retry_delay={self.retry_delay}, backoff_factor={self.backoff_factor}, max_concurrent_batches={self.max_concurrent_batches}")
    
    async def process_batch_with_retry(
        self, 
        batch: List[Dict], 
        batch_index: int, 
        cache_id: str, 
        document_context: str
    ) -> BatchResult:
        """Process a batch with retry logic and error handling"""
        
        logger.info(f"=== PROCESS_BATCH_WITH_RETRY: BATCH {batch_index} ===")
        start_time = time.time()
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                logger.info(f"Processing batch {batch_index} (attempt {retry_count + 1}/{self.max_retries + 1})")
                logger.info(f"Batch {batch_index} has {len(batch)} items")
                
                # Process the batch
                logger.info(f"Calling _process_single_batch for batch {batch_index}...")
                result = await self._process_single_batch(batch, batch_index, cache_id, document_context)
                logger.info(f"_process_single_batch completed for batch {batch_index}, got {len(result)} results")
                
                # Validate the result
                logger.info(f"Validating batch {batch_index} result...")
                if self._validate_batch_result(result, batch):
                    processing_time = time.time() - start_time
                    
                    found_count = sum(1 for item in result if item.get("found", False))
                    not_found_count = sum(1 for item in result if not item.get("found", False))
                    
                    batch_result = BatchResult(
                        batch_index=batch_index,
                        status=BatchStatus.COMPLETED,
                        items_processed=len(batch),
                        items_found=found_count,
                        items_not_found=not_found_count,
                        results=result,
                        errors=[],
                        processing_time=processing_time,
                        retry_count=retry_count,
                        confidence_score=self._calculate_confidence_score(result)
                    )
                    
                    logger.info(f"Batch {batch_index} completed successfully in {processing_time:.2f}s")
                    logger.info(f"Batch {batch_index} found {found_count} items, not found {not_found_count} items")
                    return batch_result
                else:
                    logger.error(f"Batch {batch_index} validation failed")
                    raise ValueError("Batch result validation failed")
                    
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                logger.error(f"Batch {batch_index} attempt {retry_count} failed: {e}")
                
                if retry_count <= self.max_retries:
                    delay = self.retry_delay * (self.backoff_factor ** (retry_count - 1))
                    logger.warning(f"Batch {batch_index} failed (attempt {retry_count}): {e}. Retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Batch {batch_index} failed after {self.max_retries + 1} attempts: {e}")
        
        # All retries exhausted
        processing_time = time.time() - start_time
        logger.error(f"Batch {batch_index} all retries exhausted after {processing_time:.2f}s")
        return BatchResult(
            batch_index=batch_index,
            status=BatchStatus.FAILED,
            items_processed=0,
            items_found=0,
            items_not_found=0,
            results=[],
            errors=[f"Failed after {self.max_retries + 1} attempts: {last_error}"],
            processing_time=processing_time,
            retry_count=retry_count,
            confidence_score=0.0
        )
    
    async def _process_single_batch(
        self, 
        batch: List[Dict], 
        batch_index: int, 
        cache_id: str, 
        document_context: str
    ) -> List[Dict[str, Any]]:
        """Process a single batch with enhanced error handling"""
        
        logger.info(f"=== _PROCESS_SINGLE_BATCH: BATCH {batch_index} ===")
        logger.info(f"Batch {batch_index} has {len(batch)} items")
        
        try:
            # Get system instructions
            logger.info(f"Getting system instructions for batch {batch_index}...")
            system_instructions = self.system_instructions.get_checklist_matching_instructions()
            logger.info(f"System instructions length: {len(system_instructions)} characters")
            
            # Create enhanced prompt with system instructions
            logger.info(f"Creating enhanced prompt for batch {batch_index}...")
            prompt = self._create_enhanced_prompt(batch, document_context, system_instructions)
            logger.info(f"Enhanced prompt length: {len(prompt)} characters")
            
            # Process with Gemini
            logger.info(f"Calling Gemini client for batch {batch_index}...")
            logger.info(f"Cache ID: {cache_id}")
            result = self.gemini_client.match_checklist_batch_with_system_instructions(
                batch, cache_id, document_context, system_instructions
            )
            logger.info(f"Gemini client returned {len(result)} results for batch {batch_index}")
            
            # Validate and clean the result
            logger.info(f"Validating and cleaning results for batch {batch_index}...")
            validated_result = self._validate_and_clean_result(result, batch)
            logger.info(f"Validated result has {len(validated_result)} items for batch {batch_index}")
            
            return validated_result
            
        except Exception as e:
            logger.error(f"Error processing batch {batch_index}: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _create_enhanced_prompt(
        self, 
        batch: List[Dict], 
        document_context: str, 
        system_instructions: str
    ) -> str:
        """Create enhanced prompt with system instructions"""
        
        # Format checklist items
        checklist_text = ""
        for i, item in enumerate(batch, 1):
            checklist_text += f"{i}. Category: {item['Category']}\n"
            checklist_text += f"   Scope: {item['Scope of Work']}\n"
            checklist_text += f"   Checklist: {item['Checklist']}\n"
            checklist_text += f"   Sector: {item['Sector']}\n\n"
        
        return f"""
SYSTEM INSTRUCTIONS:
{system_instructions}

DOCUMENT CONTEXT:
The following construction documents have been uploaded and processed:
{document_context}

CHECKLIST ITEMS TO MATCH:
{checklist_text}

ENHANCED MATCHING REQUIREMENTS:
1. Use construction expertise to identify relevant matches
2. Consider context and meaning, not just keywords
3. Validate all references against document context
4. Provide detailed reasoning for each match
5. Use conservative matching approach (quality over quantity)

RESPONSE FORMAT:
Return your response in this exact JSON format:
{{
  "matches": [
    {{
      "checklist_index": 1,
      "found": true,
      "confidence": "HIGH",
      "sheet_references": ["A1.1", "A1.2"],
      "spec_references": ["03 30 00"],
      "notes": "Found in architectural drawings and concrete specifications",
      "reasoning": "The checklist item about concrete work is directly referenced in the structural drawings and concrete specification section",
      "validation_score": 0.95
    }}
  ],
  "total_items": {len(batch)},
  "found_count": 0,
  "not_found_count": 0,
  "processing_metadata": {{
    "batch_size": {len(batch)},
    "processing_time": 0.0,
    "confidence_threshold": 0.8
  }}
}}

IMPORTANT:
- Only mark items as found if you have HIGH confidence
- Provide clear, actionable reasoning
- Validate all references exist in documents
- Consider construction industry standards
- Be conservative in matching decisions
"""
    
    def _validate_batch_result(self, result: List[Dict], original_batch: List[Dict]) -> bool:
        """Validate batch processing result"""
        
        if not isinstance(result, list):
            logger.error("Batch result is not a list")
            return False
        
        if len(result) != len(original_batch):
            logger.error(f"Result length mismatch: expected {len(original_batch)}, got {len(result)}")
            return False
        
        # Validate each result item
        for i, item in enumerate(result):
            if not self._validate_result_item(item, original_batch[i]):
                logger.error(f"Invalid result item at index {i}")
                return False
        
        return True
    
    def _validate_result_item(self, result_item: Dict, original_item: Dict) -> bool:
        """Validate individual result item"""
        
        required_fields = ['category', 'scope_of_work', 'checklist', 'sector', 'found']
        
        for field in required_fields:
            if field not in result_item:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate found status
        if not isinstance(result_item['found'], bool):
            logger.error("Found field must be boolean")
            return False
        
        # Validate references if found
        if result_item['found']:
            if 'sheet_number' not in result_item or 'spec_section' not in result_item:
                logger.error("Found items must have sheet_number and spec_section")
                return False
        
        return True
    
    def _validate_and_clean_result(self, result: List[Dict], original_batch: List[Dict]) -> List[Dict]:
        """Validate and clean batch result"""
        
        cleaned_result = []
        
        for i, (result_item, original_item) in enumerate(zip(result, original_batch)):
            try:
                # Ensure all required fields are present
                cleaned_item = {
                    'row_id': original_item.get('row_id', i),
                    'category': result_item.get('category', original_item['Category']),
                    'scope_of_work': result_item.get('scope_of_work', original_item['Scope of Work']),
                    'checklist': result_item.get('checklist', original_item['Checklist']),
                    'sector': result_item.get('sector', original_item['Sector']),
                    'found': result_item.get('found', False),
                    'sheet_number': result_item.get('sheet_number', ''),
                    'spec_section': result_item.get('spec_section', ''),
                    'notes': result_item.get('notes', ''),
                    'reasoning': result_item.get('reasoning', ''),
                    'confidence': result_item.get('confidence', 'LOW'),
                    'validation_score': result_item.get('validation_score', 0.0)
                }
                
                cleaned_result.append(cleaned_item)
                
            except Exception as e:
                logger.error(f"Error cleaning result item {i}: {e}")
                # Add fallback item
                cleaned_result.append({
                    'row_id': original_item.get('row_id', i),
                    'category': original_item['Category'],
                    'scope_of_work': original_item['Scope of Work'],
                    'checklist': original_item['Checklist'],
                    'sector': original_item['Sector'],
                    'found': False,
                    'sheet_number': '',
                    'spec_section': '',
                    'notes': '',
                    'reasoning': f'Error processing item: {str(e)}',
                    'confidence': 'LOW',
                    'validation_score': 0.0
                })
        
        return cleaned_result
    
    def _calculate_confidence_score(self, results: List[Dict]) -> float:
        """Calculate overall confidence score for batch results"""
        
        if not results:
            return 0.0
        
        total_score = 0.0
        valid_items = 0
        
        for item in results:
            if item.get('found', False):
                # Use validation score if available, otherwise estimate from confidence
                validation_score = item.get('validation_score', 0.0)
                if validation_score > 0:
                    total_score += validation_score
                else:
                    # Estimate from confidence level
                    confidence = item.get('confidence', 'LOW')
                    if confidence == 'HIGH':
                        total_score += 0.9
                    elif confidence == 'MEDIUM':
                        total_score += 0.7
                    else:
                        total_score += 0.3
                valid_items += 1
        
        return total_score / valid_items if valid_items > 0 else 0.0
    
    async def process_multiple_batches(
        self, 
        batches: List[List[Dict]], 
        cache_id: str, 
        document_context: str
    ) -> List[BatchResult]:
        """Process multiple batches with concurrency control"""
        
        logger.info(f"=== ENHANCED BATCH PROCESSOR: STARTING PROCESSING OF {len(batches)} BATCHES ===")
        logger.info(f"Cache ID: {cache_id}")
        logger.info(f"Document context length: {len(document_context)} characters")
        logger.info(f"Max concurrent batches: {self.max_concurrent_batches}")
        
        # Create semaphore to limit concurrent processing
        semaphore = asyncio.Semaphore(self.max_concurrent_batches)
        logger.info(f"Created semaphore with limit: {self.max_concurrent_batches}")
        
        async def process_batch_with_semaphore(batch, batch_index):
            logger.info(f"=== STARTING BATCH {batch_index + 1}/{len(batches)} ===")
            logger.info(f"Batch {batch_index + 1} has {len(batch)} items")
            logger.info(f"First item in batch {batch_index + 1}: {batch[0]['Checklist'][:50]}...")
            
            async with semaphore:
                logger.info(f"Acquired semaphore for batch {batch_index + 1}")
                try:
                    result = await self.process_batch_with_retry(batch, batch_index, cache_id, document_context)
                    logger.info(f"Completed batch {batch_index + 1} with status: {result.status}")
                    logger.info(f"Batch {batch_index + 1} processed {result.items_processed} items, found {result.items_found}")
                    return result
                except Exception as e:
                    logger.error(f"Exception in batch {batch_index + 1}: {e}")
                    raise
        
        # Create tasks for all batches
        logger.info("Creating tasks for all batches...")
        tasks = [
            process_batch_with_semaphore(batch, i) 
            for i, batch in enumerate(batches)
        ]
        logger.info(f"Created {len(tasks)} tasks, starting asyncio.gather...")
        
        # Process batches concurrently
        logger.info("Calling asyncio.gather...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"asyncio.gather completed, processing {len(results)} results")
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch {i} failed with exception: {result}")
                processed_results.append(BatchResult(
                    batch_index=i,
                    status=BatchStatus.FAILED,
                    items_processed=0,
                    items_found=0,
                    items_not_found=0,
                    results=[],
                    errors=[f"Exception: {str(result)}"],
                    processing_time=0.0,
                    retry_count=0,
                    confidence_score=0.0
                ))
            else:
                processed_results.append(result)
        
        logger.info(f"=== ENHANCED BATCH PROCESSOR: COMPLETED PROCESSING {len(processed_results)} BATCHES ===")
        return processed_results

    def process_multiple_batches_sync(
        self,
        batches: List[List[Dict]],
        cache_id: str,
        document_context: str,
        tracker_id: str = None,
        output_generator = None
    ) -> List[List[Dict]]:
        """Process multiple batches synchronously (no asyncio)"""
        
        logger.info(f"=== ENHANCED BATCH PROCESSOR SYNC: STARTING PROCESSING OF {len(batches)} BATCHES ===")
        logger.info(f"Cache ID: {cache_id}")
        logger.info(f"Document context length: {len(document_context)} characters")
        
        batch_results = []
        for batch_index, batch in enumerate(batches):
            try:
                logger.info(f"Processing batch {batch_index + 1}/{len(batches)} with {len(batch)} items")
                
                # Get system instructions
                system_instructions = self.system_instructions.get_checklist_matching_instructions()
                
                # Process with Gemini
                result = self.gemini_client.match_checklist_batch_with_system_instructions(
                    batch, cache_id, document_context, system_instructions
                )
                
                # Validate and clean the result
                validated_result = self._validate_and_clean_result(result, batch)
                batch_results.append(validated_result)
                
                logger.info(f"Completed batch {batch_index + 1} with {len(validated_result)} results")
                # Update progress after each batch
                if tracker_id and output_generator:
                    output_generator.update_progress(tracker_id, batch_index, validated_result, "processing")
                
            except Exception as e:
                logger.error(f"Exception while processing batch {batch_index}: {e}")
                # Create fallback results for this batch
                fallback_results = []
                for item in batch:
                    fallback_item = {
                        'row_id': item.get('row_id', batch_index * len(batch) + batch.index(item) + 1),
                        'category': item['Category'],
                        'scope_of_work': item['Scope of Work'],
                        'checklist': item['Checklist'],
                        'sector': item['Sector'],
                        'found': False,
                        'sheet_number': '',
                        'spec_section': '',
                        'notes': '',
                        'reasoning': f'Processing failed: {str(e)}',
                        'confidence': 'LOW',
                        'validation_score': 0.0
                    }
                    fallback_results.append(fallback_item)
                
                batch_results.append(fallback_results)
                logger.info(f"Added fallback results for batch {batch_index + 1}")
                # Update progress for failed batch
                if tracker_id and output_generator:
                    output_generator.update_progress(tracker_id, batch_index, fallback_results, "failed", str(e))
        
        logger.info(f"=== ENHANCED BATCH PROCESSOR SYNC: COMPLETED PROCESSING {len(batch_results)} BATCHES ===")
        return batch_results

    def _process_single_batch_sync(
        self, 
        batch: List[Dict], 
        batch_index: int, 
        cache_id: str, 
        document_context: str
    ) -> List[Dict[str, Any]]:
        """Process a single batch synchronously (no asyncio)"""
        
        logger.info(f"=== _PROCESS_SINGLE_BATCH_SYNC: BATCH {batch_index} ===")
        logger.info(f"Batch {batch_index} has {len(batch)} items")
        
        try:
            # Get system instructions
            logger.info(f"Getting system instructions for batch {batch_index}...")
            system_instructions = self.system_instructions.get_checklist_matching_instructions()
            logger.info(f"System instructions length: {len(system_instructions)} characters")
            
            # Create enhanced prompt
            logger.info(f"Creating enhanced prompt for batch {batch_index}...")
            prompt = self._create_enhanced_prompt(batch, document_context, system_instructions)
            logger.info(f"Enhanced prompt length: {len(prompt)} characters")
            
            # Process with Gemini (synchronous call)
            logger.info(f"Calling Gemini client for batch {batch_index}...")
            logger.info(f"Cache ID: {cache_id}")
            
            result = self.gemini_client.match_checklist_batch_with_system_instructions(
                batch, cache_id, document_context, system_instructions
            )
            
            logger.info(f"Gemini client returned result for batch {batch_index}")
            
            # Validate and clean the result
            logger.info(f"Validating and cleaning result for batch {batch_index}...")
            validated_result = self._validate_and_clean_result(result, batch)
            
            logger.info(f"Batch {batch_index} processing completed with {len(validated_result)} results")
            return validated_result
            
        except Exception as e:
            logger.error(f"Error processing batch {batch_index}: {e}")
            raise
    
    def create_combined_json(self, session_id: str, process_id: str) -> str:
        """Create combined JSON file from all successful and failed responses"""
        try:
            logger.info(f"Creating combined JSON for session: {session_id}, process: {process_id}")
            
            # Combine all JSON outputs
            combined_data = self.json_combiner.combine_all_json_outputs(session_id, process_id)
            
            # Save the combined JSON
            combined_file_path = self.json_combiner.save_combined_json(combined_data, session_id, process_id)
            
            logger.info(f"Combined JSON created successfully: {combined_file_path}")
            return combined_file_path
            
        except Exception as e:
            logger.error(f"Error creating combined JSON: {e}")
            raise
    
    def get_combined_json_path(self, session_id: str, process_id: str) -> Optional[str]:
        """Get the path to the combined JSON file"""
        try:
            return self.json_combiner.get_combined_json_path(session_id, process_id)
        except Exception as e:
            logger.error(f"Error getting combined JSON path: {e}")
            return None 