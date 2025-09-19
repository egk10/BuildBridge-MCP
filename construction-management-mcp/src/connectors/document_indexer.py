"""
Document Indexer for Construction Management MCP

Handles document search and indexing for construction documents stored in
SharePoint, OneDrive, and local repositories.
"""

import os
import json
import hashlib
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from pathlib import Path
import tempfile

import msal
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File


class DocumentIndexer:
    """Indexes and searches construction documents"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize document indexer
        
        Args:
            config: Configuration dictionary with credentials and settings
        """
        self.config = config
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.tenant_id = config['tenant_id']
        self.sharepoint_site = config['sharepoint_site']
        
        # Local mode toggle: skip SharePoint auth when true
        self.local_mode = bool(
            config.get('local_mode') or
            self.sharepoint_site in ('local-test', 'local', '')
        )

        # Document storage locations
        self.document_libraries = config.get('document_libraries', ['Documents', 'Shared Documents'])
        self.local_docs_path = config.get('local_docs_path', './data/documents')
        
        # Index storage
        self.index_file = config.get('index_file', './data/document_index.json')
        self.document_index = {}
        self.keyword_index = {}
        
        # Document type mappings
        self.document_types = {
            '.pdf': 'PDF Document',
            '.docx': 'Word Document',
            '.doc': 'Word Document',
            '.xlsx': 'Excel Spreadsheet',
            '.xls': 'Excel Spreadsheet',
            '.pptx': 'PowerPoint Presentation',
            '.ppt': 'PowerPoint Presentation',
            '.dwg': 'AutoCAD Drawing',
            '.dxf': 'AutoCAD Exchange',
            '.jpg': 'Image',
            '.jpeg': 'Image',
            '.png': 'Image',
            '.tiff': 'Image',
            '.txt': 'Text Document',
            '.rtf': 'Rich Text Document'
        }
        
        # Construction document categories
        self.construction_categories = {
            'drawings': ['drawing', 'plan', 'blueprint', 'dwg', 'dxf'],
            'specifications': ['spec', 'specification', 'requirements'],
            'contracts': ['contract', 'agreement', 'terms'],
            'reports': ['report', 'analysis', 'summary', 'status'],
            'permits': ['permit', 'license', 'approval'],
            'safety': ['safety', 'incident', 'accident', 'msds'],
            'schedules': ['schedule', 'timeline', 'gantt', 'calendar'],
            'budgets': ['budget', 'cost', 'estimate', 'invoice'],
            'photos': ['photo', 'image', 'picture', 'jpg', 'png'],
            'correspondence': ['email', 'letter', 'memo', 'correspondence']
        }
        
        # Initialize authentication only if NOT in local mode
        if not self.local_mode:
            self._init_auth()
        else:
            # In local mode, set dummy values to avoid attribute errors
            self.app = None
            self.access_token = None
        
        # Load existing index
        self._load_index()
    
    def _init_auth(self):
        """Initialize SharePoint authentication"""
        try:
            self.app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )
            self._get_access_token()
        except Exception as e:
            raise Exception(f"Failed to initialize document indexer authentication: {str(e)}")
    
    def _get_access_token(self):
        """Get access token for SharePoint"""
        scopes = [f"{self.sharepoint_site}/.default"]
        result = self.app.acquire_token_for_client(scopes=scopes)
        
        if "access_token" in result:
            self.access_token = result["access_token"]
        else:
            raise Exception(f"Failed to acquire token for documents: {result.get('error_description', 'Unknown error')}")
    
    def _get_sharepoint_context(self):
        """Get SharePoint client context"""
        try:
            ctx = ClientContext(self.sharepoint_site)
            ctx.with_access_token(self.access_token)
            return ctx
        except Exception as e:
            raise Exception(f"Failed to create SharePoint context for documents: {str(e)}")
    
    def _load_index(self):
        """Load existing document index from file"""
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.document_index = data.get('documents', {})
                    self.keyword_index = data.get('keywords', {})
        except Exception as e:
            print(f"Warning: Failed to load document index: {str(e)}")
            self.document_index = {}
            self.keyword_index = {}
    
    def _save_index(self):
        """Save document index to file"""
        try:
            os.makedirs(os.path.dirname(self.index_file), exist_ok=True)
            
            data = {
                'documents': self.document_index,
                'keywords': self.keyword_index,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save document index: {str(e)}")
    
    def index_sharepoint_documents(self, force_refresh: bool = False):
        """
        Index documents from SharePoint document libraries
        
        Args:
            force_refresh: Force re-indexing of all documents
        """
        try:
            ctx = self._get_sharepoint_context()
            
            for library_name in self.document_libraries:
                try:
                    # Get document library
                    doc_library = ctx.web.lists.get_by_title(library_name)
                    
                    # Get all files in the library
                    files = doc_library.root_folder.files
                    ctx.load(files)
                    ctx.execute_query()
                    
                    for file in files:
                        self._index_sharepoint_file(ctx, file, library_name, force_refresh)
                        
                except Exception as e:
                    print(f"Warning: Failed to index library {library_name}: {str(e)}")
                    continue
            
            # Save updated index
            self._save_index()
            
        except Exception as e:
            raise Exception(f"Failed to index SharePoint documents: {str(e)}")
    
    def _index_sharepoint_file(self, ctx: ClientContext, file: File, library: str, force_refresh: bool = False):
        """Index a single SharePoint file"""
        try:
            file_url = file.server_relative_url
            file_id = hashlib.md5(file_url.encode()).hexdigest()
            
            # Check if file already indexed and not modified
            if not force_refresh and file_id in self.document_index:
                existing = self.document_index[file_id]
                if existing.get('modified') == file.time_last_modified:
                    return  # Skip if not modified
            
            # Get file extension and type
            file_ext = os.path.splitext(file.name)[1].lower()
            doc_type = self.document_types.get(file_ext, 'Unknown')
            
            # Determine document category
            category = self._categorize_document(file.name)
            
            # Extract keywords from filename and path
            keywords = self._extract_keywords(file.name, file_url)
            
            # Create document record
            doc_record = {
                'id': file_id,
                'title': file.name,
                'location': file_url,
                'library': library,
                'type': doc_type,
                'category': category,
                'size': file.length,
                'modified': file.time_last_modified,
                'created': file.time_created,
                'keywords': keywords,
                'source': 'sharepoint'
            }
            
            # Try to extract content from text-based files
            if file_ext in ['.txt', '.rtf']:
                try:
                    content = self._extract_file_content(ctx, file)
                    doc_record['content_preview'] = content[:500]  # First 500 characters
                    keywords.extend(self._extract_keywords_from_content(content))
                except:
                    pass  # Continue without content if extraction fails
            
            # Add to document index
            self.document_index[file_id] = doc_record
            
            # Update keyword index
            self._update_keyword_index(file_id, keywords)
            
        except Exception as e:
            print(f"Warning: Failed to index file {file.name}: {str(e)}")
    
    def index_local_documents(self, force_refresh: bool = False):
        """
        Index documents from local directory
        
        Args:
            force_refresh: Force re-indexing of all documents
        """
        if not os.path.exists(self.local_docs_path):
            return  # No local documents to index
        
        try:
            for root, dirs, files in os.walk(self.local_docs_path):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    self._index_local_file(file_path, force_refresh)
            
            # Save updated index
            self._save_index()
            
        except Exception as e:
            raise Exception(f"Failed to index local documents: {str(e)}")
    
    def _index_local_file(self, file_path: str, force_refresh: bool = False):
        """Index a single local file"""
        try:
            file_id = hashlib.md5(file_path.encode()).hexdigest()
            file_stat = os.stat(file_path)
            
            # Check if file already indexed and not modified
            if not force_refresh and file_id in self.document_index:
                existing = self.document_index[file_id]
                if existing.get('modified') == file_stat.st_mtime:
                    return  # Skip if not modified
            
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1].lower()
            doc_type = self.document_types.get(file_ext, 'Unknown')
            
            # Determine document category
            category = self._categorize_document(file_name)
            
            # Extract keywords
            keywords = self._extract_keywords(file_name, file_path)
            
            # Create document record
            doc_record = {
                'id': file_id,
                'title': file_name,
                'location': file_path,
                'type': doc_type,
                'category': category,
                'size': file_stat.st_size,
                'modified': file_stat.st_mtime,
                'created': file_stat.st_ctime,
                'keywords': keywords,
                'source': 'local'
            }
            
            # Try to extract content from text files
            if file_ext in ['.txt', '.rtf']:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        doc_record['content_preview'] = content[:500]
                        keywords.extend(self._extract_keywords_from_content(content))
                except:
                    pass
            
            # Add to indexes
            self.document_index[file_id] = doc_record
            self._update_keyword_index(file_id, keywords)
            
        except Exception as e:
            print(f"Warning: Failed to index local file {file_path}: {str(e)}")
    
    def _categorize_document(self, filename: str) -> str:
        """Categorize document based on filename"""
        filename_lower = filename.lower()
        
        for category, keywords in self.construction_categories.items():
            if any(keyword in filename_lower for keyword in keywords):
                return category
        
        return 'general'
    
    def _extract_keywords(self, filename: str, file_path: str) -> List[str]:
        """Extract keywords from filename and path"""
        keywords = []
        
        # Extract from filename (remove extension)
        name_without_ext = os.path.splitext(filename)[0]
        
        # Split by common separators
        words = []
        import re
        words.extend(re.split(r'[_\-\s\.]+', name_without_ext.lower()))
        words.extend(re.split(r'[_\-\s\.\/\\]+', file_path.lower()))
        
        # Filter and clean keywords
        for word in words:
            word = word.strip()
            if len(word) > 2 and word.isalnum():  # Only alphanumeric words longer than 2 chars
                keywords.append(word)
        
        # Add construction-specific keywords if found
        for category, cat_keywords in self.construction_categories.items():
            if any(kw in filename.lower() for kw in cat_keywords):
                keywords.append(category)
        
        return list(set(keywords))  # Remove duplicates
    
    def _extract_keywords_from_content(self, content: str) -> List[str]:
        """Extract keywords from document content"""
        if not content:
            return []
        
        import re
        
        # Extract words (alphanumeric sequences)
        words = re.findall(r'\b[a-zA-Z]\w{2,}\b', content.lower())
        
        # Common construction terms to prioritize
        construction_terms = [
            'project', 'construction', 'building', 'contractor', 'subcontractor',
            'schedule', 'timeline', 'milestone', 'budget', 'cost', 'expense',
            'safety', 'incident', 'permit', 'inspection', 'compliance',
            'drawing', 'specification', 'blueprint', 'plan', 'design'
        ]
        
        # Filter for relevant keywords
        keywords = []
        for word in words:
            if word in construction_terms or len(word) > 6:  # Long words or construction terms
                keywords.append(word)
        
        # Return top 20 most common keywords
        from collections import Counter
        return [word for word, count in Counter(keywords).most_common(20)]
    
    def _update_keyword_index(self, doc_id: str, keywords: List[str]):
        """Update the keyword index with document keywords"""
        for keyword in keywords:
            if keyword not in self.keyword_index:
                self.keyword_index[keyword] = []
            
            if doc_id not in self.keyword_index[keyword]:
                self.keyword_index[keyword].append(doc_id)
    
    def _extract_file_content(self, ctx: ClientContext, file: File) -> str:
        """Extract content from SharePoint file (for text files)"""
        try:
            # Download file content
            content = file.get_content()
            ctx.execute_query()
            
            # Decode content
            return content.value.decode('utf-8', errors='ignore')
        except:
            return ""
    
    def search_documents(self, query: str, doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search documents by keywords or content
        
        Args:
            query: Search query (keywords)
            doc_type: Optional document type filter
        
        Returns:
            List of matching documents
        """
        query_lower = query.lower()
        query_words = query_lower.split()
        
        # Find documents matching keywords
        matching_docs = set()
        
        # Search in keyword index
        for keyword, doc_ids in self.keyword_index.items():
            if any(word in keyword for word in query_words):
                matching_docs.update(doc_ids)
        
        # Search in document titles and content
        for doc_id, doc_info in self.document_index.items():
            title_lower = doc_info['title'].lower()
            content_lower = doc_info.get('content_preview', '').lower()
            
            if (any(word in title_lower for word in query_words) or 
                any(word in content_lower for word in query_words)):
                matching_docs.add(doc_id)
        
        # Filter by document type if specified
        results = []
        for doc_id in matching_docs:
            doc_info = self.document_index[doc_id]
            
            if doc_type and doc_type.lower() not in doc_info['type'].lower():
                continue
            
            # Calculate relevance score
            relevance = self._calculate_relevance(doc_info, query_words)
            doc_info['relevance_score'] = relevance
            
            results.append(doc_info.copy())
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return results
    
    def _calculate_relevance(self, doc_info: Dict[str, Any], query_words: List[str]) -> float:
        """Calculate document relevance score"""
        score = 0.0
        
        title_lower = doc_info['title'].lower()
        content_lower = doc_info.get('content_preview', '').lower()
        keywords_lower = [kw.lower() for kw in doc_info.get('keywords', [])]
        
        for word in query_words:
            # Title matches are worth more
            if word in title_lower:
                score += 10.0
            
            # Keyword matches
            if any(word in kw for kw in keywords_lower):
                score += 5.0
            
            # Content matches
            if word in content_lower:
                score += 2.0
        
        # Boost score for construction documents
        if doc_info.get('category') != 'general':
            score *= 1.2
        
        return score
    
    def get_documents_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all documents in a specific category
        
        Args:
            category: Document category
        
        Returns:
            List of documents in the category
        """
        results = []
        for doc_info in self.document_index.values():
            if doc_info.get('category') == category:
                results.append(doc_info.copy())
        
        # Sort by modification date (newest first)
        results.sort(key=lambda x: x.get('modified', 0), reverse=True)
        
        return results
    
    def get_recent_documents(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get recently modified documents
        
        Args:
            days: Number of days to look back
        
        Returns:
            List of recent documents
        """
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        results = []
        for doc_info in self.document_index.values():
            modified_time = doc_info.get('modified', 0)
            if isinstance(modified_time, str):
                try:
                    modified_time = datetime.fromisoformat(modified_time).timestamp()
                except:
                    continue
            
            if modified_time > cutoff_time:
                results.append(doc_info.copy())
        
        # Sort by modification date (newest first)
        results.sort(key=lambda x: x.get('modified', 0), reverse=True)
        
        return results
    
    def rebuild_index(self):
        """Rebuild the entire document index"""
        self.document_index.clear()
        self.keyword_index.clear()
        
        # Index SharePoint documents
        self.index_sharepoint_documents(force_refresh=True)
        
        # Index local documents
        self.index_local_documents(force_refresh=True)
        
        print(f"Index rebuilt with {len(self.document_index)} documents")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the document index"""
        stats = {
            'total_documents': len(self.document_index),
            'total_keywords': len(self.keyword_index),
            'categories': {},
            'types': {},
            'sources': {}
        }
        
        for doc_info in self.document_index.values():
            # Count by category
            category = doc_info.get('category', 'unknown')
            stats['categories'][category] = stats['categories'].get(category, 0) + 1
            
            # Count by type
            doc_type = doc_info.get('type', 'unknown')
            stats['types'][doc_type] = stats['types'].get(doc_type, 0) + 1
            
            # Count by source
            source = doc_info.get('source', 'unknown')
            stats['sources'][source] = stats['sources'].get(source, 0) + 1
        
        return stats