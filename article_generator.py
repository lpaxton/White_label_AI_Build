#!/usr/bin/env python3
"""
Article Generator - RAG + Ollama
Generate new articles in your writing style using your existing content as examples.
"""

import os
import json
import re
from typing import List, Dict, Optional
from pathlib import Path
import requests
import chromadb

class ArticleGenerator:
    def __init__(self, articles_dir: str, model_name: str = "llama3.2", ollama_url: str = "http://localhost:11434"):
        """
        Initialize the Article Generator

        Args:
        articles_dir: Directory containing your article .txt files
        model_name: Ollama model to use for generation
        ollama_url: URL of your Ollama server
        """
        self.articles_dir = Path(articles_dir)
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.articles_loaded = False

        # Initialize ChromaDB with new client configuration
        self.chroma_client = chromadb.PersistentClient(
            path="./article_generator_db"
        )

        # Create or get collection
        try:
            self.collection = self.chroma_client.get_collection("articles")
        except:
            self.collection = self.chroma_client.create_collection("articles")

    def load_articles(self, force_reload: bool = False) -> Dict[str, int]:
        """
        Load articles from directory into vector database

        Args:
        force_reload: If True, reload even if already loaded

        Returns:
        Dict with loading statistics
        """
        if self.articles_loaded and not force_reload:
            print(" Articles already loaded. Use force_reload=True to reload.")
            return {"status": "already_loaded"}

        if not self.articles_dir.exists():
            raise FileNotFoundError(f"Articles directory not found: {self.articles_dir}")

        # Find all .txt files
        article_files = list(self.articles_dir.glob("*.txt"))

        if not article_files:
            raise FileNotFoundError(f"No .txt files found in {self.articles_dir}")

        print(f" Loading {len(article_files)} articles...")

        # Clear existing collection if reloading
        if force_reload:
            try:
                self.chroma_client.delete_collection("articles")
                self.collection = self.chroma_client.create_collection("articles")
            except:
                pass

        all_chunks = []
        all_metadatas = []
        all_ids = []

        total_chunks = 0

        for i, file_path in enumerate(article_files):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                if not content:
                    continue

                # Split into chunks
                chunks = self._chunk_text(content)

                for j, chunk in enumerate(chunks):
                    chunk_id = f"article_{i}_{j}"
                    metadata = {
                        "filename": file_path.name,
                        "chunk_index": j,
                        "total_chunks": len(chunks)
                    }

                    all_chunks.append(chunk)
                    all_metadatas.append(metadata)
                    all_ids.append(chunk_id)
                    total_chunks += 1

                if (i + 1) % 10 == 0:
                    print(f" Processed {i + 1}/{len(article_files)} files...")

            except Exception as e:
                print(f" Error processing {file_path.name}: {e}")
                continue

        if not all_chunks:
            raise ValueError("No valid content found in article files")

        # Add to ChromaDB in batches
        batch_size = 100
        for i in range(0, len(all_chunks), batch_size):
            batch_chunks = all_chunks[i:i + batch_size]
            batch_metadata = all_metadatas[i:i + batch_size]
            batch_ids = all_ids[i:i + batch_size]

            self.collection.add(
                documents=batch_chunks,
                metadatas=batch_metadata,
                ids=batch_ids
            )

            print(f" Added batch {(i // batch_size) + 1}/{(len(all_chunks) - 1) // batch_size + 1}")

        self.articles_loaded = True

        stats = {
            "files_processed": len(article_files),
            "total_chunks": total_chunks,
            "status": "loaded"
        }

        print(f" Loaded {len(article_files)} articles ({total_chunks} chunks)")
        return stats

    def _chunk_text(self, text: str, chunk_size: int = 1500, overlap: int = 300) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            if end >= len(text):
                chunks.append(text[start:])
                break

            # Try to break at sentence boundary
            chunk = text[start:end]
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')

            break_point = max(last_period, last_newline)

            if break_point > start + chunk_size // 2:
                end = start + break_point + 1

            chunks.append(text[start:end])
            start = end - overlap

        return chunks

    def generate_content(self, prompt: str, num_examples: int = 3, temperature: float = 0.7, max_tokens: int = 5000) -> str:
        """
        Generate new content based on prompt and similar examples

        Args:
        prompt: Topic or prompt for generation
        num_examples: Number of similar chunks to use as examples
        temperature: Creativity level (0.0-1.0)
        max_tokens: Maximum length of generated content

        Returns:
        Generated article content
        """
        if not self.articles_loaded:
            raise ValueError("Articles not loaded. Call load_articles() first.")

        print(f" Finding {num_examples} similar examples for: '{prompt}'")

        # Search for similar content
        results = self.collection.query(
            query_texts=[prompt],
            n_results=num_examples
        )

        if not results['documents'] or not results['documents'][0]:
            raise ValueError("No similar content found. Try a different prompt or load more articles.")

        similar_chunks = results['documents'][0]

        print(f" Found {len(similar_chunks)} relevant examples")

        # Optimize examples to prevent overly long prompts
        optimized_examples = []
        total_length = 0
        max_prompt_length = 8000  # Limit total prompt length

        for i, chunk in enumerate(similar_chunks):
            # Truncate very long chunks
            if len(chunk) > 1000:
                chunk = chunk[:1000] + "..."

            example_text = f"Example {i+1}:\n{chunk}"

            # Check if adding this example would exceed our limit
            if total_length + len(example_text) > max_prompt_length:
                print(f" Truncating examples to stay within prompt limits ({len(optimized_examples)} examples used)")
                break

            optimized_examples.append(example_text)
            total_length += len(example_text)

        if not optimized_examples:
            # Fallback: use at least one example, even if it's long
            optimized_examples = [f"Example 1:\n{similar_chunks[0][:800]}..."]

        examples_text = "\n\n---\n\n".join(optimized_examples)

        full_prompt = f"""You are a professional content writer. Based on the writing style and tone of the examples below, write a new article about: {prompt}

Here are examples of the writing style to emulate:

{examples_text}

---

IMPORTANT: Write ONLY the final article content. Do not include thinking processes, explanations, or meta-commentary. Start directly with the article title or opening paragraph.

Write a comprehensive, well-structured article about "{prompt}" in the same writing style, tone, and format as the examples above. The article should be detailed, informative, and engaging. Include multiple sections, practical examples, and actionable insights. Aim for {max_tokens//5} to {max_tokens//3} words to provide thorough coverage of the topic.

Article:"""

        print(f" Prompt length: {len(full_prompt)} characters ({len(optimized_examples)} examples)")

        print(" Generating content with Ollama...")

        # Special handling for DeepSeek models
        if "deepseek" in self.model_name.lower():
            print(" Using DeepSeek-specific prompting strategy")
            deepseek_prompt = f"""Write a comprehensive professional article about: {prompt}

Use this writing style as a guide:
{optimized_examples[0][:300] if optimized_examples else "Professional, informative tone"}

Write a detailed article with multiple sections, examples, and actionable insights. Aim for {max_tokens//5} to {max_tokens//3} words:"""

            try:
                response = self._call_ollama(deepseek_prompt, temperature, max_tokens)
                if response and len(response) > 50:
                    print(" DeepSeek content generated successfully!")
                    return response
            except Exception as e:
                print(f" DeepSeek failed: {e}")
                # Fall through to regular retry logic

        # Try generation with retry logic
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    print(f" Retry attempt {attempt}/{max_retries}")
                    simple_prompt = f"""Write a detailed {max_tokens//5}-{max_tokens//3} word article about: {prompt}

Include multiple sections, examples, and practical insights. Make sure to write a complete article with a proper conclusion.

Article:"""
                    response = self._call_ollama(simple_prompt, temperature, max_tokens)
                else:
                    response = self._call_ollama(full_prompt, temperature, max_tokens)

                if response and len(response) > 50:
                    if self._is_article_complete(response):
                        print(" Content generated successfully!")
                        return response
                    else:
                        print(" Article appears incomplete, will retry with different approach")
                        if attempt == max_retries:
                            if len(response) > 500:
                                print(" Returning incomplete but substantial content")
                                return response
                            raise Exception("Article appears incomplete")
                else:
                    raise Exception(f"Generated content too short: {len(response)} chars")

            except Exception as e:
                if attempt == max_retries:
                    if "deepseek" in self.model_name.lower():
                        raise Exception(f"DeepSeek-R1 '{self.model_name}' failed to generate content. This model is known to be finicky. Try: 1) Use llama3.2 or mistral instead 2) Very simple prompts work better 3) Ensure you have 32GB+ RAM 4) Try restarting Ollama 5) DeepSeek may refuse certain topics")
                    else:
                        raise Exception(f"Model '{self.model_name}' failed to generate content after {max_retries + 1} attempts. Try: 1) Use a different model (llama3.2 or mistral) 2) Simplify your prompt 3) Reduce number of examples 4) Restart Ollama")
                else:
                    print(f" Attempt {attempt + 1} failed: {e}")

    def _is_article_complete(self, text: str) -> bool:
        """Check if an article appears to be complete"""
        text = text.strip()
        if len(text) < 100:
            return False

        if text.endswith(('.', '!', '?', '"', "'")):
            return True

        last_lines = text.split('\n')[-3:]
        conclusion_indicators = ['conclusion', 'summary', 'final', 'end', 'ultimately', 'in summary']

        for line in last_lines:
            if any(indicator in line.lower() for indicator in conclusion_indicators):
                return True

        return len(text) > 1000

    def _call_ollama(self, prompt: str, temperature: float = 0.7, max_tokens: int = 5000) -> str:
        """Call Ollama API for text generation with dynamic timeout"""
        base_timeout = 60
        if "70b" in self.model_name.lower() or "deepseek" in self.model_name.lower():
            timeout = 300
        elif "13b" in self.model_name.lower() or len(self.model_name) > 10:
            timeout = 180
        else:
            timeout = 120

        if max_tokens > 1500:
            timeout += 60

        print(f" Calling Ollama (model: {self.model_name}, timeout: {timeout}s)...")

        options = {
            "temperature": temperature,
            "num_predict": max_tokens,
            "stop": [],
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }

        if "deepseek" in self.model_name.lower():
            options.update({
                "temperature": min(temperature, 0.3),
                "top_p": 0.8,
                "repeat_penalty": 1.05,
                "top_k": 20,
                "stop": [],
            })
            print(f" Using DeepSeek-optimized parameters: temp={options['temperature']}")
        else:
            options["stop"] = ["---END---", "###END###"]

        try:
            response = requests.post(f"{self.ollama_url}/api/generate", json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": options
            }, timeout=timeout)

            if not response.ok:
                error_text = ""
                try:
                    error_data = response.json()
                    error_text = error_data.get("error", "Unknown error")
                except:
                    error_text = f"HTTP {response.status_code}"
                raise Exception(f"Ollama API error: {error_text}")

            data = response.json()
            generated_text = data.get("response", "").strip()

            print(f" Ollama raw response: {data}")
            print(f" Generated text length: {len(generated_text) if generated_text else 0}")

            if not generated_text:
                error_msg = "Ollama returned empty response"
                if "error" in data:
                    error_msg += f": {data['error']}"
                elif data.get("done", False) and not generated_text:
                    error_msg += ". The model completed but produced no content. This may be due to: 1) Prompt too complex 2) Model overloaded 3) Content filtered"
                else:
                    error_msg += f". Raw response: {data}"
                raise Exception(error_msg)

            original_length = len(generated_text)
            if "<think>" in generated_text and "</think>" in generated_text:
                think_end = generated_text.find("</think>")
                if think_end != -1:
                    article_content = generated_text[think_end + 8:].strip()
                    if article_content:
                        generated_text = article_content
                        print(f" Extracted article content from DeepSeek thinking format ({len(article_content)} chars from {original_length} total)")
                    else:
                        print(" No content found after </think>, using full response")
            elif "<think>" in generated_text:
                print(" Incomplete thinking block detected, extracting what we can")
                think_start = generated_text.find("<think>")
                if think_start > 0:
                    generated_text = generated_text[:think_start].strip()
                    print(f" Extracted content before thinking block: {len(generated_text)} chars")
                else:
                    raise Exception("Response contains incomplete thinking block with no content. Try reducing the number of examples or using a different model.")

            import re
            cleaned_text = re.sub(r'<[^>]+>', '', generated_text).strip()
            if cleaned_text != generated_text:
                print(f" Cleaned XML tags: {len(generated_text)} -> {len(cleaned_text)} chars")
                generated_text = cleaned_text

            last_sentence = generated_text.strip()
            if (last_sentence and not last_sentence.endswith(('.', '!', '?', '"', "'")) and
                    not last_sentence.endswith((':', ';', ')')) and
                    len(last_sentence.split()[-1]) < 20):
                print(f" Content appears cut off (ends with: '{last_sentence[-50:]}')")
                sentences = generated_text.split('.')
                if len(sentences) > 1:
                    complete_content = '.'.join(sentences[:-1]) + '.'
                    print(f" Trimmed incomplete sentence: {len(generated_text)} -> {len(complete_content)} chars")
                    generated_text = complete_content

            if not generated_text or len(generated_text) < 100:
                raise Exception(f"Generated content is too short ({len(generated_text)} chars) or empty after processing. The model may have only returned thinking process or been filtered. Try using a different model, simpler prompt, or adjusting the settings.")

            return generated_text

        except requests.exceptions.Timeout:
            raise Exception(f"Ollama request timed out after {timeout} seconds. Try using a smaller model or reducing the number of examples.")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Cannot connect to Ollama at {self.ollama_url}. Make sure Ollama is running and accessible.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to connect to Ollama at {self.ollama_url}: {e}")

    def analyze_style(self) -> Dict[str, any]:
        """
        Analyze the writing style of loaded articles

        Returns:
        Dictionary with style analysis
        """
        if not self.articles_loaded:
            raise ValueError("Articles not loaded. Call load_articles() first.")

        print(" Analyzing writing style...")

        all_docs = self.collection.get()
        documents = all_docs['documents']

        if not documents:
            return {"error": "No documents found"}

        all_text = " ".join(documents)

        sentences = re.split(r'[.!?]+', all_text)
        sentences = [s.strip() for s in sentences if s.strip()]

        words = all_text.split()

        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0

        formal_words = ['therefore', 'furthermore', 'consequently', 'moreover', 'however']
        casual_words = ['really', 'pretty', 'quite', 'very', 'actually', 'basically']
        technical_words = ['implementation', 'algorithm', 'methodology', 'analysis', 'framework']

        formal_count = sum(all_text.lower().count(word) for word in formal_words)
        casual_count = sum(all_text.lower().count(word) for word in casual_words)
        technical_count = sum(all_text.lower().count(word) for word in technical_words)

        tone_scores = {
            'formal': formal_count,
            'casual': casual_count,
            'technical': technical_count
        }

        dominant_tone = max(tone_scores.keys(), key=lambda k: tone_scores[k])

        analysis = {
            "total_documents": len(documents),
            "total_words": len(words),
            "total_sentences": len(sentences),
            "avg_sentence_length": round(avg_sentence_length, 1),
            "avg_word_length": round(avg_word_length, 1),
            "dominant_tone": dominant_tone,
            "tone_scores": tone_scores,
            "vocabulary_richness": len(set(word.lower() for word in words)) / len(words) if words else 0
        }

        print(" Style Analysis Results:")
        print(f" Total articles processed: {analysis['total_documents']}")
        print(f" Average sentence length: {analysis['avg_sentence_length']} words")
        print(f" Average word length: {analysis['avg_word_length']} characters")
        print(f" Dominant tone: {analysis['dominant_tone']}")
        print(f" Vocabulary richness: {analysis['vocabulary_richness']:.2%}")

        return analysis

    def list_articles(self) -> List[Dict[str, str]]:
        """List all loaded articles with metadata"""
        if not self.articles_loaded:
            return []

        all_docs = self.collection.get()
        metadatas = all_docs['metadatas']

        files = {}
        for meta in metadatas:
            filename = meta['filename']
            if filename not in files:
                files[filename] = {
                    'filename': filename,
                    'chunks': 0
                }
            files[filename]['chunks'] += 1

        return list(files.values())


