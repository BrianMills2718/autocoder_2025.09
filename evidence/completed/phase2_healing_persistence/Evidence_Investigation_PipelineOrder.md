135:            raw_blueprint = self.healer.heal_blueprint(raw_blueprint)
141:            self._validate_system_structure(raw_blueprint)
146:            system_blueprint = self.port_generator.auto_generate_ports(system_blueprint)
148:            self._validate_system_semantics(system_blueprint)
190:            combined_blueprint = self.port_generator.auto_generate_ports(combined_blueprint)
193:            self._validate_system_semantics(combined_blueprint)
342:    def _validate_system_structure(self, blueprint: Dict[str, Any]) -> None:
606:    def _validate_system_semantics(self, system_blueprint: ParsedSystemBlueprint) -> None:
612:        self._validate_unique_component_names(system.components)
615:        self._validate_binding_references(system.components, system.bindings)
618:        self._validate_schema_compatibility(system.components, system.bindings, system_blueprint.schemas)
621:        self._validate_resource_conflicts(system.components)
624:        self._validate_component_type_constraints(system.components, system.bindings)
627:        self._validate_architectural_patterns(system_blueprint)
629:    def _validate_unique_component_names(self, components: List[ParsedComponent]) -> None:
649:    def _validate_binding_references(self, components: List[ParsedComponent], bindings: List[ParsedBinding]) -> None:
698:    def _validate_schema_compatibility(self, components: List[ParsedComponent], 
795:    def _validate_resource_conflicts(self, components: List[ParsedComponent]) -> None:
860:            self._validate_resource_conflicts_original(components)
862:    def _validate_resource_conflicts_original(self, components: List[ParsedComponent]) -> None:
875:    def _validate_component_type_constraints(self, components: List[ParsedComponent], 
900:    def _validate_architectural_patterns(self, system_blueprint: ParsedSystemBlueprint) -> None:
