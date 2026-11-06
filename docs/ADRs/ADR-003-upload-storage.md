# ADR-003 ΓÇö Local volume storage with authorized streaming

- **Status:** Accepted
- **Date:** 06 November 2026
- **Phase:** 2 (design), implemented in Phase 6/9
- **Deciders:** Architecture workstream (DOC), backend workstream (BE)
- **References:** FR-010, FR-023, FR-037; SRS SEC-09, SEC-10; TRD ┬º10; ARCHITECTURE ┬º4.2

---

## Context

Citizens attach up to three images per complaint; officers attach progress and resolution evidence. Images are personal data and can reveal a citizen's location. P0 must run locally with one command and has no cloud storage credentials. Any storage choice must still prevent unauthenticated access and must not let a filename influence a filesystem path.

## Decision

Images are stored on a **local named Docker volume** (`civictrack_uploads`, mounted at `/app/uploads`) and served only through an **authenticated streaming endpoint**.

Rules:

1. Path scheme is `{UPLOAD_DIR}/{yyyy}/{mm}/{complaint_id}/{uuid4}.{ext}`. The client filename is stored as metadata for display and is **never** used to build a path.
2. Validation happens before write: size Γëñ 5 MiB (`5_242_880` bytes), MIME in `image/jpeg|png|webp`, Pillow `verify()` succeeds, detected format matches, dimensions Γëñ 10,000 ├ù 10,000.
3. Files are written to a temp file and atomically moved into place. If any file in a request fails, the whole request fails and temp files are removed.
4. Database metadata is inserted in the same transaction as the owning complaint or update. Orphan files are tolerated and reaped by an operational cleanup; orphan rows are not possible because the transaction owns them.
5. Serving goes through `GET /complaints/{id}/images/{image_id}/file`, which re-applies the complaint detail scope rules and verifies the image belongs to that complaint. Response is `Content-Disposition: inline`, `Cache-Control: private, max-age=300`, stored MIME type.
6. No static file mount, no directory listing, no predictable unauthenticated URL, no public bucket.
7. Maximum 3 images per request and 10 per complaint lifetime.

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| S3 / object storage | Requires credentials and network the local-first P0 cannot assume; adds a deployment dependency. |
| Store bytes in MySQL (`BLOB`) | Bloats the database, hurts backup/restore, and complicates streaming. |
| Serve from nginx static path | Would make images public and bypass per-complaint authorization. |
| Keep original filename as the path | Path traversal and collision risk. |
| Client-side compression only | Server must still enforce limits; client validation is UX only. |

## Consequences

**Easier**

- One-command local start with no external service.
- Authorization is uniform: the same scope function guards detail and image bytes.
- Tests can assert 403/404 on image access for another department or citizen.

**Harder / constrained**

- The volume must be backed up separately from MySQL; a restore needs both.
- Horizontal scaling of the API requires a shared volume or a later migration to object storage.
- Streaming is synchronous and occupies a worker for the transfer duration.

**Forbidden**

- Building a path from user input.
- Writing the file after the database transaction commits.
- Returning a filesystem path or a raw storage key in any API response.

## Enforcement

| Check | Where |
|---|---|
| Unauthenticated image request returns 401 | `T-COMP` / `T-RBAC` |
| Cross-department image request returns 403 | `T-RBAC` |
| Oversized or spoofed image rejected | `T-COMP` |
| Image path contains a UUID, not the client filename | `T-COMP` |
| Transaction rollback removes metadata and temp files | `T-COMP` integration test |

*End of ADR-003.*
