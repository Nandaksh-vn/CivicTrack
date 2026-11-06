# CivicTrack — Third-Party Licenses & Attributions

> **Document:** `docs/LICENSES.md`  
> **Release:** v1.0.0-p0  

CivicTrack is built using open-source libraries and frameworks. All dependencies have been screened for commercial compatibility (permissive open-source licenses: MIT, Apache 2.0, BSD-3-Clause).

---

## 1. Backend Dependencies

| Package | Version | License | Usage |
|---|---|---|---|
| `fastapi` | 0.115.11 | MIT | Web API framework |
| `uvicorn` | 0.34.0 | BSD-3-Clause | ASGI production server |
| `sqlalchemy` | 2.0.38 | MIT | ORM and SQL toolkit |
| `alembic` | 1.14.1 | MIT | Database migration tool |
| `pymysql` | 1.1.1 | MIT | MySQL Python driver |
| `pydantic` | 2.10.6 | MIT | Data parsing and validation |
| `bcrypt` | 4.3.0 | Apache-2.0 | Password hashing |
| `pyjwt` | 2.10.1 | MIT | Bearer token creation and validation |
| `pillow` | 11.1.0 | HPND / MIT-like | Image processing & magic-byte validation |
| `pytest` | 8.3.5 | MIT | Test suite runner |

---

## 2. Frontend Dependencies

| Package | Version | License | Usage |
|---|---|---|---|
| `react` | 18.3.1 | MIT | User interface framework |
| `react-dom` | 18.3.1 | MIT | DOM rendering engine |
| `react-router-dom` | 6.28.2 | MIT | Client-side routing |
| `@tanstack/react-query`| 5.66.0 | MIT | Server-state caching and synchronization |
| `tailwindcss` | 3.4.17 | MIT | Utility-first CSS styling |
| `lucide-react` | 0.475.0 | ISC | Icon system |
| `zod` | 3.24.2 | MIT | Schema validation |
| `vite` | 6.1.0 | MIT | Frontend build tooling |
| `vitest` | 2.1.9 | MIT | Frontend unit testing |

---

## 3. Container Images

| Image | Base OS | License | Purpose |
|---|---|---|---|
| `python:3.12-slim` | Debian 12 | Python-2.0 | Backend runtime |
| `node:20-alpine` | Alpine Linux | MIT | Frontend builder |
| `nginx:1.27-alpine`| Alpine Linux | 2-clause BSD-like | Static file server and proxy |
| `mysql:8.4` | Oracle Linux | GPLv2 with FOSS Exception | Primary relational database |

