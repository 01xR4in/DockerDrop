# DockerDrop 🐳📦

**A tiny, self-hosted file share you can stand up in one command — and that can only ever touch one folder.**

DockerDrop wraps a dependency-free Python HTTP server in a hardened container.
Drop files in from any browser or the command line, grab them from any device on
your network, and rest easy knowing the container is locked down to a single
`shared/` directory with no root, no extra capabilities, and a read-only filesystem.

---

## Why DockerDrop

- **Zero dependencies** — the server is pure Python standard library. No frameworks, no pip installs.
- **One command to run** — `docker compose up -d --build` and you're sharing.
- **Locked to one folder** — the container can read and write `shared/` and nothing else.
- **Hardened by default** — non-root, read-only rootfs, all capabilities dropped, resource-limited.
- **Works everywhere** — upload from a browser form, `curl`, or any device on the LAN.

## What's inside

```
dockerdrop/
├── Dockerfile            # slim base, server baked in, runs as a non-root user
├── docker-compose.yml    # all the container hardening lives here
├── .dockerignore
├── upload_server.py      # the stdlib-only HTTP server
├── README.md             # you are here
└── shared/               # the ONE folder DockerDrop can touch
```

The server is copied **into the image**, not into `shared/`, so the code itself
is never exposed in the file listing.

## Quick start

```bash
cd dockerdrop

# DockerDrop runs as UID 10001 and must be able to write into ./shared.
# Run this once:
sudo chown -R 10001:10001 shared     # preferred
# chmod 777 shared                   # simpler, less strict

docker compose up -d --build
```

That's it. Now you can:

| Action            | How                                                      |
|-------------------|----------------------------------------------------------|
| Browse / download | open `http://<host-ip>:8000/`                            |
| Upload (browser)  | open `http://<host-ip>:8000/upload`                      |
| Upload (CLI)      | `curl -F "file=@photo.jpg" http://<host-ip>:8000/upload` |

Stop and remove with `docker compose down`.

## Heads-up: the permissions step

Because DockerDrop runs as a non-root user with a read-only root filesystem, the
**host** `shared/` directory must be writable by UID 10001. If an upload fails
with a permission error, run the `chown`/`chmod` above. This is by design — the
container has no way to grant itself access to anything outside `shared/`.

## How it's hardened

DockerDrop isn't just "a script in a box." Every layer narrows what it can do:

- **Non-root user** (UID 10001) — nothing runs as root.
- **Read-only root filesystem** — code and OS can't be modified at runtime; only `shared/` and a small `noexec` `/tmp` tmpfs are writable.
- **All Linux capabilities dropped** (`cap_drop: ALL`) — it binds port 8000, so it needs none.
- **No privilege escalation** (`no-new-privileges:true`) — blocks setuid tricks.
- **Resource limits** (`pids_limit`, `mem_limit`, `memswap_limit`, `cpus`) — contain runaway or flood traffic.
- **Minimal `python:3.12-slim` base, no dependencies** — small attack surface.
- **`init: true`, log rotation, isolated bridge network, single published port** — clean, contained operation.

### Want to go further?

- Pin the base image by digest (`FROM python:3.12-slim@sha256:...`).
- Switch to a distroless base (`gcr.io/distroless/python3`) for no shell at all.
- Restrict the port to localhost (`127.0.0.1:8000:8000`) and reach it over VPN/SSH.

## ⚠️ Security note: no authentication

DockerDrop has **no login**. Anyone who can reach port 8000 can upload and
download files, and uploads overwrite same-named files. Run it only on a network
you trust, or put it behind a reverse proxy (Caddy, nginx, Traefik) that adds
TLS and basic auth.

---

*DockerDrop — drop it at the dock.* 🐳