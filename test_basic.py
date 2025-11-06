"""
Test suite for the persona-based content selector.
Basic tests that don't require API keys.
"""
import sys
import os

# Test 1: XML Parser
print("Test 1: XML Parser")
from xml_parser import ContentParser

parser = ContentParser('sample_content.xml')
content = parser.get_all_content()
assert len(content) == 12, "Should parse 12 content items"
assert content[0]['title'] == "Introduction to Cloud Computing", "First item title should match"
assert all('id' in item for item in content), "All items should have ID"
print("✓ XML Parser tests passed")

# Test 2: LLM Provider Factory
print("\nTest 2: LLM Provider Factory")
from llm_providers import get_llm_provider

# Test that factory recognizes provider types
try:
    # This will fail due to missing API key, but factory should work
    get_llm_provider('invalid_provider')
    assert False, "Should raise ValueError for invalid provider"
except ValueError as e:
    assert "Unknown provider type" in str(e)
    print("✓ LLM Provider factory correctly validates provider types")

# Test 3: Content Selector Initialization
print("\nTest 3: Content Selector Initialization")
from content_selector import PersonaContentSelector

# Create a mock LLM provider for testing
class MockLLMProvider:
    def generate_response(self, prompt):
        return """SELECTED CONTENT IDS: 1, 2, 3

REASONING:
These items are beginner-friendly and provide a good foundation."""

mock_provider = MockLLMProvider()
selector = PersonaContentSelector('sample_content.xml', mock_provider)
assert selector.parser is not None, "Parser should be initialized"
print("✓ Content Selector initialization passed")

# Test 4: Content Selection with Mock Provider
print("\nTest 4: Content Selection Logic")
results = selector.select_content_for_persona("A beginner in tech", max_items=5)
assert results['persona'] == "A beginner in tech", "Persona should match"
assert 'selected_content' in results, "Should have selected content"
assert 'llm_reasoning' in results, "Should have reasoning"
assert results['total_selected'] == 3, "Should select 3 items (from mock response)"
print("✓ Content selection logic passed")

# Test 5: Response Parsing
print("\nTest 5: LLM Response Parsing")
test_response = "SELECTED CONTENT IDS: 4, 7, 12\n\nREASONING: Advanced content"
ids = selector._parse_llm_response(test_response)
assert len(ids) == 3, "Should extract 3 IDs"
assert '4' in ids and '7' in ids and '12' in ids, "Should extract correct IDs"
print("✓ Response parsing passed")

# Test 6: Main CLI Help
print("\nTest 6: CLI Help Display")
import subprocess
result = subprocess.run(
    [sys.executable, 'main.py', '--help'],
    capture_output=True,
    text=True
)
assert result.returncode == 0, "Help should display successfully"
assert 'provider' in result.stdout.lower(), "Help should mention provider option"
print("✓ CLI help display passed")

print("\n" + "="*50)
print("All tests passed! ✓")
print("="*50)
print("\nNote: API integration tests require valid API keys.")
print("Set OPENAI_API_KEY or ANTHROPIC_API_KEY to test those providers.")
print("Install and run Ollama locally to test the Ollama provider.")
