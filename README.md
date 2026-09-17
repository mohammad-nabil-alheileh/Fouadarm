# Fouad Farm

A nursery inventory and point-of-sale system: FIFO batch tracking for plant
stock, order/checkout management with partial payments, and reporting — with
a bilingual (English/Arabic, RTL-aware) web frontend.

**Stack:** FastAPI + SQLAlchemy Core (no ORM) on the backend, Postgres for
storage, Alembic for migrations, and a static HTML/CSS/JS frontend served by
nginx. Everything runs in Docker, so setup is the same shape on Linux and
Windows — the differences are just in which tools you install first.

---

## 1. Prerequisites

### Linux
- **Docker Engine** and the **Docker Compose plugin**. On most distros:
  ```bash
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker $USER   # then log out/in so you can run docker without sudo
  ```
  Confirm with:
  ```bash
  docker --version
  docker compose version
  ```
- `git` to clone the repo.

### Windows
- **Docker Desktop** (includes Docker Compose) — [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/).
  During install, keep the **WSL 2 backend** enabled (the default) rather
  than the older Hyper-V-only mode — it's faster and matches how the
  containers behave on Linux.
- **Git for Windows**, or clone from inside WSL2.
- Run all commands below from either **PowerShell** or a **WSL2 terminal**
  (e.g. Ubuntu on WSL). If you use PowerShell, run it as your normal user —
  Docker Desktop handles the privilege boundary, you don't need "Run as
  Administrator" for `docker` commands.

> If you're doing regular development rather than just running the app,
> working from inside WSL2 (`\\wsl$\...` or a WSL home directory) is
> noticeably faster than a `C:\...` path, since Docker Desktop's WSL2 backend
> avoids the Windows/Linux filesystem translation overhead.

---

## 2. Clone and start

Same on both platforms:

```bash
git clone <your-repo-url> fouad-farm
cd fouad-farm
docker compose up --build
```

(On Linux with an older standalone Compose install, use `docker-compose up
--build` — hyphenated — instead of `docker compose`.)

This builds and starts three containers:

| Service        | What it is                          | Port on your machine |
|----------------|--------------------------------------|-----------------------|
| `db`           | Postgres 16                         | `5433` |
| `web_backend`  | FastAPI app (Uvicorn)                | `5000` |
| `web_frontend` | nginx serving the static frontend    | `8080` |

First boot takes a bit longer while Postgres initializes and the backend
image builds. Once it settles, open:

- **App:** http://localhost:8080
- **API root:** http://localhost:5000
- **Interactive API docs (Swagger UI):** http://localhost:5000/docs

Press `Ctrl+C` to stop, or run `docker compose down` from another terminal
in the project folder. Add `-v` (`docker compose down -v`) if you also want
to wipe the Postgres data volume and start fresh.

---

## 3. Database migrations (Alembic)

The backend container's `dockerfile` already runs `alembic upgrade head`
before starting Uvicorn, so a fresh `docker compose up` will have an
up-to-date schema automatically.

If you change a table definition in `backend/src/infrastructure/tables.py`
and need to generate a new migration, run it **inside the backend
container** so it uses the same `DATABASE_URL` the app uses:

```bash
docker compose exec web_backend alembic revision --autogenerate -m "describe your change"
docker compose exec web_backend alembic upgrade head
```

This works identically on Linux and Windows — `docker compose exec` runs
the command inside the Linux container regardless of your host OS. Because
`backend/` is bind-mounted into the container, the generated migration file
appears directly in `backend/alembic/versions/` on your host machine too.

> Running `alembic revision --autogenerate` **outside** the container (e.g.
> directly on your host Python) will *not* see `DATABASE_URL` unless you
> export it yourself first, and will otherwise fall back to whatever's
> hardcoded in `alembic.ini` — which won't match this project's database.
> Always run Alembic commands through `docker compose exec` unless you've
> deliberately set up a matching local environment.

---

## 4. Using the app

- The sidebar has **Dashboard**, **Products & Batches**, **New Order**,
  **Orders**, and **Reports**.
- The **EN / AR** toggle in the top bar switches the whole interface,
  including layout direction (right-to-left for Arabic) — your language
  choice is remembered in the browser for next time.
- **Products & Batches** is where you add products and log batches (with
  quarter/foot/line location codes); stock is deducted FIFO automatically
  whenever an order is placed or stock is trashed.
- **New Order** is the point-of-sale screen: pick products, adjust
  quantities, optionally record a payment or override the total, and place
  the order.
- **Orders** shows every order with amount paid/remaining, lets you record
  additional payments on partially-paid orders, edit an order's items or
  customer, or cancel it (which returns stock to inventory).
- **Reports** covers batch stock levels, customer spending history, top
  products, and a multi-filter order search (customer, product, payment
  method, paid/unpaid, and date range).

---

## 5. Troubleshooting

**Port already in use (`8080`, `5000`, or `5433`)**
Something else on your machine is using that port. Either stop the other
process, or change the left-hand side of the port mapping in
`docker-compose.yml`, e.g. `"8081:80"` to use 8081 instead of 8080.

**Containers exit immediately / backend can't reach the database**
Check the logs:
```bash
docker compose logs web_backend
docker compose logs db
```
`docker-compose.yml`'s `DATABASE_URL` currently points at `db:5433`, but the
`db` service doesn't override Postgres's default port — it listens on
`5432` internally. If you see connection errors here, either change
`DATABASE_URL` to use `5432`, or add `command: -p 5433` under the `db`
service (and update its healthcheck to match) so Postgres actually listens
on `5433`. Pick one and make it consistent across `DATABASE_URL`, the `db`
service, and its healthcheck.

**Windows: Docker Desktop won't start / "WSL 2 installation is incomplete"**
Run `wsl --update` in PowerShell, then restart Docker Desktop. Make sure
virtualization is enabled in your BIOS/UEFI (it usually is by default on
modern machines).

**Linux: "permission denied" on `/var/run/docker.sock`**
You're not in the `docker` group yet, or haven't re-logged-in since being
added. Run `sudo usermod -aG docker $USER`, then fully log out and back in
(or `newgrp docker` for the current shell).

**Changes to frontend files not showing up**
The frontend is built into the nginx image at `docker compose up --build`
time rather than bind-mounted, so after editing anything in
`frontend/templates/`, rebuild that one service:
```bash
docker compose up --build web_frontend
```
Also hard-refresh the browser (Ctrl+Shift+R / Cmd+Shift+R) to bypass any
cached CSS/JS.

**Line endings (Windows)**
If you edit shell scripts or the `dockerfile`s on Windows with an editor
that saves CRLF line endings, some tools inside the Linux containers can
choke on the `\r`. Configure Git to keep them LF on checkout:
```bash
git config --global core.autocrlf input
```

---

## 6. Project layout

```
backend/            FastAPI app (domain / application / infrastructure / presentation layers)
  alembic/           Migrations
  src/
frontend/
  templates/         Static HTML/CSS/JS served by nginx
  nginx.conf
docker-compose.yml
```
