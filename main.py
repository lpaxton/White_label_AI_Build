"""
CLI Application for Persona-Based Content Selection
Allows users to describe personas and get customized content recommendations.
"""
import argparse
import os
import sys
from dotenv import load_dotenv
from content_selector import PersonaContentSelector
from llm_providers import get_llm_provider


def print_banner():
    """Print application banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║          Persona-Based Content Selector                       ║
║          AI-Powered Content Curation System                   ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_results(results: dict):
    """
    Print the selection results in a formatted way.
    
    Args:
        results: Results dictionary from content selector.
    """
    print("\n" + "="*70)
    print("PERSONA DESCRIPTION:")
    print("="*70)
    print(results['persona'])
    
    print("\n" + "="*70)
    print(f"SELECTED CONTENT ({results['total_selected']} items):")
    print("="*70)
    
    for idx, content in enumerate(results['selected_content'], 1):
        print(f"\n{idx}. {content['title']}")
        print(f"   Category: {content['category']} | Difficulty: {content['difficulty']}")
        print(f"   Duration: {content['duration']}")
        print(f"   Description: {content['description']}")
        print(f"   Tags: {content['tags']}")
    
    print("\n" + "="*70)
    print("AI REASONING:")
    print("="*70)
    print(results['llm_reasoning'])
    print("\n")


def create_llm_provider(args):
    """
    Create LLM provider based on command-line arguments.
    
    Args:
        args: Parsed command-line arguments.
        
    Returns:
        Initialized LLM provider instance.
    """
    llm_kwargs = {}
    
    if args.provider == 'openai':
        if args.api_key:
            llm_kwargs['api_key'] = args.api_key
        if args.model:
            llm_kwargs['model'] = args.model
    elif args.provider == 'anthropic':
        if args.api_key:
            llm_kwargs['api_key'] = args.api_key
        if args.model:
            llm_kwargs['model'] = args.model
    elif args.provider == 'ollama':
        if args.model:
            llm_kwargs['model'] = args.model
        if args.ollama_host:
            llm_kwargs['host'] = args.ollama_host
    
    return get_llm_provider(args.provider, **llm_kwargs)


def interactive_mode(args):
    """
    Run in interactive mode where users can enter multiple personas.
    
    Args:
        args: Parsed command-line arguments.
    """
    print_banner()
    print(f"Provider: {args.provider.upper()}")
    print(f"XML File: {args.xml_file}")
    print(f"Max Items: {args.max_items}")
    print("\nEnter persona descriptions (type 'exit' or 'quit' to stop)\n")
    
    # Initialize LLM provider
    try:
        llm_provider = create_llm_provider(args)
        selector = PersonaContentSelector(args.xml_file, llm_provider)
    except Exception as e:
        print(f"Error initializing LLM provider: {str(e)}")
        sys.exit(1)
    
    # Interactive loop
    while True:
        try:
            print("-" * 70)
            persona = input("\nEnter persona description: ").strip()
            
            if persona.lower() in ['exit', 'quit', 'q']:
                print("\nThank you for using the Content Selector!")
                break
            
            if not persona:
                print("Please enter a valid persona description.")
                continue
            
            print("\nAnalyzing and selecting content...")
            results = selector.select_content_for_persona(persona, args.max_items)
            print_results(results)
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Please try again or type 'exit' to quit.\n")


def single_query_mode(args):
    """
    Run a single query with the provided persona.
    
    Args:
        args: Parsed command-line arguments.
    """
    print_banner()
    
    # Initialize LLM provider
    try:
        llm_provider = create_llm_provider(args)
        selector = PersonaContentSelector(args.xml_file, llm_provider)
    except Exception as e:
        print(f"Error initializing LLM provider: {str(e)}")
        sys.exit(1)
    
    # Process query
    try:
        print("Analyzing and selecting content...")
        results = selector.select_content_for_persona(args.persona, args.max_items)
        print_results(results)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description='Select content from XML based on persona descriptions using AI.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode with OpenAI
  python main.py --provider openai --xml-file sample_content.xml
  
  # Single query with Anthropic Claude
  python main.py --provider anthropic --persona "Senior software engineer learning ML" --xml-file content.xml
  
  # Using Ollama locally
  python main.py --provider ollama --model llama2 --xml-file sample_content.xml
  
Environment Variables:
  OPENAI_API_KEY      - OpenAI API key
  ANTHROPIC_API_KEY   - Anthropic API key
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--provider',
        type=str,
        required=True,
        choices=['openai', 'anthropic', 'ollama'],
        help='LLM provider to use'
    )
    
    parser.add_argument(
        '--xml-file',
        type=str,
        default='sample_content.xml',
        help='Path to XML content file (default: sample_content.xml)'
    )
    
    # Optional arguments
    parser.add_argument(
        '--persona',
        type=str,
        help='Persona description (if not provided, runs in interactive mode)'
    )
    
    parser.add_argument(
        '--max-items',
        type=int,
        default=5,
        help='Maximum number of content items to select (default: 5)'
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        help='API key for OpenAI or Anthropic (can also use env vars)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        help='Model name to use (provider-specific)'
    )
    
    parser.add_argument(
        '--ollama-host',
        type=str,
        default='http://localhost:11434',
        help='Ollama server host (default: http://localhost:11434)'
    )
    
    args = parser.parse_args()
    
    # Check if XML file exists
    if not os.path.exists(args.xml_file):
        print(f"Error: XML file '{args.xml_file}' not found.")
        sys.exit(1)
    
    # Run in appropriate mode
    if args.persona:
        single_query_mode(args)
    else:
        interactive_mode(args)


if __name__ == '__main__':
    main()
