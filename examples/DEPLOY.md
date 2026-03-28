# Deployment Guide

## Prerequisites

- Cloud Foundry CLI installed
- Access to a Cloud Foundry instance
- Git repository for your buildpack (or use local path)

## Quick Deploy

From the `examples/` directory:

```bash
cf push
```

The `manifest.yml` specifies everything needed:
- Python buildpack (provides Python runtime)
- C64 BASIC buildpack (provides interpreter and server)
- Start command
- Memory allocation

## File Requirements

Your application directory needs:

### Required Files

1. **manifest.yml** - Cloud Foundry manifest
```yaml
---
applications:
  - name: my-app
    memory: 256M
    buildpacks:
      - python_buildpack
      - https://github.com/yourusername/c64-buildpack.git
```

2. **runtime.txt** - Python version
```
python-3.11.x
```

3. **c64-services.yml** - Service configuration
```yaml
services:
  - path: /endpoint
    program: program.bas
```

4. **program.bas** - Your BASIC program(s)

### Optional Files

- **Procfile** - Alternative way to specify start command (overrides bin/release)
  ```
  web: python3 bridge/server.py
  ```
- **.cfignore** - Files to exclude from upload

## Buildpack Order

**Critical:** The buildpack order matters!

1. **First: python_buildpack** - Provides Python runtime
2. **Second: c64-buildpack** - Uses Python to install dependencies and run server

If you reverse the order, the C64 buildpack won't have Python available during compile.

## Python Version

Specify in `runtime.txt`:
- `python-3.11.x` - Latest Python 3.11
- `python-3.11.14` - Specific version
- `python-3.x` - Latest Python 3

See [Python buildpack docs](https://docs.cloudfoundry.org/buildpacks/python/) for supported versions.

## Troubleshooting

### "python3: command not found"

The Python buildpack didn't run. Check:
- Is `python_buildpack` listed first in buildpacks?
- Does `runtime.txt` exist?
- Is the Python version supported?

### Dependencies not installing

Check:
- Is `bridge/requirements.txt` present in the buildpack?
- Are the dependencies compatible with the Python version?
- Check staging logs: `cf logs my-app --recent`

### Application won't start

Check:
- Is `command: python3 bridge/server.py` in manifest?
- Are BASIC programs and config in the right location?
- Check app logs: `cf logs my-app`

## Multiple Apps

You can define multiple apps in one manifest:

```yaml
---
applications:
  - name: c64-api-prod
    memory: 256M
    buildpacks:
      - python_buildpack
      - https://github.com/yourusername/c64-buildpack.git
    
  - name: c64-api-test
    memory: 128M
    buildpacks:
      - python_buildpack
      - https://github.com/yourusername/c64-buildpack.git
```

Deploy specific app: `cf push c64-api-prod`

## Using Local Buildpack

For testing during development:

```bash
cf push my-app -b python_buildpack -b /path/to/c64-buildpack
```

Or create a cached buildpack:

```bash
cd c64-buildpack
zip -r c64-buildpack.zip bin/ bridge/
cf push my-app -b python_buildpack -b c64-buildpack.zip
```

## Environment Variables

Set in manifest or via CLI:

```yaml
env:
  C64_CONFIG: c64-services.yml
  PORT: 8080
```

Or:
```bash
cf set-env my-app C64_CONFIG custom-config.yml
cf restage my-app
```

## Scaling

```bash
# More instances
cf scale my-app -i 3

# More memory
cf scale my-app -m 512M

# Both
cf scale my-app -i 3 -m 512M
```

## Logs

```bash
# Stream logs
cf logs my-app

# Recent logs
cf logs my-app --recent

# App info
cf app my-app
```
