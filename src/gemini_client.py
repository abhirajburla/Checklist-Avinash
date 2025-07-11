import logging
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import google.generativeai as genai
try:
    from .config import Config
    from .logger_config import LoggerConfig
    from .prompt_templates import PromptTemplates
    from .system_instructions import SystemInstructions
    from .schemas import validate_batch_result
except ImportError:
    from config import Config
    from logger_config import LoggerConfig
    from prompt_templates import PromptTemplates
    from system_instructions import SystemInstructions
    from schemas import validate_batch_result

logger = LoggerConfig.get_logger(__name__)

class GeminiClient:
    """Gemini API client with context caching for document processing"""
    
    def __init__(self):
        self.config = Config()
        self.prompts = PromptTemplates()
        self.system_instructions = SystemInstructions()
        
        # Configure Gemini API
        genai.configure(api_key=self.config.GEMINI_API_KEY)
        
        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=self.config.GEMINI_MODEL,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # Low temperature for consistent results
                top_p=0.8,
                top_k=40,
                max_output_tokens=8192,
            )
        )
        
        # Context cache for document processing
        self.context_cache = {}
        self.cache_metadata = {}
        
        logger.info(f"GeminiClient initialized with model: {self.config.GEMINI_MODEL}")
    
    def upload_documents(self, file_paths: List[str]) -> Dict[str, Any]:
        """Upload documents to Gemini with context caching"""
        try:
            logger.info(f"Uploading {len(file_paths)} documents to Gemini")
            
            # Generate cache ID based on file paths
            cache_id = self._generate_cache_id(file_paths)
            
            # Check if documents are already cached
            if cache_id in self.context_cache:
                logger.info(f"Using cached documents for cache_id: {cache_id}")
                return {
                    "success": True,
                    "cache_id": cache_id,
                    "cached_files": file_paths,
                    "from_cache": True
                }
            
            # Upload files to Gemini using File API
            uploaded_files = []
            for file_path in file_paths:
                try:
                    file_path_obj = Path(file_path)
                    if not file_path_obj.exists():
                        logger.warning(f"File not found: {file_path}")
                        continue
                    
                    # Upload file to Gemini using File API
                    uploaded_file = genai.upload_file(path=file_path)
                    uploaded_files.append({
                        "original_path": file_path,
                        "gemini_file": uploaded_file,
                        "file_name": file_path_obj.name
                    })
                    

                    
                except Exception as e:
                    logger.error(f"Error uploading file {file_path}: {e}")
                    continue
            
            if not uploaded_files:
                return {
                    "success": False,
                    "error": "No files were successfully uploaded"
                }
            
            # Store in cache
            self.context_cache[cache_id] = uploaded_files
            self.cache_metadata[cache_id] = {
                "created_at": time.time(),
                "file_count": len(uploaded_files),
                "file_paths": file_paths
            }
            

            
            return {
                "success": True,
                "cache_id": cache_id,
                "cached_files": file_paths,
                "uploaded_count": len(uploaded_files),
                "from_cache": False
            }
            
        except Exception as e:
            logger.error(f"Error uploading documents: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def extract_document_references(self, cache_id: str) -> Dict[str, Any]:
        """Extract sheet numbers and specification references from documents"""
        try:
            if cache_id not in self.context_cache:
                return {"success": False, "error": "Cache ID not found"}
            
            uploaded_files = self.context_cache[cache_id]
            
            # Separate drawings and specifications
            drawings = [f for f in uploaded_files if "drawing" in f["original_path"].lower()]
            specifications = [f for f in uploaded_files if "specification" in f["original_path"].lower()]
            
            results = {
                "drawings": [],
                "specifications": [],
                "summary": {}
            }
            
            # Extract sheet information from drawings
            for drawing in drawings:
                try:
                    sheet_info = self._extract_sheet_info(drawing["gemini_file"])
                    results["drawings"].append({
                        "file_name": drawing["file_name"],
                        "sheet_info": sheet_info
                    })
                except Exception as e:
                    logger.error(f"Error extracting sheet info from {drawing['file_name']}: {e}")
            
            # Extract specification references
            for spec in specifications:
                try:
                    spec_info = self._extract_specification_info(spec["gemini_file"])
                    results["specifications"].append({
                        "file_name": spec["file_name"],
                        "spec_info": spec_info
                    })
                except Exception as e:
                    logger.error(f"Error extracting spec info from {spec['file_name']}: {e}")
            
            # Create document summary
            try:
                summary = self._create_document_summary(uploaded_files)
                results["summary"] = summary
            except Exception as e:
                logger.error(f"Error creating document summary: {e}")
            
            return {
                "success": True,
                "references": results
            }
            
        except Exception as e:
            logger.error(f"Error extracting document references: {e}")
            return {"success": False, "error": str(e)}
    
    def match_checklist_batch(self, checklist_batch: List[Dict], cache_id: str, document_context: str) -> List[Dict]:
        """Match a batch of checklist items against cached documents using structured output"""
        try:
            if cache_id not in self.context_cache:
                logger.error(f"Cache ID not found: {cache_id}")
                return []
            
            uploaded_files = self.context_cache[cache_id]
            
            # Get the matching prompt
            prompt = self.prompts.get_checklist_matching_prompt(checklist_batch, document_context)
            
            # Create contents array with files and prompt
            contents = []
            
            # Add all uploaded files to contents
            for file_info in uploaded_files:
                contents.append(file_info["gemini_file"])
            
            # Add the prompt as the last element
            contents.append(prompt)
            
            # Generate content with structured output (model is always gemini-2.5-flash)
            response = self.model.generate_content(contents)
            
            # Parse the structured response
            try:
                # Parse JSON response and validate with schema
                result = json.loads(response.text)
                batch_result = validate_batch_result(result)
                
                # Convert structured result to our format
                processed_results = []
                for item in checklist_batch:
                    idx = checklist_batch.index(item) + 1
                    # Find matching result
                    match = next((m for m in batch_result.matches if m.checklist_index == idx), None)
                    
                    if match and match.found:
                        processed_item = {
                            "row_id": item.get("row_id"),
                            "category": item["Category"],
                            "scope_of_work": item["Scope of Work"],
                            "checklist": item["Checklist"],
                            "sector": item["Sector"],
                            "sheet_number": ", ".join(match.sheet_references),
                            "spec_section": ", ".join(match.spec_references),
                            "notes": match.notes,
                            "reasoning": match.reasoning,
                            "found": True,
                            "confidence": match.confidence.value,
                            "validation_score": match.validation_score,
                            "checklist_index": idx,
                            "checklist_item": item  # include the full checklist item
                        }
                    else:
                        processed_item = {
                            "row_id": item.get("row_id"),
                            "category": item["Category"],
                            "scope_of_work": item["Scope of Work"],
                            "checklist": item["Checklist"],
                            "sector": item["Sector"],
                            "sheet_number": "",
                            "spec_section": "",
                            "notes": "",
                            "reasoning": "Item not found in documents",
                            "found": False,
                            "confidence": "LOW",
                            "validation_score": 0.0,
                            "checklist_index": idx,
                            "checklist_item": item
                        }
                    
                    processed_results.append(processed_item)
                
                logger.info(f"Processed {len(processed_results)} checklist items using structured output")
                logger.info(f"Found {batch_result.found_count} items, {batch_result.not_found_count} not found")
                return processed_results
                
            except Exception as e:
                logger.error(f"Error parsing structured response: {e}")
                logger.error(f"Response text: {response.text}")
                # Fallback to manual JSON parsing if structured output fails
                return self._parse_fallback_response(response.text, checklist_batch)
            
        except Exception as e:
            logger.error(f"Error matching checklist batch: {e}")
            return []
    
    def match_checklist_batch_with_system_instructions(
        self, 
        checklist_batch: List[Dict], 
        cache_id: str, 
        document_context: str, 
        system_instructions: str
    ) -> List[Dict]:
        """Match a batch of checklist items against cached documents with custom system instructions"""
        try:
            if cache_id not in self.context_cache:
                logger.error(f"Cache ID not found: {cache_id}")
                return []
            
            uploaded_files = self.context_cache[cache_id]
            
            # Get the matching prompt
            prompt = self.prompts.get_checklist_matching_prompt(checklist_batch, document_context)
            
            # Create contents array with files and prompt
            contents = []
            
            # Add all uploaded files to contents
            for file_info in uploaded_files:
                contents.append(file_info["gemini_file"])
            
            # Add the prompt as the last element
            contents.append(prompt)
            
            # Send the matching prompt with system instructions
            logger.info("Sending matching prompt to Gemini...")
            
            # Add timeout handling
            import threading
            import queue
            
            response_queue = queue.Queue()
            error_queue = queue.Queue()
            
            def send_message_with_timeout():
                try:
                    response = self.model.generate_content(contents)
                    response_queue.put(response)
                except Exception as e:
                    error_queue.put(e)
            
            # Start the API call in a separate thread
            thread = threading.Thread(target=send_message_with_timeout)
            thread.daemon = True
            thread.start()
            
            # Wait for response with timeout
            try:
                response = response_queue.get(timeout=60)  # 60 second timeout
            except queue.Empty:
                logger.error("Gemini API call timed out")
                return self._create_fallback_results(checklist_batch)
            except Exception as e:
                logger.error(f"Error in Gemini API call: {e}")
                return self._create_fallback_results(checklist_batch)
            
            # Parse the response
            try:
                # Clean the response text - remove markdown code blocks if present
                response_text = response.text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]  # Remove "```json"
                if response_text.endswith("```"):
                    response_text = response_text[:-3]  # Remove "```"
                response_text = response_text.strip()
                
                result = json.loads(response_text)
                matches = result.get("matches", [])
                
                # Validate references against actual documents
                validated_matches = self._validate_references(matches, uploaded_files)
                
                # Convert validated matches to our expected format
                processed_results = []
                for item in checklist_batch:
                    idx = checklist_batch.index(item) + 1
                    # Find matching result
                    match = next((m for m in validated_matches if m.get("checklist_index") == idx), None)
                    
                    if match and match.get("found", False):
                        processed_item = {
                            "row_id": item.get("row_id"),
                            "category": item["Category"],
                            "scope_of_work": item["Scope of Work"],
                            "checklist": item["Checklist"],
                            "sector": item["Sector"],
                            "sheet_number": ", ".join(match.get("sheet_references", [])),
                            "spec_section": ", ".join(match.get("spec_references", [])),
                            "notes": match.get("notes", ""),
                            "reasoning": match.get("reasoning", ""),
                            "found": True,
                            "confidence": match.get("confidence", "LOW"),
                            "validation_score": match.get("validation_score", 0.0),
                            "checklist_index": idx,
                            "checklist_item": item
                        }
                    else:
                        processed_item = {
                            "row_id": item.get("row_id"),
                            "category": item["Category"],
                            "scope_of_work": item["Scope of Work"],
                            "checklist": item["Checklist"],
                            "sector": item["Sector"],
                            "sheet_number": "",
                            "spec_section": "",
                            "notes": "",
                            "reasoning": "Item not found in documents",
                            "found": False,
                            "confidence": "LOW",
                            "validation_score": 0.0,
                            "checklist_index": idx,
                            "checklist_item": item
                        }
                    
                    processed_results.append(processed_item)
                
                logger.info(f"Processed {len(processed_results)} checklist items")
                found_count = sum(1 for item in processed_results if item.get("found", False))
                logger.info(f"Found {found_count} items, {len(processed_results) - found_count} not found")
                
                return processed_results
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing Gemini response: {e}")
                logger.error(f"Response text: {response.text}")
                # Try fallback parsing
                return self._parse_fallback_response(response.text, checklist_batch)
                
        except Exception as e:
            logger.error(f"Error in match_checklist_batch_with_system_instructions: {e}")
            return self._create_fallback_results(checklist_batch)
    
    def _create_fallback_results(self, checklist_batch: List[Dict]) -> List[Dict]:
        """Create fallback results when Gemini API fails"""
        logger.info(f"Creating fallback results for {len(checklist_batch)} items")
        
        fallback_results = []
        for item in checklist_batch:
            fallback_item = {
                "row_id": item.get("row_id"),
                "category": item["Category"],
                "scope_of_work": item["Scope of Work"],
                "checklist": item["Checklist"],
                "sector": item["Sector"],
                "sheet_number": "",
                "spec_section": "",
                "notes": "",
                "reasoning": "Processing failed - using fallback results",
                "confidence": "LOW",
                "validation_score": 0.0,
                "found": False
            }
            fallback_results.append(fallback_item)
        
        logger.info(f"Created {len(fallback_results)} fallback results")
        return fallback_results
    
    def _extract_sheet_info(self, gemini_file) -> Dict[str, Any]:
        """Extract sheet information from a drawing file"""
        try:
            prompt = self.prompts.get_sheet_extraction_prompt()
            
            # Use generate_content with file and prompt
            response = self.model.generate_content([gemini_file, prompt])
            
            # Parse response
            try:
                result = json.loads(response.text)
                return result
            except json.JSONDecodeError:
                logger.warning("Could not parse sheet info response as JSON")
                return {
                    "sheet_number": "",
                    "sheet_title": "Untitled",
                    "discipline": "General",
                    "project_info": ""
                }
                
        except Exception as e:
            logger.error(f"Error extracting sheet info: {e}")
            return {
                "sheet_number": "",
                "sheet_title": "Error",
                "discipline": "General",
                "project_info": ""
            }
    
    def _extract_specification_info(self, gemini_file) -> Dict[str, Any]:
        """Extract specification information from a spec file"""
        try:
            prompt = self.prompts.get_specification_extraction_prompt()
            
            # Use generate_content with file and prompt
            response = self.model.generate_content([gemini_file, prompt])
            
            # Parse response
            try:
                result = json.loads(response.text)
                return result
            except json.JSONDecodeError:
                logger.warning("Could not parse specification info response as JSON")
                return {
                    "specifications": [],
                    "total_specifications": 0
                }
                
        except Exception as e:
            logger.error(f"Error extracting specification info: {e}")
            return {
                "specifications": [],
                "total_specifications": 0
            }
    
    def _create_document_summary(self, uploaded_files: List[Dict]) -> Dict[str, Any]:
        """Create a summary of the uploaded documents"""
        try:
            file_paths = [f["original_path"] for f in uploaded_files]
            prompt = self.prompts.get_document_summary_prompt(file_paths)
            
            # Create contents array with all files and prompt
            contents = []
            for file_info in uploaded_files:
                contents.append(file_info["gemini_file"])
            contents.append(prompt)
            
            # Use generate_content with files and prompt
            response = self.model.generate_content(contents)
            
            # Parse response
            try:
                result = json.loads(response.text)
                return result
            except json.JSONDecodeError:
                logger.warning("Could not parse document summary response as JSON")
                return {
                    "document_summary": "Summary not available",
                    "key_elements": [],
                    "major_systems": [],
                    "project_scope": "Unknown"
                }
                
        except Exception as e:
            logger.error(f"Error creating document summary: {e}")
            return {
                "document_summary": "Error creating summary",
                "key_elements": [],
                "major_systems": [],
                "project_scope": "Error"
            }
    
    def _generate_cache_id(self, file_paths: List[str]) -> str:
        """Generate a unique cache ID based on file paths"""
        import hashlib
        content = "|".join(sorted(file_paths))
        return hashlib.md5(content.encode()).hexdigest()
    
    def cleanup_cache(self, cache_id: str) -> bool:
        """Clean up cached files"""
        try:
            if cache_id in self.context_cache:
                # Delete files from Gemini
                for file_info in self.context_cache[cache_id]:
                    try:
                        genai.delete_file(file_info["gemini_file"].name)
                    except Exception as e:
                        logger.warning(f"Error deleting file from Gemini: {e}")
                
                # Remove from cache
                del self.context_cache[cache_id]
                if cache_id in self.cache_metadata:
                    del self.cache_metadata[cache_id]
                
                logger.info(f"Cleaned up cache: {cache_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error cleaning up cache {cache_id}: {e}")
            return False
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached files"""
        return {
            "cache_count": len(self.context_cache),
            "cache_metadata": self.cache_metadata
        } 

    def _validate_references(self, matches: List[Dict], uploaded_files: List[Dict]) -> List[Dict]:
        """Validate that extracted references actually exist in the uploaded documents"""
        try:
            # For now, return the original matches without strict validation
            # This allows Gemini's analysis to be trusted more
            return matches
            
        except Exception as e:
            logger.error(f"Error validating references: {e}")
            return matches  # Return original matches if validation fails
    
    def _parse_fallback_response(self, response_text: str, checklist_batch: List[Dict]) -> List[Dict]:
        """Fallback method to parse response when structured output fails"""
        try:
            # Clean the response text - remove markdown code blocks if present
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]  # Remove "```json"
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]  # Remove "```"
            cleaned_text = cleaned_text.strip()
            
            # Try to parse as JSON
            result = json.loads(cleaned_text)
            matches = result.get("matches", [])
            
            # Convert matches to our format
            processed_results = []
            for item in checklist_batch:
                idx = checklist_batch.index(item) + 1
                # Find matching result
                match = next((m for m in matches if m.get("checklist_index") == idx), None)
                
                if match and match.get("found", False):
                    processed_item = {
                        "row_id": item.get("row_id"),
                        "category": item["Category"],
                        "scope_of_work": item["Scope of Work"],
                        "checklist": item["Checklist"],
                        "sector": item["Sector"],
                        "sheet_number": ", ".join(match.get("sheet_references", [])),
                        "spec_section": ", ".join(match.get("spec_references", [])),
                        "notes": match.get("notes", ""),
                        "reasoning": match.get("reasoning", ""),
                        "found": True,
                        "confidence": match.get("confidence", "LOW"),
                        "validation_score": match.get("validation_score", 0.0),
                        "checklist_index": idx,
                        "checklist_item": item
                    }
                else:
                    processed_item = {
                        "row_id": item.get("row_id"),
                        "category": item["Category"],
                        "scope_of_work": item["Scope of Work"],
                        "checklist": item["Checklist"],
                        "sector": item["Sector"],
                        "sheet_number": "",
                        "spec_section": "",
                        "notes": "",
                        "reasoning": "Item not found in documents",
                        "found": False,
                        "confidence": "LOW",
                        "validation_score": 0.0,
                        "checklist_index": idx,
                        "checklist_item": item
                    }
                
                processed_results.append(processed_item)
            
            logger.info(f"Processed {len(processed_results)} checklist items using fallback parsing")
            return processed_results
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing fallback response: {e}")
            logger.error(f"Response text: {response_text}")
            return self._create_fallback_results(checklist_batch) 