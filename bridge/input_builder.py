"""
INPUT Builder for C64 BASIC
Constructs INPUT strings from query parameters
"""

from typing import Dict, List
from urllib.parse import parse_qs
from config_parser import Service, Parameter


class InputBuilder:
    """Builds INPUT strings for C64 BASIC programs"""
    
    @staticmethod
    def build_input_string(service: Service, query_string: str) -> str:
        """
        Build an INPUT string from query parameters
        
        Args:
            service: Service definition with parameter mappings
            query_string: Raw query string from URL (e.g., "a=5&b=3")
            
        Returns:
            Formatted INPUT string (e.g., "5,3" or '"ALICE",25')
        """
        if not service.params:
            return ""
        
        # Parse query string
        query_params = parse_qs(query_string) if query_string else {}
        
        # Build input values in order
        input_values = []
        for param in service.params:
            # Get value from query params or use default
            values = query_params.get(param.query, [])
            value = values[0] if values else param.default
            
            if value is None:
                raise ValueError(f"Missing required parameter: {param.query}")
            
            # Format value based on type
            if param.type == "string":
                # String: quote it and escape internal quotes
                escaped = value.replace('"', '""')  # C64 BASIC uses "" for quotes
                input_values.append(f'"{escaped}"')
            elif param.type == "integer":
                # Integer: validate and pass as-is
                try:
                    int(value)
                    input_values.append(value)
                except ValueError:
                    raise ValueError(f"Parameter {param.query} must be an integer")
            else:  # float
                # Float: validate and pass as-is
                try:
                    float(value)
                    input_values.append(value)
                except ValueError:
                    raise ValueError(f"Parameter {param.query} must be a number")
        
        return ",".join(input_values)
    
    @staticmethod
    def build_input_statement(service: Service) -> str:
        """
        Build the INPUT statement that the BASIC program should use
        
        Args:
            service: Service definition
            
        Returns:
            INPUT statement (e.g., "INPUT A,B" or "INPUT N$,A%")
        """
        if not service.params:
            return ""
        
        var_names = [param.basic_var for param in service.params]
        return f"INPUT {','.join(var_names)}"
