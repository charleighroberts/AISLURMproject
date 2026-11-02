# Team devbox

A blank Debian 13 machine in Docker that teammates log into over SSH, until the IA Lab VM is ready. Each
person gets their own account with passwordless `sudo`. Home folders persist across restarts and rebuilds.

## For teammates: get access

1. **Make a key pair** (once per laptop). In PowerShell, Terminal or Git Bash:

   ```bash
   ssh-keygen -t ed25519
   ```

   Press Enter to accept the location. A passphrase is optional but recommended.

2. **Send Charleigh your public key**: the contents of `~/.ssh/id_ed25519.pub` (on Windows,
   `C:\Users\<you>\.ssh\id_ed25519.pub`). It's one line starting with `ssh-ed25519`. Never send the file
   without `.pub`; that one is your private key.

3. **Connect** once Charleigh says you're added:

   ```bash
   ssh -p 2222 <username>@<host>
   ```

   Type `yes` the first time to trust the box. VS Code: install **Remote - SSH** and connect to
   `<username>@<host>:2222`.

## For Charleigh: add or remove someone

Save their public key as `devbox/keys/<username>.pub` (lowercase; the file name becomes the login name),
then restart:

```bash
docker compose -f devbox/docker-compose.yml restart
```

Delete the file and restart to revoke a login. The router must forward **TCP 2222** to this PC, and the
host name you give out must be DNS-only, not proxied, in Cloudflare (Cloudflare's proxy doesn't carry SSH).

First-time setup on a new host: `docker compose -f devbox/docker-compose.yml up -d --build`.

## Safety

The port is open to the internet, and the box shares a PC with live websites, so:

- **Keys only.** No passwords exist in the box. Root can't log in, and users can't add keys themselves.
- **Fenced off from the host.** The box reaches the internet, but not this PC, other containers, or the
  home network. The entrypoint sets the firewall, then drops the `NET_ADMIN` capability before SSH starts,
  so not even `sudo` can change it.
- **No access to Docker or the host's files.** It's an unprivileged container with no host folders mounted.
