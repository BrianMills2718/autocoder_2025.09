#!/usr/bin/env python3
"""
Dependency Graph Visualization for Autocoder CC

Provides visualization and analysis of dependency graphs,
including circular dependency detection and graphical output.
"""
import json
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict, deque
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
import logging

from autocoder_cc.observability import get_logger


@dataclass
class DependencyNode:
    """Represents a node in the dependency graph"""
    name: str
    module_type: str  # interface, implementation, factory
    lifecycle: str    # singleton, transient, scoped
    dependencies: List[str]
    metadata: Dict[str, Any]


@dataclass
class DependencyCycle:
    """Represents a circular dependency"""
    nodes: List[str]
    
    def __str__(self) -> str:
        return " -> ".join(self.nodes + [self.nodes[0]])


class DependencyGraphAnalyzer:
    """Analyzes dependency graphs for issues and patterns"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, DependencyNode] = {}
        
    def add_node(
        self,
        name: str,
        module_type: str,
        lifecycle: str,
        dependencies: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a node to the dependency graph"""
        node = DependencyNode(
            name=name,
            module_type=module_type,
            lifecycle=lifecycle,
            dependencies=dependencies,
            metadata=metadata or {}
        )
        
        self.nodes[name] = node
        self.graph.add_node(name, **node.__dict__)
        
        # Add edges for dependencies
        for dep in dependencies:
            self.graph.add_edge(name, dep)
    
    def build_from_container(self, container: Any) -> None:
        """Build graph from dependency container"""
        graph_data = container.get_dependency_graph()
        registrations = container.get_all_registrations()
        
        for interface, registration in registrations.items():
            name = interface.__name__
            
            self.add_node(
                name=name,
                module_type="interface" if hasattr(interface, '__abstractmethods__') else "implementation",
                lifecycle=registration.lifecycle.value,
                dependencies=graph_data.get(name, []),
                metadata={
                    "resolution_count": registration.metadata.resolution_count,
                    "average_time_ms": registration.metadata.average_resolution_time_ms,
                    "tags": registration.metadata.tags,
                    "description": registration.metadata.description
                }
            )
    
    def find_circular_dependencies(self) -> List[DependencyCycle]:
        """Find all circular dependencies in the graph"""
        cycles = []
        
        try:
            # Find all simple cycles
            simple_cycles = list(nx.simple_cycles(self.graph))
            
            for cycle in simple_cycles:
                cycles.append(DependencyCycle(nodes=cycle))
                
        except nx.NetworkXNoCycle:
            # No cycles found
            pass
        
        return cycles
    
    def find_dependency_chains(self, start_node: str) -> Dict[str, List[str]]:
        """Find all dependency chains from a starting node"""
        chains = {}
        
        if start_node not in self.graph:
            return chains
        
        # BFS to find all paths
        queue = deque([(start_node, [start_node])])
        visited = set()
        
        while queue:
            current, path = queue.popleft()
            
            if current in visited:
                continue
            visited.add(current)
            
            # Get dependencies
            for neighbor in self.graph.successors(current):
                new_path = path + [neighbor]
                chains[neighbor] = new_path
                
                if neighbor not in visited:
                    queue.append((neighbor, new_path))
        
        return chains
    
    def get_dependency_layers(self) -> List[Set[str]]:
        """Get dependency layers (topological ordering)"""
        layers = []
        
        try:
            # Create a copy for manipulation
            remaining_graph = self.graph.copy()
            
            while remaining_graph:
                # Find nodes with no dependencies
                layer = {
                    node for node in remaining_graph.nodes()
                    if remaining_graph.out_degree(node) == 0
                }
                
                if not layer:
                    # Circular dependency exists
                    break
                
                layers.append(layer)
                remaining_graph.remove_nodes_from(layer)
            
        except Exception as e:
            self.logger.warning(f"Error computing dependency layers: {e}")
        
        return layers
    
    def get_dependency_stats(self) -> Dict[str, Any]:
        """Get statistics about the dependency graph"""
        stats = {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "average_dependencies": sum(
                self.graph.out_degree(n) for n in self.graph.nodes()
            ) / max(self.graph.number_of_nodes(), 1),
            "max_dependencies": max(
                (self.graph.out_degree(n) for n in self.graph.nodes()),
                default=0
            ),
            "circular_dependencies": len(self.find_circular_dependencies()),
            "dependency_layers": len(self.get_dependency_layers()),
            "isolated_nodes": len(list(nx.isolates(self.graph))),
            "hub_nodes": self._find_hub_nodes(threshold=5)
        }
        
        # Lifecycle distribution
        lifecycle_dist = defaultdict(int)
        for node in self.nodes.values():
            lifecycle_dist[node.lifecycle] += 1
        stats["lifecycle_distribution"] = dict(lifecycle_dist)
        
        return stats
    
    def _find_hub_nodes(self, threshold: int = 5) -> List[Tuple[str, int]]:
        """Find nodes with many dependencies (potential issues)"""
        hubs = []
        
        for node in self.graph.nodes():
            out_degree = self.graph.out_degree(node)
            if out_degree >= threshold:
                hubs.append((node, out_degree))
        
        return sorted(hubs, key=lambda x: x[1], reverse=True)
    
    def visualize(
        self,
        output_path: Optional[Path] = None,
        layout: str = "hierarchical",
        show_labels: bool = True,
        highlight_cycles: bool = True
    ) -> None:
        """Visualize the dependency graph"""
        plt.figure(figsize=(16, 12))
        
        # Choose layout algorithm
        if layout == "hierarchical":
            # Try to create hierarchical layout based on dependency layers
            layers = self.get_dependency_layers()
            pos = self._hierarchical_layout(layers)
        elif layout == "spring":
            pos = nx.spring_layout(self.graph, k=2, iterations=50)
        elif layout == "circular":
            pos = nx.circular_layout(self.graph)
        else:
            pos = nx.kamada_kawai_layout(self.graph)
        
        # Color nodes by lifecycle
        node_colors = []
        for node in self.graph.nodes():
            if node in self.nodes:
                lifecycle = self.nodes[node].lifecycle
                if lifecycle == "singleton":
                    node_colors.append("#4CAF50")  # Green
                elif lifecycle == "transient":
                    node_colors.append("#2196F3")  # Blue
                elif lifecycle == "scoped":
                    node_colors.append("#FF9800")  # Orange
                else:
                    node_colors.append("#9E9E9E")  # Gray
            else:
                node_colors.append("#9E9E9E")
        
        # Draw nodes
        nx.draw_networkx_nodes(
            self.graph,
            pos,
            node_color=node_colors,
            node_size=1000,
            alpha=0.8
        )
        
        # Draw edges
        edge_colors = []
        edge_widths = []
        
        if highlight_cycles:
            # Find edges that are part of cycles
            cycles = self.find_circular_dependencies()
            cycle_edges = set()
            
            for cycle in cycles:
                for i in range(len(cycle.nodes)):
                    u = cycle.nodes[i]
                    v = cycle.nodes[(i + 1) % len(cycle.nodes)]
                    cycle_edges.add((u, v))
        
        for u, v in self.graph.edges():
            if highlight_cycles and (u, v) in cycle_edges:
                edge_colors.append("#F44336")  # Red for cycles
                edge_widths.append(3.0)
            else:
                edge_colors.append("#757575")  # Gray for normal
                edge_widths.append(1.0)
        
        nx.draw_networkx_edges(
            self.graph,
            pos,
            edge_color=edge_colors,
            width=edge_widths,
            alpha=0.6,
            arrows=True,
            arrowsize=20,
            arrowstyle="->"
        )
        
        # Draw labels
        if show_labels:
            nx.draw_networkx_labels(
                self.graph,
                pos,
                font_size=8,
                font_weight="bold"
            )
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor="#4CAF50", label="Singleton"),
            Patch(facecolor="#2196F3", label="Transient"),
            Patch(facecolor="#FF9800", label="Scoped"),
            Patch(facecolor="#F44336", label="Circular Dependency")
        ]
        plt.legend(handles=legend_elements, loc="upper left")
        
        plt.title("Dependency Graph Visualization", fontsize=16)
        plt.axis("off")
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            self.logger.info(f"Dependency graph saved to {output_path}")
        else:
            plt.show()
    
    def _hierarchical_layout(self, layers: List[Set[str]]) -> Dict[str, Tuple[float, float]]:
        """Create hierarchical layout based on dependency layers"""
        pos = {}
        
        if not layers:
            # Fallback to spring layout
            return nx.spring_layout(self.graph)
        
        y_spacing = 2.0
        
        for layer_idx, layer in enumerate(layers):
            layer_nodes = list(layer)
            x_spacing = 2.0
            
            # Center the layer horizontally
            total_width = (len(layer_nodes) - 1) * x_spacing
            start_x = -total_width / 2
            
            for node_idx, node in enumerate(layer_nodes):
                x = start_x + node_idx * x_spacing
                y = -layer_idx * y_spacing
                pos[node] = (x, y)
        
        return pos
    
    def export_to_dot(self, output_path: Path) -> None:
        """Export graph to DOT format for Graphviz"""
        from networkx.drawing.nx_agraph import write_dot
        
        # Add attributes for visualization
        for node in self.graph.nodes():
            if node in self.nodes:
                node_data = self.nodes[node]
                self.graph.nodes[node]["label"] = f"{node}\\n({node_data.lifecycle})"
                
                # Color based on lifecycle
                if node_data.lifecycle == "singleton":
                    self.graph.nodes[node]["fillcolor"] = "lightgreen"
                elif node_data.lifecycle == "transient":
                    self.graph.nodes[node]["fillcolor"] = "lightblue"
                elif node_data.lifecycle == "scoped":
                    self.graph.nodes[node]["fillcolor"] = "lightyellow"
                
                self.graph.nodes[node]["style"] = "filled"
        
        # Highlight circular dependencies
        cycles = self.find_circular_dependencies()
        for cycle in cycles:
            for i in range(len(cycle.nodes)):
                u = cycle.nodes[i]
                v = cycle.nodes[(i + 1) % len(cycle.nodes)]
                if self.graph.has_edge(u, v):
                    self.graph.edges[u, v]["color"] = "red"
                    self.graph.edges[u, v]["penwidth"] = "2"
        
        write_dot(self.graph, output_path)
        self.logger.info(f"Graph exported to DOT format: {output_path}")
    
    def generate_report(self) -> str:
        """Generate a comprehensive dependency analysis report"""
        lines = [
            "Dependency Graph Analysis Report",
            "=" * 50,
            ""
        ]
        
        # Basic statistics
        stats = self.get_dependency_stats()
        lines.extend([
            "Graph Statistics:",
            "-" * 30,
            f"Total Nodes: {stats['total_nodes']}",
            f"Total Dependencies: {stats['total_edges']}",
            f"Average Dependencies per Node: {stats['average_dependencies']:.2f}",
            f"Maximum Dependencies: {stats['max_dependencies']}",
            f"Dependency Layers: {stats['dependency_layers']}",
            f"Isolated Nodes: {stats['isolated_nodes']}",
            ""
        ])
        
        # Lifecycle distribution
        lines.extend([
            "Lifecycle Distribution:",
            "-" * 30
        ])
        for lifecycle, count in stats['lifecycle_distribution'].items():
            percentage = (count / stats['total_nodes']) * 100
            lines.append(f"{lifecycle.capitalize()}: {count} ({percentage:.1f}%)")
        lines.append("")
        
        # Circular dependencies
        cycles = self.find_circular_dependencies()
        lines.extend([
            "Circular Dependencies:",
            "-" * 30
        ])
        
        if cycles:
            for idx, cycle in enumerate(cycles, 1):
                lines.append(f"{idx}. {cycle}")
        else:
            lines.append("No circular dependencies detected ✓")
        lines.append("")
        
        # Hub nodes
        lines.extend([
            "High-Dependency Nodes (Potential Issues):",
            "-" * 30
        ])
        
        hubs = stats['hub_nodes']
        if hubs:
            for node, dep_count in hubs[:5]:  # Top 5
                lines.append(f"{node}: {dep_count} dependencies")
        else:
            lines.append("No high-dependency nodes found ✓")
        lines.append("")
        
        # Dependency layers
        layers = self.get_dependency_layers()
        lines.extend([
            "Dependency Layers (Bottom-up):",
            "-" * 30
        ])
        
        for idx, layer in enumerate(layers):
            lines.append(f"Layer {idx}: {', '.join(sorted(layer))}")
        
        return "\n".join(lines)


