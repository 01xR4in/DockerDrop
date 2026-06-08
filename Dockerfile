# Pinned slim base keeps the attack surface small (no compilers, no pip deps).
# To pin by digest (stronger supply-chain hardening), use the form below with a
# digest you've confirmed points to a 3.13-slim image:
#   FROM python:3.13-slim@sha256:<digest>
FROM python:3.13-slim@sha256:aa938a849bcb82dce8f49480f056ab82bf5c1c3ebc294f0430f37b6820e7f286

# No .pyc files (rootfs is read-only at runtime), unbuffered logs to stdout.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a fixed, unprivileged user/group. No home, no login shell.
RUN groupadd --gid 10001 app \
 && useradd  --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app

# Bake the server into the image (immutable). It is NOT placed in /shared,
# so the served folder never exposes the code itself.
COPY upload_server.py /app/upload_server.py

# Drop to the unprivileged user.
USER 10001:10001

EXPOSE 8000

# Serve ONLY the /shared volume. Nothing else in the container is reachable.
CMD ["python3", "upload_server.py", "8000", "/shared"]