def main():
    """Interactive mode for the Article Generator"""
    print(" Article Generator - RAG + Ollama")
    print("=" * 50)

    articles_dir = input("Enter path to your articles directory (or press Enter for './my_articles'): ").strip()
    if not articles_dir:
        articles_dir = "./my_articles"

    if not os.path.exists(articles_dir):
        print(f" Directory not found: {articles_dir}")
        print("Please create the directory and add your .txt files, then run again.")
        return

    model_name = input("Enter Ollama model name (or press Enter for 'llama3.2'): ").strip()
    if not model_name:
        model_name = "llama3.2"

    try:
        print(f"\n Initializing generator with model: {model_name}")
        generator = ArticleGenerator(articles_dir, model_name=model_name)

        print(" Loading articles...")
        stats = generator.load_articles()
        print(f" Loaded {stats['files_processed']} files with {stats['total_chunks']} chunks")

        print("\n Analyzing your writing style...")
        analysis = generator.analyze_style()

        print("\n" + "=" * 50)
        print(" Ready to generate! Enter topics or type 'quit' to exit.")
        print(" Tips:")
        print(" Be specific: 'The benefits of remote work for developers'")
        print(" Match your content: Use topics similar to your existing articles")
        print(" Experiment: Try different phrasings for different results")
        print("=" * 50)

        while True:
            prompt = input("\n Topic/Prompt: ").strip()

            if prompt.lower() in ['quit', 'exit', 'q']:
                break

            if not prompt:
                continue

            try:
                print("\n Generation Settings:")
                num_examples = input(f"Number of examples to use (default 3): ").strip()
                num_examples = int(num_examples) if num_examples else 3

                temperature = input(f"Creativity level 0.0-1.0 (default 0.7): ").strip()
                temperature = float(temperature) if temperature else 0.7

                content = generator.generate_content(
                    prompt=prompt,
                    num_examples=num_examples,
                    temperature=temperature
                )

                print("\n" + "="*50)
                print(" GENERATED CONTENT:")
                print("="*50)
                print(content)
                print("="*50)

                save = input("\n Save to file? (y/N): ").strip().lower()
                if save in ['y', 'yes']:
                    filename = f"generated_{prompt.replace(' ', '_')[:30]}.txt"
                    filename = re.sub(r'[^\w\-_.]', '', filename)

                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"Topic: {prompt}\n")
                        f.write(f"Generated: {generator.model_name}\n")
                        f.write(f"Examples: {num_examples}, Temperature: {temperature}\n")
                        f.write("\n" + "="*50 + "\n\n")
                        f.write(content)

                    print(f" Saved to: {filename}")

            except Exception as e:
                print(f" Generation error: {e}")
                print(" Try a different prompt or check your Ollama connection")

    except Exception as e:
        print(f" Error: {e}")
        print("\n Troubleshooting:")
        print(" Make sure Ollama is running: ollama serve")
        print(f" Check if model exists: ollama list")
        print(f" Install model if needed: ollama pull {model_name}")
        print(" Verify articles directory contains .txt files")

if __name__ == "__main__":
    main()
