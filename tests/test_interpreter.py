#!/usr/bin/env python3
"""
Test the C64 BASIC interpreter
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bridge'))

from basic_interpreter import BasicInterpreter, run_basic_program


def test_hello():
    """Test hello.bas"""
    print("Testing hello.bas...")
    
    source = """
10 REM HELLO WORLD SERVICE
20 PRINT "HELLO FROM COMMODORE 64!"
30 PRINT "READY TO SERVE"
"""
    
    output = run_basic_program(source)
    print(f"Output:\n{output}")
    
    assert "HELLO FROM COMMODORE 64!" in output
    assert "READY TO SERVE" in output
    print("✓ hello.bas works!\n")


def test_add():
    """Test add.bas"""
    print("Testing add.bas...")
    
    source = """
10 REM ADDITION SERVICE
20 INPUT A,B
30 PRINT "RESULT: ";A+B
"""
    
    output = run_basic_program(source, "5,3")
    print(f"Output:\n{output}")
    
    assert "RESULT:  8" in output  # C64 pads positive numbers with a leading space
    print("✓ add.bas works!\n")


def test_variables():
    """Test variable assignment"""
    print("Testing variables...")
    
    source = """
10 A = 5
20 B = 3
30 C = A + B
40 PRINT C
"""
    
    output = run_basic_program(source)
    print(f"Output:\n{output}")
    
    assert "8" in output
    print("✓ Variables work!\n")


def test_string_variables():
    """Test string variables"""
    print("Testing string variables...")
    
    source = """
10 N$ = "ALICE"
20 PRINT "HELLO ";N$
"""
    
    output = run_basic_program(source)
    print(f"Output:\n{output}")
    
    assert "HELLO ALICE" in output
    print("✓ String variables work!\n")


def test_if_then():
    """Test IF/THEN"""
    print("Testing IF/THEN...")
    
    source = """
10 A = 5
20 IF A > 3 THEN PRINT "BIG"
30 IF A < 3 THEN PRINT "SMALL"
40 PRINT "DONE"
"""
    
    output = run_basic_program(source)
    print(f"Output:\n{output}")
    
    assert "BIG" in output
    assert "SMALL" not in output
    assert "DONE" in output
    print("✓ IF/THEN works!\n")


def test_for_loop():
    """Test FOR/NEXT loop"""
    print("Testing FOR/NEXT...")
    
    source = """
10 FOR I = 1 TO 3
20 PRINT I;
30 NEXT I
"""
    
    output = run_basic_program(source)
    print(f"Output:\n{output}")
    
    assert "1" in output
    assert "2" in output
    assert "3" in output
    print("✓ FOR/NEXT works!\n")


def test_gosub_return():
    """Test GOSUB/RETURN"""
    print("Testing GOSUB/RETURN...")
    
    source = """
10 PRINT "START"
20 GOSUB 100
30 PRINT "END"
40 GOTO 200
100 PRINT "SUBROUTINE"
110 RETURN
200 REM DONE
"""
    
    output = run_basic_program(source)
    print(f"Output:\n{output}")
    
    assert "START" in output
    assert "SUBROUTINE" in output
    assert "END" in output
    print("✓ GOSUB/RETURN works!\n")


def test_string_functions():
    """Test string functions"""
    print("Testing string functions...")
    
    # LEFT$
    source = """
10 A$ = "HELLO"
20 PRINT LEFT$(A$,3)
"""
    output = run_basic_program(source)
    print(f"LEFT$ output: {output}")
    assert "HEL" in output
    
    # RIGHT$
    source = """
10 A$ = "HELLO"
20 PRINT RIGHT$(A$,3)
"""
    output = run_basic_program(source)
    print(f"RIGHT$ output: {output}")
    assert "LLO" in output
    
    # MID$
    source = """
10 A$ = "HELLO"
20 PRINT MID$(A$,2,3)
"""
    output = run_basic_program(source)
    print(f"MID$ output: {output}")
    assert "ELL" in output
    
    # LEN
    source = """
10 A$ = "HELLO"
20 PRINT LEN(A$)
"""
    output = run_basic_program(source)
    print(f"LEN output: {output}")
    assert "5" in output
    
    # CHR$ and ASC
    source = """
10 PRINT CHR$(65)
20 PRINT ASC("A")
"""
    output = run_basic_program(source)
    print(f"CHR$/ASC output: {output}")
    assert "A" in output
    assert "65" in output

    # CHR$ PETSCII codes for maze characters (C64 SHIFT+M and SHIFT+N)
    source = """
