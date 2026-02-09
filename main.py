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

def generar_qr(data, logo_path, estilo):
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=0,
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
                if estilo == "Circular (Puntos)":
                    draw.ellipse([x, y, x+40, y+40], fill=255)
                elif estilo == "Liquid Pro (Gusano)":
                    draw.rounded_rectangle(
                        [x+2, y+2, x+38, y+38],
                        radius=15,
                        fill=255
                    )
                else:
                    draw.rectangle([x, y, x+40, y+40], fill=255)

    qr_color = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    qr_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    qr_img.paste(qr_color, (0, 0), mask)

    if logo_path and os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo = ImageOps.contain(logo, (int(size * 0.25), int(size * 0.25)))
        pos = ((size - logo.width)//2, (size - logo.height)//2)
        qr_img.paste(logo, pos, logo)

    bg = Image.new("RGBA", (size + 80, size + 80), (255, 255, 255, 255))
    bg.paste(qr_img, (40, 40), qr_img)

    buf = io.BytesIO()
    bg.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode(), buf.getvalue()

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

        def on_logo_picked(e):
            nonlocal logo_path
            if e.files:
                logo_path = e.files[0].path
                btn_logo.text = "Logo cargado"
                btn_logo.bgcolor = "green"
                page.update()

        def on_save(e):
            if e.path and qr_bytes:
                with open(e.path, "wb") as f:
                    f.write(qr_bytes)
                page.show_snack_bar(
                    ft.SnackBar(ft.Text("QR guardado"), open=True)
                )

        picker_logo = ft.FilePicker(on_result=on_logo_picked)
        picker_save = ft.FilePicker(on_result=on_save)
        page.overlay.extend([picker_logo, picker_save])

        txt_data = ft.TextField(label="Texto / URL", bgcolor="#222222")

        dd_style = ft.Dropdown(
            label="Estilo",
            value="Liquid Pro (Gusano)",
            options=[
                ft.dropdown.Option("Liquid Pro (Gusano)"),
                ft.dropdown.Option("Normal (Cuadrado)"),
                ft.dropdown.Option("Circular (Puntos)")
            ],
            bgcolor="#222222"
        )

        btn_logo = ft.ElevatedButton(
            "Subir logo",
            icon="image",
            on_click=lambda _: picker_logo.pick_files()
        )

        img_preview = ft.Image(
            width=280,
            height=280,
            visible=False,
            fit="contain"
        )

        btn_save = ft.ElevatedButton(
            "Guardar QR",
            icon="save",
            disabled=True,
            on_click=lambda _: picker_save.save_file(file_name="qr.png")
        )

        def generar(e):
            nonlocal qr_bytes
            if not txt_data.value:
                return

            b64, binary = generar_qr(
                txt_data.value,
                logo_path,
                dd_style.value
            )

            qr_bytes = binary
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
                    ft.Text("QR + LOGO", size=24, weight="bold"),
                    txt_data,
                    dd_style,
                    btn_logo,
                    btn_gen,
                    img_preview,
                    btn_save
                ],
                spacing=15
            )
        )

    except Exception:
        page.add(
            ft.Text(
                traceback.format_exc(),
                color="red",
                selectable=True
            )
        )

ft.app(target=main, assets_dir="assets")
