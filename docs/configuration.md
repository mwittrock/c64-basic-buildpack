# Configuration Guide: c64-services.yml

This guide explains how to configure your Commodore 64 BASIC web services using the `c64-services.yml` configuration file.

## Basic Structure

```yaml
# Global settings (optional)
timeout: 10                    # Default timeout in seconds (default: 5)
show_service_list: false       # Show service list at / (default: false)

# Service definitions (required)
services:
  - path: /endpoint            # HTTP path
    program: program.bas       # BASIC program file
    params:                    # Query parameters (optional)
      - query: name            # Query parameter name
        var: N                 # BASIC variable name
        type: string           # Type: string, integer, or float
        default: ""            # Default value (optional)
    output_type: string        # Output type (default: string)
    catch_errors: false        # Enable ERROR: detection (default: false)
    timeout: 5                 # Service-specific timeout (optional)
```

## Global Settings

### timeout

**Type:** Integer (seconds)  
**Default:** 5  
**Description:** Default execution timeout for all services. Can be overridden per service.

```yaml
timeout: 10  # All services timeout after 10 seconds by default
```

### show_service_list

**Type:** Boolean  
**Default:** false  
**Description:** When true, displays a list of available services at the root path (`/`). Disabled by default — opt in explicitly if you want the endpoint index exposed.

```yaml
show_service_list: true  # Expose service list at /
```

## Service Definition

Each service in the `services` array defines an HTTP endpoint that executes a BASIC program.

### path

**Required**  
**Type:** String  
**Description:** The HTTP endpoint path for this service.

```yaml
path: /fibonacci      # Service available at /fibonacci
path: /api/calculate  # Service available at /api/calculate
```

### program

**Required**  
**Type:** String  
**Description:** The BASIC program file to execute (relative to application root).

```yaml
program: fibonacci.bas
program: programs/calculate.bas
```

### params

**Optional**  
**Type:** Array of parameter definitions  
**Description:** Maps HTTP query parameters to BASIC INPUT variables.

Each parameter has:
- `query` - Query parameter name in the URL
- `var` - BASIC variable name (without type suffix)
- `type` - Parameter type (`string`, `integer`, or `float`)
- `default` - Default value if parameter not provided (optional)

**Example:**

```yaml
params:
  - query: n          # URL: ?n=10
    var: N            # BASIC: INPUT N%
    type: integer
  - query: name       # URL: ?name=Alice
    var: N            # BASIC: INPUT N$
    type: string
    default: "World"  # Default if not provided
  - query: pi         # URL: ?pi=3.14159
    var: P            # BASIC: INPUT P
    type: float
```

### Parameter Types

| Type      | BASIC Suffix | Example Query      | BASIC Variable | Notes                    |
|-----------|--------------|-------------------|----------------|--------------------------|
| `string`  | `$`          | `?name=Bob`       | `N$`           | All strings              |
| `integer` | `%`          | `?count=5`        | `C%`           | Whole numbers only       |
| `float`   | *(none)*     | `?value=3.14`     | `V`            | Decimal numbers          |

**Important:** The `var` field should specify the variable name WITHOUT the type suffix. The buildpack automatically adds the correct suffix (`$` for string, `%` for integer) when generating the INPUT statement.

### output_type

**Optional**  
**Type:** String (`string`, `integer`, `float`, `boolean`)  
**Default:** `string`  
**Description:** How to interpret the BASIC program's output.

```yaml
output_type: string    # Output treated as text
output_type: integer   # Output parsed as integer
output_type: float     # Output parsed as float
output_type: boolean   # Output parsed as TRUE/FALSE
```

**Output Type Behavior:**

| Type      | BASIC Output   | Plain Text Response | JSON Response                           |
|-----------|----------------|---------------------|-----------------------------------------|
| `string`  | `HELLO WORLD`  | `HELLO WORLD`       | `{"result": "HELLO WORLD", ...}`        |
| `integer` | ` 42 `         | ` 42 `              | `{"result": 42, ...}`                   |
| `float`   | ` 3.14159 `    | ` 3.14159 `         | `{"result": 3.14159, ...}`              |
| `boolean` | `TRUE`         | `TRUE`              | `{"result": true, ...}`                 |

**For boolean output:** Your BASIC program must output exactly `TRUE` or `FALSE` (case-insensitive). Any other output will result in an error.

### catch_errors

**Optional**  
**Type:** Boolean  
**Default:** false  
**Description:** When true, detects if program output starts with "ERROR:" and returns HTTP 500 with error details.

```yaml
catch_errors: true
```

**In your BASIC program:**

```basic
10 INPUT A, B
20 IF B=0 THEN PRINT "ERROR: DIVISION BY ZERO" : END
30 PRINT A/B
```

**Result when B=0:**
- Plain text: DIVISION BY ZERO (and HTTP status 500)
- JSON: `{"error": "DIVISION BY ZERO", "status": "error"}` (and HTTP status 500)

### timeout

**Optional**  
**Type:** Integer (seconds)  
**Default:** Global timeout value  
**Description:** Service-specific execution timeout. Overrides global timeout.

```yaml
timeout: 15  # This service gets 15 seconds
```

## Configuration Validation

The buildpack validates your `c64-services.yml` configuration at server startup time. If validation fails, the application will not start and you'll see a clear error message in the deployment logs.

### Validation Checks

#### 1. Duplicate Service Paths

**Error:** `ValueError: Duplicate service path '/path' defined in configuration`

The buildpack checks for duplicate service paths and rejects configurations where the same path is defined multiple times.

❌ **Invalid:**
```yaml
services:
  - path: /test
    program: version1.bas
  - path: /test      # Duplicate!
    program: version2.bas
```

✅ **Valid:**
```yaml
services:
  - path: /test/v1
    program: version1.bas
  - path: /test/v2
    program: version2.bas
```

What happens: During `cf push`, the buildpack stages successfully, but when the server tries to start, it detects the duplicate and crashes with an error. The deployment will fail and you'll see the error in `cf logs`.

#### 2. Missing Program Files

**Error:** `FileNotFoundError: Program file not found: program.bas (service: /path)`

The buildpack verifies that all BASIC program files referenced in the configuration actually exist.

❌ **Invalid:**
```yaml
services:
  - path: /fibonacci
    program: fibonacci.bas  # File doesn't exist!
```

✅ **Valid:**
```yaml
services:
  - path: /fibonacci
    program: fibonacci.bas  # File exists in project
```

What happens: Same as duplicate paths - staging succeeds, but server startup fails with a clear error message identifying which file is missing and which service needs it.

### When Validation Occurs

- **During `cf push`:** Buildpack scripts run successfully (no validation yet)
- **After staging:** Application attempts to start
- **Server startup:** Configuration is loaded and validated
- **On validation failure:** Server crashes immediately with descriptive error
- **Result:** `cf push` reports failure; check `cf logs your-app --recent` for details

This "fail fast" approach ensures you know immediately if there's a configuration problem - no silent failures or mysterious runtime issues.