10 PRINT CHR$(205)
20 PRINT CHR$(206)
"""
    output = run_basic_program(source)
    print(f"CHR$ PETSCII maze output: {repr(output)}")
    assert "/" in output, f"CHR$(205) should produce '/' but got: {repr(output)}"
    assert "\\" in output, f"CHR$(206) should produce '\\' but got: {repr(output)}"
    
    # STR$ and VAL
    source = """
10 PRINT STR$(42)
20 PRINT VAL("123")
"""
    output = run_basic_program(source)
    print(f"STR$/VAL output: {output}")
    assert "42" in output
    assert "123" in output
    
    print("✓ String functions work!\n")


def test_math_functions():
    """Test math functions"""
    print("Testing math functions...")
    
    # ABS
    source = """
10 PRINT ABS(-5)
"""
    output = run_basic_program(source)
    print(f"ABS output: {output}")
    assert "5" in output
    
    # INT
    source = """
10 PRINT INT(3.7)
"""
    output = run_basic_program(source)
    print(f"INT output: {output}")
    assert "3" in output
    
    # SQR
    source = """
10 PRINT INT(SQR(16))
"""
    output = run_basic_program(source)
    print(f"SQR output: {output}")
    assert "4" in output
    
    # SGN
    source = """
10 PRINT SGN(-5)
20 PRINT SGN(0)
30 PRINT SGN(5)
"""
    output = run_basic_program(source)
    print(f"SGN output: {output}")
    assert "-1" in output
    assert "0" in output
    assert "1" in output
    
    print("✓ Math functions work!\n")


def test_arrays():
    """Test array support"""
    print("Testing arrays...")
    
    # Simple 1D array
    source = """
10 DIM A(5)
20 A(0) = 10
30 A(5) = 50
40 PRINT A(0);A(5)
"""
    output = run_basic_program(source)
    print(f"1D array output: {output}")
    assert "10" in output
    assert "50" in output
    
    # 2D array
    source = """
10 DIM B(2,2)
20 B(0,0) = 1
30 B(1,1) = 4
40 PRINT B(0,0);B(1,1)
"""
    output = run_basic_program(source)
    print(f"2D array output: {output}")
    assert "1" in output
    assert "4" in output
    
    # Array in loop
    source = """
10 DIM A(3)
20 FOR I = 0 TO 3
30 A(I) = I * 10
40 NEXT I
50 PRINT A(2)
"""
    output = run_basic_program(source)
    print(f"Array in loop output: {output}")
    assert "20" in output
    
    print("✓ Arrays work!\n")


def test_ti_and_rnd():
    """Test TI system variable and RND seeding"""
    print("Testing TI and RND...")
    
    # Test TI returns a value
    source = """
10 PRINT TI
"""
    output = run_basic_program(source)
    print(f"TI output: {output}")
    # TI should be 0 or a small number at start
    assert output.strip().isdigit()
    
    # Test RND seeding with TI
    source = """
10 A = RND(-TI)
20 PRINT INT(RND(1)*100)
"""
    output = run_basic_program(source)
    print(f"RND with TI seed output: {output}")
    # Should output a random number 0-99
    result = int(output.strip())
    assert 0 <= result < 100
    
    print("✓ TI and RND work!\n")


def test_long_variable_names():
    """Test C64 BASIC long variable name semantics.

    C64 BASIC allows variable names up to 80 characters but only the first
    two characters are significant.  Extra characters are silently ignored.
    """
    print("Testing long variable names...")

    # Long all-alpha name: HELLO -> HE
    source = """
10 LET HELLO = 42
20 PRINT HE
"""
    output = run_basic_program(source)
    assert "42" in output, f"HELLO should alias HE, got: {output!r}"

    # Long name aliases short name: last assignment wins
    source = """
10 LET COUNTER = 10
20 LET CO = 99
30 PRINT COUNTER
"""
    output = run_basic_program(source)
    assert "99" in output, f"COUNTER and CO should be the same variable, got: {output!r}"

    # Name with digit as second significant char: A1BXYZ -> A1
    source = """
10 LET A1BXYZ = 7
20 PRINT A1
"""
    output = run_basic_program(source)
    assert "7" in output, f"A1BXYZ should alias A1, got: {output!r}"

    # Long name with trailing digits: HELLO1 -> HE (not HE1)
    source = """
10 LET HELLO1 = 55
20 PRINT HE
"""
    output = run_basic_program(source)
    assert "55" in output, f"HELLO1 should alias HE, got: {output!r}"

    # Type suffix still recognised after long name: NAMES$ -> NA$
    source = """
