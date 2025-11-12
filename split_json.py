#!/usr/bin/env python3
"""
JSON Article Splitter
Splits large article JSON files into smaller chunks for better LLM processing
"""

import json
import argparse
import os
import sys
from math import ceil

def split_json_file(input_file: str, num_chunks: int = 10, output_dir: str = None):
    """Split a large JSON file into smaller chunks"""
    
    # Load the original file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        print(f"📁 Loaded {len(articles)} articles from {input_file}")
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return []
    
    if len(articles) <= num_chunks:
        print(f"⚠️  File has {len(articles)} articles, less than {num_chunks} chunks. Using {len(articles)} chunks instead.")
        num_chunks = len(articles)
    
    # Calculate chunk size
    chunk_size = ceil(len(articles) / num_chunks)
    print(f"📊 Splitting into {num_chunks} chunks of ~{chunk_size} articles each")
    
    # Create output directory
    if output_dir is None:
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_dir = f"{base_name}_chunks"
    
    os.makedirs(output_dir, exist_ok=True)
    print(f"📂 Output directory: {output_dir}")
    
    # Split and save chunks
    chunk_files = []
    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, len(articles))
        
        if start_idx >= len(articles):
            break
            
        chunk = articles[start_idx:end_idx]
        chunk_filename = f"chunk_{i+1:02d}_of_{num_chunks:02d}.json"
        chunk_path = os.path.join(output_dir, chunk_filename)
        
        try:
            with open(chunk_path, 'w', encoding='utf-8') as f:
                json.dump(chunk, f, indent=2, ensure_ascii=False)
            
            chunk_files.append(chunk_path)
            print(f"✅ Created {chunk_filename} with {len(chunk)} articles ({start_idx+1}-{end_idx})")
            
        except Exception as e:
            print(f"❌ Error writing chunk {i+1}: {e}")
    
    # Create a manifest file
    manifest = {
        "original_file": input_file,
        "total_articles": len(articles),
        "num_chunks": len(chunk_files),
        "chunk_files": [os.path.basename(f) for f in chunk_files],
        "chunk_paths": chunk_files
    }
    
    manifest_path = os.path.join(output_dir, "manifest.json")
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"📋 Created manifest: {manifest_path}")
    except Exception as e:
        print(f"⚠️  Could not create manifest: {e}")
    
    print(f"\n🎉 Successfully split {input_file} into {len(chunk_files)} chunks")
    print(f"📁 Files saved in: {output_dir}")
    return chunk_files

def main():
    parser = argparse.ArgumentParser(description="Split large JSON article files into smaller chunks")
    parser.add_argument("input_file", help="Path to input JSON file")
    parser.add_argument("--chunks", type=int, default=10, help="Number of chunks to create (default: 10)")
    parser.add_argument("--output-dir", help="Output directory (default: <filename>_chunks)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"❌ Input file not found: {args.input_file}")
        sys.exit(1)
    
    chunk_files = split_json_file(args.input_file, args.chunks, args.output_dir)
    
    if chunk_files:
        print(f"\n💡 Usage examples:")
        print(f"# Process all chunks with persona finder:")
        print(f"python persona_finder_chunked.py \"{args.output_dir}\" \"your persona description\"")
        print(f"\n# Process individual chunks:")
        for i, chunk_file in enumerate(chunk_files[:3]):  # Show first 3 as examples
            print(f"python persona_finder.py \"{chunk_file}\" \"your persona\"")
        if len(chunk_files) > 3:
            print(f"# ... and {len(chunk_files) - 3} more chunks")

if __name__ == "__main__":
    main()