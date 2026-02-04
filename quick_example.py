#!/usr/bin/env python3
"""
Quick Example - Article Generator
Simple demonstration of the Article Generator functionality
"""

import os
from article_generator import ArticleGenerator

def create_sample_articles():
    """Create sample articles for demonstration"""
    sample_dir = "./sample_articles"
    os.makedirs(sample_dir, exist_ok=True)
    
    sample_articles = {
        "productivity_tips.txt": """
# 5 Productivity Tips That Actually Work

In today's fast-paced world, productivity isn't just about working harder—it's about working smarter. After years of experimenting with different approaches, I've discovered these five strategies that consistently deliver results.

## 1. Time Blocking
Instead of keeping a simple to-do list, assign specific time slots to each task. This creates accountability and helps you estimate how long things actually take.

## 2. The Two-Minute Rule
If something takes less than two minutes to complete, do it immediately. This prevents small tasks from accumulating into overwhelming piles.

## 3. Batch Similar Tasks
Group related activities together. Answer all your emails at once, make all your phone calls in sequence, or batch your content creation sessions.

## 4. Digital Minimalism
Reduce notification noise. Turn off non-essential alerts and create designated times for checking messages and social media.

## 5. Regular Reviews
Weekly reviews help you adjust your approach and celebrate progress. What worked? What didn't? What needs to change?

The key is consistency. Pick one or two strategies that resonate with you and implement them gradually. Productivity is a practice, not a destination.
        """,
        
        "remote_work_guide.txt": """
# Remote Work: A Complete Guide for Success

Remote work has transformed from a rare perk to a mainstream option. Whether you're new to working from home or looking to optimize your setup, this guide covers everything you need to know.

## Setting Up Your Workspace

Your environment significantly impacts your productivity and well-being. Choose a dedicated space, even if it's just a corner of a room. Invest in a comfortable chair and good lighting. Your future self will thank you.

## Communication Best Practices

Clear communication becomes even more critical when you can't tap someone on the shoulder. Be explicit in your messages, use video calls for complex discussions, and establish regular check-ins with your team.

## Managing Distractions

Working from home means dealing with unique distractions—from household chores to family members. Create boundaries by setting specific work hours and communicating them clearly to others in your home.

## Staying Connected

Combat isolation by scheduling virtual coffee chats, participating in team activities, and maintaining relationships with colleagues. Remote work doesn't mean working in complete isolation.

## Maintaining Work-Life Balance

Without the physical separation of an office, it's easy for work to creep into personal time. Establish clear start and stop times, create transition rituals, and protect your personal time.

Remember, successful remote work requires intentional effort. Experiment with different approaches to find what works best for your situation and personality.
        """,
        
        "technology_trends.txt": """
# Technology Trends Shaping Our Future

The pace of technological change continues to accelerate. Understanding emerging trends helps us prepare for the opportunities and challenges ahead. Here are the key developments to watch.

## Artificial Intelligence Integration

AI is moving beyond specialized applications into everyday tools. From writing assistants to code generation, AI is becoming an integral part of how we work and create.

## Sustainable Technology

Green technology isn't just about electric cars anymore. We're seeing innovations in energy storage, carbon capture, and sustainable manufacturing processes that could reshape entire industries.

## Decentralized Systems

Blockchain and distributed systems are enabling new models of organization and ownership. While cryptocurrencies grab headlines, the underlying technologies have far broader applications.

## Edge Computing

Processing data closer to where it's generated reduces latency and improves privacy. This shift enables new applications in IoT, autonomous vehicles, and augmented reality.

## Quantum Computing Progress

While still experimental, quantum computing is approaching practical applications in cryptography, drug discovery, and optimization problems that are impossible for classical computers.

The common thread among these trends is their potential to democratize capabilities that were previously available only to large organizations. This creates opportunities for innovation and disruption across all sectors.
        """
    }
    
    for filename, content in sample_articles.items():
        with open(os.path.join(sample_dir, filename), 'w', encoding='utf-8') as f:
            f.write(content.strip())
    
    return sample_dir

def main():
    """Run a quick example of the Article Generator"""
    print("🚀 Article Generator - Quick Example")
    print("=" * 40)
    
    # Create sample articles if they don't exist
    sample_dir = "./sample_articles"
    if not os.path.exists(sample_dir) or not os.listdir(sample_dir):
        print("📝 Creating sample articles for demonstration...")
        create_sample_articles()
        print(f"✅ Sample articles created in {sample_dir}")
    
    try:
        # Initialize generator with sample articles
        print("\n🔧 Initializing Article Generator...")
        generator = ArticleGenerator(sample_dir, model_name="llama3.2")
        
        # Load articles
        print("📚 Loading sample articles...")
        stats = generator.load_articles()
        print(f"✅ Loaded {stats['files_processed']} articles with {stats['total_chunks']} chunks")
        
        # Show articles
        articles = generator.list_articles()
        print("\n📄 Available articles:")
        for article in articles:
            print(f"  • {article['filename']} ({article['chunks']} chunks)")
        
        # Analyze writing style
        print("\n🔍 Analyzing writing style...")
        analysis = generator.analyze_style()
        
        # Generate example content
        example_prompts = [
            "Tips for effective team collaboration",
            "The future of artificial intelligence in business",
            "How to build better habits"
        ]
        
        print("\n" + "=" * 50)
        print("🎯 Generating example content...")
        print("=" * 50)
        
        for i, prompt in enumerate(example_prompts, 1):
            print(f"\n📝 Example {i}: {prompt}")
            print("-" * 30)
            
            try:
                content = generator.generate_content(
                    prompt=prompt,
                    num_examples=2,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                # Show first 200 characters
                preview = content[:200] + "..." if len(content) > 200 else content
                print(preview)
                
                # Save to file
                filename = f"example_{i}_{prompt.replace(' ', '_')[:20]}.txt"
                filename = filename.replace('/', '_').replace('\\', '_')
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Prompt: {prompt}\n")
                    f.write(f"Generated with: {generator.model_name}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(content)
                
                print(f"💾 Saved full content to: {filename}")
                
            except Exception as e:
                print(f"❌ Generation failed: {e}")
        
        print("\n" + "=" * 50)
        print("✅ Quick example complete!")
        print("💡 Next steps:")
        print("  1. Add your own .txt articles to a folder")
        print("  2. Run: python article_generator.py")
        print("  3. Experiment with different prompts and settings")
        print("=" * 50)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Make sure you have:")
        print("  • Ollama installed and running (ollama serve)")
        print("  • The llama3.2 model installed (ollama pull llama3.2)")
        print("  • Required Python packages (pip install -r requirements.txt)")

if __name__ == "__main__":
    main()