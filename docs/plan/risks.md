# Known Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| OOM during rembg + TFLite | High | Blocking | Sequential loading; silueta fallback; 512 MB swap |
| Style transfer too slow (>120 s) | Medium | UX only | Acceptable given display refresh rate; cache on re-entry |
| IMX500 detection misses animals | Medium | Functional gap | COCO includes dog/cat/bird; test with target animals early |
| SD card corruption under power loss | Medium | Data loss | `sync` after config writes; read-only rootfs option later |
| 22-pin cable not obtained | Low | Blocking | Document as hard prerequisite |
| rembg onnxruntime ARM wheel unavailable | Low | Blocking | Test install early in Sprint 1 on Pi hardware |
| Tampered model loaded via install.sh | Low | High | SHA-256 checksum verification (SEC-01) |
| Malformed config causes undefined behaviour | Medium | High | Startup validation with fail-fast (SEC-02) |
| Process privilege escalation via systemd | Low | High | Full sandbox directives (SEC-03) |
| Known CVE in Pillow <10.4 | Medium | Medium | Version floor bumped to >=10.4 (SEC-05) |
| Supply chain attack via pip packages | Low | High | Hash-pinned requirements (SEC-04) |
| Core dump fills SD card on 512 MB device | Low | Medium | LimitCORE=0 + ulimit in install.sh (SEC-10) |
| Security log fills SD card storage | Medium | Medium | journald SystemMaxUse=50M in Sprint 4 service (RG-07) |
