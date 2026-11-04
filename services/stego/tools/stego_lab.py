import argparse
from pathlib import Path
import numpy as np
from PIL import Image
from stego_svc.synthetic import embed_lsb, natural_image, png_bytes
from PIL import PngImagePlugin
from stego_svc import png
from stego_svc.verdict import classify

def main():
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("embed"); p.add_argument("input"); p.add_argument("output"); p.add_argument("--rate", type=float, default=.1); p.add_argument("--mode", choices=("seq", "random"), default="seq")
    d = sub.add_parser("demo"); d.add_argument("output")
    c = sub.add_parser("calibrate"); c.add_argument("folder")
    args = parser.parse_args()
    if args.command == "embed":
        pixels = np.asarray(Image.open(args.input).convert("RGB")); Path(args.output).write_bytes(png_bytes(embed_lsb(pixels, args.rate, args.mode)))
    elif args.command == "demo":
        output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
        clean = natural_image(0, 256)
        (output / "1-limpia.png").write_bytes(png_bytes(clean))
        (output / "3-revision-manual-lsb.png").write_bytes(png_bytes(embed_lsb(natural_image(1, 256), .50, "random")))
        info = PngImagePlugin.PngInfo(); info.add_text("Comment", "x" * 2000)
        (output / "2-problema-zip-al-final.png").write_bytes(png_bytes(clean, pnginfo=info))
        (output / "4-invalida-no-es-imagen.png").write_bytes(b"esto no es una imagen")
        print(f"imágenes de demo escritas en {output}")
    elif args.command == "calibrate":
        paths = sorted(p for p in Path(args.folder).iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
        if len(paths) < 15: raise SystemExit("se requieren al menos 15 imágenes")
        cfg = {"chi2_p": .995, "rs_rate": .15, "entropy_trigger": None}
        variants = {"limpia": []}
        for mode in ("seq", "random"):
            for rate in (.05, .10, .25, .50): variants[f"{mode} {rate:.0%}"] = []
        for path in paths:
            image = Image.open(path).convert("RGB")
            image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            clean = np.asarray(image).copy()
            variants["limpia"].append(png.analyze(png_bytes(clean), cfg))
            for mode in ("seq", "random"):
                for rate in (.05, .10, .25, .50):
                    altered = embed_lsb(clean, rate, mode)
                    variants[f"{mode} {rate:.0%}"].append(png.analyze(png_bytes(altered), cfg))
        print("variante | limpias | revision_manual | problema | total")
        for name, results in variants.items():
            counts = {"limpia": 0, "revision_manual": 0, "problema": 0}
            for item in results: counts[classify(item)] += 1
            print(f"{name} | {counts['limpia']} | {counts['revision_manual']} | {counts['problema']} | {len(results)}")
if __name__ == "__main__": main()
