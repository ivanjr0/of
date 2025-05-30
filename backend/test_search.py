#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from app.llms import extract_search_keywords, search_relevant_content
from app.models import Content
from django.contrib.auth.models import User

def test_search_components():
    print("=== Testing Search Components ===")
    
    # Test 1: Keyword extraction
    print("\n1. Testing keyword extraction...")
    test_query = "What are the key Python libraries for machine learning?"
    keywords = extract_search_keywords(test_query)
    print(f"Query: {test_query}")
    print(f"Extracted keywords: {keywords}")
    
    # Test 2: Check if we have test content
    print("\n2. Checking available content...")
    try:
        user = User.objects.get(username='testuser')
        contents = Content.objects.filter(user=user, processed=True)
        print(f"Found {len(contents)} processed contents for user {user.username}")
        for content in contents:
            print(f"  - {content.name} (concepts: {content.key_concepts})")
    except User.DoesNotExist:
        print("Test user not found")
        return
    
    # Test 3: Test search function with debug
    print("\n3. Testing full search function...")
    results, debug_info = search_relevant_content(
        test_query, 
        user.id, 
        limit=3, 
        include_debug=True
    )
    
    print(f"Found {len(results)} content items")
    print(f"Debug info:")
    print(f"  - Keywords extracted: {debug_info['query_analysis']['extracted_keywords']}")
    print(f"  - Keyword search time: {debug_info['query_analysis']['keyword_search_time_ms']}ms")
    print(f"  - Vector search time: {debug_info['query_analysis']['vector_search_time_ms']}ms")
    print(f"  - Total indexed contents: {debug_info['query_analysis']['total_indexed_contents']}")
    print(f"  - Relevant passages: {len(debug_info['relevant_passages'])}")
    
    # Test 4: Test keyword-only search
    print("\n4. Testing keyword-only search (no vector)...")
    from django.db.models import Q
    from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
    
    if keywords:
        search_query = SearchQuery(" | ".join(keywords), search_type='raw')
        keyword_results = Content.objects.filter(
            user_id=user.id,
            is_deleted=False
        ).annotate(
            search=SearchVector('name', 'content', 'key_concepts'),
            rank=SearchRank(SearchVector('name', 'content', 'key_concepts'), search_query)
        ).filter(
            Q(search=search_query) | Q(name__icontains=test_query[:50])
        ).order_by('-rank')
        
        print(f"Keyword search found {len(keyword_results)} results")
        for result in keyword_results:
            print(f"  - {result.name} (rank: {result.rank})")

if __name__ == "__main__":
    test_search_components() 