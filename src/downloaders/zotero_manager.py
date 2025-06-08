#!/usr/bin/env python3
"""
Zotero Library Manager for the Physics Literature Synthesis Pipeline.

This is the BASE manager that provides core Zotero Web API functionality.
For advanced features like DOI-based PDF downloads, see EnhancedZoteroLibraryManager.

ARCHITECTURE DECISION:
===================
We maintain TWO separate managers for the following reasons:

1. SINGLE RESPONSIBILITY:
   - ZoteroLibraryManager: Pure Zotero API operations (650+ lines)
   - EnhancedZoteroLibraryManager: Browser automation + DOI downloads (800+ lines)
   
2. DEPENDENCY SEPARATION:
   - Basic: Only requires PyZotero (lightweight)
   - Enhanced: Requires Selenium + ChromeDriver (heavyweight)
   
3. DEPLOYMENT FLEXIBILITY:
   - Minimal environments can use basic manager only
   - Full deployments get enhanced features when dependencies available
   
4. MAINTAINABILITY:
   - Combined file would be 1400+ lines (too large)
   - Easier to test and debug separate concerns
   - Clear inheritance hierarchy: Enhanced inherits from Basic

USAGE GUIDELINES:
===============
- Use ZoteroLibraryManager for: Basic library sync, metadata extraction, file downloads
- Use EnhancedZoteroLibraryManager for: DOI-based PDF downloads, browser automation
- Factory function in __init__.py automatically selects the appropriate manager

INHERITANCE RELATIONSHIP:
========================
ZoteroLibraryManager (this file)
    └── EnhancedZoteroLibraryManager (enhanced_zotero_manager.py)
        ├── Inherits ALL basic functionality
        ├── Adds DOI download capabilities  
        ├── Adds browser automation features
        └── Gracefully degrades when Selenium unavailable
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

try:
    from pyzotero import zotero
    PYZOTERO_AVAILABLE = True
except ImportError:
    PYZOTERO_AVAILABLE = False
    
from ..utils.logging_config import get_logger
from ..utils.file_utils import clean_filename, ensure_directory_exists

logger = get_logger(__name__)

@dataclass
class ZoteroItem:
    """Container for Zotero item metadata."""
    key: str
    title: str
    authors: List[str]
    abstract: str = ""
    year: Optional[str] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    item_type: str = ""
    tags: List[str] = None
    collections: List[str] = None
    attachments: List[Dict[str, Any]] = None
    date_added: Optional[str] = None
    date_modified: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.collections is None:
            self.collections = []
        if self.attachments is None:
            self.attachments = []

@dataclass
class ZoteroAttachment:
    """Container for Zotero attachment metadata."""
    key: str
    parent_item: str
    title: str
    filename: str
    content_type: str
    md5: Optional[str] = None
    file_size: Optional[int] = None
    link_mode: str = ""
    
@dataclass
class SyncResult:
    """Result of synchronization operation."""
    items_processed: int
    items_synced: int
    files_downloaded: int
    errors: List[str]
    processing_time: float

class ZoteroLibraryManager:
    """
    Core Zotero Library Manager - Base Implementation
    
    This class provides essential Zotero Web API functionality including:
    ✅ Library synchronization via PyZotero
    ✅ Item and attachment retrieval  
    ✅ Collection management
    ✅ BibTeX export
    ✅ File downloads (existing attachments)
    
    For advanced features, see EnhancedZoteroLibraryManager:
    🚀 DOI-based PDF downloads
    🚀 Browser automation  
    🚀 Publisher-specific download strategies
    
    Dependencies: PyZotero only (lightweight)
    """
    
    def __init__(self, 
                 library_id: str,
                 library_type: str = "user",  # or "group"
                 api_key: str = None,
                 output_directory: Path = None):
        """
        Initialize core Zotero library manager.
        
        Args:
            library_id: Zotero library ID (user ID or group ID)
            library_type: "user" for personal library, "group" for group library
            api_key: Zotero API key (get from https://www.zotero.org/settings/keys)
            output_directory: Directory to save downloaded files
            
        Note:
            For DOI-based PDF downloads, use EnhancedZoteroLibraryManager instead.
        """
        if not PYZOTERO_AVAILABLE:
            raise ImportError(
                "PyZotero is required for Zotero integration. "
                "Install with: pip install pyzotero"
            )
        
        self.library_id = library_id
        self.library_type = library_type
        self.api_key = api_key or os.getenv("ZOTERO_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Zotero API key is required. Set ZOTERO_API_KEY environment "
                "variable or pass api_key parameter."
            )
        
        # Initialize PyZotero client
        try:
            self.zot = zotero.Zotero(
                self.library_id, 
                self.library_type, 
                self.api_key
            )
            logger.info(f"Connected to Zotero {library_type} library: {library_id}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Zotero: {e}")
        
        # Set up output directory
        self.output_directory = output_directory or Path("documents/zotero_sync")
        ensure_directory_exists(self.output_directory)
        
        # Create subdirectories for different file types
        self.pdf_directory = self.output_directory / "pdfs"
        self.other_files_directory = self.output_directory / "other_files"
        ensure_directory_exists(self.pdf_directory)
        ensure_directory_exists(self.other_files_directory)
        
        # Statistics tracking
        self.stats = {
            'items_retrieved': 0,
            'attachments_found': 0,
            'files_downloaded': 0,
            'errors': []
        }
        
        logger.info(f"Basic Zotero manager initialized. For DOI downloads, use EnhancedZoteroLibraryManager.")
        logger.info(f"Basic Zotero manager initialized with output: {self.output_directory}")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Zotero and get library information.
        
        Returns:
            Dictionary with connection status and library info
        """
        try:
            # Test basic connectivity
            key_info = self.zot.key_info()
            
            # Get library statistics
            item_count = self.zot.num_items()
            
            # Get some sample items
            sample_items = self.zot.top(limit=3)
            
            result = {
                'connected': True,
                'library_type': self.library_type,
                'library_id': self.library_id,
                'api_permissions': key_info,
                'total_items': item_count,
                'sample_items': len(sample_items),
                'error': None
            }
            
            logger.info(f"Connection test successful: {item_count} items in library")
            return result
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                'connected': False,
                'error': str(e)
            }
    
    def get_all_items(self, 
                     collections: List[str] = None,
                     item_types: List[str] = None,
                     tags: List[str] = None,
                     since: str = None) -> List[ZoteroItem]:
        """
        Retrieve all items from the Zotero library with optional filtering.
        
        Args:
            collections: List of collection IDs to filter by
            item_types: List of item types to include (e.g., ['journalArticle', 'book'])
            tags: List of tags to filter by
            since: Library version to sync since (for incremental updates)
        
        Returns:
            List of ZoteroItem objects
        """
        logger.info("Retrieving items from Zotero library...")
        
        items = []
        
        try:
            # Prepare search parameters
            params = {}
            
            if since:
                params['since'] = since
            
            if item_types:
                # For multiple item types, we need multiple API calls
                all_raw_items = []
                for item_type in item_types:
                    params['itemType'] = item_type
                    self.zot.add_parameters(**params)
                    type_items = self.zot.everything(self.zot.top())
                    all_raw_items.extend(type_items)
            else:
                # Get all top-level items
                self.zot.add_parameters(**params)
                all_raw_items = self.zot.everything(self.zot.top())
            
            logger.info(f"Retrieved {len(all_raw_items)} raw items from Zotero")
            
            # Process each item
            for raw_item in all_raw_items:
                try:
                    zotero_item = self._parse_zotero_item(raw_item)
                    
                    # Apply collection filter if specified
                    if collections and not any(col in zotero_item.collections for col in collections):
                        continue
                    
                    # Apply tag filter if specified
                    if tags and not any(tag in zotero_item.tags for tag in tags):
                        continue
                    
                    items.append(zotero_item)
                    
                except Exception as e:
                    logger.warning(f"Error parsing item {raw_item.get('key', 'unknown')}: {e}")
                    self.stats['errors'].append(f"Parse error for item: {e}")
            
            self.stats['items_retrieved'] = len(items)
            logger.info(f"Successfully parsed {len(items)} items")
            
            return items
            
        except Exception as e:
            logger.error(f"Error retrieving items from Zotero: {e}")
            self.stats['errors'].append(f"Retrieval error: {e}")
            return []
    
    def get_item_attachments(self, item_key: str) -> List[ZoteroAttachment]:
        """
        Get all attachments for a specific item.
        
        Args:
            item_key: Zotero item key
        
        Returns:
            List of ZoteroAttachment objects
        """
        try:
            # Get child items (which include attachments)
            children = self.zot.children(item_key)
            
            attachments = []
            for child in children:
                if child['data']['itemType'] == 'attachment':
                    attachment = self._parse_attachment(child, item_key)
                    if attachment:
                        attachments.append(attachment)
            
            return attachments
            
        except Exception as e:
            logger.warning(f"Error getting attachments for item {item_key}: {e}")
            return []
    
    def download_attachment(self, 
                           attachment: ZoteroAttachment,
                           overwrite: bool = False) -> Optional[Path]:
        """
        Download an attachment file from Zotero.
        
        Args:
            attachment: ZoteroAttachment object
            overwrite: Whether to overwrite existing files
        
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Determine output directory based on file type
            if attachment.content_type == 'application/pdf':
                output_dir = self.pdf_directory
                extension = '.pdf'
            else:
                output_dir = self.other_files_directory
                # Try to get extension from filename
                if '.' in attachment.filename:
                    extension = '.' + attachment.filename.split('.')[-1]
                else:
                    extension = '.bin'  # fallback
            
            # Create safe filename
            safe_filename = clean_filename(attachment.filename or f"{attachment.key}{extension}")
            output_path = output_dir / safe_filename
            
            # Check if file already exists
            if output_path.exists() and not overwrite:
                logger.debug(f"File already exists: {output_path}")
                return output_path
            
            # Download file content
            logger.info(f"Downloading attachment: {attachment.filename}")
            
            file_content = self.zot.file(attachment.key)
            
            # Write to disk
            with open(output_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"Downloaded attachment to: {output_path}")
            self.stats['files_downloaded'] += 1
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error downloading attachment {attachment.key}: {e}")
            self.stats['errors'].append(f"Download error for {attachment.key}: {e}")
            return None
    
    def sync_library(self, 
                    download_attachments: bool = True,
                    file_types: Set[str] = None,
                    collections: List[str] = None,
                    overwrite_files: bool = False) -> SyncResult:
        """
        Synchronize the entire Zotero library.
        
        Args:
            download_attachments: Whether to download attachment files
            file_types: Set of content types to download (e.g., {'application/pdf'})
            collections: List of collection IDs to sync (None for all)
            overwrite_files: Whether to overwrite existing files
        
        Returns:
            SyncResult with synchronization statistics
        """
        start_time = time.time()
        logger.info("Starting Zotero library synchronization...")
        
        # Default file types if not specified
        if file_types is None:
            file_types = {'application/pdf', 'text/plain', 'text/html'}
        
        # Reset stats
        self.stats = {
            'items_retrieved': 0,
            'attachments_found': 0,
            'files_downloaded': 0,
            'errors': []
        }
        
        # Get all items
        items = self.get_all_items(collections=collections)
        
        items_synced = 0
        
        if download_attachments:
            logger.info("Downloading attachments...")
            
            for item in items:
                try:
                    # Get attachments for this item
                    attachments = self.get_item_attachments(item.key)
                    self.stats['attachments_found'] += len(attachments)
                    
                    # Download relevant attachments
                    for attachment in attachments:
                        if attachment.content_type in file_types:
                            downloaded_path = self.download_attachment(
                                attachment, overwrite=overwrite_files
                            )
                            if downloaded_path:
                                # Store download path in item metadata
                                item.attachments.append({
                                    'key': attachment.key,
                                    'filename': attachment.filename,
                                    'content_type': attachment.content_type,
                                    'local_path': str(downloaded_path)
                                })
                    
                    items_synced += 1
                    
                    # Add small delay to be respectful to Zotero servers
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error syncing item {item.key}: {e}")
                    self.stats['errors'].append(f"Sync error for {item.key}: {e}")
        
        processing_time = time.time() - start_time
        
        result = SyncResult(
            items_processed=len(items),
            items_synced=items_synced,
            files_downloaded=self.stats['files_downloaded'],
            errors=self.stats['errors'],
            processing_time=processing_time
        )
        
        logger.info(f"Synchronization complete: {result.items_processed} items, "
                   f"{result.files_downloaded} files downloaded in {processing_time:.2f}s")
        
        return result
    
    def get_collections(self) -> List[Dict[str, Any]]:
        """
        Get all collections in the library.
        
        Returns:
            List of collection dictionaries
        """
        try:
            collections = self.zot.collections()
            
            collection_info = []
            for coll in collections:
                collection_info.append({
                    'key': coll['key'],
                    'name': coll['data']['name'],
                    'parent': coll['data'].get('parentCollection', None),
                    'num_items': coll['meta'].get('numItems', 0)
                })
            
            return collection_info
            
        except Exception as e:
            logger.error(f"Error retrieving collections: {e}")
            return []
    
    def get_library_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive library statistics.
        
        Returns:
            Dictionary with library statistics
        """
        try:
            # Basic counts
            total_items = self.zot.num_items()
            
            # Get collections info
            collections = self.get_collections()
            
            # Get some sample items to analyze types
            sample_items = self.zot.top(limit=100)
            item_types = {}
            for item in sample_items:
                item_type = item['data']['itemType']
                item_types[item_type] = item_types.get(item_type, 0) + 1
            
            stats = {
                'total_items': total_items,
                'total_collections': len(collections),
                'item_types_sample': item_types,
                'collections': collections[:10],  # First 10 collections
                'library_type': self.library_type,
                'library_id': self.library_id,
                'sync_stats': self.stats
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting library stats: {e}")
            return {'error': str(e)}
    
    def _parse_zotero_item(self, raw_item: Dict[str, Any]) -> ZoteroItem:
        """
        Parse raw Zotero API response into ZoteroItem object.
        
        Args:
            raw_item: Raw item data from Zotero API
        
        Returns:
            ZoteroItem object
        """
        data = raw_item['data']
        
        # Extract basic fields
        key = raw_item['key']
        title = data.get('title', '').strip()
        item_type = data.get('itemType', '')
        abstract = data.get('abstractNote', '').strip()
        year = data.get('date', '')
        journal = data.get('publicationTitle', '') or data.get('journalAbbreviation', '')
        doi = data.get('DOI', '')
        url = data.get('url', '')
        
        # Extract year from date if it's a full date
        if year and len(year) >= 4:
            try:
                year = year[:4]  # Take first 4 characters as year
            except:
                year = None
        
        # Extract authors
        authors = []
        creators = data.get('creators', [])
        for creator in creators:
            if creator.get('creatorType') in ['author', 'editor']:
                first_name = creator.get('firstName', '')
                last_name = creator.get('lastName', '')
                if first_name and last_name:
                    authors.append(f"{first_name} {last_name}")
                elif last_name:
                    authors.append(last_name)
                elif creator.get('name'):  # Single name field
                    authors.append(creator['name'])
        
        # Extract tags
        tags = [tag['tag'] for tag in data.get('tags', [])]
        
        # Extract collections
        collections = data.get('collections', [])
        
        # Extract dates
        date_added = data.get('dateAdded')
        date_modified = data.get('dateModified')
        
        return ZoteroItem(
            key=key,
            title=title,
            authors=authors,
            abstract=abstract,
            year=year,
            journal=journal,
            doi=doi,
            url=url,
            item_type=item_type,
            tags=tags,
            collections=collections,
            date_added=date_added,
            date_modified=date_modified
        )
    
    def _parse_attachment(self, 
                         raw_attachment: Dict[str, Any], 
                         parent_key: str) -> Optional[ZoteroAttachment]:
        """
        Parse raw attachment data into ZoteroAttachment object.
        
        Args:
            raw_attachment: Raw attachment data from Zotero API
            parent_key: Key of parent item
        
        Returns:
            ZoteroAttachment object or None if not a file attachment
        """
        data = raw_attachment['data']
        
        # Only process stored file attachments
        if data.get('linkMode') != 'imported_file':
            return None
        
        key = raw_attachment['key']
        title = data.get('title', '')
        filename = data.get('filename', '')
        content_type = data.get('contentType', '')
        md5 = data.get('md5')
        link_mode = data.get('linkMode', '')
        
        return ZoteroAttachment(
            key=key,
            parent_item=parent_key,
            title=title,
            filename=filename,
            content_type=content_type,
            md5=md5,
            link_mode=link_mode
        )
    
    def export_items_to_bibtex(self, 
                              items: List[ZoteroItem] = None,
                              output_path: Path = None) -> Path:
        """
        Export items to BibTeX format using Zotero's built-in export.
        
        Args:
            items: List of ZoteroItem objects to export (None for all)
            output_path: Path for output file
        
        Returns:
            Path to created BibTeX file
        """
        if output_path is None:
            output_path = self.output_directory / "zotero_export.bib"
        
        try:
            # If no specific items provided, export everything
            if items is None:
                # Export all items in BibTeX format
                bibtex_data = self.zot.everything(self.zot.top(format='bibtex'))
            else:
                # Export specific items by their keys
                item_keys = [item.key for item in items]
                # Note: PyZotero might require chunking for large requests
                if len(item_keys) <= 50:
                    bibtex_data = self.zot.items(itemKey=','.join(item_keys), format='bibtex')
                else:
                    # Chunk the request for large numbers of items
                    all_bibtex = []
                    for i in range(0, len(item_keys), 50):
                        chunk = item_keys[i:i+50]
                        chunk_data = self.zot.items(itemKey=','.join(chunk), format='bibtex')
                        if hasattr(chunk_data, 'entries'):
                            all_bibtex.extend(chunk_data.entries)
                    
                    # Create a mock bibtex object
                    from types import SimpleNamespace
                    bibtex_data = SimpleNamespace()
                    bibtex_data.entries = all_bibtex
            
            # Write to file
            if hasattr(bibtex_data, 'dump'):
                # Standard bibtexparser object
                with open(output_path, 'w', encoding='utf-8') as f:
                    bibtex_data.dump(f)
            else:
                # Fallback: write entries manually
                with open(output_path, 'w', encoding='utf-8') as f:
                    if hasattr(bibtex_data, 'entries'):
                        for entry in bibtex_data.entries:
                            f.write(f"@{entry.get('ENTRYTYPE', 'article')}{{{entry.get('ID', 'unknown')},\n")
                            for key, value in entry.items():
                                if key not in ['ENTRYTYPE', 'ID']:
                                    f.write(f"  {key} = {{{value}}},\n")
                            f.write("}\n\n")
            
            logger.info(f"Exported BibTeX to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting to BibTeX: {e}")
            raise
    
    def find_items_with_attachments(self, 
                                   content_types: Set[str] = None) -> List[ZoteroItem]:
        """
        Find all items that have file attachments of specified types.
        
        Args:
            content_types: Set of content types to look for
        
        Returns:
            List of ZoteroItem objects that have matching attachments
        """
        if content_types is None:
            content_types = {'application/pdf'}
        
        all_items = self.get_all_items()
        items_with_attachments = []
        
        for item in all_items:
            attachments = self.get_item_attachments(item.key)
            
            # Check if any attachment matches our criteria
            has_matching_attachment = any(
                att.content_type in content_types 
                for att in attachments
            )
            
            if has_matching_attachment:
                # Store attachment info in the item
                item.attachments = [
                    {
                        'key': att.key,
                        'filename': att.filename,
                        'content_type': att.content_type
                    }
                    for att in attachments
                    if att.content_type in content_types
                ]
                items_with_attachments.append(item)
        
        logger.info(f"Found {len(items_with_attachments)} items with matching attachments")
        return items_with_attachments