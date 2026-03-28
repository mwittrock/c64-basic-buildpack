# HTTP status codes

This page lists the HTTP status codes you can receive in response to calling a service deployed with the Commodore 64 BASIC buildpack.

## Success Responses

### 200 OK

Successful execution.

**Example:**
```bash
curl "https://example.com/add?a=5&b=3"
# Returns: 8 (HTTP 200)
```

## Client Error Responses

### 400 Bad Request

Invalid or missing required parameters.

**Causes:**
- Missing required parameter (no default provided)
- Invalid parameter type (e.g., "abc" for integer parameter)

**Example:**
```bash
curl "https://example.com/add?a=5"
# Returns: HTTP 400 (missing parameter 'b')
```

Fix: Provide all required parameters or set defaults in config.

### 404 Not Found

No service matched the request path, or the configured BASIC program file is missing.

**Causes:**
- Path does not match any endpoint defined in `c64-services.yml`
- Root path `/` requested and `show_service_list` is not enabled

**Example:**
```bash
curl "https://example.com/unknown"
# Returns: HTTP 404 (service not found)
```

Fix: Check that the path matches an entry in `c64-services.yml`.

### 406 Not Acceptable

Unsupported Accept header.

**Causes:**
- Accept header requests unsupported format (not `Accept: text/plain` or `Accept: application/json`)

**Example:**
```bash
curl -H "Accept: application/xml" "https://example.com/add?a=5&b=3"
# Returns: HTTP 406
```

Fix: Use `Accept: text/plain` or `Accept: application/json`.

## Server Error Responses

### 500 Internal Server Error

Program execution error or timeout.

**Causes:**
- Program prints "ERROR:" (with `catch_errors: true`)
- Program timeout exceeded
- Interpreter error (syntax error, runtime error)
- Output doesn't match `output_type`

**Example:**
```bash
curl "https://example.com/divide?a=10&b=0"
# Returns: HTTP 500 (division by zero error)
```

Fix: Handle errors in BASIC program or fix program logic.

### 501 Not Implemented

HTTP method not supported.

**Causes:**
- Request uses a method other than GET (e.g., POST, PUT, DELETE)

**Example:**
```bash
curl -X POST "https://example.com/add?a=5&b=3"
# Returns: HTTP 501
```

Fix: Use GET requests.
