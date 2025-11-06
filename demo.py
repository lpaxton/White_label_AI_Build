"""
Demo script showing the application in action with a mock LLM.
This demonstrates the core functionality without requiring API keys.
"""
import sys
from xml_parser import ContentParser
from content_selector import PersonaContentSelector


class DemoLLMProvider:
    """Mock LLM provider for demonstration purposes."""
    
    def __init__(self, scenario='developer'):
        self.scenario = scenario
    
    def generate_response(self, prompt):
        """Generate a mock response based on the scenario."""
        
        if 'manager' in prompt.lower() or 'leadership' in prompt.lower():
            return """SELECTED CONTENT IDS: 3, 6, 9

REASONING:
For a manager or someone learning leadership skills, I've selected:

1. Leadership Essentials (ID: 3) - This is fundamental for any manager, covering communication, decision-making, and team management. It's at an intermediate level which is perfect for someone stepping into a leadership role.

2. Agile Project Management (ID: 6) - Essential for modern managers to understand how to lead teams effectively using Agile methodologies. The Scrum and Kanban knowledge will be immediately applicable.

3. Financial Analysis for Managers (ID: 9) - Managers need to understand financials to make informed business decisions. This course provides the necessary foundation for reading and interpreting financial data.

These three courses provide a well-rounded foundation for management skills, covering people management, project execution, and business acumen."""
        
        elif 'beginner' in prompt.lower() or 'new' in prompt.lower() or 'junior' in prompt.lower():
            return """SELECTED CONTENT IDS: 1, 4, 8

REASONING:
For a beginner or junior professional, I've selected foundational content:

1. Introduction to Cloud Computing (ID: 1) - This beginner-level course provides essential knowledge about cloud technologies, which are fundamental in modern tech. The 30-minute duration makes it accessible without being overwhelming.

2. Data Science Fundamentals (ID: 4) - Even for non-data roles, understanding basic statistics and data visualization is valuable. This beginner course provides practical skills that apply across many roles.

3. Customer Service Excellence (ID: 8) - Soft skills are crucial for career success. This course teaches communication and problem-solving skills that are valuable regardless of technical role.

These courses are all beginner-level, relatively short, and provide broad foundational knowledge suitable for someone starting their career."""
        
        elif 'data' in prompt.lower() or 'analytics' in prompt.lower() or 'science' in prompt.lower():
            return """SELECTED CONTENT IDS: 4, 7, 12

REASONING:
For someone interested in data science and analytics:

1. Data Science Fundamentals (ID: 4) - Perfect starting point covering statistics, visualization, and basic ML concepts. Essential foundation before moving to advanced topics.

2. Machine Learning with TensorFlow (ID: 7) - Advanced course for building and training neural networks. This takes the theoretical knowledge from fundamentals and applies it to real-world deep learning projects.

3. SQL for Data Analysis (ID: 12) - Crucial skill for any data professional. Being able to extract and analyze data from databases is fundamental to all data work.

This progression takes someone from fundamentals through practical SQL skills and into advanced machine learning, providing a comprehensive data science learning path."""
        
        elif 'devops' in prompt.lower() or 'infrastructure' in prompt.lower():
            return """SELECTED CONTENT IDS: 1, 5, 10

REASONING:
For someone interested in DevOps and infrastructure:

1. Introduction to Cloud Computing (ID: 1) - Essential foundation for understanding IaaS, PaaS, and SaaS models that are core to modern DevOps practices.

2. Cybersecurity Best Practices (ID: 5) - DevOps engineers must understand security to build secure pipelines and infrastructure. This covers essential security practices for protecting systems.

3. DevOps Practices (ID: 10) - Advanced course covering CI/CD, containerization, and infrastructure as code - the core technical skills needed for a DevOps role.

These courses provide both the foundational cloud knowledge and the advanced technical DevOps skills needed for this career path."""
        
        else:  # Default: well-rounded professional development
            return """SELECTED CONTENT IDS: 2, 3, 5, 6, 11

REASONING:
For general professional development, I've selected a diverse set of skills:

1. Advanced Python Programming (ID: 2) - Technical skill development is always valuable, and Python is widely applicable across many domains.

2. Leadership Essentials (ID: 3) - Leadership skills are important even for individual contributors and help with career advancement.

3. Cybersecurity Best Practices (ID: 5) - Security awareness is crucial for all professionals in today's digital workplace.

4. Agile Project Management (ID: 6) - Understanding Agile helps in working effectively in modern team environments.

5. Marketing Strategy Basics (ID: 11) - Understanding business strategy provides valuable perspective regardless of role.

This diverse selection helps build both technical and soft skills for well-rounded professional growth."""


def run_demo():
    """Run the demonstration."""
    
    print("="*70)
    print("PERSONA-BASED CONTENT SELECTOR - DEMONSTRATION")
    print("="*70)
    print("\nThis demo shows how the AI analyzes personas and selects content.")
    print("(Using mock LLM - no API keys required)\n")
    
    # Demo scenarios
    scenarios = [
        {
            'persona': 'New manager promoted from individual contributor, needs leadership skills',
            'scenario': 'manager'
        },
        {
            'persona': 'Junior developer just graduated from coding bootcamp, starting first tech job',
            'scenario': 'beginner'
        },
        {
            'persona': 'Data analyst wanting to transition into machine learning and AI',
            'scenario': 'data'
        },
        {
            'persona': 'System administrator wanting to learn DevOps and cloud infrastructure',
            'scenario': 'devops'
        }
    ]
    
    for idx, scenario in enumerate(scenarios, 1):
        print("\n" + "="*70)
        print(f"DEMO SCENARIO {idx} of {len(scenarios)}")
        print("="*70)
        
        # Create mock provider and selector
        mock_provider = DemoLLMProvider(scenario=scenario['scenario'])
        selector = PersonaContentSelector('sample_content.xml', mock_provider)
        
        # Run selection
        results = selector.select_content_for_persona(scenario['persona'])
        
        # Display results
        print(f"\nPERSONA: {results['persona']}")
        print(f"\nSELECTED {results['total_selected']} CONTENT ITEMS:\n")
        
        for i, content in enumerate(results['selected_content'], 1):
            print(f"{i}. {content['title']}")
            print(f"   Category: {content['category']} | Difficulty: {content['difficulty']}")
            print(f"   Duration: {content['duration']}")
            print(f"   Tags: {content['tags']}")
            print()
        
        print("AI REASONING:")
        print("-" * 70)
        # Print reasoning but limit length for readability
        reasoning_lines = results['llm_reasoning'].split('\n')
        for line in reasoning_lines[:15]:  # First 15 lines
            print(line)
        if len(reasoning_lines) > 15:
            print("...")
        
        if idx < len(scenarios):
            input("\nPress Enter to see next scenario...")
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nTo use with real LLMs, run:")
    print("  python main.py --provider openai --xml-file sample_content.xml")
    print("  python main.py --provider anthropic --xml-file sample_content.xml")
    print("  python main.py --provider ollama --model llama2 --xml-file sample_content.xml")
    print("\nSee USAGE.md for more examples!")


if __name__ == '__main__':
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Goodbye!")
        sys.exit(0)
