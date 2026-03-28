#!/usr/bin/env python3
"""
Test script for C64 buildpack components
"""

import sys
import os

# Add bridge directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bridge'))

from config_parser import ConfigParser, Parameter, Service
from input_builder import InputBuilder


def test_config_parser():
    """Test config parsing"""
    print("Testing Config Parser...")
    
    # Create a test service manually
    service = Service(
        path="/add",
        program="add.bas",
        params=[
            Parameter(query="a", var="A", type="float"),
            Parameter(query="b", var="B", type="float")
        ]
    )
    
    print(f"  Service path: {service.path}")
    print(f"  Program: {service.program}")
    print(f"  Parameters: {[p.basic_var for p in service.params]}")
    print("  OK Config parser works\n")
    
    return service


def test_input_builder(service):
    """Test INPUT string building"""
    print("Testing INPUT Builder...")
    
    # Test numeric parameters
    input_str = InputBuilder.build_input_string(service, "a=5&b=3")
    print(f"  Query: a=5&b=3")
    print(f"  INPUT string: {input_str}")
    assert input_str == "5,3", f"Expected '5,3', got '{input_str}'"
    
    # Test string parameter
    string_service = Service(
        path="/greet",
        program="greet.bas",
        params=[Parameter(query="name", var="N", type="string")]
    )
    
    input_str = InputBuilder.build_input_string(string_service, "name=Alice")
    print(f"  Query: name=Alice")
    print(f"  INPUT string: {input_str}")
    assert input_str == '"Alice"', f"Expected '\"Alice\"', got '{input_str}'"
    
    # Test INPUT statement generation
    stmt = InputBuilder.build_input_statement(service)
    print(f"  INPUT statement: {stmt}")
    assert stmt == "INPUT A,B", f"Expected 'INPUT A,B', got '{stmt}'"
    
    print("  OK INPUT builder works\n")


def test_parameter_types():
    """Test different parameter types"""
    print("Testing Parameter Types...")
    
    # Integer parameter
    param_int = Parameter(query="count", var="C", type="integer")
    print(f"  Integer: {param_int.var} -> {param_int.basic_var}")
    assert param_int.basic_var == "C%"
    
    # String parameter
    param_str = Parameter(query="name", var="N", type="string")
    print(f"  String: {param_str.var} -> {param_str.basic_var}")
    assert param_str.basic_var == "N$"
    
    # Float parameter
    param_float = Parameter(query="value", var="V", type="float")
    print(f"  Float: {param_float.var} -> {param_float.basic_var}")
    assert param_float.basic_var == "V"
    
    print("  OK Parameter types work\n")


def test_duplicate_path_detection():
    """Test that duplicate paths are detected"""
    print("Testing duplicate path detection...")

    import tempfile
    import yaml

    # Create temporary .bas files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.bas', delete=False) as f1:
        f1.write('10 PRINT "TEST1"')
        test1_file = f1.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.bas', delete=False) as f2:
        f2.write('10 PRINT "TEST2"')
        test2_file = f2.name

    # Create temporary config with duplicate paths
    config_data = {
        'services': [
            {'path': '/test', 'program': test1_file},
            {'path': '/test', 'program': test2_file}
        ]
    }

    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(config_data, f)
        config_file = f.name

    try:
        parser = ConfigParser(config_file)
        try:
            parser.load()
            # Should not reach here
            print("  X Failed to detect duplicate path!")
            assert False, "Duplicate path should have been detected"
        except ValueError as e:
            assert "Duplicate service path" in str(e)
            print(f"  OK Duplicate path detected: {e}")
    finally:
        os.remove(config_file)
        os.remove(test1_file)
        os.remove(test2_file)

    print()


def test_missing_program_file():
    """Test that missing program files are detected"""
    print("Testing missing program file detection...")

    import tempfile
    import yaml

    # Create temporary config pointing to non-existent file
    config_data = {
        'services': [
            {'path': '/test', 'program': 'definitely_does_not_exist.bas'}
        ]
    }

    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(config_data, f)
        config_file = f.name

    try:
        parser = ConfigParser(config_file)
        try:
            parser.load()
            # Should not reach here
            print("  X Failed to detect missing program file!")
            assert False, "Missing program file should have been detected"
        except FileNotFoundError as e:
            assert "Program file not found" in str(e)
            print(f"  OK Missing file detected: {e}")
    finally:
        os.remove(config_file)

    print()


def main():
    """Run all tests"""
    print("=" * 60)
    print("C64 Buildpack Component Tests")
    print("=" * 60)
    print()

    try:
        service = test_config_parser()
        test_input_builder(service)
        test_parameter_types()
        test_duplicate_path_detection()
        test_missing_program_file()

        print("=" * 60)
        print("All tests passed! OK")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\nX Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nX Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
