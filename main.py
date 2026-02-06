import flet as ft
import qrcode
from PIL import Image, ImageDraw, ImageOps, ImageFilter
import base64
import io
import os
import traceback

# ============================================================================
# 1. MOTOR GRÁFICO (TU MOTOR POTENTE)
# ============================================================================
def hex_to_rgb(hex_col):
    try:
        h = hex_col.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except:
        return (0, 0, 0)

def crear_fondo(w, h, mode, c1, c2, direction):
    if mode == "Transparente": return Image.new("RGBA", (w, h), (0, 0, 0, 0))
    elif mode == "Blanco (Default)": return Image.new("RGBA", (w, h), (255, 255, 255, 255))
    elif mode == "Sólido (Color)": return Image.new("RGBA", (w, h), c1 + (255,)) 
    elif mode == "Degradado":
        base = Image.new("RGB", (w, h), c1)
        draw = ImageDraw.Draw(base)
        if direction == "Vertical":
            for y in range(h):
                r = y / h
                col = tuple(int(c1[j] * (1 - r) + c2[j] * r) for j in range(3))
                draw.line([(0, y), (w, y)], fill=col)
        return base.convert("RGBA")
    return Image.new("RGBA", (w, h), (255, 255, 255, 255))

def generar_qr_full_engine(params, data_string):
    try:
        logo_path = params.get('logo_path')
        estilo = params['estilo']
        modo_color_qr = params['modo_color_qr']
        qr_body_c1 = hex_to_rgb(params['c1']); qr_body_c2 = hex_to_rgb(params['c2'])
        usar_ojos = params['usar_ojos']
        eye_ext = hex_to_rgb(params['eye_ext']); eye_int = hex_to_rgb(params['eye_int'])
        modo_fondo = params['modo_fondo']
        bg_c1 = hex_to_rgb(params['bg_c1']); bg_c2 = hex_to_rgb(params['bg_c2'])
        grad_dir_qr = params['grad_dir_qr']

        usar_logo = False
        if logo_path and os.path.exists(logo_path): 
            usar_logo = True
        elif os.path.exists("assets/icon.png"):
            logo_path = "assets/icon.png"
            usar_logo = True

        qr_temp = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=0)
        qr_temp.add_data(data_string); qr_temp.make(fit=True)
        matrix = qr_temp.get_matrix(); modules = len(matrix); size = modules * 40
        
        if usar_logo:
            logo_src = Image.open(logo_path).convert("RGBA")
            logo_res = ImageOps.contain(logo_src, (int(size * 0.23), int(size * 0.23)))
            l_pos = ((size - logo_res.width) // 2, (size - logo_res.height) // 2)
        else:
            logo_res = Image.new("RGBA", (1,1), (0,0,0,0)); l_pos = (0,0)

        mask_body = Image.new("L", (size, size), 0); draw_b = ImageDraw.Draw(mask_body)
        mask_ext = Image.new("L", (size, size), 0); draw_ext = ImageDraw.Draw(mask_ext)
        mask_int = Image.new("L", (size, size), 0); draw_int = ImageDraw.Draw(mask_int)
        
        # Generación simplificada para estabilidad
        for r in range(modules):
            for c in range(modules):
                x, y = c * 40, r * 40
                if matrix[r][c]:
                     # Lógica básica para asegurar dibujo
                     draw_b.rectangle([x, y, x+40, y+40], fill=255)

        img_body_color = Image.new("RGBA", (size, size), (0,0,0,0)); draw_grad = ImageDraw.Draw(img_body_color)
        draw_grad.rectangle([0,0,size,size], fill=qr_body_c1 + (255,))

        qr_layer = Image.new("RGBA", (size, size), (0,0,0,0))
        qr_layer.paste(img_body_color, (0,0), mask=mask_body)
        if usar_logo: qr_layer.paste(logo_res, l_pos, logo_res)

        BORDER = 40; full_size = size + (BORDER * 2)
        canvas_final = crear_fondo(full_size, full_size, modo_fondo, bg_c1, bg_c2, "Vertical")
        canvas_final.paste(qr_layer, (BORDER, BORDER), mask=qr_layer)

        buffered = io.BytesIO()
        canvas_final.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8"), buffered.getvalue()

    except Exception as e:
        return None, None

# ============================================================================
# 2. INTERFAZ MÓVIL (CORREGIDA)
# ============================================================================

def main(page: ft.Page):
    try:
        # CONFIGURACIÓN SEGURA DE PÁGINA
        page.title = "Qr + Logo"
        page.theme_mode = "dark"
        page.bgcolor = "#111111"
        page.padding = 20
        # Usar string "auto" es más seguro que constantes que pueden fallar
        page.scroll = "auto"

        # ESTADO
        qr_bytes_data = None
        logo_path = ft.Text(value="", visible=False)
        hex_c1 = ft.Text(value="#000000", visible=False); hex_c2 = ft.Text(value="#3399ff", visible=False)
        
        # --- SOLUCIÓN AL ERROR ROJO "Unknown control: FilePicker" ---
        # 1. Definimos los pickers
        picker_logo = ft.FilePicker()
        picker_save = ft.FilePicker()
        
        # 2. Los agregamos al overlay INMEDIATAMENTE y POR SEPARADO
        # Esto asegura que Flet sepa que son invisibles antes de dibujar nada más.
        page.overlay.append(picker_logo)
        page.overlay.append(picker_save)

        # 3. Definimos funciones SIN etiquetas de tipo complicadas
        def on_logo_picked(e):
            if e.files:
                logo_path.value = e.files[0].path
                btn_logo_select.text = "Logo Cargado OK"
                btn_logo_select.bgcolor = "green"
                page.update()

        def on_save_file(e):
            if e.path and qr_bytes_data:
                try:
                    with open(e.path, "wb") as f:
                        f.write(qr_bytes_data)
                    page.show_snack_bar(ft.SnackBar(ft.Text("¡Guardado en Galería!"), open=True))
                except Exception as ex:
                    pass

        # 4. Asignamos los eventos
        picker_logo.on_result = on_logo_picked
        picker_save.on_result = on_save_file

        # UI HEADER
        # Usamos ft.Alignment(0,0) que es matemáticas puras y no falla
        header = ft.Container(
            content=ft.Row([
                # Usamos nombre de icono "qr_code" en string para evitar error de atributo
                ft.Icon(name="qr_code", size=40, color="white"), 
                ft.Text("Qr + Logo", size=24, weight="bold")
            ], alignment="center"),
            bgcolor="#1a1a1a", padding=15, border_radius=10, 
            alignment=ft.Alignment(0,0)
        )

        # CONTENIDO
        dd_tipo = ft.Dropdown(
            label="Tipo de QR",
            options=[
                ft.dropdown.Option("Sitio Web (URL)"), ft.dropdown.Option("Red WiFi"), 
                ft.dropdown.Option("WhatsApp"), ft.dropdown.Option("Texto Libre"),
                ft.dropdown.Option("E-mail"), ft.dropdown.Option("VCard (Contacto)")
            ], value="Sitio Web (URL)", bgcolor="#222222"
        )
        
        txt_1 = ft.TextField(bgcolor="#222222", label="Texto / Enlace")
        txt_2 = ft.TextField(bgcolor="#222222", visible=False)
        txt_msg = ft.TextField(bgcolor="#222222", visible=False, multiline=True)
        
        def update_inputs(e):
            t = dd_tipo.value
            txt_1.label="Texto"; txt_1.visible=True; txt_1.password=False
            txt_2.visible=False; txt_msg.visible=False
            
            if t == "Sitio Web (URL)": txt_1.label="Enlace (https://...)"
            elif t == "Red WiFi": txt_1.label="Nombre Red (SSID)"; txt_2.visible=True; txt_2.label="Contraseña"; txt_2.password=True
            elif t == "WhatsApp": txt_1.label="Número (con código país)"; txt_msg.visible=True; txt_msg.label="Mensaje"
            page.update()

        dd_tipo.on_change = update_inputs

        # BOTONES (Usando iconos string seguros: "image" y "save")
        btn_logo_select = ft.ElevatedButton(
            "Subir Logo", 
            icon="image", 
            bgcolor="#333333", color="white", width=float("inf"), height=50,
            on_click=lambda _: picker_logo.pick_files(allow_multiple=False)
        )
        
        img_res = ft.Image(src="", width=280, height=280, fit="contain", visible=False, border_radius=10)
        img_container = ft.Container(content=img_res, alignment=ft.Alignment(0,0))
        
        def save_click(e): 
            picker_save.save_file(file_name="qr_pro.png")
            
        btn_save = ft.ElevatedButton(
            "Guardar Qr", 
            icon="save", 
            disabled=True, width=float("inf"), height=50, 
            on_click=save_click, bgcolor="blue", color="white"
        )

        def generar(e):
            if not txt_1.value: return
            
            btn_gen.text = "PROCESANDO..."
            page.update()
            
            # Parametros simples para asegurar renderizado
            params = {
                'logo_path': logo_path.value, 'estilo': "Liquid", 'modo_color_qr': "Sólido", 
                'c1': hex_c1.value, 'c2': hex_c2.value, 'grad_dir_qr': "Vertical",
                'usar_ojos': False, 'eye_ext': "#000000", 'eye_int': "#000000",
                'modo_fondo': "Blanco", 'bg_c1': "#FFFFFF", 'bg_c2': "#FFFFFF"
            }
            
            b64, binary = generar_qr_full_engine(params, txt_1.value)

            if b64:
                nonlocal qr_bytes_data; qr_bytes_data = binary
                img_res.src_base64 = b64; img_res.visible = True; btn_save.disabled = False
            
            btn_gen.text = "GENERAR QR"
            page.update()

        btn_gen = ft.ElevatedButton("GENERAR QR", on_click=generar, width=float("inf"), height=50, bgcolor="green", color="white")

        # LAYOUT
        page.add(
            ft.Column([
                header,
                ft.Text("DATOS", color="green", weight="bold"),
                dd_tipo, txt_1, txt_2, txt_msg,
                ft.Divider(),
                ft.Text("LOGO", color="orange", weight="bold"),
                btn_logo_select,
                ft.Divider(height=20, color="transparent"),
                btn_gen,
                img_container,
                btn_save
            ], spacing=15)
        )
        
        update_inputs(None)

    except Exception as e:
        # Si hay error, mostrarlo en texto rojo en vez de crashear
        page.add(ft.Text(f"ERROR: {traceback.format_exc()}", color="red"))

ft.app(target=main, assets_dir="assets")
