"""
Content Selector Module
Uses LLMs to select content based on persona descriptions.
"""
from typing import List, Dict
from xml_parser import ContentParser
from llm_providers import LLMProvider


class PersonaContentSelector:
    """Select content based on persona using LLM."""
    
    def __init__(self, xml_file_path: str, llm_provider: LLMProvider):
        """
        Initialize the content selector.
        
        Args:
            xml_file_path: Path to the XML content file.
            llm_provider: LLM provider to use for selection.
        """
        self.parser = ContentParser(xml_file_path)
        self.llm_provider = llm_provider
    
    def select_content_for_persona(
        self, 
        persona_description: str, 
        max_items: int = 5
    ) -> Dict:
        """
        Select content items that match the persona description.
        
        Args:
            persona_description: Free-text description of the user persona.
            max_items: Maximum number of content items to return.
            
        Returns:
            Dictionary with selected content and reasoning.
        """
        # Get all content as formatted text
        content_text = self.parser.get_content_as_text()
        
        # Create prompt for LLM
        prompt = self._create_selection_prompt(
            persona_description, 
            content_text, 
            max_items
        )
        
        # Get LLM response
        llm_response = self.llm_provider.generate_response(prompt)
        
        # Parse the response to extract content IDs
        selected_ids = self._parse_llm_response(llm_response)
        
        # Get full details of selected content
        all_content = self.parser.get_all_content()
        selected_content = [
            item for item in all_content 
            if item['id'] in selected_ids
        ]
        
        return {
            'persona': persona_description,
            'selected_content': selected_content,
            'llm_reasoning': llm_response,
            'total_selected': len(selected_content)
        }
    
    def _create_selection_prompt(
        self, 
        persona_description: str, 
        content_text: str, 
        max_items: int
    ) -> str:
        """
        Create the prompt for the LLM.
        
        Args:
            persona_description: Description of the persona.
            content_text: Formatted text of all available content.
            max_items: Maximum number of items to select.
            
        Returns:
            Formatted prompt string.
        """
        prompt = f"""You are an expert content curator. Based on the persona description below, select the most relevant content items from the available content library.

PERSONA DESCRIPTION:
{persona_description}

AVAILABLE CONTENT:
{content_text}

INSTRUCTIONS:
1. Analyze the persona description carefully
2. Select up to {max_items} content items that would be most valuable and relevant for this persona
3. Consider their role, experience level, learning goals, and interests
4. For each selected item, provide the Content ID

Please respond in the following format:

SELECTED CONTENT IDS: [list the IDs separated by commas, e.g., "1, 3, 7"]

REASONING:
[Explain why each content item was selected for this persona]
"""
        return prompt
    
    def _parse_llm_response(self, response: str) -> List[str]:
        """
        Parse LLM response to extract content IDs.
        
        Args:
            response: Raw response from LLM.
            
        Returns:
            List of content IDs.
        """
        ids = []
        
        # Look for the line with content IDs
        lines = response.split('\n')
        for line in lines:
            if 'SELECTED CONTENT IDS' in line.upper() or 'CONTENT IDS' in line.upper():
                # Extract everything after the colon
                parts = line.split(':', 1)
                if len(parts) > 1:
                    id_text = parts[1]
                    # Remove brackets and split by comma
                    id_text = id_text.replace('[', '').replace(']', '').replace('"', '').replace("'", '')
                    ids = [id.strip() for id in id_text.split(',') if id.strip()]
                    break
        
        return ids
