#!/usr/bin/env python3
"""
TDD State Tracker - Enforces Test-Driven Development workflow
Inspired by tdd-guard, adapted for AutoCoder
"""
import enum
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


class TDDPhase(enum.Enum):
    """TDD workflow phases"""
    INIT = "INIT"           # Initial state
    RED = "RED"             # Writing failing tests
    GREEN = "GREEN"         # Making tests pass
    REFACTOR = "REFACTOR"   # Improving code
    COMPLETE = "COMPLETE"   # Feature complete


class TDDViolation(Exception):
    """Raised when TDD workflow is violated"""
    pass


@dataclass
class TestResult:
    """Test execution result"""
    test_name: str
    passed: bool
    duration: float
    error: Optional[str] = None
    file_path: Optional[str] = None


@dataclass
class TDDSession:
    """TDD session tracking"""
    feature_name: str
    start_time: datetime
    current_phase: TDDPhase
    test_files: List[str] = field(default_factory=list)
    implementation_files: List[str] = field(default_factory=list)
    test_results: List[TestResult] = field(default_factory=list)
    phase_history: List[Tuple[TDDPhase, datetime]] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)


class TDDStateTracker:
    """Track and enforce TDD workflow states"""
    
    def __init__(self, session_file: Path = None):
        """Initialize TDD state tracker"""
        self.session_file = session_file or Path(".tdd_session.json")
        self.current_session: Optional[TDDSession] = None
        self.load_session()
    
    def load_session(self):
        """Load existing TDD session if available"""
        if self.session_file.exists():
            try:
                with open(self.session_file, 'r') as f:
                    data = json.load(f)
                    self.current_session = TDDSession(
                        feature_name=data['feature_name'],
                        start_time=datetime.fromisoformat(data['start_time']),
                        current_phase=TDDPhase(data['current_phase']),
                        test_files=data.get('test_files', []),
                        implementation_files=data.get('implementation_files', []),
                        test_results=[],  # Don't persist test results
                        phase_history=[(TDDPhase(p), datetime.fromisoformat(t)) 
                                     for p, t in data.get('phase_history', [])],
                        violations=data.get('violations', [])
                    )
            except Exception:
                # If loading fails, start fresh
                self.current_session = None
    
    def save_session(self):
        """Save current TDD session"""
        if self.current_session:
            data = {
                'feature_name': self.current_session.feature_name,
                'start_time': self.current_session.start_time.isoformat(),
                'current_phase': self.current_session.current_phase.value,
                'test_files': self.current_session.test_files,
                'implementation_files': self.current_session.implementation_files,
                'phase_history': [(p.value, t.isoformat()) 
                                for p, t in self.current_session.phase_history],
                'violations': self.current_session.violations
            }
            with open(self.session_file, 'w') as f:
                json.dump(data, f, indent=2)
    
    def start_session(self, feature_name: str):
        """Start a new TDD session"""
        self.current_session = TDDSession(
            feature_name=feature_name,
            start_time=datetime.now(),
            current_phase=TDDPhase.INIT,
            phase_history=[(TDDPhase.INIT, datetime.now())]
        )
        self.save_session()
        return self.current_session
    
    def end_session(self):
        """End current TDD session"""
        if self.current_session:
            self.transition_to(TDDPhase.COMPLETE)
            self.save_session()
            # Archive session
            archive_path = Path(f".tdd_history/{self.current_session.feature_name}_{int(time.time())}.json")
            archive_path.parent.mkdir(exist_ok=True)
            self.session_file.rename(archive_path)
            self.current_session = None
    
    def get_current_phase(self) -> Optional[TDDPhase]:
        """Get current TDD phase"""
        return self.current_session.current_phase if self.current_session else None
    
    def transition_to(self, new_phase: TDDPhase):
        """Transition to new TDD phase"""
        if not self.current_session:
            raise TDDViolation("No active TDD session")
        
        current = self.current_session.current_phase
        
        # Validate transition
        if not self._is_valid_transition(current, new_phase):
            violation = f"Invalid transition: {current.value} -> {new_phase.value}"
            self.current_session.violations.append(violation)
            self.save_session()
            raise TDDViolation(violation)
        
        # Record transition
        self.current_session.current_phase = new_phase
        self.current_session.phase_history.append((new_phase, datetime.now()))
        self.save_session()
    
    def _is_valid_transition(self, from_phase: TDDPhase, to_phase: TDDPhase) -> bool:
        """Check if phase transition is valid"""
        valid_transitions = {
            TDDPhase.INIT: [TDDPhase.RED],
            TDDPhase.RED: [TDDPhase.GREEN, TDDPhase.RED],  # Can write more tests
            TDDPhase.GREEN: [TDDPhase.REFACTOR, TDDPhase.RED, TDDPhase.COMPLETE],
            TDDPhase.REFACTOR: [TDDPhase.GREEN, TDDPhase.RED, TDDPhase.COMPLETE],
            TDDPhase.COMPLETE: []
        }
        return to_phase in valid_transitions.get(from_phase, [])
    
    def validate_file_operation(self, file_path: str, operation: str) -> bool:
        """Validate file operation against TDD rules"""
        if not self.current_session:
            return True  # No session, no restrictions
        
        file_path = Path(file_path)
        is_test = self._is_test_file(file_path)
        phase = self.current_session.current_phase
        
        # Track files
        if is_test and str(file_path) not in self.current_session.test_files:
            self.current_session.test_files.append(str(file_path))
        elif not is_test and str(file_path) not in self.current_session.implementation_files:
            self.current_session.implementation_files.append(str(file_path))
        
        # Validation rules
        if operation in ['WRITE', 'CREATE']:
            if not is_test and phase == TDDPhase.RED:
                violation = f"Cannot write implementation during RED phase: {file_path}"
                self.current_session.violations.append(violation)
                self.save_session()
                raise TDDViolation(violation)
            
            if is_test and phase == TDDPhase.GREEN:
                # Writing new tests in GREEN phase triggers transition to RED
                self.transition_to(TDDPhase.RED)
        
        return True
    
    def _is_test_file(self, file_path: Path) -> bool:
        """Check if file is a test file"""
        return 'test' in file_path.name.lower() or file_path.parts and 'tests' in file_path.parts
    
    def record_test_results(self, results: List[TestResult]):
        """Record test execution results"""
        if not self.current_session:
            return
        
        self.current_session.test_results = results
        
        # Analyze results for phase transitions
        all_pass = all(r.passed for r in results)
        any_fail = any(not r.passed for r in results)
        
        phase = self.current_session.current_phase
        
        if phase == TDDPhase.RED and any_fail:
            # Good - tests are failing as expected
            pass
        elif phase == TDDPhase.RED and all_pass and results:
            # Tests unexpectedly passing - likely not following TDD
            print("⚠️ WARNING: Tests passing in RED phase - ensure tests fail first!")
        elif phase == TDDPhase.GREEN and all_pass and results:
            # Good - tests are passing
            pass
        elif phase == TDDPhase.GREEN and any_fail:
            # Still have failing tests
            print("❌ Tests still failing in GREEN phase")
        elif phase == TDDPhase.REFACTOR and any_fail:
            # Refactoring broke tests!
            violation = "Refactoring broke tests - revert changes!"
            self.current_session.violations.append(violation)
            self.save_session()
            print(f"❌ {violation}")
    
    def suggest_next_action(self) -> str:
        """Suggest next action based on current state"""
        if not self.current_session:
            return "Start a new TDD session with: tdd start <feature_name>"
        
        phase = self.current_session.current_phase
        results = self.current_session.test_results
        
        suggestions = {
            TDDPhase.INIT: "Write your first failing test",
            TDDPhase.RED: "Run tests to ensure they fail, then write minimal code to pass",
            TDDPhase.GREEN: "Consider refactoring or write more tests",
            TDDPhase.REFACTOR: "Improve code quality while keeping tests green",
            TDDPhase.COMPLETE: "Feature complete! Start a new session for next feature"
        }
        
        # More specific suggestions based on test results
        if phase == TDDPhase.RED and results and all(r.passed for r in results):
            return "⚠️ Tests are passing! Write a test that fails for the feature you want"
        elif phase == TDDPhase.GREEN and results and any(not r.passed for r in results):
            return "Fix the failing tests before proceeding"
        
        return suggestions.get(phase, "Continue with TDD workflow")
    
    def get_session_summary(self) -> Dict:
        """Get current session summary"""
        if not self.current_session:
            return {"status": "No active session"}
        
        duration = datetime.now() - self.current_session.start_time
        
        return {
            "feature": self.current_session.feature_name,
            "phase": self.current_session.current_phase.value,
            "duration": str(duration).split('.')[0],
            "test_files": len(self.current_session.test_files),
            "implementation_files": len(self.current_session.implementation_files),
            "violations": len(self.current_session.violations),
            "phase_history": [p.value for p, _ in self.current_session.phase_history],
            "next_action": self.suggest_next_action()
        }
    
    def validate_refactoring(self, before_tests: List[TestResult], after_tests: List[TestResult]):
        """Validate that refactoring didn't break tests"""
        if not self.current_session or self.current_session.current_phase != TDDPhase.REFACTOR:
            return
        
        # All tests that passed before should still pass
        before_passing = {t.test_name for t in before_tests if t.passed}
        after_passing = {t.test_name for t in after_tests if t.passed}
        
        broken_tests = before_passing - after_passing
        if broken_tests:
            violation = f"Refactoring broke {len(broken_tests)} tests: {', '.join(broken_tests)}"
            self.current_session.violations.append(violation)
            self.save_session()
            raise TDDViolation(violation)
    
    def record_success(self, description: str, mutation_score: float = None):
        """Record a successful TDD cycle completion with optional mutation testing score"""
        if not self.current_session:
            raise TDDViolation("No active TDD session")
            
        if self.current_session.current_phase not in [TDDPhase.REFACTOR, TDDPhase.GREEN]:
            # Allow recording success from mutation testing phase as well
            if mutation_score is None:
                raise TDDViolation("Can only record success after GREEN/REFACTOR phase or with mutation testing results")
        
        success_record = {
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "phase": self.current_session.current_phase.value,
            "session_duration": (datetime.now() - self.current_session.start_time).total_seconds()
        }
        
        if mutation_score is not None:
            success_record["mutation_score"] = mutation_score
            success_record["quality_level"] = self._assess_quality_level(mutation_score)
        
        # Add success record to session
        if not hasattr(self.current_session, 'successes'):
            self.current_session.successes = []
        self.current_session.successes.append(success_record)
        
        self.save_session()
        
        if mutation_score is not None:
            print(f"✅ TDD Success recorded with {mutation_score:.1%} mutation score: {description}")
        else:
            print(f"✅ TDD Success recorded: {description}")
    
    def _assess_quality_level(self, mutation_score: float) -> str:
        """Assess quality level based on mutation score"""
        if mutation_score >= 0.9:
            return "excellent"
        elif mutation_score >= 0.8:
            return "good"
        elif mutation_score >= 0.6:
            return "fair"
        else:
            return "poor"
    
    def get_mutation_testing_guidance(self, mutation_score: float) -> str:
        """Provide TDD guidance based on mutation testing results"""
        if mutation_score >= 0.85:
            return "🎯 Excellent TDD practice! Your tests are high quality."
        elif mutation_score >= 0.7:
            return "🔄 Good TDD, but consider adding tests for survived mutations."
        elif mutation_score >= 0.5:
            return "🔴 Return to RED phase - add more comprehensive tests."
        else:
            return "⚠️ TDD cycle needs significant improvement - test quality is poor."


# Global instance for easy access
_tracker = None

def get_tracker() -> TDDStateTracker:
    """Get global TDD state tracker instance"""
    global _tracker
    if _tracker is None:
        _tracker = TDDStateTracker()
    return _tracker