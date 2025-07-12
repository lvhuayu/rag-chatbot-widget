#!/usr/bin/env python3
"""
Test script to verify base64 encoding fix for embeddings
"""

import pickle
import base64
import numpy as np

def test_base64_encoding():
    """Test base64 encoding of pickle data"""
    
    # Create a simple embedding
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    # Original pickle approach (this was causing the error)
    embedding_blob = pickle.dumps(np.array(embedding))
    print(f"Original pickle blob (first 50 chars): {str(embedding_blob)[:50]}...")
    
    # New base64 approach
    embedding_b64 = base64.b64encode(embedding_blob).decode('utf-8')
    print(f"Base64 encoded (first 50 chars): {embedding_b64[:50]}...")
    
    # Test JavaScript string format
    js_string = f"Buffer.from('{embedding_b64}', 'base64')"
    print(f"JavaScript format: {js_string[:50]}...")
    
    # Verify we can decode it back
    decoded_blob = base64.b64decode(embedding_b64)
    decoded_array = pickle.loads(decoded_blob)
    print(f"Decoded array: {decoded_array}")
    
    print("✅ Base64 encoding test passed!")

if __name__ == "__main__":
    test_base64_encoding() 