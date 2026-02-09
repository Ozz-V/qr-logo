import flet as ft
import qrcode
from PIL import Image, ImageDraw, ImageOps
import base64
import io
import os
import traceback

# ======================================================
# MOTOR QR
# ======================================================

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def crear_fondo(w, h, modo, c1, c2):
    if modo == "Transparente":
        return Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if modo == "Sólido (Color)":
        return Image.new("RGBA", (w, h), c1 + (255,))
    return Image.new("RGBA", (w, h), (255, 255, 255, 255))

def generar_qr_full_engine(params, data):
    try:
        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=0
        )
        qr.add_data(data)
        qr.make(fit=True)

        matrix = qr.get_matrix()
        modules = len(matrix)
        size = modules * 40

        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)

        for r in range(modules):
            for c in range(modules):
                if matrix[r][c]:
                    x, y = c * 40, r * 40
                    draw.rounded_rectangle(
                        [x + 2, y + 2, x + 38, y + 38],
                        radius=12,
                        fill=255
                    )

        body_color = hex_to_rgb(params["c1"])
        qr_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        body_img = Image.new("RGBA", (size, size), body_color + (255,))
        qr_layer.paste(body_img, (0, 0), mask)

        if params["logo_path"] and os.path.exists(params["logo_path"]):
            logo = Image.open(params["logo_path"]).convert("RGBA")
            logo = ImageOps.contain(logo, (int(size * 0.25), int(size * 0.25)))
            pos = ((size - logo.width) // 2, (size - logo.height) // 2)
            qr_layer.paste(logo, pos, logo)

        bg = crear_fondo(
            size + 80,
            size + 80,
            params["modo_fondo"],
            hex_to_rgb(params["bg_c1"]),
            hex_to_rgb(params["bg_c2"]),
        )

        bg.paste(qr_layer, (40, 40), qr_layer)

        buf = io.BytesIO()
        bg.save(buf, format="PNG")

        return base64.b64encode(buf.getvalue()).decode(), buf.getvalue()

    except:
        return None, None

# ======================================================
# APP
# ======================================================

def main(page: ft.Page):
    try:
        page.title = "QR + Logo"
        page.theme_mode = "dark"
        page.bgcolor = "#111111"
        page.padding = 20
        page.scroll = "auto"

        qr_bytes = None
        logo_path = ""

        # -------------------------------
        # FilePickers (ANDROID SAFE)
        # -------------------------------

        def on_logo_picked(e: ft.FilePickerResultEvent):
            nonlocal logo_path
            if e.files:
                logo_path = e.files[0].path
                btn_logo.text = "Logo cargado"
                btn_logo.bgcolor = "green"
                page.update()

        def on_save(e: ft.FilePickerResultEvent):
            if e.path and qr_bytes:
                with open(e.path, "wb") as f:
                    f.write(qr_bytes)
                page.show_snack_bar(ft.SnackBar(ft.Text("QR guardado")))

        picker_logo = ft.FilePicker(on_result=on_logo_picked)
        picker_save = ft.FilePicker(on_result=on_save)
        page.overlay.extend([picker_logo, picker_save])

        # -------------------------------
        # UI
        # -------------------------------

        txt_data = ft.TextField(label="Texto / URL", bgcolor="#222222")

        btn_logo = ft.ElevatedButton(
            "Subir logo",
            icon="image",
            on_click=lambda _: picker_logo.pick_files()
        )

        img_preview = ft.Image(width=260, height=260, visible=False)

        btn_save = ft.ElevatedButton(
            "Guardar QR",
            icon="save",
            disabled=True,
            on_click=lambda _: picker_save.save_file("qr.png")
        )

        def generar(e):
            nonlocal qr_bytes
            if not txt_data.value:
                return

            params = {
                "logo_path": logo_path,
                "c1": "#000000",
                "bg_c1": "#FFFFFF",
                "bg_c2": "#FFFFFF",
                "modo_fondo": "Blanco (Default)",
            }

            b64, raw = generar_qr_full_engine(params, txt_data.value)
            if b64:
                qr_bytes = raw
                img_preview.src_base64 = b64
                img_preview.visible = True
                btn_save.disabled = False
                page.update()

        btn_gen = ft.ElevatedButton(
            "GENERAR QR",
            bgcolor="green",
            color="white",
            height=50,
            on_click=generar
        )

        page.add(
            ft.Column(
                [
                    ft.Text("QR + Logo", size=24, weight="bold"),
                    txt_data,
                    btn_logo,
                    btn_gen,
                    img_preview,
                    btn_save,
                ],
                spacing=15,
            )
        )

    except Exception:
        page.add(ft.Text(traceback.format_exc(), color="red"))

ft.app(target=main, assets_dir="assets")
