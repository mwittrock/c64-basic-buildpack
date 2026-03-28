# C64 BASIC Language Reference

This document describes the subset of Commodore BASIC V2.0 supported by the buildpack.

## Why a Subset?

The buildpack implements Commodore BASIC V2.0 — the same dialect shipped on stock Commodore 64s. However, it implements only the portion of that dialect that makes sense for writing web services.

Commodore 64 BASIC was designed for a machine with a keyboard, a screen, peripherals, and direct access to memory-mapped hardware. Many of its statements exist solely to control that hardware. In a cloud environment none of those things exist: there are no printers to write to, no memory addresses to poke, no files to open on a floppy disk.

The subset was therefore chosen by a single criterion: **does this feature serve computation or program flow?** Everything that does is included. Everything that only serves hardware interaction is excluded.

The goal is that a program using only supported features runs on both a real Commodore 64 (actual hardware or emulated) and as a deployed web service — with one deliberate exception described below.

## Supported Statements at a Glance

### Statements

| Statement            | Purpose                                      |
|----------------------|----------------------------------------------|
| `REM`                | Comment                                      |
| `LET`                | Variable assignment                          |
| `DIM`                | Declare array                                |
| `PRINT`              | Output text and values                       |
| `INPUT`              | Read input — **behaves differently; see below** |
| `IF … THEN`          | Conditional branch                           |
| `FOR … TO … STEP`    | Counted loop                                 |
| `NEXT`               | End of FOR loop                              |
| `GOTO`               | Unconditional jump                           |
| `GOSUB`              | Call subroutine                              |
| `RETURN`             | Return from subroutine                       |
| `END`                | Stop execution                               |
| `STOP`               | Stop execution (same as END)                 |
| `DATA`               | Embed constant data in the program           |
| `READ`               | Read next value from DATA                    |
| `RESTORE`            | Reset the DATA pointer                       |
| `DEF FN`             | Define a single-parameter user function      |

### Built-in Functions

| Function         | Category |
|------------------|----------|
| `ABS`, `INT`, `SGN`, `SQR` | Math     |
| `SIN`, `COS`, `TAN`, `ATN` | Trigonometry |
| `EXP`, `RND`     | Math     |
| `LEFT$`, `RIGHT$`, `MID$` | Strings  |
| `LEN`, `CHR$`, `ASC`, `STR$`, `VAL` | Strings |

### System Variables

| Variable | Description                   |
|----------|-------------------------------|
| `TI`     | System timer (jiffies / 60 s) |

### INPUT — the one statement that behaves differently

On a real Commodore 64, `INPUT` pauses the program and waits for the user to type a value at the keyboard. In a web service there is no keyboard and no interactive session: the HTTP request arrives complete, with all its parameters, before the program starts.

When running as a web service, `INPUT` does not block for keyboard input. Instead, it reads from the HTTP query parameters mapped in `c64-services.yml`. The program never pauses; it runs to completion in a single pass and sends its `PRINT` output as the HTTP response.

Why keep INPUT at all? Because it is the natural Commodore 64 idiom for accepting external values, and preserving it means the same program file runs on real hardware and in the cloud without modification. The optional prompt string (e.g. `INPUT "ENTER N"; N%`) is written for the human sitting at the Commodore 64 keyboard; the buildpack's BASIC interpreter ignores it, but real hardware displays it.

Mapping is defined in `c64-services.yml`:

```yaml
params:
  - name: n
    variable: N
    type: integer
```

A request to `/fibonacci?n=10` sets the variable `N%` to `10` before execution begins.

To learn more about the `c64-services.yml` configuration file, go [here](configuration.md).