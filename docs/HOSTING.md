# Listening away from your computer

After [SETUP.md](SETUP.md) the player runs on your computer at http://localhost:8077.
This guide shows how to reach it from your phone, from outside your home, or at your own web address.

> **Keep it private.** The built site contains the game's music. It is for you, not for the public.
> Every option below is either reachable only by your own devices or sits behind a login.
> Do not put the built site on public hosting (GitHub Pages, Netlify, an open web server).

## Which option to choose

| | Option | Works where | Cost | Difficulty |
|---|---|---|---|---|
| A | [Phone on the same Wi-Fi](#a-phone-on-the-same-wi-fi) | at home only | free | 2 minutes |
| **B** | [**Tailscale**](#b-tailscale-recommended) (recommended) | anywhere, on your own devices | free | 10 minutes |
| C | [Always-on home server](#c-always-on-home-server) | adds 24/7 to A, B or D | a spare PC, mini PC or Raspberry Pi | 30 minutes |
| D | [Your own domain with Cloudflare](#d-your-own-domain-with-cloudflare) | anywhere, in any browser, at a nice address | domain, about $10–12 a year | 1 hour |

**Recommendation: B.** It is free, works from anywhere, gives you HTTPS (so the player installs as an app on the phone),
and nothing is open to the internet. Choose D only if you want a nice address such as `radio.yourname.xyz`
and do not want to install an app on your devices.

With A, B and D on your own PC, the PC must be on and `serve.py` must be running. Option C removes that.

---

## A. Phone on the same Wi-Fi

1. Start the server for the local network:
   ```powershell
   py site\serve.py 8077 0.0.0.0
   ```
   If Windows asks whether to allow Python on networks, allow **Private networks** only.
2. Run `ipconfig` and find **IPv4 Address** (Russian Windows: **IPv4-адрес**), for example `192.168.1.20`.
3. On the phone, open `http://192.168.1.20:8077`.

**Limits:** works only at home. The address is plain `http`, so the phone can bookmark the page but cannot install it as an app.

---

## B. Tailscale (recommended)

[Tailscale](https://tailscale.com) connects your own devices into a private network. Only devices signed in to your
account can open the player. The personal plan is free for non-commercial use.

1. **Install Tailscale on the PC** and sign in (Google, Microsoft, GitHub or Apple account):
   ```powershell
   winget install -e --id Tailscale.Tailscale
   ```
2. **Install Tailscale on the phone** (App Store or Google Play) and sign in with **the same account**.
3. **Start the player** on the PC as usual:
   ```powershell
   py site\serve.py 8077
   ```
4. **Share it inside your Tailscale network with HTTPS.** In a second PowerShell window:
   ```powershell
   tailscale serve --bg 8077
   ```
   The first time, it prints a link to enable HTTPS for your network: open it, confirm, and run the command again.
   It then prints your address, for example `https://my-pc.tail1234.ts.net`.
5. **On the phone**, with Tailscale switched on, open that address. Use the browser menu → **Add to Home screen**
   to install the player as an app.

**Check:** turn off Wi-Fi on the phone and open the address over mobile data. The player must open.

**Stop sharing:** `tailscale serve reset`.

---

## C. Always-on home server

Use this when you do not want to keep your PC on. Any always-on Linux machine works: a mini PC, an old laptop,
a Raspberry Pi 4/5, a NAS with Docker. It needs about 1.5 GB of space and almost no CPU.
The build itself still runs on your Windows PC; the server only serves the finished files.

1. **Install Docker** on the server ([guide](https://docs.docker.com/engine/install/)).
2. **Copy the files** from your PC. In PowerShell in the `radioport` folder, with `user@192.168.1.50` being your server:
   ```powershell
   scp -r site user@192.168.1.50:radioport-site
   scp -r deploy user@192.168.1.50:radioport
   ```
   This copies the built site to `~/radioport-site` and the configs to `~/radioport` on the server. It takes a few minutes (1.4 GB).
   If `docker` needs `sudo` on your server, write `sudo docker compose up -d` in the next step.
3. **Put the site in place and start it.** On the server:
   ```bash
   sudo mv ~/radioport-site /srv/radioport
   rm /srv/radioport/serve.py /srv/radioport/start.bat
   cd ~/radioport && docker compose up -d
   ```
   The container is `nginx:alpine` with a 128 MB memory limit and read-only files. It restarts by itself after a reboot.
4. **Check:** open `http://192.168.1.50:8090` from a device at home.

Now reach it from outside with B (install Tailscale on the server and run `tailscale serve --bg 8090` there)
or with D (point the tunnel to `http://localhost:8090`).

**Optional, automatic code updates:** `deploy/radioport-deploy.sh` with its systemd timer pulls new code from git every
2 minutes and never touches the music. Setup steps: [README.ru.md, «Деплой из git»](../README.ru.md#деплой-из-git).

---

## D. Your own domain with Cloudflare

You get an address such as `https://radio.yourname.xyz` that opens in any browser. Before the player, Cloudflare
shows a login page: you type your email, receive a one-time code, and only then see the player.
Nobody else gets in. Nothing on your router needs to change: `cloudflared` connects out to Cloudflare.

**What you need:**

- a free Cloudflare account;
- a domain, about $10–12 a year (see [Choosing and buying a domain](#choosing-and-buying-a-domain));
- a bank card: for the domain, and Cloudflare Zero Trust may ask for one even on its free plan;
- the player running on your PC (`py site\serve.py 8077`) or on a home server (option C, port 8090).

> **Fair use.** Cloudflare's terms restrict serving large media files through its CDN. Traffic for one person
> listening to their own music is small, but it is a grey area. Step 5 turns caching off for the player,
> so the music only passes through the tunnel. If you want to stay clear of this question, use option B.

### Steps

Do them **in this order**: the login (step 3) must exist before the address goes live (step 4).
Otherwise the player is public for a few minutes.

1. **Get the domain into Cloudflare.**
   Buy it in the dashboard under **Domain Registration → Register Domains**; it is then set up automatically.
   If you bought it elsewhere, click **Add a domain**, choose the **Free** plan, and change the nameservers at your
   registrar to the two Cloudflare shows. Wait until the domain status is **Active** (minutes to a few hours).
2. **Open Zero Trust** (left menu in the Cloudflare dashboard). The first time, pick a team name and the **Free** plan.
3. **Create the login.** Go to **Access → Applications → Add an application → Self-hosted**.
   - Application name: `Radioport`; domain: subdomain `radio`, your domain.
   - Policy: action **Allow**, rule **Include → Emails** → your email address.
   - Login method: **One-time PIN** (enabled by default).
   - Save.
4. **Create the tunnel.** Go to **Networks → Tunnels → Create a tunnel → Cloudflared**, name it `radioport`.
   - Cloudflare shows an install command for your system. On Windows, run it in PowerShell **as administrator**:
     it installs `cloudflared` as a service, so it starts with Windows.
   - In the next step add a **public hostname** (in some versions: **published application route**):
     subdomain `radio`, your domain, service type **HTTP**, URL `localhost:8077`
     (`localhost:8090` on a home server from option C).
   - Save.
5. **Turn off caching for the player.** In the dashboard of your domain: **Caching → Cache Rules → Create rule**,
   when **Hostname equals** `radio.yourname.xyz`, then **Bypass cache**. Deploy.
6. **Check** in a private browser window: `https://radio.yourname.xyz` must show the Cloudflare login page, not the player.
   After the one-time code from your email, the player opens.

**Turn it off:** delete the public hostname in the tunnel; the address stops working at once.

### Choosing and buying a domain

**Where:** [Cloudflare Registrar](https://www.cloudflare.com/products/registrar/) sells domains at cost, with no markup
and the same price for renewal. A `.com` costs about $10–11 a year, a `.xyz` about $11–12.
Prices change; the dashboard shows the current price before you pay. Not every ending is available there
(for example `.ru` is not); for those, buy elsewhere and use **Add a domain** in step 1.

**What name:**

- Buy one short domain for yourself and use **subdomains** for projects: `radio.yourname.xyz`, `music.yourname.xyz`.
  One domain covers all your future home projects.
- Easy to say and type: one or two words, no hyphens, no digits that can be confused with letters.
- **Do not use game trademarks** in the domain: no `cyberpunk`, `cdpr`, `nightcity` and similar.
  A domain with a brand name can be taken away, and it points attention at a private site with the game's music.
- Endings: `.com` is the most familiar; `.xyz`, `.dev`, `.me` are cheap and short. `.dev` works only over HTTPS,
  which Cloudflare provides anyway.

**Check before buying:** search for the name in the registrar. Renewal price matters more than the first-year price;
at Cloudflare they are the same.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Tailscale address does not open on the phone | Tailscale must be switched on in the phone app, and both devices signed in to the same account. On the PC, `serve.py` must be running. |
| `tailscale` is not recognized | Open a new PowerShell window after installing Tailscale. |
| Cloudflare shows error 1033 or 502 | The tunnel cannot reach the player: start `py site\serve.py 8077` (or the Docker container) and check that the service URL in the tunnel uses the same port. |
| The Cloudflare address opens the player without a login | Stop: delete the public hostname, create the Access application (step 3), then add the hostname again. |
| No one-time code arrives | Check the spam folder. The address in the Access policy must match exactly. |
| Music stutters from outside | Your home upload speed is the limit. One song needs about 0.3 Mbit/s; check that nothing else is uploading. |
