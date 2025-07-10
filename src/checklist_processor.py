import pandas as pd
import logging
from typing import List, Dict, Tuple
from pathlib import Path
try:
    from .config import Config
    from .logger_config import LoggerConfig
except ImportError:
    from config import Config
    from logger_config import LoggerConfig

logger = LoggerConfig.get_logger(__name__)

class ChecklistProcessor:
    """Handles loading and processing of the master checklist"""
    
    def __init__(self):
        self.config = Config()
        self.master_checklist = None
        self.batches = []
        self.total_items = 0
        
    def load_master_checklist(self) -> bool:
        """Load master checklist from CSV file"""
        try:
            if not Path(self.config.MASTER_CHECKLIST_PATH).exists():
                logger.error(f"Master checklist file not found: {self.config.MASTER_CHECKLIST_PATH}")
                return False
            
            # Load CSV file
            self.master_checklist = pd.read_csv(self.config.MASTER_CHECKLIST_PATH)
            logger.info(f"Loaded master checklist with {len(self.master_checklist)} items")
            
            # Validate required columns
            required_columns = ['Category', 'Scope of Work', 'Checklist', 'Sector']
            missing_columns = [col for col in required_columns if col not in self.master_checklist.columns]
            
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return False
            
            # Clean the data
            self.master_checklist = self._clean_checklist_data()
            self.total_items = len(self.master_checklist)
            
            logger.info(f"Successfully loaded and cleaned {self.total_items} checklist items")
            return True
            
        except Exception as e:
            logger.error(f"Error loading master checklist: {str(e)}")
            return False
    
    def _clean_checklist_data(self) -> pd.DataFrame:
        """Clean and validate the checklist data"""
        if self.master_checklist is None:
            raise ValueError("Master checklist is not loaded")
            
        df = self.master_checklist.copy()
        
        # Remove any rows where critical fields are empty
        df = df.dropna(subset=['Category', 'Scope of Work', 'Checklist'])
        
        # Clean whitespace
        df['Category'] = df['Category'].str.strip()
        df['Scope of Work'] = df['Scope of Work'].str.strip()
        df['Checklist'] = df['Checklist'].str.strip()
        df['Sector'] = df['Sector'].str.strip()
        
        # Remove duplicate checklist items
        df = df.drop_duplicates(subset=['Category', 'Scope of Work', 'Checklist'])
        
        # Add row index for tracking
        df = df.reset_index(drop=True)
        df['row_id'] = df.index + 1
        
        return df
    
    def create_batches(self, batch_size: int = 10) -> List[List[Dict]]:  # Changed from 50 to 10
        """Create batches of checklist items for processing"""
        if self.master_checklist is None:
            logger.error("Master checklist not loaded")
            return []
        
        batches = []
        for i in range(0, len(self.master_checklist), batch_size):
            batch = self.master_checklist[i:i + batch_size]
            batches.append(batch.to_dict(orient="records"))
        
        logger.info(f"Created {len(batches)} batches of size {batch_size}")
        return batches
    
    def get_batch(self, batch_index: int) -> List[Dict]:
        """Get a specific batch by index"""
        if 0 <= batch_index < len(self.batches):
            return self.batches[batch_index]
        return []
    
    def get_batch_count(self) -> int:
        """Get total number of batches"""
        return len(self.batches)
    
    def get_total_items(self) -> int:
        """Get total number of checklist items"""
        return self.total_items
    
    def get_checklist_item_by_row_id(self, row_id: int) -> Dict:
        """Get a specific checklist item by row ID"""
        if self.master_checklist is None:
            return {}
        
        item = self.master_checklist[self.master_checklist['row_id'] == row_id]
        if not item.empty:
            return item.iloc[0].to_dict()
        return {}
    
    def create_output_template(self) -> List[Dict]:
        """Create output template with all checklist items"""
        if self.master_checklist is None:
            logger.error("Master checklist not loaded")
            return []
        
        output_template = []
        for _, row in self.master_checklist.iterrows():
            item = {
                "row_id": row['row_id'],
                "category": row['Category'],
                "scope_of_work": row['Scope of Work'],
                "checklist": row['Checklist'],
                "sector": row['Sector'],
                "sheet_number": "",
                "spec_section": "",
                "notes": "",
                "reasoning": "",
                "found": False
            }
            output_template.append(item)
        
        return output_template
    
    def get_checklist_summary(self) -> Dict:
        """Get summary statistics of the checklist"""
        if self.master_checklist is None:
            return {}
        
        summary = {
            "total_items": self.total_items,
            "categories": self.master_checklist['Category'].value_counts().to_dict(),
            "sectors": self.master_checklist['Sector'].value_counts().to_dict(),
            "scopes": self.master_checklist['Scope of Work'].nunique(),
            "batches": len(self.batches)
        }
        
        return summary
    
    def initialize(self) -> bool:
        """Initialize the checklist processor"""
        try:
            if not self.load_master_checklist():
                return False
            
            self.batches = self.create_batches()
            logger.info("Checklist processor initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing checklist processor: {str(e)}")
            return False 