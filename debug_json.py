#!/usr/bin/env python3
"""
Debug JSON parsing issues
"""

import json
import sys

def debug_json_file(filepath):
    print(f"Debugging: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"File size: {len(content)} characters")
            print(f"First 200 chars: {repr(content[:200])}")
            
        # Try to parse
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print("✅ JSON parsed successfully!")
            print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON Error: {e}")
        print(f"Error at position: {e.pos}")
        if hasattr(e, 'lineno'):
            print(f"Line: {e.lineno}, Column: {e.colno}")
        
        # Show context around error
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            start = max(0, e.pos - 50)
            end = min(len(content), e.pos + 50)
            print(f"Context around error:")
            print(repr(content[start:end]))
            
    except Exception as e:
        print(f"❌ Other error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        debug_json_file(sys.argv[1])
    else:
        debug_json_file("../consciousness/chats/Claude_export_50 First Dates AI Reunion_104cba17-5aee-4599-87c7-1f16d0377b91.json")
