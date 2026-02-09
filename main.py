import flet as ft
import qrcode
from PIL import Image, ImageDraw, ImageOps
import base64
import io
import os
import traceback

# ======================================================
# UTILIDADES
# ======================================================
def hex_to_rgb(hex_col):
    try:
        h = hex_col.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except:
        return (0, 0, 0)

def crear_fondo(w, h, mode, c1, c2):
    if mode == "Transparente":
        return Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if mode == "Blanco (Default)":
        return Image.new("RGBA", (w, h), (255, 255, 255, 255))
    if mode == "Sólido (Color)":
        return Image.new("RGBA", (w, h), c1 + (255,))
    return Image.new("RGBA", (w, h), (255, 255, 255, 255))

# ======================================================
# MOTOR QR COMPLETO
# ======================================================
def generar_qr_full(params, data):
    try:
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

        estilo = params["estilo"]
        qr_color = hex_to_rgb(params["c1"])
        bg_color = hex_to_rgb(params["bg_c1"])

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

        qr_layer = Image.new("RGBA", (size, size), qr_color + (255,))
        qr_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        qr_img.paste(qr_layer, (0, 0), mask)

        if params["logo_path"] and os.path.exists(params["logo_path"]):
            logo = Image.open(params["logo_path"]).convert("RGBA")
            logo = ImageOps.contain(logo, (int(size * 0.25), int(size * 0.25)))
            pos = ((size - logo.width)//2, (size - logo.height)//2)
            qr_img.paste(logo, pos, logo)

        border = 40
        final_size = size + border * 2
        bg = crear_fondo(
            final_size,
            final_size,
            params["modo_fondo"],
            bg_color,
            bg_color
        )
        bg.paste(qr_img, (border, border), qr_img)

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

        # ================= FILE PICKERS =================
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
                    ft.SnackBar(ft.Text("QR guardado correctamente"), open=True)
                )

        picker_logo = ft.FilePicker(on_result=on_logo_picked)
        picker_save = ft.FilePicker(on_result=on_save)
        page.overlay.extend([picker_logo, picker_save])

        # ================= DATOS =================
        dd_tipo = ft.Dropdown(
            label="Tipo QR",
            value="Sitio Web (URL)",
            options=[
                ft.dropdown.Option("Sitio Web (URL)"),
                ft.dropdown.Option("Red WiFi"),
                ft.dropdown.Option("WhatsApp"),
                ft.dropdown.Option("Texto Libre"),
            ],
            bgcolor="#222222",
        )

        txt_1 = ft.TextField(label="Enlace", bgcolor="#222222")
        txt_2 = ft.TextField(label="Contraseña", bgcolor="#222222", visible=False)
        txt_msg = ft.TextField(label="Mensaje", bgcolor="#222222", visible=False)

        def update_inputs(e):
            t = dd_tipo.value
            txt_2.visible = False
            txt_msg.visible = False
            if t == "Red WiFi":
                txt_1.label = "SSID"
                txt_2.visible = True
            elif t == "WhatsApp":
                txt_1.label = "Número"
                txt_msg.visible = True
            else:
                txt_1.label = "Texto / URL"
            page.update()

        dd_tipo.on_change = update_inputs

        # ================= DISEÑO =================
        dd_estilo = ft.Dropdown(
            label="Estilo",
            value="Liquid Pro (Gusano)",
            options=[
                ft.dropdown.Option("Liquid Pro (Gusano)"),
                ft.dropdown.Option("Normal (Cuadrado)"),
                ft.dropdown.Option("Circular (Puntos)"),
            ],
            bgcolor="#222222",
        )

        dd_bg = ft.Dropdown(
            label="Fondo",
            value="Blanco (Default)",
            options=[
                ft.dropdown.Option("Blanco (Default)"),
                ft.dropdown.Option("Transparente"),
                ft.dropdown.Option("Sólido (Color)"),
            ],
            bgcolor="#222222",
        )

        btn_logo = ft.ElevatedButton(
            "Subir logo",
            icon="image",
            on_click=lambda _: picker_logo.pick_files()
        )

        img_preview = ft.Image(width=280, height=280, visible=False)

        btn_save = ft.ElevatedButton(
            "Guardar QR",
            icon="save",
            disabled=True,
            on_click=lambda _: picker_save.save_file(file_name="qr.png")
        )

        def generar(e):
            nonlocal qr_bytes

            if dd_tipo.value == "Red WiFi":
                data = f"WIFI:T:WPA;S:{txt_1.value};P:{txt_2.value};;"
            elif dd_tipo.value == "WhatsApp":
                data = f"https://wa.me/{txt_1.value}?text={txt_msg.value}"
            else:
                data = txt_1.value

            if not data:
                return

            params = {
                "logo_path": logo_path,
                "estilo": dd_estilo.value,
                "c1": "#000000",
                "bg_c1": "#FFFFFF",
                "modo_fondo": dd_bg.value,
            }

            b64, binary = generar_qr_full(params, data)
            if b64:
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
                    dd_tipo, txt_1, txt_2, txt_msg,
                    dd_estilo, dd_bg,
                    btn_logo,
                    btn_gen,
                    img_preview,
                    btn_save,
                ],
                spacing=15,
            )
        )

        update_inputs(None)

    except Exception:
        page.add(ft.Text(traceback.format_exc(), color="red", selectable=True))

ft.app(target=main, assets_dir="assets")
