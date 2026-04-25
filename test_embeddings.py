"""
Embedding Test Script - Production Ready
Run this to verify embeddings are working correctly
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'

def test_embeddings():
    print("=" * 60)
    print("GOOGLE EMBEDDINGS VERIFICATION TEST")
    print("=" * 60)

    # Load environment explicitly
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found!")
        return False
    
    load_dotenv(override=True)
    api_key = os.getenv("GOOGLE_API_KEY", "")
    
    print(f"API Key found: {'✓' if api_key else '❌'}")
    if api_key:
        print(f"API Key starts with: {api_key[:8]}...")
    print()

    if not api_key or api_key == "your_google_api_key_here":
        print("❌ ERROR: No valid API key in .env file")
        print()
        print("👉 Please add your Google API key to .env:")
        print("   GOOGLE_API_KEY=your_api_key_here")
        print()
        print("👉 Get free key at: https://aistudio.google.com/app/apikey")
        return False

    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        
        print("🔍 Testing GoogleGenerativeAIEmbeddings...")
        
        # ✅ EXPLICIT API KEY PASSING (critical fix!)
        embeddings = GoogleGenerativeAIEmbeddings(
            model="text-embedding-004",
            google_api_key=api_key,
            task_type="retrieval_document"
        )

        print("✅ Embeddings class initialized")
        print("🔄 Generating test embedding...")

        # Test embedding
        test_text = "This is a test for the embedding system"
        vector = embeddings.embed_query(test_text)

        print(f"✅ Embedding generated successfully!")
        print(f"📐 Dimensions: {len(vector)}")
        print(f"🔢 First 5 values: {vector[:5]}")
        print()

        # Test ChromaDB integration
        print("🔍 Testing ChromaDB integration...")
        from langchain_chroma import Chroma
        from langchain_core.documents import Document

        test_docs = [
            Document(page_content="Test document 1", metadata={"source": "test"}),
            Document(page_content="Test document 2", metadata={"source": "test"})
        ]

        vector_store = Chroma.from_documents(
            documents=test_docs,
            embedding=embeddings,
            collection_name="test_collection"
        )

        print("✅ ChromaDB initialized successfully")

        # Test search
        results = vector_store.similarity_search("test", k=1)
        print(f"✅ Similarity search returned {len(results)} results")
        print()

        # Cleanup
        vector_store._client.delete_collection("test_collection")
        print("🧹 Test collection cleaned up")
        print()
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("✅ Embeddings system is 100% operational")
        print("✅ You can now run the Streamlit app")
        print()
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}: {str(e)}")
        print()
        print("🔧 Troubleshooting steps:")
        print("1. Verify your API key is valid and not expired")
        print("2. Run: pip install --upgrade langchain-google-genai")
        print("3. Verify you have internet connectivity")
        print("4. Check Google AI Studio for API quota limits")
        return False


if __name__ == "__main__":
    success = test_embeddings()
    sys.exit(0 if success else 1)