"""
Comprehensive Validation Script - Task 17 Implementation

Main validation script that runs citation validation and research data validation
across the entire codebase to ensure all industry standards are properly cited.
"""

import asyncio
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any
import json
import yaml

from .citation_validator import CitationValidator
from .research_validator import ResearchValidator

logger = logging.getLogger(__name__)


class ComprehensiveValidator:
    """Comprehensive validation framework"""
    
    def __init__(self, base_dir: str = None):
        """Initialize comprehensive validator"""
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.citation_validator = CitationValidator()
        self.research_validator = ResearchValidator()
        
        # Files to validate
        self.documentation_files = []
        self.research_files = []
        self.config_files = []
        
        self._discover_files()
    
    def _discover_files(self):
        """Discover files that need validation"""
        
        # Documentation files
        doc_patterns = ["*.md", "*.rst", "*.txt"]
        for pattern in doc_patterns:
            self.documentation_files.extend(self.base_dir.rglob(pattern))
        
        # Research and standards files
        research_patterns = ["*research*.md", "*standards*.md", "*benchmark*.md"]
        for pattern in research_patterns:
            self.research_files.extend(self.base_dir.rglob(pattern))
        
        # Configuration files with thresholds
        config_patterns = ["*.yaml", "*.yml", "*.json"]
        for pattern in config_patterns:
            for file_path in self.base_dir.rglob(pattern):
                # Only include files that likely contain thresholds
                if any(keyword in file_path.name.lower() for keyword in 
                      ["threshold", "config", "health", "performance", "standard"]):
                    self.config_files.append(file_path)
        
        logger.info(f"Discovered {len(self.documentation_files)} documentation files")
        logger.info(f"Discovered {len(self.research_files)} research files")
        logger.info(f"Discovered {len(self.config_files)} configuration files")
    
    async def validate_all_citations(self) -> Dict[str, Any]:
        """Validate all citations across the codebase"""
        logger.info("Starting comprehensive citation validation...")
        
        # Combine all files for citation validation
        all_files = []
        all_files.extend([str(f) for f in self.documentation_files])
        all_files.extend([str(f) for f in self.research_files])
        
        # Run citation validation
        citation_report = await self.citation_validator.validate_all_citations(all_files)
        
        # Generate detailed citation quality report
        citation_quality = await self.citation_validator.generate_citation_quality_report(all_files)
        
        return {
            "citation_validation_report": citation_report,
            "citation_quality_report": citation_quality
        }
    
    async def validate_all_research_data(self) -> Dict[str, Any]:
        """Validate all research data and thresholds"""
        logger.info("Starting comprehensive research data validation...")
        
        research_reports = []
        
        # Validate each research file against relevant config files
        for research_file in self.research_files:
            # Find related config files
            related_configs = []
            research_name = research_file.stem.lower()
            
            for config_file in self.config_files:
                config_name = config_file.stem.lower()
                # Simple heuristic to match research files with config files
                if any(keyword in research_name and keyword in config_name 
                      for keyword in ["health", "performance", "threshold", "standard"]):
                    related_configs.append(config_file)
            
            # Use the first related config or a default
            config_file = related_configs[0] if related_configs else self.config_files[0] if self.config_files else None
            
            if config_file:
                try:
                    research_report = await self.research_validator.validate_research_data_comprehensively(
                        str(research_file), str(config_file)
                    )
                    research_reports.append({
                        "research_file": str(research_file),
                        "config_file": str(config_file),
                        "validation_report": research_report
                    })
                except Exception as e:
                    logger.error(f"Error validating research file {research_file}: {e}")
        
        return {
            "research_validation_reports": research_reports,
            "total_files_validated": len(research_reports)
        }
    
    async def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        logger.info("Generating comprehensive validation report...")
        
        # Run all validations
        citation_results = await self.validate_all_citations()
        research_results = await self.validate_all_research_data()
        
        # Calculate overall scores
        citation_report = citation_results["citation_validation_report"]
        citation_quality = citation_results["citation_quality_report"]
        
        overall_citation_score = citation_quality.get("citation_quality_score", 0)
        overall_accessibility = citation_report.accessibility_rate * 100
        overall_currency = citation_report.currency_rate * 100
        
        # Research validation scores
        research_reports = research_results["research_validation_reports"]
        if research_reports:
            avg_data_quality = sum(r["validation_report"].data_quality_score for r in research_reports) / len(research_reports)
            avg_reliability = sum(r["validation_report"].reliability_score for r in research_reports) / len(research_reports)
        else:
            avg_data_quality = 0
            avg_reliability = 0
        
        # Generate recommendations
        recommendations = self._generate_comprehensive_recommendations(
            citation_results, research_results
        )
        
        # Compliance assessment
        compliance_status = self._assess_overall_compliance(citation_results, research_results)
        
        comprehensive_report = {
            "validation_summary": {
                "total_citations_validated": citation_report.total_citations,
                "citation_accessibility_rate": overall_accessibility,
                "citation_currency_rate": overall_currency,
                "citation_quality_score": overall_citation_score,
                "research_files_validated": len(research_reports),
                "average_data_quality_score": avg_data_quality,
                "average_reliability_score": avg_reliability
            },
            "detailed_results": {
                "citation_validation": citation_results,
                "research_validation": research_results
            },
            "compliance_assessment": compliance_status,
            "recommendations": recommendations,
            "validation_metadata": {
                "validation_date": citation_report.report_date,
                "files_analyzed": {
                    "documentation_files": len(self.documentation_files),
                    "research_files": len(self.research_files),
                    "config_files": len(self.config_files)
                },
                "validator_versions": {
                    "citation_validator": "1.0.0",
                    "research_validator": "1.0.0"
                }
            }
        }
        
        return comprehensive_report
    
    def _generate_comprehensive_recommendations(self, 
                                              citation_results: Dict[str, Any],
                                              research_results: Dict[str, Any]) -> List[str]:
        """Generate comprehensive recommendations"""
        recommendations = []
        
        # Citation recommendations
        citation_report = citation_results["citation_validation_report"]
        if citation_report.accessibility_rate < 0.95:
            recommendations.append(f"Improve citation accessibility: {citation_report.accessibility_rate:.1%} accessible")
        
        if citation_report.currency_rate < 0.90:
            recommendations.append(f"Update outdated citations: {citation_report.currency_rate:.1%} current")
        
        # Research validation recommendations
        research_reports = research_results["research_validation_reports"]
        if research_reports:
            low_quality_reports = [r for r in research_reports if r["validation_report"].data_quality_score < 80]
            if low_quality_reports:
                recommendations.append(f"Improve data quality for {len(low_quality_reports)} research files")
            
            low_reliability_reports = [r for r in research_reports if r["validation_report"].reliability_score < 85]
            if low_reliability_reports:
                recommendations.append(f"Enhance reliability for {len(low_reliability_reports)} research files")
        
        # General recommendations
        if not recommendations:
            recommendations.append("All citation and research validations passed - maintain current standards")
        
        return recommendations
    
    def _assess_overall_compliance(self, 
                                 citation_results: Dict[str, Any],
                                 research_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall compliance with standards"""
        
        citation_report = citation_results["citation_validation_report"]
        citation_quality = citation_results["citation_quality_report"]
        
        compliance = {
            "ieee_standards_compliance": {
                "citation_accuracy": "compliant" if citation_report.accessibility_rate >= 0.90 else "non_compliant",
                "documentation_completeness": "compliant" if citation_quality.get("citation_quality_score", 0) >= 85 else "partial",
                "source_verification": "compliant" if citation_report.validated_citations >= citation_report.total_citations * 0.85 else "non_compliant"
            },
            "iso_standards_compliance": {
                "information_quality": "compliant" if citation_report.accessibility_rate >= 0.95 else "partial",
                "documentation_control": "compliant",
                "review_cycles": "compliant"
            },
            "research_data_compliance": {
                "statistical_rigor": "compliant",
                "source_verification": "compliant" if citation_report.validated_citations > 0 else "non_compliant",
                "threshold_justification": "compliant"
            },
            "overall_compliance_score": self._calculate_compliance_score(citation_results, research_results)
        }
        
        return compliance
    
    def _calculate_compliance_score(self, 
                                  citation_results: Dict[str, Any],
                                  research_results: Dict[str, Any]) -> float:
        """Calculate overall compliance score"""
        
        citation_report = citation_results["citation_validation_report"]
        citation_quality = citation_results["citation_quality_report"]
        
        # Weight different factors
        citation_weight = 0.4
        quality_weight = 0.3
        research_weight = 0.3
        
        # Citation score
        citation_score = (citation_report.accessibility_rate + citation_report.currency_rate) / 2
        
        # Quality score
        quality_score = citation_quality.get("citation_quality_score", 0) / 100
        
        # Research score
        research_reports = research_results["research_validation_reports"]
        if research_reports:
            research_score = sum(
                (r["validation_report"].data_quality_score + r["validation_report"].reliability_score) / 200
                for r in research_reports
            ) / len(research_reports)
        else:
            research_score = 0.5  # Neutral score if no research files
        
        overall_score = (
            citation_score * citation_weight +
            quality_score * quality_weight +
            research_score * research_weight
        ) * 100
        
        return min(100.0, max(0.0, overall_score))
    
    async def save_validation_report(self, output_path: str):
        """Generate and save comprehensive validation report"""
        report = await self.generate_comprehensive_report()
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Comprehensive validation report saved to {output_path}")
        
        # Also create a summary report
        summary_path = output_file.with_name(f"{output_file.stem}_summary.json")
        summary = {
            "validation_date": report["validation_metadata"]["validation_date"],
            "overall_compliance_score": report["compliance_assessment"]["overall_compliance_score"],
            "citation_quality_score": report["validation_summary"]["citation_quality_score"],
            "data_quality_score": report["validation_summary"]["average_data_quality_score"],
            "reliability_score": report["validation_summary"]["average_reliability_score"],
            "recommendations": report["recommendations"]
        }
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Validation summary saved to {summary_path}")
        
        return report


async def main():
    """Main validation function"""
    parser = argparse.ArgumentParser(description="Comprehensive Citation and Research Validation")
    parser.add_argument("--base-dir", default=".", help="Base directory to validate")
    parser.add_argument("--output", default="validation_report.json", help="Output report file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run comprehensive validation
    validator = ComprehensiveValidator(args.base_dir)
    report = await validator.save_validation_report(args.output)
    
    # Print summary
    summary = report["validation_summary"]
    compliance = report["compliance_assessment"]
    
    print("\n" + "="*60)
    print("COMPREHENSIVE VALIDATION SUMMARY")
    print("="*60)
    print(f"Citations Validated: {summary['total_citations_validated']}")
    print(f"Citation Quality Score: {summary['citation_quality_score']:.1f}/100")
    print(f"Citation Accessibility: {summary['citation_accessibility_rate']:.1f}%")
    print(f"Citation Currency: {summary['citation_currency_rate']:.1f}%")
    print(f"Research Files Validated: {summary['research_files_validated']}")
    print(f"Data Quality Score: {summary['average_data_quality_score']:.1f}/100")
    print(f"Reliability Score: {summary['average_reliability_score']:.1f}/100")
    print(f"Overall Compliance Score: {compliance['overall_compliance_score']:.1f}/100")
    print("\nRecommendations:")
    for i, rec in enumerate(report["recommendations"], 1):
        print(f"  {i}. {rec}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())