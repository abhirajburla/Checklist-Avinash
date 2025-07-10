#!/usr/bin/env python3
"""
Comprehensive Test Runner for Construction Checklist Matching System
Runs all test suites and generates detailed reports
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def run_phase1_tests():
    """Run Phase 1 tests (basic functionality)"""
    print("\n" + "="*60)
    print("🏗️  PHASE 1 TESTS - Basic System Setup")
    print("="*60)
    
    try:
        # Test basic imports
        from config import Config
        from checklist_processor import ChecklistProcessor
        from document_handler import DocumentHandler
        
        print("✅ Basic imports successful")
        
        # Test configuration
        config = Config()
        assert config.GEMINI_API_KEY, "GEMINI_API_KEY not found"
        assert config.BATCH_SIZE > 0, "Invalid batch size"
        print("✅ Configuration validation passed")
        
        # Test checklist processor
        processor = ChecklistProcessor()
        processor.initialize()
        total_items = processor.get_total_items()
        assert total_items > 0, "No checklist items found"
        print(f"✅ Checklist processor initialized with {total_items} items")
        
        # Test document handler
        handler = DocumentHandler()
        assert handler.config, "Document handler config not found"
        print("✅ Document handler initialized")
        
        print("🎉 Phase 1 tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Phase 1 tests failed: {e}")
        return False

def run_phase2_tests():
    """Run Phase 2 tests (document processing and Gemini integration)"""
    print("\n" + "="*60)
    print("📄 PHASE 2 TESTS - Document Processing & Gemini Integration")
    print("="*60)
    
    try:
        # Test Gemini client
        from gemini_client import GeminiClient
        from prompt_templates import PromptTemplates
        
        print("✅ Gemini client imports successful")
        
        # Test prompt templates
        prompts = PromptTemplates()
        checklist_prompt = prompts.get_checklist_matching_prompt([], "test context")
        assert len(checklist_prompt) > 100, "Prompt too short"
        print("✅ Prompt templates working")
        
        # Test matching engine
        from matching_engine import MatchingEngine
        
        # Mock client for testing
        class MockGeminiClient:
            def __init__(self):
                self.context_cache = {"test": []}
            def upload_documents(self, files):
                return {"success": True, "cache_id": "test_cache"}
            def match_checklist_batch(self, *args):
                return []
        
        mock_client = MockGeminiClient()
        engine = MatchingEngine(mock_client)
        print("✅ Matching engine initialized")
        
        print("🎉 Phase 2 tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Phase 2 tests failed: {e}")
        return False

def run_phase3_tests():
    """Run Phase 3 tests (enhanced features)"""
    print("\n" + "="*60)
    print("🚀 PHASE 3 TESTS - Enhanced Features & Validation")
    print("="*60)
    
    try:
        # Import and run Phase 3 test
        from test_phase3 import main as phase3_main
        return phase3_main()
        
    except Exception as e:
        print(f"❌ Phase 3 tests failed: {e}")
        return False

def run_integration_tests():
    """Run full integration tests"""
    print("\n" + "="*60)
    print("🔗 INTEGRATION TESTS - End-to-End System")
    print("="*60)
    
    try:
        # Test complete workflow
        from config import Config
        from checklist_processor import ChecklistProcessor
        from document_handler import DocumentHandler
        from gemini_client import GeminiClient
        from matching_engine import MatchingEngine
        from system_instructions import SystemInstructions
        from reference_validator import ReferenceValidator
        from enhanced_batch_processor import EnhancedBatchProcessor
        
        print("✅ All components imported successfully")
        
        # Test configuration
        config = Config()
        assert config.ENABLE_SYSTEM_INSTRUCTIONS
        assert config.ENABLE_REFERENCE_VALIDATION
        print("✅ Enhanced configuration loaded")
        
        # Test component initialization
        instructions = SystemInstructions()
        validator = ReferenceValidator()
        processor = ChecklistProcessor()
        
        processor.initialize()
        total_items = processor.get_total_items()
        print(f"✅ System initialized with {total_items} checklist items")
        
        # Test enhanced features
        checklist_instructions = instructions.get_checklist_matching_instructions()
        assert "construction document analyst" in checklist_instructions
        
        validation_result = validator.validate_sheet_number("A1.1")
        assert validation_result.is_valid
        
        print("✅ Enhanced features working correctly")
        
        print("🎉 Integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_test_report(results):
    """Generate a comprehensive test report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_phases": 3,
        "phases_passed": sum(results.values()),
        "phases_failed": len(results) - sum(results.values()),
        "results": results,
        "status": "PASSED" if all(results.values()) else "FAILED"
    }
    
    # Save report
    report_file = Path(__file__).parent.parent / "docs" / "test_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    """Run comprehensive test suite"""
    print("🚀 CONSTRUCTION CHECKLIST MATCHING SYSTEM")
    print("📋 COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    results = {}
    
    # Run all test phases
    results["phase1"] = run_phase1_tests()
    results["phase2"] = run_phase2_tests()
    results["phase3"] = run_phase3_tests()
    results["integration"] = run_integration_tests()
    
    # Calculate results
    total_time = time.time() - start_time
    passed = sum(results.values())
    total = len(results)
    
    # Generate report
    report = generate_test_report(results)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print(f"Total Time: {total_time:.2f} seconds")
    print(f"Status: {report['status']}")
    
    if all(results.values()):
        print("\n🎉 ALL TESTS PASSED! System is ready for production.")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
    
    print(f"\n📄 Detailed report saved to: docs/test_report.json")
    
    return all(results.values())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 