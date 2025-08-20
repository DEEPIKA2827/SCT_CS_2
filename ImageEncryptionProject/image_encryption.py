#!/usr/bin/env python3
"""
Image Cipher: simple, reversible image "encryption" using pixel manipulation.
- Math operations: XOR / ADD / SUB (per-channel, modulo 256)
- Channel swaps: swap R<->G, R<->B, G<->B (self-inverse)

Usage examples are at the bottom of this file in the __main__ section.
"""

from PIL import Image
import argparse
import os
import sys

def clamp_key(key: int) -> int:
    if key is None:
        raise ValueError("This operation requires --key (0-255).")
    if not (0 <= key <= 255):
        raise ValueError("Key must be between 0 and 255.")
    return key

def apply_math(pixel, op, key):
    # pixel is a tuple of (R,G,B[,A])
    # Only transform RGB; keep A (alpha) unchanged if present
    r, g, b, a = (pixel + (255,))[:4]  # ensure we have RGBA (fake full alpha if missing)
    if op == "xor":
        r = r ^ key
        g = g ^ key
        b = b ^ key
    elif op == "add":
        r = (r + key) % 256
        g = (g + key) % 256
        b = (b + key) % 256
    elif op == "sub":
        r = (r - key) % 256
        g = (g - key) % 256
        b = (b - key) % 256
    else:
        raise ValueError(f"Unknown math op: {op}")
    return (r, g, b, a)

def apply_swap(pixel, swap):
    r, g, b, a = (pixel + (255,))[:4]
    if swap == "rg":
        r, g = g, r
    elif swap == "rb":
        r, b = b, r
    elif swap == "gb":
        g, b = b, g
    else:
        raise ValueError("swap must be one of: rg, rb, gb")
    return (r, g, b, a)

def process_image(in_path, out_path, mode, op, key=None, swap=None):
    if not os.path.isfile(in_path):
        raise FileNotFoundError(f"Input image not found: {in_path}")

    img = Image.open(in_path).convert("RGBA")
    pixels = list(img.getdata())
    out_pixels = []

    if op in ("xor", "add", "sub"):
        # Determine direction for reversible math
        k = clamp_key(key)
        # For decrypt: invert the operation
        if mode == "decrypt":
            if op == "add":
                effective = "sub"
            elif op == "sub":
                effective = "add"
            else:
                effective = "xor"  # XOR is its own inverse
        else:
            effective = op

        for p in pixels:
            out_pixels.append(apply_math(p, effective, k))

    elif op == "swap":
        if swap not in ("rg", "rb", "gb"):
            raise ValueError("For --op swap, provide --swap {rg|rb|gb}")
        # Swaps are self-inverse → apply same swap for both encrypt & decrypt
        for p in pixels:
            out_pixels.append(apply_swap(p, swap))

    else:
        raise ValueError("Unsupported --op. Choose from: xor, add, sub, swap")

    img_out = Image.new("RGBA", img.size)
    img_out.putdata(out_pixels)

    # Preserve original format if possible; default to PNG
    ext = os.path.splitext(out_path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        # Convert back to RGB to save as JPEG (no alpha channel)
        img_out = img_out.convert("RGB")
    img_out.save(out_path)
    return out_path

def build_argparser():
    p = argparse.ArgumentParser(
        description="Simple reversible image cipher using pixel manipulation."
    )
    p.add_argument("--input", "-i", required=True, help="Path to input image")
    p.add_argument("--output", "-o", required=True, help="Path to output image")
    p.add_argument("--mode", "-m", choices=["encrypt", "decrypt"], required=True,
                   help="encrypt or decrypt")
    p.add_argument("--op", choices=["xor", "add", "sub", "swap"], required=True,
                   help="Operation to apply: xor/add/sub/swap")
    p.add_argument("--key", type=int, help="Key (0-255) for xor/add/sub")
    p.add_argument("--swap", choices=["rg", "rb", "gb"],
                   help="For --op swap, which channels to swap")
    return p

def main():
    parser = build_argparser()
    args = parser.parse_args()

    try:
        out_path = process_image(
            in_path=args.input,
            out_path=args.output,
            mode=args.mode,
            op=args.op,
            key=args.key,
            swap=args.swap
        )
        print(f"Success ✅ Wrote: {out_path}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
