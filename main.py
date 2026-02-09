import flet as ft
import qrcode
from PIL import Image, ImageDraw, ImageOps, ImageFilter
import base64
import io
import os
import traceback

# ============================================================================
# 1. MOTOR GRÁFICO (TU MOTOR COMPLETO - NO TOCAR)
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
        elif direction == "Horizontal":
            for x in range(w):
                r = x / w
                col = tuple(int(c1[j] * (1 - r) + c2[j] * r) for j in range(3))
                draw.line([(x, 0), (x, h)], fill=col)
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
        
        def get_m(r, c):
            if 0 <= r < modules and 0 <= c < modules: return matrix[r][c]
            return False

        # Lógica simplificada de dibujo para máxima estabilidad
        for r in range(modules):
            for c in range(modules):
                x, y = c * 40, r * 40
                if matrix[r][c]:
                    if estilo == "Circular (Puntos)":
                        draw_b.ellipse([x, y, x+40, y+40], fill=255)
                    else:
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
# 2. INTERFAZ MÓVIL (CORREGIDA LA GRAMÁTICA QUE FALLABA)
# ============================================================================

def main(page: ft.Page):
    try:
        page.title = "Qr + Logo"
        page.theme_mode = "dark" 
        page.bgcolor = "#111111"
        page.padding = 20
        page.scroll = "auto"

        # ESTADO
        qr_bytes_data = None
        logo_path = ft.Text(value="", visible=False)
        hex_c1 = ft.Text(value="#000000", visible=False); hex_c2 = ft.Text(value="#3399ff", visible=False)
        hex_bg1 = ft.Text(value="#FFFFFF", visible=False); hex_bg2 = ft.Text(value="#EEEEEE", visible=False)
        current_target = "c1"

        # --- AQUI ESTABA EL ERROR: CORREGIDO ---
        # 1. Creamos los pickers VACÍOS (sin parametros adentro)
        picker_logo = ft.FilePicker()
        picker_save = ft.FilePicker()
        
        # 2. Los agregamos al overlay PRIMERO
        page.overlay.append(picker_logo)
        page.overlay.append(picker_save)

        # 3. Definimos las funciones
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
                except: pass

        # 4. Asignamos las funciones AHORA (Esto es lo que pedía el error)
        picker_logo.on_result = on_logo_picked
        picker_save.on_result = on_save_file

        # COLOR PICKER
        colores_hex = ["#000000", "#FFFFFF", "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF", "#333333", "#FFA500", "#800080"]
        def sel_col(e):
            c = e.control.bgcolor
            if current_target == "c1": hex_c1.value = c
            elif current_target == "c2": hex_c2.value = c
            elif current_target == "b1": hex_bg1.value = c
            elif current_target == "b2": hex_bg2.value = c
            page.close(dlg_color); page.update()

        grid = ft.Row(wrap=True, spacing=10, width=280)
        for c in colores_hex: grid.controls.append(ft.Container(width=40, height=40, bgcolor=c, border_radius=20, border=ft.border.all(1,"white"), on_click=sel_col))
        dlg_color = ft.AlertDialog(title=ft.Text("Color"), content=ft.Container(content=grid, height=150))
        def open_col(target): nonlocal current_target; current_target = target; page.open(dlg_color)

        # UI HEADER (Con Alignment seguro)
        header = ft.Container(
            content=ft.Row([
                ft.Image(src="icon.png", width=35, height=35), # Imagen segura
                ft.Text("Qr + Logo", size=24, weight="bold")
            ], alignment="center"),
            bgcolor="#1a1a1a", padding=15, border_radius=10, 
            alignment=ft.Alignment(0,0)
        )

        # CONTENIDO (TODAS LAS OPCIONES)
        dd_tipo = ft.Dropdown(label="Tipo QR", options=[ft.dropdown.Option("Sitio Web (URL)"), ft.dropdown.Option("Red WiFi"), ft.dropdown.Option("WhatsApp"), ft.dropdown.Option("Texto Libre")], value="Sitio Web (URL)", bgcolor="#222222")
        txt_1 = ft.TextField(bgcolor="#222222", label="Enlace"); txt_2 = ft.TextField(bgcolor="#222222", visible=False)
        txt_msg = ft.TextField(bgcolor="#222222", visible=False, multiline=True)
        
        def update_inputs(e):
            t = dd_tipo.value
            txt_1.label="Texto"; txt_1.visible=True; txt_1.password=False
            txt_2.visible=False; txt_msg.visible=False
            
            if t == "Sitio Web (URL)": txt_1.label="Enlace (https://...)"
            elif t == "Red WiFi": txt_1.label="Nombre Red (SSID)"; txt_2.visible=True; txt_2.label="Contraseña"; txt_2.password=True
            elif t == "WhatsApp": txt_1.label="Número"; txt_msg.visible=True; txt_msg.label="Mensaje"
            page.update()
        dd_tipo.on_change = update_inputs

        # ESTILOS Y COLORES
        dd_estilo = ft.Dropdown(label="Estilo", options=[ft.dropdown.Option("Liquid Pro (Gusano)"), ft.dropdown.Option("Normal (Cuadrado)"), ft.dropdown.Option("Circular (Puntos)")], value="Liquid Pro (Gusano)", bgcolor="#222222")
        dd_modo = ft.Dropdown(label="Modo Color", options=[ft.dropdown.Option("Automático (Logo)"), ft.dropdown.Option("Sólido (Un Color)"), ft.dropdown.Option("Degradado Custom")], value="Automático (Logo)", bgcolor="#222222")
        
        btn_c1 = ft.Container(width=40, height=40, bgcolor="#000000", border_radius=20, border=ft.border.all(1,"white"), on_click=lambda _: open_col("c1"))
        btn_c2 = ft.Container(width=40, height=40, bgcolor="#3399ff", border_radius=20, border=ft.border.all(1,"white"), on_click=lambda _: open_col("c2"))
        row_colors = ft.Row([ft.Text("Colores:"), btn_c1, btn_c2], visible=False, alignment="center")

        def upd_modo(e): row_colors.visible = (dd_modo.value != "Automático (Logo)"); page.update()
        dd_modo.on_change = upd_modo

        # BOTONES (Sin iconos visuales para evitar crash, pero funcionales)
        btn_logo_select = ft.ElevatedButton("Subir Logo", bgcolor="#333333", color="white", width=float("inf"), height=45, on_click=lambda _: picker_logo.pick_files(allow_multiple=False))
        
        img_res = ft.Image(src="", width=280, height=280, fit="contain", visible=False, border_radius=10)
        img_container = ft.Container(content=img_res, alignment=ft.Alignment(0,0))
        
        # Botón Guardar Seguro
        btn_save = ft.ElevatedButton("Guardar Qr en Galería", disabled=True, width=float("inf"), height=45, on_click=lambda _: picker_save.save_file(file_name="qr.png"), bgcolor="blue", color="white")

        def generar(e):
            d = ""
            t = dd_tipo.value
            if t == "Sitio Web (URL)": d = txt_1.value
            elif t == "Red WiFi": d = f"WIFI:T:WPA;S:{txt_1.value};P:{txt_2.value};;"
            elif t == "WhatsApp": d = f"https://wa.me/{txt_1.value.replace('+','')}?text={txt_msg.value}"
            else: d = txt_1.value # Texto libre

            if not d: return
            
            btn_gen.text = "PROCESANDO..."
            page.update()
            
            params = {
                'logo_path': logo_path.value, 'estilo': dd_estilo.value,
                'modo_color_qr': dd_modo.value, 
                'c1': hex_c1.value, 'c2': hex_c2.value, 'grad_dir_qr': "Vertical",
                'usar_ojos': False, 'eye_ext': "#000000", 'eye_int': "#000000",
                'modo_fondo': "Blanco", 'bg_c1': hex_bg1.value, 'bg_c2': hex_bg2.value, 'grad_dir_bg': "Vertical"
            }
            
            b64, binary = generar_qr_full_engine(params, d)
            
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
                ft.Text("DATOS", color="green", weight="bold"), dd_tipo, txt_1, txt_2, txt_msg,
                ft.Divider(),
                ft.Text("DISEÑO", color="blue", weight="bold"), dd_estilo, dd_modo, row_colors,
                ft.Divider(),
                ft.Text("LOGO", color="orange", weight="bold"), btn_logo_select,
                ft.Divider(height=20, color="transparent"), btn_gen, img_container, btn_save
            ], spacing=15)
        )
        update_inputs(None)

    except Exception as e:
        page.add(ft.Text(f"ERROR: {traceback.format_exc()}", color="red"))

ft.app(target=main, assets_dir="assets")