class DependencyGraphVisualizer:
    """High-level interface for dependency visualization"""
    
    def __init__(self, container: Any):
        self.container = container
        self.analyzer = DependencyGraphAnalyzer()
        self.logger = get_logger(self.__class__.__name__)
    
    def analyze_and_visualize(
        self,
        output_dir: Optional[Path] = None,
        formats: List[str] = ["png", "dot", "report"]
    ) -> Dict[str, Any]:
        """Perform complete dependency analysis and visualization"""
        # Build graph from container
        self.analyzer.build_from_container(self.container)
        
        results = {
            "stats": self.analyzer.get_dependency_stats(),
            "cycles": [str(c) for c in self.analyzer.find_circular_dependencies()],
            "layers": [list(layer) for layer in self.analyzer.get_dependency_layers()]
        }
        
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate visualizations
            if "png" in formats:
                self.analyzer.visualize(
                    output_path=output_dir / "dependency_graph.png",
                    layout="hierarchical"
                )
                results["png_path"] = str(output_dir / "dependency_graph.png")
            
            if "dot" in formats:
                self.analyzer.export_to_dot(output_dir / "dependency_graph.dot")
                results["dot_path"] = str(output_dir / "dependency_graph.dot")
            
            if "report" in formats:
                report = self.analyzer.generate_report()
                report_path = output_dir / "dependency_analysis.txt"
                report_path.write_text(report)
                results["report_path"] = str(report_path)
                results["report"] = report
            
            # Save JSON summary
            json_path = output_dir / "dependency_analysis.json"
            with open(json_path, "w") as f:
                json.dump(results, f, indent=2)
            results["json_path"] = str(json_path)
        
        return results