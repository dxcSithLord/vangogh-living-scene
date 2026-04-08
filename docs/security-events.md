# Security Events Catalog

> Reference for all security events defined in `src/security_log.py`.
> See SECURITY-POLICY.md for standards traceability.

## Event types

All events are defined in the `SecurityEvent` enum and emitted via
`log_security_event()` to the dedicated `security` logger. Each event
has a default severity from `_EVENT_SEVERITY`.

| Event | Severity | Emitting module(s) | Description |
|-------|----------|---------------------|-------------|
| `CONFIG_VALIDATION_FAIL` | ERROR | `config_validator.py` | One or more config values failed type, range, or path validation at startup. All errors are logged before `sys.exit(1)`. |
| `CHECKSUM_MISMATCH` | CRITICAL | `install.sh`, `bundle-offline.sh` | A downloaded model or transferred artifact failed SHA-256 verification. Build-time only — not emitted at runtime. |
| `ERROR_THRESHOLD_BREACH` | WARNING | `main.py` | RSS exceeds `memory.rss_warning_mb` after a pipeline stage, or the image pipeline raised an unhandled exception. |
| `BOUNDS_VIOLATION` | WARNING | (reserved) | Slot coordinates or image dimensions fail boundary validation. Defined for future use; validation currently raises `ValueError` directly. |
| `INVALID_FILE_TYPE` | WARNING | (reserved) | An image file fails magic byte verification. Defined for future use; `compositor.py` currently raises `ValueError` directly. |
| `FILE_SIZE_EXCEEDED` | WARNING | (reserved) | A JSON or image file exceeds its size cap. Defined for future use; `slots.py` currently raises `ValueError` directly. |

## Emitting a security event

```python
from src.security_log import SecurityEvent, log_security_event

log_security_event(
    SecurityEvent.CONFIG_VALIDATION_FAIL,
    "Config validation failed with 3 error(s): ...",
)
```

## Log format

```
2026-04-08T12:34:56 security ERROR [CONFIG_VALIDATION_FAIL] Config validation failed...
```

Fields: `timestamp`, logger name (`security`), severity, `[event_type]`, detail message.

## Logger initialisation

`init_security_logger()` is called twice:

1. **Bootstrap** (before config validation): console-only, so
   `CONFIG_VALIDATION_FAIL` can be emitted during `validate_or_exit()`.
2. **Full init** (after config validation): adds the optional `FileHandler`
   from `security_log.file` in config.

Both calls are idempotent — each handler type is added at most once.

## Reserved events

`BOUNDS_VIOLATION`, `INVALID_FILE_TYPE`, and `FILE_SIZE_EXCEEDED` are
defined in the enum with severity mappings but are not yet emitted from
application code. The corresponding validations currently raise
`ValueError` directly. These events are reserved for a future sprint
that adds security event emission to input validation paths.
