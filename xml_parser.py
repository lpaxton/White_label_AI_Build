"""
XML Content Parser Module
Handles parsing and extracting content from XML files.
"""
import xml.etree.ElementTree as ET
from typing import List, Dict


class ContentParser:
    """Parse XML content files and extract structured data."""
    
    def __init__(self, xml_file_path: str):
        """
        Initialize the parser with an XML file.
        
        Args:
            xml_file_path: Path to the XML file containing content.
        """
        self.xml_file_path = xml_file_path
        self.content_items = []
        self._parse()
    
    def _parse(self):
        """Parse the XML file and extract content items."""
        try:
            tree = ET.parse(self.xml_file_path)
            root = tree.getroot()
            
            for content_elem in root.findall('content'):
                content_dict = {
                    'id': content_elem.get('id'),
                    'title': self._get_text(content_elem, 'title'),
                    'description': self._get_text(content_elem, 'description'),
                    'category': self._get_text(content_elem, 'category'),
                    'difficulty': self._get_text(content_elem, 'difficulty'),
                    'tags': self._get_text(content_elem, 'tags'),
                    'duration': self._get_text(content_elem, 'duration'),
                }
                self.content_items.append(content_dict)
        except Exception as e:
            raise Exception(f"Error parsing XML file: {str(e)}")
    
    def _get_text(self, element, tag_name: str) -> str:
        """
        Safely extract text from an XML element.
        
        Args:
            element: Parent XML element.
            tag_name: Name of the child tag to extract.
            
        Returns:
            Text content or empty string if not found.
        """
        child = element.find(tag_name)
        return child.text if child is not None and child.text else ""
    
    def get_all_content(self) -> List[Dict]:
        """
        Get all parsed content items.
        
        Returns:
            List of content dictionaries.
        """
        return self.content_items
    
    def get_content_as_text(self) -> str:
        """
        Get all content formatted as text for LLM processing.
        
        Returns:
            Formatted string of all content.
        """
        text_parts = []
        for idx, item in enumerate(self.content_items, 1):
            text = f"""
Content #{idx} (ID: {item['id']}):
Title: {item['title']}
Description: {item['description']}
Category: {item['category']}
Difficulty: {item['difficulty']}
Tags: {item['tags']}
Duration: {item['duration']}
"""
            text_parts.append(text)
        
        return "\n".join(text_parts)
