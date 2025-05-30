"""
Client Manager - Singleton pattern for external service connections
Handles OpenAI, Qdrant, and embedding model initialization
"""
import os
import sys
from typing import Optional, Union, List
from pathlib import Path

import openai
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


class ClientManager:
    """Singleton class to manage all external service connections"""
    
    _instance: Optional['ClientManager'] = None
    _openai_client: Optional[openai.OpenAI] = None
    _qdrant_client: Optional[QdrantClient] = None
    _embedding_model: Optional[Union[str, object]] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ClientManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_clients()
            self._initialized = True
    
    def _initialize_clients(self):
        """Initialize all external service clients"""
        print("Initializing Client Manager...")
        
        # Load environment variables
        BASE_DIR = Path(__file__).resolve().parent.parent
        env_path = BASE_DIR / ".env"
        load_dotenv(dotenv_path=env_path)
        
        # Initialize OpenAI client
        self._initialize_openai()
        
        # Initialize Qdrant client (skip in tests)
        if 'test' not in sys.argv and 'pytest' not in sys.modules:
            self._initialize_qdrant()
        else:
            print("Skipping Qdrant initialization in test mode")
            self._qdrant_client = None
    
    def _initialize_openai(self):
        """Initialize OpenAI client"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("Warning: OPENAI_API_KEY environment variable is not set")
                if not os.getenv("DEBUG", "True").lower() == "true" and 'test' not in sys.argv and 'pytest' not in sys.modules:
                    print("Please set it using: export OPENAI_API_KEY='your-api-key'")
                    sys.exit(1)
                self._openai_client = None
            else:
                self._openai_client = openai.OpenAI(api_key=api_key)
                print("OpenAI client initialized successfully")
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI client: {e}")
            self._openai_client = None
    
    def _initialize_qdrant(self):
        """Initialize Qdrant client and ensure collections exist"""
        try:
            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
            self._qdrant_client = QdrantClient(url=qdrant_url)
            print(f"Qdrant client initialized with URL: {qdrant_url}")
            
            # Ensure collections exist
            self._setup_qdrant_collections()
            
        except Exception as e:
            print(f"Warning: Failed to initialize Qdrant client: {e}")
            print("Vector search will be disabled")
            self._qdrant_client = None
    
    def _setup_qdrant_collections(self):
        """Setup required Qdrant collections"""
        if not self._qdrant_client:
            return
            
        try:
            # Use 1536 dimensions for OpenAI embeddings, 384 for sentence transformers
            vector_size = 1536 if self.get_embedding_model() == "openai" else 384
            self._qdrant_client.create_collection(
                collection_name="content_embeddings",
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            print("Qdrant collection 'content_embeddings' ready")
        except Exception as e:
            print(f"Warning: Qdrant collection setup failed: {e}")
            print("This is normal if the collection already exists")
    
    def _initialize_embedding_model(self):
        """Initialize embedding model (lazy loading)"""
        if self._embedding_model is not None:
            return
            
        embedding_type = os.getenv("EMBEDDING_MODEL_TYPE", "openai")
        if embedding_type == "openai":
            self._embedding_model = "openai"
            print("Using OpenAI embeddings")
        else:
            try:
                from sentence_transformers import SentenceTransformer
                model_name = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")
                self._embedding_model = SentenceTransformer(model_name)
                print(f"Initialized SentenceTransformer model: {model_name}")
            except ImportError:
                print("Warning: sentence-transformers not available, falling back to OpenAI embeddings")
                self._embedding_model = "openai"
    
    @property
    def openai_client(self) -> Optional[openai.OpenAI]:
        """Get the OpenAI client"""
        return self._openai_client
    
    @property
    def qdrant_client(self) -> Optional[QdrantClient]:
        """Get the Qdrant client"""
        return self._qdrant_client
    
    def get_embedding_model(self) -> Union[str, object]:
        """Get the embedding model"""
        if self._embedding_model is None:
            self._initialize_embedding_model()
        return self._embedding_model
    
    def get_embeddings(self, text: str) -> List[float]:
        """Get embeddings for text using configured method"""
        model = self.get_embedding_model()
        if model == "openai" and self._openai_client:
            # Use OpenAI embeddings
            model_name = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            response = self._openai_client.embeddings.create(model=model_name, input=text)
            return response.data[0].embedding
        elif hasattr(model, 'encode'):
            # Use sentence transformers
            return model.encode(text).tolist()
        else:
            raise ValueError("No embedding model available")
    
    def is_openai_available(self) -> bool:
        """Check if OpenAI client is available"""
        return self._openai_client is not None
    
    def is_qdrant_available(self) -> bool:
        """Check if Qdrant client is available"""
        return self._qdrant_client is not None
    
    def get_client_status(self) -> dict:
        """Get status of all clients"""
        return {
            "openai": {
                "available": self.is_openai_available(),
                "client_type": type(self._openai_client).__name__ if self._openai_client else None
            },
            "qdrant": {
                "available": self.is_qdrant_available(),
                "client_type": type(self._qdrant_client).__name__ if self._qdrant_client else None
            },
            "embedding_model": {
                "type": str(type(self._embedding_model).__name__) if self._embedding_model else None,
                "model": str(self._embedding_model) if isinstance(self._embedding_model, str) else "SentenceTransformer"
            }
        }


# Global instance
client_manager = ClientManager() 