10 LET NAMES$ = "BOB"
20 PRINT NA$
"""
    output = run_basic_program(source)
    assert "BOB" in output, f"NAMES$ should alias NA$, got: {output!r}"

    print("✓ Long variable names work!\n")


def test_variable_type_suffixes():
    """Test that A, A% and A$ are three distinct variables.

    The type suffix (none = float, % = integer, $ = string) is part of the
    variable identity, so the same base name with different suffixes must not
    alias each other.
    """
    print("Testing variable type suffix uniqueness...")

    source = """
10 LET A = 1.5
20 LET A% = 2
30 LET A$ = "THREE"
40 PRINT A
50 PRINT A%
60 PRINT A$
"""
    output = run_basic_program(source)
    lines = [l.strip() for l in output.strip().splitlines()]

    assert "1.5" in lines[0], f"A (float) should be 1.5, got: {lines[0]!r}"
    assert lines[1] == "2",   f"A% (integer) should be 2, got: {lines[1]!r}"
    assert lines[2] == "THREE", f"A$ (string) should be THREE, got: {lines[2]!r}"

    # Assigning to one must not affect the others
    source = """
10 LET A = 10
20 LET A% = 20
30 LET A$ = "THIRTY"
40 LET A = 99
50 PRINT A
60 PRINT A%
70 PRINT A$
"""
    output = run_basic_program(source)
    lines = [l.strip() for l in output.strip().splitlines()]

    assert "99" in lines[0],     f"A (float) should be 99 after reassignment, got: {lines[0]!r}"
    assert lines[1] == "20",     f"A% should be unchanged at 20, got: {lines[1]!r}"
    assert lines[2] == "THIRTY", f"A$ should be unchanged at THIRTY, got: {lines[2]!r}"

    print("✓ Variable type suffixes are unique!\n")


def test_data_read_restore():
    """Test DATA, READ and RESTORE statements"""
    print("Testing DATA/READ/RESTORE...")

    # Basic READ from DATA
    source = """
10 DATA 10,20,30
20 READ A,B,C
30 PRINT A;B;C
"""
    output = run_basic_program(source)
    print(f"Basic READ output: {output}")
    assert "10" in output
    assert "20" in output
    assert "30" in output

    # READ string data
    source = """
10 DATA "HELLO","WORLD"
20 READ A$,B$
30 PRINT A$;" ";B$
"""
    output = run_basic_program(source)
    print(f"String DATA output: {output}")
    assert "HELLO WORLD" in output

    # RESTORE resets pointer to start of DATA
    source = """
10 DATA 1,2,3
20 READ A
30 READ B
40 RESTORE
50 READ C
60 PRINT A;B;C
"""
    output = run_basic_program(source)
    print(f"RESTORE output: {output}")
    lines = output.strip().splitlines()
    # A=1, B=2, C=1 (RESTORE rewinds to first DATA item)
    assert " 1 " in lines[0] or lines[0].startswith("1") or " 1" in lines[0]
    assert " 2 " in lines[0] or "2" in lines[0]
    # C should equal A (both read first DATA item)
    nums = [t.strip() for t in lines[0].split() if t.strip()]
    assert nums[0] == nums[2], f"After RESTORE, third READ should return first value again, got: {lines[0]!r}"

    # DATA spread across multiple lines
    source = """
10 DATA 7
20 DATA 8,9
30 READ X,Y,Z
40 PRINT X;Y;Z
"""
    output = run_basic_program(source)
    print(f"Multi-line DATA output: {output}")
    assert "7" in output
    assert "8" in output
    assert "9" in output

    # DATA at end of program (numeric)
    source = """
10 READ A,B,C
20 PRINT A;B;C
30 END
40 DATA 4,5,6
"""
    output = run_basic_program(source)
    print(f"DATA at end (numeric) output: {output}")
    assert "4" in output
    assert "5" in output
    assert "6" in output

    # DATA at end of program (strings)
    source = """
10 READ N$,G$
20 PRINT "HELLO ";N$;" ";G$
30 END
40 DATA "COMMODORE","64"
"""
    output = run_basic_program(source)
    print(f"DATA at end (strings) output: {output}")
    assert "HELLO COMMODORE 64" in output

    print("✓ DATA/READ/RESTORE work!\n")


def main():
    """Run all tests"""
    print("=" * 60)
    print("C64 BASIC Interpreter Tests")
    print("=" * 60)
    print()

    try:
        test_hello()
        test_add()
        test_variables()
        test_string_variables()
        test_if_then()
        test_for_loop()
        test_gosub_return()
        test_string_functions()
        test_math_functions()
        test_arrays()
        test_ti_and_rnd()
        test_long_variable_names()
        test_variable_type_suffixes()
        test_data_read_restore()
        
        print("=" * 60)
        print("All tests passed! ✓")
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
