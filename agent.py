import os
from typing import Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from retrieval import get_retriever
from tools_utils import get_directory_diag

load_dotenv()


def create_tools(codebase_name: str):

    @tool
    def search_codebase(query: str, file_path_filter: Optional[str] = None, node_type_filter: Optional[str] = None):
        """
        Search the codebase for relevant code snippets, functions, classes, or documentation.
        
        Args:
            query: The search query describing what you are looking for.
            file_path_filter: Optional. Filter results to a specific file path (partial match allowed).
            node_type_filter: Optional. Filter by node type (e.g., 'function_definition', 'class_definition').
        """
        retriever = get_retriever(codebase_name)
        
        filters = {}
        if file_path_filter:
            filters["file_path"] = file_path_filter
        if node_type_filter:
            filters["node_type"] = node_type_filter
        
        docs = retriever.search(query, filters=filters if filters else None)
        
        if not docs:
            return "No relevant code found."
            
        result = ""
        for i, doc in enumerate(docs):
            result += f"--- Result {i+1} ---\n"
            meta = doc.metadata
            file_path = meta.get("file_path", "unknown")
            name = meta.get("name", "unknown")
            node_type = meta.get("node_type", "unknown")
            
            result += f"File: {file_path}\n"
            result += f"Element: {name} ({node_type})\n"
            result += f"Context:\n{doc.page_content}\n\n"
            
        return result

    @tool
    def list_directory_structure(directory: str = ".", depth: int = 2):
        """
        List the directory structure of the codebase to understand the file organization.
        
        Args:
            directory: The directory to list (default is root ".").
            depth: The depth of the directory tree to show.
        """
        try:
             return get_directory_diag(directory, depth)
        except Exception as e:
            return f"Error listing directory: {e}"

    return [search_codebase, list_directory_structure]

def get_agent(codebase_name: str):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=api_key,
        temperature=0
    )
    
    tools = create_tools(codebase_name)
    
    system_prompt = SystemMessage(content="""You are an expert Senior Software Engineer assisting a user with their codebase.
    
    Your capabilities:
    1.  **Search Codebase**: Find code snippets using semantic search. You can filter by file path or node type if you are sure.
        - **Node Types**: `class_definition`, `function_definition`, `assignment` (for variables).
    2.  **List Directory**: Explore the file structure to understand the project layout.
    
    Guidelines:
    -   Always verify your assumptions by searching the code.
    -   When asked about how something works, first search for the implementation.
    -   If the user asks about a specific file, try searching for that file's content or listing it.
    -   Be accurate and concise. Quote relevant code snippets in your explanation.
    """)
    
    
    agent = create_react_agent(llm, tools, state_modifier=system_prompt)
    return agent
