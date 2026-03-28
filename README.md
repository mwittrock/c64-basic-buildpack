# Commodore 64 BASIC Buildpack for Cloud Foundry

A Cloud Foundry buildpack that lets you write web services in Commodore 64 BASIC.

## What Is This?

This buildpack allows you to deploy web services written in Commodore 64 BASIC to Cloud Foundry. Services are executed by a Python interpreter that implements the Commodore 64 BASIC language, responding to HTTP requests with either plain text or JSON.

**Key Features:**
- ✅ Pure Python Commodore 64 BASIC interpreter
- ✅ Content negotiation (plain text or JSON responses)
- ✅ Typed outputs (string, integer, float, boolean)
- ✅ Error handling with proper HTTP status codes
- ✅ Configurable service visibility

## Quick Start

### 1. Create Your Service

**manifest.yml:**
```yaml
---
applications:
  - name: my-c64-app
    memory: 256M
    buildpacks:
      - https://github.com/mwittrock/c64-basic-buildpack.git
```

**c64-services.yml:**
```yaml
services:
  - path: /hello
    program: hello.bas
```

**hello.bas:**
```basic
10 PRINT "HELLO FROM COMMODORE 64!"
```

### 2. Deploy to Cloud Foundry

```bash
cf push
```

That's it! The manifest specifies the buildpack, and the buildpack handles the rest.

### 3. Test Your Service

```bash
# Plain text response
curl https://my-c64-app.example.com/hello

# JSON response
curl -H "Accept: application/json" https://my-c64-app.example.com/hello
```

## Example Services

The `examples/` directory contains working services you can deploy immediately.

## Configuration Reference

To learn about the `c64-service.yml` file, please refer to [the documentation](docs/configuration.md).

## Content Negotiation

Control response format with the `Accept` request header:

```bash
# Plain text (default)
curl https://my-c64-app.example.com/fibonacci?n=10
# Returns: " 55 "

# JSON
curl -H "Accept: application/json" https://my-c64-app.example.com/fibonacci?n=10
# Returns: {"result": 55, "status": "success"}

# Unsupported format
curl -H "Accept: application/xml" https://my-c64-app.example.com/fibonacci?n=10
# Returns: HTTP 406 Not Acceptable
```

Supported Accept headers:
- `text/plain` → Plain text response
- `application/json` → JSON response
- `*/*` → Plain text response (default)
- Anything else → HTTP 406

For an overview of other HTTP status codes, please refer to [the documentation](docs/http-status-codes.md).

## C64 BASIC Language Support

The buildpack supports a subset of Commodore BASIC V2.0. Statements that relate to peripherals, memory, I/O, etc. are not supported, since that doesn't make sense in the cloud.

For a full overview of supported statements and functions, please refer to [the documentation](docs/basic-language.md).

## Contributing

I'm not currently looking for contributions to the project.

## License

The Commodore 64 BASIC buildpack is licensed under the MIT open-source license. For the full license text, please see the LICENSE.txt file in the root of the repository.
