"""
Config Parser for C64 BASIC Services
Parses c64-services.yml configuration files
"""

import os
import yaml
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Parameter:
    """Represents a parameter mapping from query param to BASIC variable"""
    query: str          # Query parameter name (e.g., "name")
    var: str            # BASIC variable name (e.g., "N")
    type: str           # Type: "string", "integer", or "float"
    default: Optional[str] = None
    
    @property
    def basic_var(self) -> str:
        """Return the BASIC variable with proper suffix"""
        if self.type == "string":
            return f"{self.var}$"
        elif self.type == "integer":
            return f"{self.var}%"
        else:  # float
            return self.var


@dataclass
class Service:
    """Represents a single C64 BASIC service"""
    path: str
    program: str
    params: List[Parameter]
    timeout: Optional[int] = None  # Per-service timeout override
    catch_errors: bool = False  # If True, detect "ERROR: " prefix and return HTTP 500
    output_type: str = "string"  # Output type: "string", "integer", "float", or "boolean"


class ConfigParser:
    """Parses c64-services.yml configuration"""
    
    def __init__(self, config_path: str = "c64-services.yml"):
        self.config_path = config_path
        self.services: Dict[str, Service] = {}
        self.global_timeout: int = 5  # Default global timeout in seconds
        self.show_service_list: bool = False  # Default: hide service list at /
        
    def load(self):
        """Load and parse the configuration file"""
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Load global timeout if specified
        if 'timeout' in config:
            self.global_timeout = int(config['timeout'])
        
        # Load show_service_list if specified
        if 'show_service_list' in config:
            self.show_service_list = bool(config['show_service_list'])
        
        for service_def in config.get('services', []):
            params = []
            for param_def in service_def.get('params', []):
                params.append(Parameter(
                    query=param_def['query'],
                    var=param_def['var'],
                    type=param_def['type'],
                    default=param_def.get('default')
                ))
            
            # Get service-specific timeout or use None (will use global)
            service_timeout = service_def.get('timeout')
            
            # Get catch_errors flag (defaults to False)
            catch_errors = service_def.get('catch_errors', False)
            
            # Get output_type (defaults to "string")
            output_type = service_def.get('output_type', 'string')
            if output_type not in ['string', 'integer', 'float', 'boolean']:
                raise ValueError(f"Invalid output_type '{output_type}' for service {service_def['path']}. Must be one of: string, integer, float, boolean")
            
            service = Service(
                path=service_def['path'],
                program=service_def['program'],
                params=params,
                timeout=service_timeout,
                catch_errors=catch_errors,
                output_type=output_type
            )

            # Check for duplicate paths
            if service.path in self.services:
                raise ValueError(f"Duplicate service path '{service.path}' defined in configuration")

            # Check if program file exists
            if not os.path.exists(service.program):
                raise FileNotFoundError(f"Program file not found: {service.program} (service: {service.path})")

            self.services[service.path] = service
    
    def get_service(self, path: str) -> Optional[Service]:
        """Get service definition for a path"""
        return self.services.get(path)
    
    def get_timeout(self, service: Service) -> int:
        """Get effective timeout for a service (service-specific or global)"""
        return service.timeout if service.timeout is not None else self.global_timeout
    
    def list_services(self) -> List[str]:
        """Return list of all service paths"""
        return list(self.services.keys())
