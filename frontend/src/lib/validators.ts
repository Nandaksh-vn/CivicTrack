import { z } from "zod";

export const MAX_IMAGE_BYTES = 5 * 1024 * 1024;
export const ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"] as const;
export const MAX_SUBMISSION_IMAGES = 3;

const email = z
  .string()
  .trim()
  .min(3, "Email is required.")
  .max(190)
  .regex(/^[\w.+]+@[\w-]+(\.[\w-]+)+$/, "Enter a valid email address.");
const phone = z
  .string()
  .trim()
  .regex(/^[0-9+\s-]{7,20}$/, "Phone must be 7–20 characters (digits, +, spaces, dashes).")
  .optional()
  .or(z.literal(""));

export const registerSchema = z.object({
  full_name: z.string().trim().min(2, "Name must be at least 2 characters.").max(120),
  email,
  password: z
    .string()
    .min(8, "Password must be at least 8 characters.")
    .max(72, "Password must be at most 72 characters."),
  phone,
});
export type RegisterValues = z.infer<typeof registerSchema>;

export const loginSchema = z.object({
  email: email.min(1, "Email is required."),
  password: z.string().min(1, "Password is required.").max(72),
});
export type LoginValues = z.infer<typeof loginSchema>;

export const complaintSchema = z.object({
  title: z.string().trim().min(5, "Title must be at least 5 characters.").max(150),
  description: z
    .string()
    .trim()
    .min(20, "Description must be at least 20 characters.")
    .max(2000, "Description must be at most 2,000 characters."),
  category_id: z.coerce.number().int().min(1, "Choose a category."),
  location_text: z.string().trim().max(255).optional(),
  latitude: z.coerce.number().min(-90).max(90).optional(),
  longitude: z.coerce.number().min(-180).max(180).optional(),
});
export type ComplaintValues = z.infer<typeof complaintSchema>;

export const rejectSchema = z.object({
  reason: z
    .string()
    .trim()
    .min(10, "Reason must be at least 10 characters.")
    .max(1000, "Reason must be at most 1,000 characters."),
});

export const progressSchema = z.object({
  note: z
    .string()
    .trim()
    .min(5, "Note must be at least 5 characters.")
    .max(2000, "Note must be at most 2,000 characters."),
  set_status: z.enum(["IN_PROGRESS"]).optional(),
});

export const resolveSchema = z.object({
  resolution_note: z
    .string()
    .trim()
    .min(10, "Resolution note must be at least 10 characters.")
    .max(2000, "Resolution note must be at most 2,000 characters."),
});

export const superintendentActionSchema = z.object({
  action_type: z.enum(["INSTRUCTION", "FOLLOW_UP", "REASSIGN", "NOTE"]),
  note: z
    .string()
    .trim()
    .min(5, "Note must be at least 5 characters.")
    .max(2000, "Note must be at most 2,000 characters."),
  directed_department_id: z.coerce.number().int().min(1).optional(),
});

export function validateImageFiles(files: File[]): string | null {
  if (files.length > MAX_SUBMISSION_IMAGES) {
    return `Choose at most ${MAX_SUBMISSION_IMAGES} images.`;
  }
  for (const file of files) {
    if (!ALLOWED_IMAGE_TYPES.includes(file.type as (typeof ALLOWED_IMAGE_TYPES)[number])) {
      return `${file.name}: only JPEG, PNG, or WebP images are supported.`;
    }
    if (file.size > MAX_IMAGE_BYTES) {
      return `${file.name}: each image must be 5 MiB or smaller.`;
    }
  }
  return null;
}
