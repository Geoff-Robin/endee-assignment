import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types
from endee import Endee
from treeSitter import TreeSitter

# Load environment variables
load_dotenv()

ENDEE_API_KEY = os.getenv("ENDEE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not ENDEE_API_KEY:
    print("WARNING: ENDEE_API_KEY not found in environment variables.")
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in environment variables.")

# Initialize clients
if GEMINI_API_KEY:
    genai_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    genai_client = None

if ENDEE_API_KEY:
    endee_client = Endee()
else:
    endee_client = None


EXTENSION_TO_LANGUAGE: Dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "javascript",
    ".java": "java",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".rs": "rust",
    ".go": "go",
    ".zig": "zig",
    ".sh": "bash",
}

INTERESTING_NODE_TYPES = {
    "python": {
        "class_definition",
        "function_definition",
        "assignment",
    }
}

try:
    from tools import get_excluded_patterns
except ImportError:
    def get_excluded_patterns():
        return [".git", "__pycache__", ".venv", ".DS_Store", "node_modules", "dist", "build"]

def get_embedding(text: str) -> List[float]:
    """Generates embedding using Google GenAI."""
    if not genai_client:
        # Fallback placeholder if no key
        return [0.1] * 768 
    
    try:
        # User specified model: models/text-embedding-004
        response = genai_client.models.embed_content(
            model="models/text-embedding-004",
            contents=text
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"Error generating embedding: {e}")
        # Return zero vector or re-raise. For robustness, returning zero-ish vector of likely size (768 for text-embedding-004)
        return [0.0] * 768

def extract_node_name(node, content_bytes):
    """
    Attempts to extract the name of a node (function/class name).
    """
    name_node = node.child_by_field_name("name")
    if name_node:
        return content_bytes[name_node.start_byte : name_node.end_byte].decode("utf-8")
    
    # Fallback: look for identifier
    for i in range(node.child_count):
        child = node.child(i)
        if child.type == "identifier":
             return content_bytes[child.start_byte : child.end_byte].decode("utf-8")
    
    return "anonymous"

def ingest_folder(directory: str, codebase_name: str):
    """
    Recursively ingests a folder.
    """
    print(f"Starting ingestion for folder: {directory}")
    root_path = Path(directory)
    excluded_patterns = set(get_excluded_patterns())
    
    for root, dirs, files in os.walk(directory):
        # Modify dirs in-place to skip excluded
        dirs[:] = [d for d in dirs if d not in excluded_patterns and not d.startswith('.')]
        
        for file in files:
            if file in excluded_patterns or file.startswith('.'):
                continue
            
            file_path = Path(root) / file
            # Simple extension check
            if file_path.suffix.lower() in EXTENSION_TO_LANGUAGE:
                try:
                    ingest_file(str(file_path), codebase_name)
                except Exception as e:
                    print(f"Failed to ingest file {file_path}: {e}")

def ingest_file(file_path: str, codebase_name: str):
    """
    Parses and ingests a single file.
    """
    path_obj = Path(file_path)
    extension = path_obj.suffix.lower()
    
    if extension not in EXTENSION_TO_LANGUAGE:
        # Skip unsupported
        return
    
    language = EXTENSION_TO_LANGUAGE[extension]
    
    # Read content
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content_str = f.read()
    content_bytes = content_str.encode("utf-8")

    # Parse
    parser = TreeSitter(language=language)
    tree = parser.parse(file_path)
    root_node = tree.root_node
    
    nodes_to_index = []
    
    
    cursor = tree.walk()
    
    # We will collect all nodes of interest
    stack = [root_node]
    
    target_types = INTERESTING_NODE_TYPES.get(language, set())
    
    collected_blocks = [] # List of (node, name, type)

    def traverse(node):
        if node.type in target_types:
            name = extract_node_name(node, content_bytes)
            collected_blocks.append((node, name, node.type))
            if node.type == "class_definition":
                # Recurse to find methods
                for i in range(node.child_count):
                    traverse(node.child(i))
            return 
        
        # Recurse
        for i in range(node.child_count):
            traverse(node.child(i))

    if target_types:
        traverse(root_node)
    else:
        # Fallback: Treat whole file as one block
        collected_blocks.append((root_node, path_obj.name, "file"))

    if not endee_client:
        print("Endee client not initialized (missing key?). Skipping upsert.")
        return

    index = None
    try:
        index = endee_client.get_index(codebase_name)
    except Exception:
        print(f"Index '{codebase_name}' not found. Creating it...")
        try:
            index = endee_client.create_index(codebase_name, dimension=768, space_type="cosine")
        except Exception as create_error:
            print(f"Failed to create index: {create_error}")
            return
            
    if not index:
         return

    batch = []
    for node, name, node_type in collected_blocks:
        code_bytes = content_bytes[node.start_byte : node.end_byte]
        code_str = code_bytes.decode("utf-8")
        
        # Generate embedding
        vector = get_embedding(code_str)
        
        # Construct ID
        node_id = f"{file_path}::{name}::{node.start_point[0]}"
        
        batch.append({
            "id": node_id,
            "vector": vector,
            "meta": {
                "code": code_str,
                "name": name,
                "type": node_type
            },
            "filter": {
                "extension": extension,
                "file_path": str(file_path),
                "node_type": node_type,
                "name": name
            }
        })
        print(f"Prepared ingestion for: {node_id} ({node_type})")

    if batch:
        try:
            index.upsert(batch)
            print(f"Successfully upserted {len(batch)} items for {file_path}")
        except Exception as e:
            print(f"Error upserting to Endee: {e}")

    return tree
