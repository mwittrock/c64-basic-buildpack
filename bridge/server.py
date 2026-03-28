#!/usr/bin/env python3
"""
C64 BASIC HTTP Bridge Server
Handles HTTP requests and routes them to C64 BASIC programs via Python interpreter
"""

import os
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import traceback

from config_parser import ConfigParser
from input_builder import InputBuilder
from basic_interpreter import BasicInterpreter, BasicError, BasicTimeout

PORT = int(os.environ.get('PORT', 8080))
CONFIG_FILE = os.environ.get('C64_CONFIG', 'c64-services.yml')


class C64Handler(BaseHTTPRequestHandler):
    """HTTP request handler for C64 BASIC services"""
    
    # Class-level config (shared across requests)
    config = None
    
    @classmethod
    def initialize(cls, config_path: str):
        """Initialize config (called once at startup)"""
        cls.config = ConfigParser(config_path)
        cls.config.load()
        print(f"Loaded {len(cls.config.services)} service(s):")
        print(f"Global timeout: {cls.config.global_timeout} seconds")
        for path in cls.config.list_services():
            service = cls.config.get_service(path)
            if service.timeout is not None:
                # Service has override
                print(f"  {path} → {service.program} [timeout: {service.timeout}s]")
            else:
                # Uses global timeout
                print(f"  {path} → {service.program}")
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Parse URL
            parsed = urlparse(self.path)
            path = parsed.path
            query_string = parsed.query
            
            # Special case: root path
            if path == '/':
                if self.config.show_service_list:
                    self.send_service_list()
                else:
                    self.send_error(404, "Not Found")
                return
            
            # Look up service
            service = self.config.get_service(path)
            if not service:
                self.send_error(404, f"Service not found: {path}")
                return
            
            # Check Accept header for content negotiation
            accept_header = self.headers.get('Accept', 'text/plain')
            response_format = self._negotiate_content_type(accept_header)
            
            if response_format is None:
                self.send_error(406, f"Not Acceptable. Supported formats: text/plain, application/json")
                return
            
            # Build INPUT string from query parameters
            try:
                input_string = InputBuilder.build_input_string(service, query_string)
            except ValueError as e:
                self.send_error(400, str(e))
                return
            
            # Run the BASIC program with configured timeout
            timeout = self.config.get_timeout(service)
            try:
                # Load and run the BASIC program
                with open(service.program, 'r') as f:
                    program_source = f.read()
                
                interpreter = BasicInterpreter(timeout=timeout)
                interpreter.load_program(program_source)
                interpreter.set_input(input_string)
                
                output = interpreter.run()
                
                # Check for error output if catch_errors is enabled
                if service.catch_errors and output.startswith("ERROR: "):
                    # Extract error message (remove "ERROR: " prefix and strip)
                    error_msg = output[7:].strip()
                    if response_format == 'json':
                        self._send_json_error(error_msg)
                    else:
                        self.send_error(500, f"Program error: {error_msg}")
                    return
                
                # Convert output based on output_type
                try:
                    converted_output = self._convert_output(output, service.output_type)
                except ValueError as e:
                    if response_format == 'json':
                        self._send_json_error(str(e))
                    else:
                        self.send_error(500, f"Output conversion error: {str(e)}")
                    return
                
                # Send response in requested format
                if response_format == 'json':
                    self._send_json_response(converted_output)
                else:
                    # Plain text response
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain; charset=utf-8')
                    self.send_header('X-Powered-By', 'Commodore-64')
                    self.end_headers()
                    self.wfile.write(output.encode('utf-8'))
                
            except BasicTimeout as e:
                self.send_error(504, f"Gateway Timeout: {str(e)}")
                return
            except BasicError as e:
                self.send_error(500, f"BASIC program error: {str(e)}")
                return
            except Exception as e:
                self.send_error(500, f"Execution error: {str(e)}")
                traceback.print_exc()
                return
                
        except Exception as e:
            self.send_error(500, f"Internal error: {str(e)}")
            traceback.print_exc()
    
    def _negotiate_content_type(self, accept_header: str) -> str:
        """Determine response format based on Accept header
        
        Returns:
            'json' for application/json
            'text' for text/plain or */*, or missing
            None if unsupported format requested
        """
        # Normalize and split on comma for multiple types
        accept_types = [t.strip().lower().split(';')[0] for t in accept_header.split(',')]
        
        # Check for explicit JSON request
        if 'application/json' in accept_types:
            return 'json'
        
        # Check for explicit text or wildcard
        if 'text/plain' in accept_types or '*/*' in accept_types or 'text/*' in accept_types:
            return 'text'
        
        # Default to text if Accept header is empty or only contains whitespace
        if not accept_header.strip():
            return 'text'
        
        # Unsupported format
        return None
    
    def _convert_output(self, output: str, output_type: str):
        """Convert output string to appropriate type
        
        Args:
            output: Raw output from BASIC program
            output_type: Desired type (string, integer, float, boolean)
            
        Returns:
            Converted value
            
        Raises:
            ValueError: If conversion fails
        """
        output = output.strip()
        
        if output_type == 'string':
            return output
        elif output_type == 'integer':
            try:
                return int(output)
            except ValueError:
                raise ValueError(f"Cannot convert output to integer: '{output}'")
        elif output_type == 'float':
            try:
                return float(output)
            except ValueError:
                raise ValueError(f"Cannot convert output to float: '{output}'")
        elif output_type == 'boolean':
            output_upper = output.upper()
            if output_upper == 'TRUE':
                return True
            elif output_upper == 'FALSE':
                return False
            else:
                raise ValueError(f"Invalid boolean output: '{output}'. Expected 'TRUE' or 'FALSE'")
        else:
            raise ValueError(f"Unknown output_type: {output_type}")
    
    def _send_json_response(self, result):
        """Send successful JSON response"""
        response = {
            'result': result,
            'status': 'success'
        }
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('X-Powered-By', 'Commodore-64')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def _send_json_error(self, error_message: str):
        """Send error JSON response"""
        response = {
            'error': error_message,
            'status': 'error'
        }
        self.send_response(500)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('X-Powered-By', 'Commodore-64')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def send_service_list(self):
        """Send a list of available services"""
        services = self.config.list_services()
        
        response = "C64 BASIC Services\n"
        response += "=" * 50 + "\n\n"
        
        if not services:
            response += "No services configured.\n"
        else:
            response += "Available endpoints:\n\n"
            for path in sorted(services):
                service = self.config.get_service(path)
                response += f"  {path}\n"
                response += f"    Program: {service.program}\n"
                if service.params:
                    response += f"    Parameters:\n"
                    for param in service.params:
                        response += f"      ?{param.query}= ({param.type} → {param.basic_var})\n"
                response += "\n"
        
        response += "\nPowered by Commodore 64 BASIC\n"
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Log HTTP requests"""
        sys.stdout.write(f"{self.address_string()} - {format % args}\n")
        sys.stdout.flush()


def main():
    """Start the HTTP server"""
    print("=" * 60)
    print("C64 BASIC Bridge Server")
    print("=" * 60)
    
    # Check if config file exists
    if not os.path.exists(CONFIG_FILE):
        print(f"ERROR: Config file not found: {CONFIG_FILE}")
        sys.exit(1)
    
    # Initialize handler
    try:
        C64Handler.initialize(CONFIG_FILE)
    except Exception as e:
        print(f"ERROR: Failed to initialize: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    # Start server
    server = HTTPServer(('0.0.0.0', PORT), C64Handler)
    print(f"\nServer listening on port {PORT}")
    print("Ready to serve Commodore 64 BASIC programs!")
    print("=" * 60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n\nShutting down server...')
        server.shutdown()


if __name__ == '__main__':
    main()
