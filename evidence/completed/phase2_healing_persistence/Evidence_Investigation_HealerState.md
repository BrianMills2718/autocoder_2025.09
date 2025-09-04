19:        self.validator = ArchitecturalValidator()
20:        self.rejected_bindings = set()  # Track what we've already rejected
21:        self.generated_bindings = set()  # Track what we've already generated
23:        self.healing_history = []  # Track healing operations across attempts
24:        self.stagnation_count = 0  # Track when no progress is made
71:            self.stagnation_count = 0
23:        self.healing_history = []  # Track healing operations across attempts
24:        self.stagnation_count = 0  # Track when no progress is made
64:            self.stagnation_count += 1
65:        elif self.healing_history and operations == self.healing_history[-1]:
67:            self.stagnation_count += 1
71:            self.stagnation_count = 0
73:        # Add current operations to history
74:        self.healing_history.append(operations.copy() if operations else operations)
76:        # Stagnation if we've made no progress for 2 attempts
77:        if self.stagnation_count >= 2:
78:            self.logger.warning(f"Healing stagnated after {len(self.healing_history)} attempts")
167:            # Clear the generated/rejected sets for next attempt to allow retrying with different strategies
168:            # But keep the history to track patterns
169:            if self.stagnation_count >= 3:
170:                logger.error("Maximum stagnation count reached - stopping healing to prevent infinite loops")
