from flask import Flask, request, jsonify, render_template, send_file
import os
from dotenv import load_dotenv
import logging
from pathlib import Path
import json
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

# Import our modules
from src.config import Config
from src.logger_config import LoggerConfig
from src.document_handler import DocumentHandler
from src.checklist_processor import ChecklistProcessor
from src.gemini_client import GeminiClient
from src.matching_engine import MatchingEngine

# Setup centralized logging
LoggerConfig.setup_from_config(Config)
logger = LoggerConfig.get_logger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize components
document_handler = DocumentHandler()
checklist_processor = ChecklistProcessor()
gemini_client = GeminiClient()
matching_engine = MatchingEngine(gemini_client)

# Initialize checklist processor
if not checklist_processor.initialize():
    logger.error("Failed to initialize checklist processor")
    raise RuntimeError("Checklist processor initialization failed")

# Store processing status (in production, use Redis or database)
processing_status = {}

@app.route('/')
def index():
    """Main upload page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_documents():
    """Handle document uploads (drawings and specifications)"""
    try:
        # Get uploaded files
        drawings = request.files.getlist('drawings')
        specifications = request.files.getlist('specifications')
        
        # Validate files
        if not drawings and not specifications:
            logger.warning("No files uploaded")
            return jsonify({"error": "No files uploaded"}), 400
        
        # Process documents
        result = document_handler.process_uploads(drawings, specifications)
        
        if result['success']:
            logger.info(f"Upload successful - Upload ID: {result['upload_id']}")
            return jsonify({
                "message": "Documents uploaded successfully",
                "drawing_count": len(drawings),
                "spec_count": len(specifications),
                "upload_id": result['upload_id']
            })
        else:
            logger.error(f"Upload failed: {result['error']}")
            return jsonify({"error": result['error']}), 400
            
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({"error": "Upload failed"}), 500

@app.route('/process-documents', methods=['POST'])
def process_documents():
    """Process checklist matching for uploaded documents"""
    try:
        data = request.get_json()
        upload_id = data.get('upload_id')
        
        if not upload_id:
            logger.error("No upload_id provided")
            return jsonify({"error": "Upload ID required"}), 400
        
        # Generate process and tracker IDs
        process_id = str(uuid.uuid4())
        tracker_id = str(uuid.uuid4())
        
        # Get upload files
        upload_info = document_handler.get_upload_files(upload_id)
        
        if not upload_info["success"]:
            logger.error(f"Upload not found: {upload_info.get('error', 'Unknown error')}")
            return jsonify({"error": "Upload not found"}), 404
        
        # Get checklist batches
        # Ensure checklist processor is properly loaded
        if checklist_processor.master_checklist is None:
            logger.error("Master checklist not loaded, attempting to reload...")
            if not checklist_processor.load_master_checklist():
                logger.error("Failed to load master checklist")
                return jsonify({"error": "Failed to load master checklist"}), 500
            checklist_processor.create_batches(checklist_processor.config.BATCH_SIZE)
        
        batches = checklist_processor.create_batches(checklist_processor.config.BATCH_SIZE)
        total_batches = len(batches)
        total_items = checklist_processor.get_total_items()
        
        # Initialize processing status
        processing_status[tracker_id] = {
            'status': 'processing',
            'progress': {
                'current_batch': 0,
                'total_batches': total_batches,
                'items_processed': 0,
                'total_items': total_items,
                'progress_percentage': 0
            },
            'error': None,
            'process_id': process_id,
            'upload_id': upload_id,
            'results': []
        }
        
        # Start processing in background
        def background_process():
            try:
                # Get upload files for matching engine
                upload_files = upload_info["files"]["drawings"] + upload_info["files"]["specifications"]
                
                # Use the real matching engine instead of simulation
                matching_result = matching_engine.process_checklist_matching(upload_id)
                
                # Get results from matching engine
                engine_process_id = matching_result["process_id"]
                
                # Wait for matching engine to complete
                max_wait_time = matching_engine.config.PROCESSING_TIMEOUT  # Use configurable timeout
                wait_interval = 2  # 2 seconds
                elapsed_time = 0
                
                while elapsed_time < max_wait_time:
                    status = matching_engine.get_processing_status(engine_process_id)
                    
                    if status['status'] == 'completed':
                        break
                    elif status['status'] == 'failed':
                        error_msg = status.get('error', 'Unknown error')
                        raise Exception(f"Matching engine failed: {error_msg}")
                    
                    import time
                    time.sleep(wait_interval)
                    elapsed_time += wait_interval
                
                if elapsed_time >= max_wait_time:
                    raise Exception(f"Matching engine processing timed out after {max_wait_time} seconds")
                
                # Get final results from matching engine
                results_data = matching_engine.get_results(engine_process_id)
                
                # Update processing status with real results
                real_results = results_data.get('checklist_results', [])
                processing_status[tracker_id]['results'] = real_results
                
                # Update progress with real counts
                found_items = sum(1 for item in real_results if item.get('found', False))
                processing_status[tracker_id]['progress']['found_items'] = found_items
                processing_status[tracker_id]['progress']['not_found_items'] = len(real_results) - found_items
                
                # Clean up matching engine process
                matching_engine.cleanup_process(engine_process_id)
                
                # Create combined JSON at the end of processing
                try:
                    logger.info(f"Creating combined JSON for session: {upload_id}, process: {process_id}")
                    combined_file_path = matching_engine.enhanced_batch_processor.create_combined_json(upload_id, process_id)
                    logger.info(f"Combined JSON created successfully: {combined_file_path}")
                except Exception as e:
                    logger.error(f"Error creating combined JSON: {e}")
                    # Don't fail the entire process if combined JSON creation fails
                
                # Mark as completed
                processing_status[tracker_id]['status'] = 'completed'
                
            except Exception as e:
                logger.error(f"Background processing failed: {e}")
                processing_status[tracker_id]['status'] = 'failed'
                processing_status[tracker_id]['error'] = str(e)
        
        # Start background processing
        import threading
        thread = threading.Thread(target=background_process)
        thread.daemon = True
        thread.start()
        
        response_data = {
            "message": "Processing started",
            "process_id": process_id,
            "tracker_id": tracker_id,
            "total_items": total_items,
            "batches": total_batches
        }
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return jsonify({"error": "Processing failed"}), 500

@app.route('/progress/<tracker_id>')
def get_progress(tracker_id):
    """Get processing progress"""
    try:
        if tracker_id not in processing_status:
            logger.warning(f"Tracker {tracker_id} not found in processing_status")
            return jsonify({"error": "Tracker not found"}), 404
        
        status = processing_status[tracker_id]
        
        response_data = {
            "success": True,
            "progress": status['progress'],
            "status": status['status'],
            "error": status.get('error')
        }
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Progress error: {str(e)}")
        return jsonify({"error": "Progress check failed"}), 500

@app.route('/results/<process_id>')
def get_results(process_id):
    """Get final results in clean JSON format"""
    try:
        # Find the tracker that contains this process_id
        tracker_id = None
        for tid, status in processing_status.items():
            if status.get('process_id') == process_id:
                tracker_id = tid
                break
        
        if not tracker_id:
            logger.error(f"Process {process_id} not found in any tracker")
            return jsonify({"error": "Process not found"}), 404
        
        status = processing_status[tracker_id]
        
        if status['status'] != 'completed':
            logger.warning(f"Process {process_id} not completed yet. Status: {status['status']}")
            return jsonify({"error": "Processing not completed"}), 400
        
        # Get actual results
        results = status.get('results', [])
        
        if not results:
            logger.warning(f"No results found for process {process_id}")
            return jsonify({"error": "No results found"}), 404
        
        # Create the data structure expected by the output generator
        output_data = {
            "checklist_results": results
        }
        
        # Store in output generator cache
        matching_engine.output_generator.output_cache[process_id] = output_data
        
        # Generate clean JSON output
        clean_json = matching_engine.output_generator.generate_clean_json_output(process_id, pretty_print=True)
        
        # Parse the JSON to return as response
        clean_results = json.loads(clean_json)
        
        return jsonify(clean_results)
    except Exception as e:
        logger.error(f"Results error: {str(e)}")
        return jsonify({"error": "Failed to get results"}), 500

@app.route('/download/<process_id>')
def download_results(process_id):
    """Download results as clean JSON file with essential fields only"""
    try:
        # Find the tracker that contains this process_id
        tracker_id = None
        for tid, status in processing_status.items():
            if status.get('process_id') == process_id:
                tracker_id = tid
                break
        
        if not tracker_id:
            logger.error(f"Process {process_id} not found in any tracker")
            return jsonify({"error": "Process not found"}), 404
        
        status = processing_status[tracker_id]
        
        if status['status'] != 'completed':
            logger.warning(f"Process {process_id} not completed yet. Status: {status['status']}")
            return jsonify({"error": "Processing not completed"}), 400
        
        # Get results from the tracker
        results = status.get('results', [])
        
        if not results:
            logger.warning(f"No results found for process {process_id}")
            return jsonify({"error": "No results found"}), 404
        
        # Create the data structure expected by the output generator
        output_data = {
            "checklist_results": results
        }
        
        # Store in output generator cache
        matching_engine.output_generator.output_cache[process_id] = output_data
        
        # Generate clean JSON output
        clean_json = matching_engine.output_generator.generate_clean_json_output(process_id, pretty_print=True)
        
        # Create temporary file for download
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8')
        temp_file.write(clean_json)
        temp_file.close()
        
        logger.info(f"Clean JSON file created for download: {temp_file.name}")
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f'checklist_results_{process_id}.json',
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        import traceback
        logger.error(f"Download traceback: {traceback.format_exc()}")
        return jsonify({"error": "Download failed"}), 500

@app.route('/download-excel/<process_id>')
def download_excel_results(process_id):
    """Download results as Excel file"""
    try:
        # Find the tracker that contains this process_id
        tracker_id = None
        for tid, status in processing_status.items():
            if status.get('process_id') == process_id:
                tracker_id = tid
                break
        
        if not tracker_id:
            logger.error(f"Process {process_id} not found in any tracker")
            return jsonify({"error": "Process not found"}), 404
        
        status = processing_status[tracker_id]
        
        if status['status'] != 'completed':
            logger.warning(f"Process {process_id} not completed yet. Status: {status['status']}")
            return jsonify({"error": "Processing not completed"}), 400
        
        # Get actual results
        results = status.get('results', [])
        
        # Create the data structure expected by the Excel generator
        output_data = {
            "checklist_results": results
        }
        
        # Use the matching engine's output generator to create Excel file
        matching_engine.output_generator.output_cache[process_id] = output_data
        
        # Generate Excel file
        excel_filepath = matching_engine.output_generator.generate_excel_output(process_id)
        
        logger.info(f"Excel file generated: {excel_filepath}")
        
        return send_file(
            excel_filepath,
            as_attachment=True,
            download_name=f'checklist_results_{process_id}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"Excel download error: {str(e)}")
        import traceback
        logger.error(f"Excel download traceback: {traceback.format_exc()}")
        return jsonify({"error": "Excel download failed"}), 500

# Keep the old endpoints for backward compatibility
@app.route('/process', methods=['POST'])
def process_checklist():
    """Legacy endpoint - redirects to /process-documents"""
    return process_documents()

@app.route('/status/<process_id>')
def get_status(process_id):
    """Legacy endpoint - redirects to /progress"""
    # For backward compatibility, we'll return a simple status
    return jsonify({
        "status": "completed",
        "process_id": process_id,
        "message": "Processing completed"
    })

@app.route('/token-usage')
def get_token_usage():
    """Get token usage summary for the current session"""
    try:
        token_summary = gemini_client.get_token_usage_summary()
        return jsonify({
            "success": True,
            "token_usage": token_summary
        })
    except Exception as e:
        logger.error(f"Token usage error: {str(e)}")
        return jsonify({"error": "Failed to get token usage"}), 500

@app.route('/reset-token-tracking', methods=['POST'])
def reset_token_tracking():
    """Reset token tracking for new session"""
    try:
        gemini_client.reset_token_tracking()
        return jsonify({"message": "Token tracking reset successfully"})
    except Exception as e:
        logger.error(f"Error resetting token tracking: {e}")
        return jsonify({"error": "Failed to reset token tracking"}), 500

@app.route('/json-storage/stats')
def get_json_storage_stats():
    """Get JSON storage statistics"""
    try:
        stats = gemini_client.json_storage.get_storage_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting JSON storage stats: {e}")
        return jsonify({"error": "Failed to get storage stats"}), 500

@app.route('/json-storage/cleanup', methods=['POST'])
def cleanup_json_storage():
    """Clean up old JSON files"""
    try:
        data = request.get_json() or {}
        days = data.get('days', 7)
        deleted_count = gemini_client.json_storage.cleanup_old_files(days)
        return jsonify({
            "message": f"Cleaned up {deleted_count} old files",
            "deleted_count": deleted_count,
            "days": days
        })
    except Exception as e:
        logger.error(f"Error cleaning up JSON storage: {e}")
        return jsonify({"error": "Failed to cleanup storage"}), 500

@app.route('/json-storage/combine/<session_id>')
def combine_json_responses(session_id):
    """Combine all responses from a session"""
    try:
        combined_file = gemini_client.json_storage.combine_responses(session_id)
        if combined_file:
            return jsonify({
                "message": "Responses combined successfully",
                "file_path": combined_file
            })
        else:
            return jsonify({"error": "Failed to combine responses"}), 500
    except Exception as e:
        logger.error(f"Error combining responses: {e}")
        return jsonify({"error": "Failed to combine responses"}), 500

@app.route('/json-storage/session/<session_id>')
def get_session_responses(session_id):
    """Get all responses for a specific session"""
    try:
        responses = gemini_client.json_storage.get_session_responses(session_id)
        return jsonify({
            "session_id": session_id,
            "total_responses": len(responses),
            "responses": responses
        })
    except Exception as e:
        logger.error(f"Error getting session responses: {e}")
        return jsonify({"error": "Failed to get session responses"}), 500

if __name__ == '__main__':
    # Create necessary directories
    Path('uploads').mkdir(exist_ok=True)
    Path('cache').mkdir(exist_ok=True)
    Path('results').mkdir(exist_ok=True)
    
    # Run the application
    app.run(debug=True, port=5000) 