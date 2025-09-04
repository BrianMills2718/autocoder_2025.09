# Validation module - import from the validation.py file at autocoder level
import importlib.util
import os

# Import from the validation.py file directly 
module_path = os.path.join(os.path.dirname(__file__), '..', 'validation.py')
spec = importlib.util.spec_from_file_location("validation_module", module_path)
validation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation_module)

ConstraintValidator = validation_module.ConstraintValidator
ValidationResult = validation_module.ValidationResult 
ValidationError = validation_module.ValidationError