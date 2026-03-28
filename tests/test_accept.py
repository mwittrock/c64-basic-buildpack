import sys
sys.path.insert(0, '../bridge')

# Test the negotiation logic directly
def _negotiate_content_type(accept_header: str) -> str:
    """Determine response format based on Accept header"""
    # Normalize and split on comma for multiple types
    accept_types = [t.strip().lower().split(';')[0] for t in accept_header.split(',')]
    
    print(f"Accept header: '{accept_header}'")
    print(f"Parsed types: {accept_types}")
    
    # Check for explicit JSON request
    if 'application/json' in accept_types:
        print("Matched: application/json")
        return 'json'
    
    # Check for explicit text or wildcard
    if 'text/plain' in accept_types or '*/*' in accept_types or 'text/*' in accept_types:
        print("Matched: text/wildcard")
        return 'text'
    
    # Default to text if Accept header is empty or only contains whitespace
    if not accept_header.strip():
        print("Matched: empty header")
        return 'text'
    
    # Unsupported format
    print("No match - returning None")
    return None

# Test cases
print("=== Test 1: curl default (*/*) ===")
result = _negotiate_content_type('*/*')
print(f"Result: {result}\n")

print("=== Test 2: empty ===")
result = _negotiate_content_type('')
print(f"Result: {result}\n")

print("=== Test 3: application/json ===")
result = _negotiate_content_type('application/json')
print(f"Result: {result}\n")

print("=== Test 4: Bruno might send this ===")
result = _negotiate_content_type('*/*; q=0.8, application/json')
print(f"Result: {result}\n")
