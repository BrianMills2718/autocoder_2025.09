#!/usr/bin/env python3
"""
Web UI Generator for Domain-Specific Interfaces
==============================================

Automatically generates web UIs for API endpoints based on domain objects and routes.
Creates forms, lists, and detail views that correspond to API functionality.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import re

class DomainUIGenerator:
    """
    Generates domain-specific web UIs for API endpoints.
    
    Takes API endpoint configuration and generates:
    - HTML templates for CRUD operations
    - Form interfaces for data entry
    - List views for displaying collections
    - Detail views for individual items
    """
    
    def __init__(self):
        self.supported_methods = {'GET', 'POST', 'PUT', 'DELETE'}
    
    def generate_ui_for_endpoints(
        self, 
        endpoints: List[Dict[str, Any]], 
        domain_name: str,
        component_name: str
    ) -> Dict[str, str]:
        """
        Generate complete UI templates for a set of API endpoints.
        
        Args:
            endpoints: List of endpoint configurations with path, method, description
            domain_name: The domain object name (e.g., 'notes', 'posts', 'users')
            component_name: The component name for routing
            
        Returns:
            Dict mapping template names to HTML content
        """
        ui_templates = {}
        
        # Extract domain info from endpoints
        domain_info = self._analyze_endpoints(endpoints, domain_name)
        
        # Generate main UI template that includes all views
        ui_templates['main_ui.html'] = self._generate_main_ui_template(
            domain_info, component_name
        )
        
        # Generate individual templates
        ui_templates['list_view.html'] = self._generate_list_view_template(domain_info)
        ui_templates['create_form.html'] = self._generate_create_form_template(domain_info)
        ui_templates['edit_form.html'] = self._generate_edit_form_template(domain_info)
        ui_templates['detail_view.html'] = self._generate_detail_view_template(domain_info)
        
        return ui_templates
    
    def _analyze_endpoints(self, endpoints: List[Dict[str, Any]], domain_name: str) -> Dict[str, Any]:
        """Analyze endpoints to extract domain structure and capabilities."""
        domain_info = {
            'name': domain_name,
            'singular': domain_name.rstrip('s'),  # Simple singularization
            'plural': domain_name if domain_name.endswith('s') else f"{domain_name}s",
            'has_list': False,
            'has_create': False,
            'has_read': False,
            'has_update': False,
            'has_delete': False,
            'fields': self._infer_fields_from_domain(domain_name),
            'base_path': f"/{domain_name}"
        }
        
        # Analyze what operations are available
        for endpoint in endpoints:
            method = endpoint.get('method', '').upper()
            path = endpoint.get('path', '')
            
            if method == 'GET' and not '{id}' in path:
                domain_info['has_list'] = True
            elif method == 'GET' and '{id}' in path:
                domain_info['has_read'] = True
            elif method == 'POST':
                domain_info['has_create'] = True
            elif method == 'PUT':
                domain_info['has_update'] = True
            elif method == 'DELETE':
                domain_info['has_delete'] = True
        
        return domain_info
    
    def _infer_fields_from_domain(self, domain_name: str) -> List[Dict[str, str]]:
        """Infer likely fields based on domain name."""
        common_fields = [
            {'name': 'id', 'type': 'hidden', 'label': 'ID'},
            {'name': 'created_at', 'type': 'text', 'label': 'Created', 'readonly': True}
        ]
        
        # Domain-specific field inference
        domain_fields = {
            'notes': [
                {'name': 'title', 'type': 'text', 'label': 'Title', 'required': True},
                {'name': 'content', 'type': 'textarea', 'label': 'Content', 'required': True},
                {'name': 'tags', 'type': 'text', 'label': 'Tags'}
            ],
            'posts': [
                {'name': 'title', 'type': 'text', 'label': 'Title', 'required': True},
                {'name': 'content', 'type': 'textarea', 'label': 'Content', 'required': True},
                {'name': 'author', 'type': 'text', 'label': 'Author'},
                {'name': 'published', 'type': 'checkbox', 'label': 'Published'}
            ],
            'users': [
                {'name': 'username', 'type': 'text', 'label': 'Username', 'required': True},
                {'name': 'email', 'type': 'email', 'label': 'Email', 'required': True},
                {'name': 'full_name', 'type': 'text', 'label': 'Full Name'},
                {'name': 'active', 'type': 'checkbox', 'label': 'Active'}
            ],
            'tasks': [
                {'name': 'title', 'type': 'text', 'label': 'Title', 'required': True},
                {'name': 'description', 'type': 'textarea', 'label': 'Description'},
                {'name': 'due_date', 'type': 'date', 'label': 'Due Date'},
                {'name': 'completed', 'type': 'checkbox', 'label': 'Completed'}
            ],
            'products': [
                {'name': 'name', 'type': 'text', 'label': 'Product Name', 'required': True},
                {'name': 'description', 'type': 'textarea', 'label': 'Description'},
                {'name': 'price', 'type': 'number', 'label': 'Price', 'step': '0.01'},
                {'name': 'sku', 'type': 'text', 'label': 'SKU'}
            ]
        }
        
        specific_fields = domain_fields.get(domain_name, [
            {'name': 'name', 'type': 'text', 'label': 'Name', 'required': True},
            {'name': 'description', 'type': 'textarea', 'label': 'Description'}
        ])
        
        return common_fields + specific_fields
    
    def _generate_edit_button_if_enabled(self, domain_info: Dict[str, Any]) -> str:
        """Generate edit button if update is enabled"""
        if domain_info['has_update']:
            return '<button class="btn btn-primary" onclick="editItem(\\\'${{item.id}}\\\')">Edit</button>'
        return ''
    
    def _generate_delete_button_if_enabled(self, domain_info: Dict[str, Any]) -> str:
        """Generate delete button if delete is enabled"""
        if domain_info['has_delete']:
            return '<button class="btn btn-danger" onclick="deleteItem(\\\'${{item.id}}\\\')">Delete</button>'
        return ''
    
    def _generate_complete_javascript(self, domain_info: Dict[str, Any], component_name: str) -> str:
        """Generate complete, working JavaScript for CRUD operations."""
        domain_name = domain_info['name']
        domain_singular = domain_info['singular']
        domain_plural = domain_info['plural']
        
        return f'''
        // Generated JavaScript for {domain_name} management - Production Ready
        const API_BASE = '/{component_name}';
        const DOMAIN_PATH = '/{domain_name}';
        
        // Tab management
        function showTab(tabName) {{
            console.log('Switching to tab:', tabName);
            
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.classList.remove('active');
            }});
            document.querySelectorAll('.tab-button').forEach(btn => {{
                btn.classList.remove('active');
            }});
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            if (event && event.target) {{
                event.target.classList.add('active');
            }} else {{
                // If called programmatically, find and activate the right button
                const button = document.querySelector(`[onclick*="showTab('${{tabName}})"]`);
                if (button) button.classList.add('active');
            }}
            
            // Load data if needed
            if (tabName === 'list') {{
                loadItems();
            }}
        }}
        
        // API interaction functions
        async function loadItems() {{
            try {{
                const response = await fetch(`${{API_BASE}}${{DOMAIN_PATH}}`);
                const data = await response.json();
                renderItemList(data);
            }} catch (error) {{
                showError('Failed to load {domain_plural}');
                console.error(error);
            }}
        }}
        
        function renderItemList(data) {{
            const listView = document.getElementById('list-view');
            const items = data.items || data.{domain_plural} || data || [];
            
            if (items.length === 0) {{
                listView.innerHTML = `
                    <div class="empty-state">
                        <h3>📝 No {domain_plural} found</h3>
                        <p>Get started by creating your first {domain_singular}!</p>
                        <button class="btn btn-primary" onclick="showTab('create')">Add {domain_singular.title()}</button>
                    </div>
                `;
                return;
            }}
            
            listView.innerHTML = `
                <ul class="item-list">
                    ${{items.map(item => `
                        <li class="item-card">
                            <div class="item-title">${{item.title || item.name || `{domain_singular.title()} #${{item.id}}`}}</div>
                            <div class="item-content">${{item.content || item.description || ''}}</div>
                            <div class="item-meta">
                                ${{item.tags ? `🏷️ ${{item.tags}}` : ''}}
                                ${{item.created_at ? `📅 Created: ${{new Date(item.created_at * 1000).toLocaleDateString()}}` : ''}}
                                ${{item.id ? `🆔 ID: ${{item.id}}` : ''}}
                            </div>
                            <div class="item-actions">
                                <button class="btn btn-secondary" onclick="viewItem('${{item.id}}')">View</button>
                                {self._generate_edit_button_if_enabled(domain_info)}
                                {self._generate_delete_button_if_enabled(domain_info)}
                            </div>
                        </li>
                    `).join('')}}
                </ul>
            `;
        }}
        
        // Create functionality
        async function handleCreateSubmit(event) {{
            event.preventDefault();
            const formData = new FormData(event.target);
            const data = Object.fromEntries(formData.entries());
            
            console.log('Creating {domain_singular}:', data);
            
            try {{
                const response = await fetch(`${{API_BASE}}${{DOMAIN_PATH}}`, {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(data)
                }});
                
                console.log('Response status:', response.status);
                
                if (response.ok) {{
                    const result = await response.json();
                    console.log('Created {domain_singular}:', result);
                    showSuccess('{domain_singular.title()} created successfully!');
                    document.getElementById('create-form').reset();
                    showTab('list');
                }} else {{
                    const error = await response.text();
                    console.error('Create failed:', error);
                    showError('Failed to create {domain_singular}: ' + response.status);
                }}
            }} catch (error) {{
                console.error('Create error:', error);
                showError('Failed to create {domain_singular}: ' + error.message);
            }}
        }}
        
        // View functionality
        async function viewItem(id) {{
            try {{
                const response = await fetch(`${{API_BASE}}${{DOMAIN_PATH}}/${{id}}`);
                if (response.ok) {{
                    const result = await response.json();
                    const item = result.item || result;
                    showDetailModal(item);
                }} else {{
                    showError('Failed to load {domain_singular} details');
                }}
            }} catch (error) {{
                showError('Failed to load {domain_singular} details');
                console.error(error);
            }}
        }}
        
        // Edit functionality
        async function editItem(id) {{
            try {{
                const response = await fetch(`${{API_BASE}}${{DOMAIN_PATH}}/${{id}}`);
                if (response.ok) {{
                    const result = await response.json();
                    const item = result.item || result;
                    showEditModal(item);
                }} else {{
                    showError('Failed to load {domain_singular} for editing');
                }}
            }} catch (error) {{
                showError('Failed to load {domain_singular} for editing');
                console.error(error);
            }}
        }}
        
        async function handleEditSubmit(event) {{
            event.preventDefault();
            
            const id = document.getElementById('edit-id').value;
            const data = {{}};
            
            // Collect form data dynamically based on domain fields
            {self._generate_edit_data_collection(domain_info)}
            
            console.log('Updating {domain_singular}:', id, data);
            
            try {{
                const response = await fetch(`${{API_BASE}}${{DOMAIN_PATH}}/${{id}}`, {{
                    method: 'PUT',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(data)
                }});
                
                if (response.ok) {{
                    const result = await response.json();
                    console.log('Updated {domain_singular}:', result);
                    showSuccess('{domain_singular.title()} updated successfully!');
                    closeEditModal();
                    loadItems();
                }} else {{
                    showError('Failed to update {domain_singular}: ' + response.status);
                }}
            }} catch (error) {{
                console.error('Update error:', error);
                showError('Failed to update {domain_singular}: ' + error.message);
            }}
        }}
        
        // Delete functionality
        async function deleteItem(id) {{
            if (!confirm('Are you sure you want to delete this {domain_singular}?')) return;
            
            try {{
                const response = await fetch(`${{API_BASE}}${{DOMAIN_PATH}}/${{id}}`, {{
                    method: 'DELETE'
                }});
                
                if (response.ok) {{
                    showSuccess('{domain_singular.title()} deleted successfully!');
                    loadItems();
                }} else {{
                    showError('Failed to delete {domain_singular}');
                }}
            }} catch (error) {{
                showError('Failed to delete {domain_singular}');
                console.error(error);
            }}
        }}
        
        // Modal management - Detail View
        function showDetailModal(item) {{
            console.log('Showing detail modal for item:', item);
            const modal = document.getElementById('detail-modal') || createDetailModal();
            
            // Populate modal with item data dynamically
            {self._generate_detail_population(domain_info)}
            
            // Set up edit button
            const editBtn = document.getElementById('detail-edit-btn');
            if (editBtn) {{
                editBtn.onclick = () => {{
                    closeDetailModal();
                    editItem(item.id);
                }};
            }}
            
            // Show the modal
            modal.style.display = 'block';
            console.log('Detail modal should be visible now');
        }}
        
        function closeDetailModal() {{
            const modal = document.getElementById('detail-modal');
            if (modal) modal.style.display = 'none';
        }}
        
        function createDetailModal() {{
            const modal = document.createElement('div');
            modal.id = 'detail-modal';
            modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; display: none;';
            modal.innerHTML = `{self._generate_detail_modal_html(domain_info)}`;
            document.body.appendChild(modal);
            return modal;
        }}
        
        // Modal management - Edit View
        function showEditModal(item) {{
            const modal = document.getElementById('edit-modal') || createEditModal();
            
            // Populate form with existing data
            {self._generate_edit_population(domain_info)}
            
            modal.style.display = 'block';
        }}
        
        function closeEditModal() {{
            const modal = document.getElementById('edit-modal');
            if (modal) modal.style.display = 'none';
        }}
        
        function createEditModal() {{
            const modal = document.createElement('div');
            modal.id = 'edit-modal';
            modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; display: none;';
            modal.innerHTML = `{self._generate_edit_modal_html(domain_info)}`;
            document.body.appendChild(modal);
            return modal;
        }}
        
        // Utility functions
        function showSuccess(message) {{
            showAlert(message, 'success');
        }}
        
        function showError(message) {{
            showAlert(message, 'error');
        }}
        
        function showAlert(message, type) {{
            const existingAlert = document.querySelector('.alert');
            if (existingAlert) existingAlert.remove();
            
            const alert = document.createElement('div');
            alert.className = `alert alert-${{type}}`;
            alert.textContent = message;
            
            document.querySelector('.container').insertBefore(alert, document.querySelector('.tabs'));
            
            setTimeout(() => alert.remove(), 5000);
        }}
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            loadItems();
        }});
        '''
    
    def _generate_detail_population(self, domain_info: Dict[str, Any]) -> str:
        """Generate code to populate detail modal with item data."""
        lines = []
        for field in domain_info['fields']:
            if field['name'] == 'id':
                lines.append(f"document.getElementById('detail-{field['name']}').textContent = item.{field['name']} || 'Unknown';")
            elif field['name'] == 'created_at':
                lines.append(f"document.getElementById('detail-{field['name']}').textContent = item.{field['name']} ? new Date(item.{field['name']} * 1000).toLocaleString() : 'Unknown';")
            else:
                lines.append(f"document.getElementById('detail-{field['name']}').textContent = item.{field['name']} || 'No {field['label'].lower()}';")
        return '\n            '.join(lines)
    
    def _generate_edit_population(self, domain_info: Dict[str, Any]) -> str:
        """Generate code to populate edit form with existing data."""
        lines = []
        for field in domain_info['fields']:
            if field['name'] not in ['created_at']:  # Skip readonly fields
                lines.append(f"document.getElementById('edit-{field['name']}').value = item.{field['name']} || '';")
        return '\n            '.join(lines)
    
    def _generate_edit_data_collection(self, domain_info: Dict[str, Any]) -> str:
        """Generate code to collect form data for editing."""
        lines = []
        for field in domain_info['fields']:
            if field['name'] not in ['id', 'created_at']:  # Skip system fields
                if field.get('type') == 'checkbox':
                    lines.append(f"data.{field['name']} = document.getElementById('edit-{field['name']}').checked;")
                else:
                    lines.append(f"data.{field['name']} = document.getElementById('edit-{field['name']}').value;")
        return '\n            '.join(lines)
    
    def _generate_detail_modal_html(self, domain_info: Dict[str, Any]) -> str:
        """Generate HTML for detail modal."""
        domain_singular = domain_info['singular']
        
        # Generate field displays
        field_displays = []
        for field in domain_info['fields']:
            if field['name'] == 'id':
                continue  # ID shown in header
            elif field['name'] == 'created_at':
                field_displays.append(f'''
                        <div style="margin-bottom: 1rem;">
                            <label style="font-weight: 600; color: #555; display: block; margin-bottom: 0.5rem;">📅 Created:</label>
                            <div id="detail-{field['name']}" style="background: #f8f9fa; padding: 0.5rem 1rem; border-radius: 6px; border: 2px solid #e9ecef; color: #6c757d;"></div>
                        </div>''')
            elif field.get('type') == 'textarea':
                field_displays.append(f'''
                        <div style="margin-bottom: 1.5rem;">
                            <label style="font-weight: 600; color: #555; display: block; margin-bottom: 0.5rem;">{field['label']}:</label>
                            <div id="detail-{field['name']}" style="background: #f8f9fa; padding: 1rem; border-radius: 6px; border: 2px solid #e9ecef; white-space: pre-wrap; min-height: 100px;"></div>
                        </div>''')
            else:
                field_displays.append(f'''
                        <div style="margin-bottom: 1rem;">
                            <label style="font-weight: 600; color: #555; display: block; margin-bottom: 0.5rem;">{field['label']}:</label>
                            <div id="detail-{field['name']}" style="background: #f8f9fa; padding: 0.5rem 1rem; border-radius: 6px; border: 2px solid #e9ecef; color: #667eea;"></div>
                        </div>''')
        
        return f'''
                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 2rem; border-radius: 8px; max-width: 600px; width: 90%; max-height: 80vh; overflow-y: auto;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                            <h2 style="margin: 0; color: #333;">📝 {domain_singular.title()} Details</h2>
                            <button onclick="closeDetailModal()" style="background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #666;">✕</button>
                        </div>
                        
                        <div style="margin-bottom: 1.5rem;">
                            <h3 id="detail-title" style="color: #667eea; margin-bottom: 0.5rem; font-size: 1.5rem;"></h3>
                            <div style="color: #6c757d; font-size: 0.9rem; margin-bottom: 1rem;">
                                🆔 ID: <span id="detail-id"></span>
                            </div>
                        </div>
                        
                        {''.join(field_displays)}
                        
                        <div style="display: flex; gap: 0.5rem;">
                            <button id="detail-edit-btn" class="btn btn-primary">Edit {domain_singular.title()}</button>
                            <button onclick="closeDetailModal()" class="btn btn-secondary">Close</button>
                        </div>
                    </div>
        '''.replace('\n                        ', '\n            ')
    
    def _generate_edit_modal_html(self, domain_info: Dict[str, Any]) -> str:
        """Generate HTML for edit modal."""
        domain_singular = domain_info['singular']
        
        # Generate form fields
        form_fields = []
        for field in domain_info['fields']:
            if field['name'] in ['id', 'created_at']:
                if field['name'] == 'id':
                    field_name = field['name']
                    form_fields.append(f'<input type="hidden" id="edit-{field_name}">')
                continue
                
            field_html = self._generate_form_field_for_edit(field)
            form_fields.append(field_html)
        
        return f'''
                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 2rem; border-radius: 8px; max-width: 600px; width: 90%;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                            <h2 style="margin: 0; color: #333;">✏️ Edit {domain_singular.title()}</h2>
                            <button onclick="closeEditModal()" style="background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #666;">✕</button>
                        </div>
                        
                        <form id="edit-form" onsubmit="handleEditSubmit(event)">
                            {''.join(form_fields)}
                            
                            <div style="display: flex; gap: 0.5rem; margin-top: 1.5rem;">
                                <button type="submit" class="btn btn-primary">Update {domain_singular.title()}</button>
                                <button type="button" onclick="closeEditModal()" class="btn btn-secondary">Cancel</button>
                            </div>
                        </form>
                    </div>
        '''.replace('\n                            ', '\n                ')
    
    def _generate_form_field_for_edit(self, field: Dict[str, str]) -> str:
        """Generate HTML for edit form field."""
        field_name = field['name']
        field_type = field.get('type', 'text')
        field_label = field.get('label', field_name.title())
        required = ' required' if field.get('required') else ''
        
        base_style = 'width: 100%; padding: 0.75rem; border: 2px solid #e9ecef; border-radius: 6px; font-size: 1rem;'
        
        if field_type == 'textarea':
            return f'''
                            <div class="form-group" style="margin-bottom: 1.5rem;">
                                <label for="edit-{field_name}" style="display: block; margin-bottom: 0.5rem; font-weight: 600; color: #555;">{field_label}</label>
                                <textarea id="edit-{field_name}" style="{base_style} min-height: 120px; resize: vertical;"{required}></textarea>
                            </div>'''
        elif field_type == 'checkbox':
            return f'''
                            <div class="form-group" style="margin-bottom: 1.5rem;">
                                <label style="display: flex; align-items: center; font-weight: 600; color: #555;">
                                    <input type="checkbox" id="edit-{field_name}" style="margin-right: 0.5rem;"{required}> {field_label}
                                </label>
                            </div>'''
        else:
            step_attr = f' step="{field["step"]}"' if field.get('step') else ''
            return f'''
                            <div class="form-group" style="margin-bottom: 1.5rem;">
                                <label for="edit-{field_name}" style="display: block; margin-bottom: 0.5rem; font-weight: 600; color: #555;">{field_label}</label>
                                <input type="{field_type}" id="edit-{field_name}" style="{base_style}"{required}{step_attr}>
                            </div>'''
    
    def _generate_main_ui_template(self, domain_info: Dict[str, Any], component_name: str) -> str:
        """Generate the main UI template that includes all views."""
        domain_name = domain_info['name']
        domain_singular = domain_info['singular']
        domain_plural = domain_info['plural']
        
        # Generate the complete JavaScript functionality
        javascript_code = self._generate_complete_javascript(domain_info, component_name)
        
        # Use simple string concatenation to avoid f-string issues
        html_template = self._build_html_template(domain_info, component_name, javascript_code)
        return html_template
    
    def _build_html_template(self, domain_info: Dict[str, Any], component_name: str, javascript_code: str) -> str:
        """Build HTML template using string replacement to avoid f-string syntax issues"""
        domain_name = domain_info['name']
        domain_singular = domain_info['singular'] 
        domain_plural = domain_info['plural']
        
        # Basic working HTML template with placeholders
        template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DOMAIN_TITLE Management</title>
    <style>
        body { font-family: -apple-system, sans-serif; margin: 40px; background: #f8f9fa; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 8px; text-align: center; margin-bottom: 2rem; }
        .header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
        .tabs { display: flex; background: white; border-radius: 8px; margin-bottom: 2rem; overflow: hidden; }
        .tab-button { flex: 1; padding: 1rem 2rem; background: none; border: none; cursor: pointer; font-size: 1rem; }
        .tab-button.active { background: #f8f9fa; border-bottom: 3px solid #667eea; color: #667eea; font-weight: 600; }
        .tab-content { background: white; border-radius: 8px; padding: 2rem; display: none; }
        .tab-content.active { display: block; }
        .form-group { margin-bottom: 1.5rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 600; color: #555; }
        .form-control { width: 100%; padding: 0.75rem; border: 2px solid #e9ecef; border-radius: 6px; font-size: 1rem; }
        .form-control:focus { outline: none; border-color: #667eea; }
        textarea.form-control { resize: vertical; min-height: 100px; }
        .btn { padding: 0.75rem 1.5rem; border: none; border-radius: 6px; font-size: 1rem; font-weight: 600; cursor: pointer; margin-right: 0.5rem; }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        .btn-danger { background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); color: white; }
        .item-list { list-style: none; }
        .item-card { background: #f8f9fa; border: 2px solid #e9ecef; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; }
        .item-title { font-size: 1.25rem; font-weight: 600; color: #333; margin-bottom: 0.5rem; }
        .item-content { color: #666; margin-bottom: 1rem; }
        .item-meta { color: #6c757d; font-size: 0.9rem; margin-bottom: 1rem; }
        .item-actions { display: flex; gap: 0.5rem; }
        .alert { padding: 1rem; border-radius: 6px; margin-bottom: 1rem; }
        .alert-success { background: #d4edda; color: #155724; border: 2px solid #c3e6cb; }
        .alert-error { background: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }
        .empty-state { text-align: center; padding: 3rem; color: #6c757d; }
        .empty-state h3 { font-size: 1.5rem; margin-bottom: 1rem; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 DOMAIN_TITLE Management</h1>
            <p>Interactive interface for managing your DOMAIN_NAME</p>
        </div>
        
        <div class="tabs">
            <button class="tab-button active" onclick="showTab('list')">📋 View DOMAIN_TITLE</button>
            <button class="tab-button" onclick="showTab('create')">➕ Add DOMAIN_SINGULAR</button>
        </div>
        
        <div id="list-tab" class="tab-content active">
            <div id="list-view">
                <div class="loading">Loading DOMAIN_NAME...</div>
            </div>
        </div>
        
        <div id="create-tab" class="tab-content">
            <h2>➕ Create New DOMAIN_SINGULAR</h2>
            <form id="create-form" onsubmit="handleCreateSubmit(event)">
                CREATE_FORM_FIELDS
                <button type="submit" class="btn btn-primary">Create DOMAIN_SINGULAR</button>
            </form>
        </div>
    </div>
    
    <script>
        JAVASCRIPT_CODE
    </script>
</body>
</html>'''

        # Replace placeholders
        html = template.replace('DOMAIN_TITLE', domain_plural.title())
        html = html.replace('DOMAIN_NAME', domain_name)  
        html = html.replace('DOMAIN_SINGULAR', domain_singular.title())
        html = html.replace('JAVASCRIPT_CODE', javascript_code)
        
        # Generate create form fields
        create_fields = self._generate_create_form_fields(domain_info)
        html = html.replace('CREATE_FORM_FIELDS', create_fields)
        
        return html
    
    def _generate_create_form_fields(self, domain_info: Dict[str, Any]) -> str:
        """Generate form fields for create form"""
        fields_html = []
        for field in domain_info['fields']:
            if field['name'] in ['id', 'created_at']:
                continue
            
            field_name = field['name']
            field_label = field.get('label', field_name.title())
            field_type = field.get('type', 'text')
            required = ' required' if field.get('required') else ''
            
            if field_type == 'textarea':
                field_html = f'''
                <div class="form-group">
                    <label for="{field_name}">{field_label}</label>
                    <textarea name="{field_name}" id="{field_name}" class="form-control"{required}></textarea>
                </div>'''
            else:
                field_html = f'''
                <div class="form-group">
                    <label for="{field_name}">{field_label}</label>
                    <input type="{field_type}" name="{field_name}" id="{field_name}" class="form-control"{required}>
                </div>'''
            
            fields_html.append(field_html)
        
        return ''.join(fields_html)
    def _generate_create_tab_content(self, domain_info: Dict[str, Any]) -> str:
        """Generate the create form tab content."""
        domain_singular = domain_info['singular']
        
        form_fields = []
        for field in domain_info['fields']:
            if field['name'] in ['id', 'created_at']:
                continue  # Skip system fields
                
            field_html = self._generate_form_field(field)
            form_fields.append(field_html)
        
        return f'''
        <div id="create-tab" class="tab-content">
            <h2>➕ Create New {domain_singular.title()}</h2>
            <form id="create-form" onsubmit="handleCreateSubmit(event)">
                {''.join(form_fields)}
                <button type="submit" class="btn btn-primary">Create {domain_singular.title()}</button>
            </form>
            
            <script>
                function handleCreateSubmit(event) {{
                    event.preventDefault();
                    const formData = new FormData(event.target);
                    const data = Object.fromEntries(formData.entries());
                    
                    // Convert checkbox values
                    document.querySelectorAll('input[type="checkbox"]').forEach(cb => {{
                        data[cb.name] = cb.checked;
                    }});
                    
                    createItem(data);
                }}
            </script>
        </div>'''
    
    def _generate_edit_modal(self, domain_info: Dict[str, Any]) -> str:
        """Generate edit modal/form."""
        domain_singular = domain_info['singular']
        
        return f'''
        <!-- Edit Modal -->
        <div id="edit-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000;">
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 2rem; border-radius: 8px; max-width: 500px; width: 90%;">
                <h2>✏️ Edit {domain_singular.title()}</h2>
                <form id="edit-form">
                    <input type="hidden" name="id" id="edit-id">
                    <!-- Edit form fields will be populated by JavaScript -->
                    <div id="edit-fields"></div>
                    <div style="margin-top: 1rem;">
                        <button type="submit" class="btn btn-primary">Update {domain_singular.title()}</button>
                        <button type="button" class="btn btn-secondary" onclick="closeEditModal()">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
        
        <script>
            function editItem(id) {{
                // Load item data and populate edit form
                fetch(`${{API_BASE}}${{DOMAIN_PATH}}/${{id}}`)
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('edit-id').value = data.id;
                        // Populate form fields
                        showEditModal();
                    }});
            }}
            
            function showEditModal() {{
                document.getElementById('edit-modal').style.display = 'block';
            }}
            
            function closeEditModal() {{
                document.getElementById('edit-modal').style.display = 'none';
            }}
        </script>'''
    
    def _generate_form_field(self, field: Dict[str, str]) -> str:
        """Generate HTML for a form field."""
        field_name = field['name']
        field_type = field.get('type', 'text')
        field_label = field.get('label', field_name.title())
        required = ' required' if field.get('required') else ''
        readonly = ' readonly' if field.get('readonly') else ''
        
        if field_type == 'textarea':
            return f'''
                <div class="form-group">
                    <label for="{field_name}">{field_label}</label>
                    <textarea name="{field_name}" id="{field_name}" class="form-control"{required}{readonly}></textarea>
                </div>'''
        elif field_type == 'checkbox':
            return f'''
                <div class="form-group">
                    <label>
                        <input type="checkbox" name="{field_name}" id="{field_name}"{required}> {field_label}
                    </label>
                </div>'''
        else:
            step_attr = f' step="{field["step"]}"' if field.get('step') else ''
            return f'''
                <div class="form-group">
                    <label for="{field_name}">{field_label}</label>
                    <input type="{field_type}" name="{field_name}" id="{field_name}" class="form-control"{required}{readonly}{step_attr}>
                </div>'''
    

