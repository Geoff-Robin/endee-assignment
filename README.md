# Endee Codebase Agent

Endee is a powerful AI-powered codebase assistant designed to help developers navigate, understand, and interact with their codebases more effectively. By leveraging advanced parsing capabilities and semantic search, Endee allows you to query your project structure, find specific implementations, and get explanations for complex logic using natural language.

## 🚀 Project Overview

The core problem Endee solves is the cognitive load associated with navigating large or unfamiliar codebases. Developers often spend significant time searching for files, tracing function calls, and trying to understand how different components interact.

Endee solves this by:
1.  **Ingesting** your codebase: It parses your code into semantic chunks (functions, classes, etc.) to understand the structure.
2.  **Indexing**: It creates vector embeddings of these chunks for semantic retrieval.
3.  **Agent Interaction**: It provides a chat interface backed by a LangGraph agent that can use tools to search and explore the codebase to answer your questions accurately.

## 🛠 System Design & Technical Approach

Endee is built using a modern stack of AI and data engineering tools:

### Core Components
-   **Frontend**: Built with **Streamlit** (`app.py`), providing an interactive chat interface and sidebar for configuration.
-   **Agent**: A **LangGraph** ReAct agent (`agent.py`) powered by **Google Gemini 1.5 Flash**. It orchestrates the reasoning process and decides when to search the codebase or explore the directory structure.
-   **Ingestion Engine**:
    -   Uses **Tree-sitter** (`treeSitter.py`) for robust, language-specific parsing of source code. It supports multiple languages including Python, JavaScript, Java, C++, Go, Rust, and more.
    -   Extracts meaningful nodes (like Classes and Functions) rather than just splitting by text chunks (`ingestion_utils.py`).
-   **Vector Store**:
    -   Uses **Endee** (a vector database client) to store and retrieve code embeddings.
    -   Embeddings are generated using **Google's text-embedding-004** model.
-   **Retrieval**: `retrieval.py` implements a custom retriever compatible with LangChain that performs semantic search against the Endee vector index, with support for metadata filtering (by file path, node type, etc.).

## 📖 How to Use Endee

1.  **Start the Application**: Launch the Streamlit app.
2.  **Ingest a Codebase**:
    -   In the sidebar, enter a **Codebase Name** (e.g., "my-project").
    -   Enter the **Codebase Path** (absolute path to the project directory you want to analyze).
    -   Click **Ingest Codebase**.
    -   *Note: This process parses files and uploads embeddings to the vector store. It may take a few moments depending on the size of the project.*
3.  **Chat with the Agent**:
    -   Once ingestion is complete (or if you already have an index), the agent becomes active.
    -   Ask questions like:
        -   *"How does the authentication middleware work?"*
        -   *"Where is the User class defined?"*
        -   *"Explain the logic in `process_orders` function."*
        -   *"Show me the directory structure of the `src` folder."*

## ⚙️ Setup and Execution

### Prerequisites
-   **Python 3.12+**
-   **Google Gemini API Key**: You need a valid API key from Google AI Studio.
-   **Endee API Key**: You need an API key for the Endee vector database service.

### Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd endee-ingest
    ```

2.  **Set up Environment Variables**:
    Create a `.env` file in the root directory and add your keys:
    ```env
    GEMINI_API_KEY=your_gemini_api_key_here
    ENDEE_API_KEY=your_endee_api_key_here
    ```

3.  **Install Dependencies**:
    We recommend using `uv` or `pip` to install the dependencies defined in `pyproject.toml`.

    Using `pip`:
    ```bash
    pip install .
    ```

    Or manually installing requirements:
    ```bash
    pip install streamlit endee google-genai python-dotenv langchain langchain-google-genai langchain-community seedir tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-go tree-sitter-java tree-sitter-cpp tree-sitter-rust tree-sitter-bash tree-sitter-zig
    ```

### Running the App

Run the Streamlit application:

```bash
streamlit run app.py
```

The application will open in your default browser (usually at `http://localhost:8501`).
