# Team devbox

A blank Debian 13 machine in Docker that teammates log into over SSH. Each person gets their own account with
sudo. Home folders persist across restarts and rebuilds.

## Connect

```bash
ssh -p 2222 <username>@<host>
```

- `<username>` and the password: your line in `passwords.txt` (ask Charleigh).
- `<host>`: the host PC's public IP address, or a DNS name pointing to it. The name must be **DNS-only**, not proxied,
  in Cloudflare: Cloudflare's proxy doesn't carry SSH.
- Change your password after the first login with `passwd`.
- VS Code: install **Remote - SSH**, then connect to `<username>@<host>:2222`.

## Run it (host PC)

```bash
cp devbox/passwords.example.txt devbox/passwords.txt   # one "username:password" per line
docker compose -f devbox/docker-compose.yml up -d --build
```

The router must forward **TCP 2222** to this PC. To add or remove a person, edit `passwords.txt` and run
`docker compose -f devbox/docker-compose.yml restart`. A removed line stops that password from being
reset on restart, but it doesn't delete the account; to do that, run `userdel` inside the container.

## Safety

The port is open to the internet, so:

- Root can't log in, and only accounts listed in `passwords.txt` can.
- Passwords are long and random; each connection gets 3 tries.
- It's a container: no access to the host's files, and no Docker socket.
- Safer still: once everyone has an SSH key, turn off `PasswordAuthentication` in `sshd_devbox.conf`.
