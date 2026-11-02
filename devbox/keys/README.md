# Public keys

One file per person: `<username>.pub`, holding that person's **public** key (one line starting with
`ssh-ed25519` or `ssh-rsa`). The file name is the login name, so use lowercase letters, digits, `-` or `_`.

Restart the box after adding or removing a file:

```bash
docker compose -f devbox/docker-compose.yml restart
```

The `.pub` files stay on the host PC and are git-ignored. Never put a private key here.
