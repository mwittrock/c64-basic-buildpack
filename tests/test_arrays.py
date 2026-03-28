#!/usr/bin/env python3
"""Test array support in the interpreter"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bridge'))

from basic_interpreter import run_basic_program


def test_simple_array():
    """Test simple 1D array"""
    print("Testing simple 1D array...")
    
    source = """
10 DIM A(5)
20 A(0) = 10
30 A(1) = 20
40 A(5) = 50
50 PRINT A(0)
60 PRINT A(1)
70 PRINT A(5)
"""
    
    output = run_basic_program(source)
    print(f"Output:\n{output}")
    
    assert "10" in output
    assert "20" in output
    assert "50" in output
    print("✓ Simple array works!\n")


def test_2d_array():
    """Test 2D array"""
    print("Testing 2D array...")
    
    source = """
10 DIM B(2,2)
20 B(0,0) = 1
30 B(0,1) = 2
40 B(1,0) = 3
50 B(1,1) = 4
60 PRINT B(0,0);B(0,1)
70 PRINT B(1,0);B(1,1)
"""
    
    output = run_basic_program(source)
    print(f"Output:\n{output}")
    
    assert "1" in output and "2" in output
    assert "3" in output and "4" in output
    print("✓ 2D array works!\n")


def test_string_array():
    """Test string array"""
    print("Testing string array...")
    
    source = """
10 DIM N$(3)
20 N$(0) = "ALICE"
30 N$(1) = "BOB"
40 N$(2) = "CAROL"
50 PRINT N$(0)
60 PRINT N$(1)
70 PRINT N$(2)
"""
    
    output = run_basic_program(source)
    print(f"Output:\n{output}")
    
    assert "ALICE" in output
    assert "BOB" in output
    assert "CAROL" in output
    print("✓ String array works!\n")


def test_array_in_loop():
    """Test array with FOR loop"""
    print("Testing array in loop...")
    
    source = """
10 DIM A(5)
20 FOR I = 0 TO 5
30 A(I) = I * 10
40 NEXT I
50 FOR I = 0 TO 5
60 PRINT A(I);
70 NEXT I
"""
    
    output = run_basic_program(source)
    print(f"Output:\n{output}")
    
    assert "0" in output
    assert "10" in output
    assert "50" in output
    print("✓ Array in loop works!\n")


def main():
    """Run all array tests"""
    print("=" * 60)
    print("C64 BASIC Array Tests")
    print("=" * 60)
    print()
    
    try:
        test_simple_array()
        test_2d_array()
        test_string_array()
        test_array_in_loop()
        
        print("=" * 60)
        print("All array tests passed! ✓")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
