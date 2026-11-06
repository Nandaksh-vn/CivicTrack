import { describe, expect, it } from "vitest";

import {
  complaintSchema,
  loginSchema,
  progressSchema,
  registerSchema,
  rejectSchema,
  resolveSchema,
  validateImageFiles,
} from "@/lib/validators";

describe("validators mirror server constraints (TEST-035)", () => {
  it("register: name 2-120, password 8-72, email format, phone charset", () => {
    expect(
      registerSchema.safeParse({
        full_name: "A",
        email: "not-an-email",
        password: "short",
        phone: "abc",
      }).success,
    ).toBe(false);
    expect(
      registerSchema.safeParse({
        full_name: "Priya Sharma",
        email: "priya@example.com",
        password: "Citizen123",
        phone: "+91 98765 43210",
      }).success,
    ).toBe(true);
  });

  it("login: email required, password required (generic credential errors)", () => {
    expect(loginSchema.safeParse({ email: "", password: "" }).success).toBe(false);
    expect(loginSchema.safeParse({ email: "a@b.com", password: "x" }).success).toBe(true);
  });

  it("complaint: title 5-150, description 20-2000, category required", () => {
    expect(
      complaintSchema.safeParse({
        title: "Road",
        description: "short",
        category_id: 0,
      }).success,
    ).toBe(false);
    expect(
      complaintSchema.safeParse({
        title: "Pothole on Main Street",
        description: "A large pothole has opened near the crossing and needs repair.",
        category_id: 3,
      }).success,
    ).toBe(true);
  });

  it("reject 10-1000, progress 5-2000, resolve 10-2000", () => {
    expect(rejectSchema.safeParse({ reason: "too short" }).success).toBe(false);
    expect(rejectSchema.safeParse({ reason: "Duplicate of an existing report." }).success).toBe(
      true,
    );
    expect(progressSchema.safeParse({ note: "abc" }).success).toBe(false);
    expect(progressSchema.safeParse({ note: "Crew dispatched today." }).success).toBe(true);
    expect(resolveSchema.safeParse({ resolution_note: "short" }).success).toBe(false);
    expect(
      resolveSchema.safeParse({ resolution_note: "Road repaired and reopened to traffic." })
        .success,
    ).toBe(true);
  });

  it("image validation: max 3, JPEG/PNG/WebP only, 5 MiB cap", () => {
    const png = new File(["x"], "a.png", { type: "image/png" });
    const gif = new File(["x"], "a.gif", { type: "image/gif" });
    const big = new File(["x".repeat(6 * 1024 * 1024)], "big.png", { type: "image/png" });
    expect(validateImageFiles([png])).toBeNull();
    expect(validateImageFiles([png, png, png, png])).toMatch(/at most 3/);
    expect(validateImageFiles([gif])).toMatch(/JPEG, PNG, or WebP/);
    expect(validateImageFiles([big])).toMatch(/5 MiB/);
  });
});
