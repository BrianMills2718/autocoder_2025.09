autocoder_cc/deployment/deployment_manager.py:            shutil.rmtree(output_dir, ignore_errors=True)
autocoder_cc/coverage_html/z_bcac44b5d637f65d_structure_generator_py.html:    <p class="mis show_mis"><span class="n"><a id="t89" href="#t89">89</a></span><span class="t">        <span class="nam">gitignore_content</span> <span class="op">=</span> <span class="str">"""# Python</span>&nbsp;</span><span class="r"></span></p>
autocoder_cc/coverage_html/z_bcac44b5d637f65d_structure_generator_py.html:    <p class="mis show_mis"><span class="n"><a id="t126" href="#t126">126</a></span><span class="t">        <span class="op">(</span><span class="nam">project_dir</span> <span class="op">/</span> <span class="str">'.gitignore'</span><span class="op">)</span><span class="op">.</span><span class="nam">write_text</span><span class="op">(</span><span class="nam">gitignore_content</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
autocoder_cc/generators/scaffold/structure_generator.py:        gitignore_content = """# Python
autocoder_cc/generators/scaffold/structure_generator.py:        (project_dir / '.gitignore').write_text(gitignore_content)
autocoder_cc/tools/documentation/gemini_doc_review.py:def gather_files(paths: Iterable[str], ignore_patterns: Optional[List[str]] = None) -> List[Path]:
autocoder_cc/tools/documentation/gemini_doc_review.py:    recursively. *ignore_patterns* may contain simple Unix shell-style globs
autocoder_cc/tools/documentation/gemini_doc_review.py:    ignore_patterns = ignore_patterns or []
autocoder_cc/tools/documentation/gemini_doc_review.py:        return any(p.match(pattern) for pattern in ignore_patterns)
autocoder_cc/tools/documentation/enhanced_doc_health_dashboard.py:            if self.config.get("ignore_md_syntax_errors", False):
autocoder_cc/tools/gemini_validator/.gemini-phase3-validation.yaml:ignore_patterns:
autocoder_cc/tools/gemini_validator/.gemini-claims-validation.yaml:ignore_patterns:
autocoder_cc/tools/gemini_validator/.gemini-codebase-review.yaml:ignore_patterns:
autocoder_cc/tools/gemini_validator/gemini_cycle_review.py:                     ignore_patterns: Optional[list[str]] = None) -> Path:
autocoder_cc/tools/gemini_validator/gemini_cycle_review.py:        if ignore_patterns:
autocoder_cc/tools/gemini_validator/gemini_cycle_review.py:            ignore_pattern = ",".join(ignore_patterns)
autocoder_cc/tools/gemini_validator/gemini_cycle_review.py:            cmd.extend(["--ignore", ignore_pattern])
autocoder_cc/tools/gemini_validator/gemini_cycle_review.py:              ignore_patterns: Optional[list[str]] = None,
autocoder_cc/tools/gemini_validator/gemini_cycle_review.py:            repomix_file = self.run_repomix(project_path, output_format, ignore_patterns)
autocoder_cc/tools/gemini_validator/gemini_cycle_review.py:                config.ignore_patterns.extend(args.ignore)
