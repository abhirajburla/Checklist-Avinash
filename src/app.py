#!/usr/bin/env python3
"""
Flask Application for Construction Checklist Matching System
Main web interface for document upload and processing
"""

import os
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from pathlib import Path

# Import our modules
try:
    from .config import Config
    from .document_handler import DocumentHandler
    from .gemini_client import GeminiClient
    from .matching_engine import MatchingEngine
    from .output_generator import OutputGenerator
except ImportError:
    from config import Config
    from document_handler import DocumentHandler
    from gemini_client import GeminiClient
    from matching_engine import MatchingEngine
    from output_generator import OutputGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize components
document_handler = DocumentHandler()
gemini_client = GeminiClient()
matching_engine = MatchingEngine(gemini_client)
output_generator = OutputGenerator()

@app.route('/')
def index():
    """Main upload page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads"""
    try:
        # Get uploaded files
        drawings = request.files.getlist('drawings')
        specifications = request.files.getlist('specifications')
        
        # Filter out empty files
        drawings = [f for f in drawings if f.filename]
        specifications = [f for f in specifications if f.filename]
        
        if not drawings and not specifications:
            return jsonify({
                "success": False,
                "error": "No files were uploaded"
            }), 400
        
        # Process uploads
        result = document_handler.process_uploads(drawings, specifications)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({
            "success": False,
            "error": f"Upload failed: {str(e)}"
        }), 500

@app.route('/process-documents', methods=['POST'])
def process_documents():
    """Start document processing"""
    try:
        data = request.get_json()
        upload_id = data.get('upload_id')
        
        if not upload_id:
            return jsonify({
                "success": False,
                "error": "Upload ID is required"
            }), 400
        
        # Start processing
        result = matching_engine.process_checklist_matching(upload_id)
        
        # Get tracker ID for progress tracking
        status = matching_engine.get_processing_status(result["process_id"])
        tracker_id = status.get("tracker_id")
        
        return jsonify({
            "success": True,
            "process_id": result["process_id"],
            "tracker_id": tracker_id,
            "total_items": result["total_items"],
            "batches": result["batches"],
            "status": "processing"
        })
        
    except Exception as e:
        logger.error(f"Processing error: {e}")
        return jsonify({
            "success": False,
            "error": f"Processing failed: {str(e)}"
        }), 500

@app.route('/status/<process_id>')
def get_status(process_id):
    """Get processing status"""
    try:
        status = matching_engine.get_processing_status(process_id)
        return jsonify(status)
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({
            "success": False,
            "error": f"Status check failed: {str(e)}"
        }), 500

@app.route('/results/<process_id>')
def get_results(process_id):
    """Get processing results"""
    try:
        results = matching_engine.get_results(process_id)
        return jsonify(results)
    except Exception as e:
        logger.error(f"Results error: {e}")
        return jsonify({
            "success": False,
            "error": f"Results retrieval failed: {str(e)}"
        }), 500

@app.route('/progress/<tracker_id>')
def get_progress(tracker_id):
    """Get progress updates for a specific tracker"""
    try:
        progress = output_generator.get_progress(tracker_id)
        if progress is None:
            return jsonify({
                "success": False,
                "error": f"Progress tracker not found: {tracker_id}"
            }), 404
        
        return jsonify({
            "success": True,
            "progress": progress
        })
    except Exception as e:
        logger.error(f"Progress error: {e}")
        return jsonify({
            "success": False,
            "error": f"Progress retrieval failed: {str(e)}"
        }), 500

@app.route('/download/<process_id>')
def download_results(process_id):
    """Download results as JSON file"""
    try:
        # Generate JSON output
        json_output = output_generator.generate_json_output(process_id, pretty_print=True)
        
        # Create response with JSON content
        from flask import Response
        response = Response(
            json_output,
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename=checklist_results_{process_id}.json'
            }
        )
        return response
        
    except ValueError as e:
        logger.error(f"Download error - no output found: {e}")
        return jsonify({
            "success": False,
            "error": f"No output found for process: {process_id}"
        }), 404
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({
            "success": False,
            "error": f"Download failed: {str(e)}"
        }), 500

@app.route('/save/<process_id>')
def save_results(process_id):
    """Save results to file and return file path"""
    try:
        filepath = output_generator.save_output_to_file(process_id)
        return jsonify({
            "success": True,
            "filepath": filepath,
            "message": f"Results saved to {filepath}"
        })
    except ValueError as e:
        logger.error(f"Save error - no output found: {e}")
        return jsonify({
            "success": False,
            "error": f"No output found for process: {process_id}"
        }), 404
    except Exception as e:
        logger.error(f"Save error: {e}")
        return jsonify({
            "success": False,
            "error": f"Save failed: {str(e)}"
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "document_handler": "ok",
            "gemini_client": "ok",
            "matching_engine": "ok"
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Validate configuration
    try:
        Config.validate_config()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        exit(1)
    
    # Create necessary directories
    Path(Config.UPLOAD_FOLDER).mkdir(exist_ok=True)
    Path(Config.CACHE_FOLDER).mkdir(exist_ok=True)
    Path(Config.RESULTS_FOLDER).mkdir(exist_ok=True)
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    ) 