# HiDPI control chrome (approved — option B)

## Goal
Crisper sidebar / controls on HiDPI; not camera preview quality.

## Changes
- Detect screen DPI → `tk scaling` (clamp ~1.0–2.0); remove fixed 1.25.
- Fonts ≥15pt DejaVu; apply to raw Tk Listbox / labels.
- Sidebar width ~600–640.
