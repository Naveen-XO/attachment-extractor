"""
Output writer for JSON records and summaries.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


class OutputWriter:
    """Handles writing JSON records and summary reports."""
    
    def __init__(self, logger, output_dir: str = "output"):
        """
        Initialize output writer.
        
        Args:
            logger: Logger instance
            output_dir: Directory for output files
        """
        self.logger = logger
        self.output_dir = Path(output_dir)
        self.records_dir = self.output_dir / "records"
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.records_dir.mkdir(parents=True, exist_ok=True)
        
        self.record_counter = 0
        self.all_records = []
    
    def generate_record_id(self) -> str:
        """Generate unique record ID."""
        self.record_counter += 1
        return f"rec_{self.record_counter:05d}"
    
    def create_record(
        self,
        source_file: Path,
        file_type: str,
        extracted_fields: Dict[str, Dict[str, Any]],
        actionable: bool,
        notes: str,
        metadata: Dict[str, Any],
        source_row: int = None
    ) -> Dict[str, Any]:
        """
        Create a standardized record dictionary.
        
        Args:
            source_file: Path to source file
            file_type: Type of file (pdf, image, csv)
            extracted_fields: Extracted fields with values and confidences
            actionable: Whether record is actionable
            notes: Extraction notes
            metadata: Processing metadata
            source_row: Row number if from CSV
            
        Returns:
            Standardized record dictionary
        """
        record_id = self.generate_record_id()
        
        record = {
            "record_id": record_id,
            "source_file": str(source_file),
            "source_row": source_row,
            "file_type": file_type,
            "extracted_fields": extracted_fields,
            "actionable": actionable,
            "notes": notes,
            "metadata": {
                "processed_at": datetime.now().isoformat(),
                **metadata
            }
        }
        
        return record
    
    def write_record(self, record: Dict[str, Any]) -> Path:
        """
        Write individual JSON record file.
        
        Args:
            record: Record dictionary
            
        Returns:
            Path to written file
        """
        record_id = record['record_id']
        output_path = self.records_dir / f"{record_id}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
        
        self.all_records.append(record)
        self.logger.debug(f"Wrote record {record_id} to {output_path}")
        
        return output_path
    
    def write_index(self) -> Path:
        """
        Write index.json with all records.
        
        Returns:
            Path to index file
        """
        index_path = self.output_dir / "index.json"
        
        index = {
            "generated_at": datetime.now().isoformat(),
            "total_records": len(self.all_records),
            "records": self.all_records
        }
        
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Wrote index with {len(self.all_records)} records to {index_path}")
        return index_path
    
    def generate_summary(self, catalog_stats: Dict[str, int], 
                        skipped_count: int, processing_time: float) -> Path:
        """
        Generate human-readable summary report.
        
        Args:
            catalog_stats: File counts by type
            skipped_count: Number of skipped files
            processing_time: Total processing time in seconds
            
        Returns:
            Path to summary file
        """
        summary_path = self.output_dir / "summary.txt"
        
        # Calculate statistics
        actionable_count = sum(1 for r in self.all_records if r['actionable'])
        non_actionable_count = len(self.all_records) - actionable_count
        
        # Group by extraction method
        extraction_methods = {}
        for record in self.all_records:
            method = record['metadata'].get('extraction_method', 'unknown')
            extraction_methods[method] = extraction_methods.get(method, 0) + 1
        
        # Find low confidence records
        low_conf_records = [
            (r['record_id'], r['source_file'], r['metadata'].get('average_confidence', 0))
            for r in self.all_records
            if r['metadata'].get('average_confidence', 0) < 0.75
        ]
        low_conf_records.sort(key=lambda x: x[2])  # Sort by confidence
        
        # Write summary
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("EMAIL ATTACHMENT PROCESSING SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Processing Time: {processing_time:.1f} seconds\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("FILE STATISTICS\n")
            f.write("-" * 80 + "\n")
            for file_type, count in catalog_stats.items():
                f.write(f"  {file_type.capitalize():15s}: {count:5d}\n")
            f.write(f"  {'Total files':15s}: {catalog_stats.get('total', 0):5d}\n")
            f.write(f"  {'Skipped':15s}: {skipped_count:5d}\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("EXTRACTION RESULTS\n")
            f.write("-" * 80 + "\n")
            f.write(f"  Total records created: {len(self.all_records)}\n")
            f.write(f"  Actionable records:    {actionable_count} ({actionable_count/len(self.all_records)*100:.1f}%)\n")
            f.write(f"  Non-actionable:        {non_actionable_count} ({non_actionable_count/len(self.all_records)*100:.1f}%)\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("EXTRACTION METHODS\n")
            f.write("-" * 80 + "\n")
            for method, count in extraction_methods.items():
                f.write(f"  {method.capitalize():15s}: {count:5d}\n")
            f.write("\n")
            
            f.write("-" * 80 + "\n")
            f.write("LOW CONFIDENCE RECORDS (< 0.75)\n")
            f.write("-" * 80 + "\n")
            if low_conf_records:
                f.write(f"  Total: {len(low_conf_records)}\n\n")
                f.write("  Bottom 10 by confidence:\n")
                for record_id, source_file, conf in low_conf_records[:10]:
                    f.write(f"    {record_id} | {conf:.2f} | {Path(source_file).name}\n")
            else:
                f.write("  None - all records meet confidence threshold!\n")
            f.write("\n")
            
            f.write("-" * 80 + "\n")
            f.write("NEXT STEPS\n")
            f.write("-" * 80 + "\n")
            f.write("  1. Review low_confidence.log for records needing manual verification\n")
            f.write("  2. Check skipped_files.log to see what was not processed\n")
            f.write("  3. Filter index.json for actionable=true records for workflow\n")
            f.write("  4. Review sample records in output/records/ directory\n")
            f.write("\n")
        
        self.logger.info(f"Wrote summary report to {summary_path}")
        return summary_path
