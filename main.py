import flet as ft
import qrcode
from PIL import Image, ImageDraw, ImageOps, ImageFilter
import base64
import io
import os
import ctypes

# ============================================================================
# 0. CONFIGURACIÓN
# ============================================================================
try:
    myappid = 'comagro.qrlogo.app.v1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass

# ============================================================================
# 1. MOTOR GRÁFICO (NO TOCAR)
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
    logo_path = params['logo_path']; estilo = params['estilo']
    modo_color_qr = params['modo_color_qr']
    qr_body_c1 = hex_to_rgb(params['c1']); qr_body_c2 = hex_to_rgb(params['c2'])
    usar_ojos = params['usar_ojos']
    eye_ext = hex_to_rgb(params['eye_ext']); eye_int = hex_to_rgb(params['eye_int'])
    modo_fondo = params['modo_fondo']
    bg_c1 = hex_to_rgb(params['bg_c1']); bg_c2 = hex_to_rgb(params['bg_c2'])
    grad_dir_bg = params['grad_dir_bg']; grad_dir_qr = params['grad_dir_qr']
    
    usar_logo = False
    if logo_path and os.path.exists(logo_path): usar_logo = True

    try:
        qr_temp = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=0)
        qr_temp.add_data(data_string); qr_temp.make(fit=True)
        matrix = qr_temp.get_matrix(); modules = len(matrix); size = modules * 40
        
        if usar_logo:
            logo_src = Image.open(logo_path).convert("RGBA")
            bbox = logo_src.getbbox()
            if bbox: logo_src = logo_src.crop(bbox)
            logo_res = ImageOps.contain(logo_src, (int(size * 0.23), int(size * 0.23)))
            l_pos = ((size - logo_res.width) // 2, (size - logo_res.height) // 2)
        else:
            logo_res = Image.new("RGBA", (1,1), (0,0,0,0)); l_pos = (0,0)

        base_mask = Image.new("L", (size, size), 0)
        if usar_logo:
            base_mask.paste(logo_res.split()[3], l_pos)
            ImageDraw.floodfill(base_mask, (0, 0), 128) 
            solid_mask = base_mask.point(lambda p: 0 if p == 128 else 255)
            aura_mask = solid_mask.filter(ImageFilter.MaxFilter((40 * 2) + 1)); aura_pixels = aura_mask.load()
        else: aura_pixels = base_mask.load()

        def get_m(r, c):
            if 0 <= r < modules and 0 <= c < modules:
                if usar_logo and aura_pixels[c * 40 + 20, r * 40 + 20] > 20: return False
                return matrix[r][c]
            return False

        def es_ojo_general(r, c): return (r<7 and c<7) or (r<7 and c>=modules-7) or (r>=modules-7 and c<7)
        def es_ojo_interno(r, c):
            if not es_ojo_general(r, c): return False
            if r<7 and c<7: lr,lc=r,c
            elif r<7 and c>=modules-7: lr,lc=r,c-(modules-7)
            else: lr,lc=r-(modules-7),c
            if 2<=lr<=4 and 2<=lc<=4: return True
            return False

        mask_body = Image.new("L", (size, size), 0); draw_b = ImageDraw.Draw(mask_body)
        mask_ext = Image.new("L", (size, size), 0); draw_ext = ImageDraw.Draw(mask_ext)
        mask_int = Image.new("L", (size, size), 0); draw_int = ImageDraw.Draw(mask_int)
        
        for r in range(modules):
            for c in range(modules):
                x, y = c * 40, r * 40
                if es_ojo_general(r, c):
                    if matrix[r][c]:
                        if es_ojo_interno(r,c): draw_int.rectangle([x, y, x+40, y+40], fill=255)
                        else: draw_ext.rectangle([x, y, x+40, y+40], fill=255)
                    continue

                draw = draw_b
                if get_m(r, c):
                    if estilo == "Liquid Pro (Gusano)":
                        draw.rounded_rectangle([x+2, y+2, x+38, y+38], radius=18, fill=255)
                        if get_m(r, c+1): draw.rectangle([x+20, y+2, x+60, y+38], fill=255)
                        if get_m(r+1, c): draw.rectangle([x+2, y+20, x+38, y+60], fill=255)
                    elif estilo == "Circular (Puntos)":
                        draw.ellipse([x+1, y+1, x+39, y+39], fill=255)
                    else:
                        draw.rectangle([x, y, x+40, y+40], fill=255)

        img_body_color = Image.new("RGBA", (size, size), (0,0,0,0)); draw_grad = ImageDraw.Draw(img_body_color)
        color_final_1 = qr_body_c1; color_final_2 = qr_body_c2
        
        if modo_color_qr == "Automático (Logo)" and usar_logo:
            try: c_s = logo_res.resize((1,1)).getpixel((0,0))[:3]; color_final_1 = (0,0,0); color_final_2 = c_s
            except: pass

        if modo_color_qr == "Sólido (Un Color)": draw_grad.rectangle([0,0,size,size], fill=color_final_1 + (255,))
        else: 
            for i in range(size):
                r = i/size; col = tuple(int(color_final_1[j]*(1-r) + color_final_2[j]*r) for j in range(3)) + (255,)
                if grad_dir_qr == "Vertical": draw_grad.line([(0,i),(size,i)], fill=col)
                else: draw_grad.line([(i,0),(i,size)], fill=col)

        if usar_ojos: img_ext_color = Image.new("RGBA", (size, size), eye_ext + (255,)); img_int_color = Image.new("RGBA", (size, size), eye_int + (255,))
        else: img_ext_color = img_body_color; img_int_color = img_body_color

        qr_layer = Image.new("RGBA", (size, size), (0,0,0,0))
        qr_layer.paste(img_body_color, (0,0), mask=mask_body)
        qr_layer.paste(img_ext_color, (0,0), mask=mask_ext)
        qr_layer.paste(img_int_color, (0,0), mask=mask_int)

        if usar_logo: qr_layer.paste(logo_res, l_pos, logo_res)

        BORDER = 40; full_size = size + (BORDER * 2)
        canvas_final = crear_fondo(full_size, full_size, modo_fondo, bg_c1, bg_c2, grad_dir_bg)
        canvas_final.paste(qr_layer, (BORDER, BORDER), mask=qr_layer)

        buffered = io.BytesIO()
        canvas_final.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8"), buffered.getvalue()

    except Exception as e:
        print(f"Error: {e}")
        return None, None

# ============================================================================
# 2. INTERFAZ MÓVIL CORREGIDA
# ============================================================================

def main(page: ft.Page):
    # TITULO Y CONFIGURACIÓN
    page.title = "Generador QR Pro"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#111111"
    page.padding = 20
    page.scroll = "AUTO"  # Habilitar scroll en la página entera para seguridad
    
    # IMPORTANTE: Ahora usamos "icon.png" porque lo renombraste
    page.window_icon = "icon.png"

    # --- ESTADO ---
    qr_bytes_data = None
    logo_path_ref = ft.Ref[str]() # Usamos Ref para evitar errores de control
    
    # --- VARIABLES DE COLOR ---
    hex_c1 = ft.Text(value="#000000", visible=False); hex_c2 = ft.Text(value="#3399ff", visible=False)
    hex_eye_ext = ft.Text(value="#000000", visible=False); hex_eye_in = ft.Text(value="#000000", visible=False)
    hex_bg1 = ft.Text(value="#FFFFFF", visible=False); hex_bg2 = ft.Text(value="#EEEEEE", visible=False)
    current_target = "c1"

    # --- LOADING ---
    pr_ring = ft.ProgressRing(width=30, height=30, color="green")
    dlg_loading = ft.AlertDialog(modal=True, title=ft.Text("Procesando..."), content=ft.Container(content=pr_ring, alignment=ft.alignment.center, height=100))

    # --- FILE PICKERS (SOLUCIÓN ERROR ROJO) ---
    # Los definimos aquí y los agregamos al overlay INMEDIATAMENTE
    picker_logo = ft.FilePicker()
    picker_save = ft.FilePicker()
    page.overlay.append(picker_logo)
    page.overlay.append(picker_save)

    # --- EVENTOS ---
    def on_logo_picked(e: ft.FilePickerResultEvent):
        if e.files:
            logo_path_ref.current = e.files[0].path
            btn_logo_select.text = f"Logo cargado: {e.files[0].name}"
            btn_logo_select.bgcolor = "green"
            page.update()

    def on_save_file(e: ft.FilePickerResultEvent):
        if e.path and qr_bytes_data:
            try:
                with open(e.path, "wb") as f:
                    f.write(qr_bytes_data)
                page.show_snack_bar(ft.SnackBar(ft.Text("¡Imagen Guardada!"), open=True))
            except Exception as ex:
                print(ex)

    picker_logo.on_result = on_logo_picked
    picker_save.on_result = on_save_file

    # --- COLOR PICKER ---
    colores_hex = ["#000000", "#FFFFFF", "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF", "#333333", "#FFA500", "#800080"]
    def sel_col(e):
        c = e.control.bgcolor
        if current_target == "c1": btn_c1.bgcolor = c; hex_c1.value = c
        elif current_target == "c2": btn_c2.bgcolor = c; hex_c2.value = c
        elif current_target == "e1": btn_e1.bgcolor = c; hex_eye_ext.value = c
        elif current_target == "e2": btn_e2.bgcolor = c; hex_eye_in.value = c
        elif current_target == "b1": btn_b1.bgcolor = c; hex_bg1.value = c
        elif current_target == "b2": btn_b2.bgcolor = c; hex_bg2.value = c
        page.close(dlg_color); page.update()

    grid = ft.Row(wrap=True, spacing=10, width=280)
    for c in colores_hex: grid.controls.append(ft.Container(width=40, height=40, bgcolor=c, border_radius=20, border=ft.border.all(1,"white"), on_click=sel_col))
    dlg_color = ft.AlertDialog(title=ft.Text("Color"), content=ft.Container(content=grid, height=150))
    def open_col(target): nonlocal current_target; current_target = target; page.open(dlg_color)

    # --- CONTROLES UI ---
    # Header con el nuevo icono
    header = ft.Container(content=ft.Row([ft.Image(src="icon.png", width=40, height=40), ft.Text("QR Creator", size=22, weight="bold")], alignment="center"), padding=15, bgcolor="#1a1a1a", border_radius=10)

    # Inputs
    dd_tipo = ft.Dropdown(label="Tipo QR", options=[ft.dropdown.Option("Sitio Web (URL)"), ft.dropdown.Option("Texto Libre"), ft.dropdown.Option("WhatsApp"), ft.dropdown.Option("WiFi")], value="Sitio Web (URL)", bgcolor="#222222")
    txt_1 = ft.TextField(bgcolor="#222222", label="Enlace / Texto"); txt_msg = ft.TextField(bgcolor="#222222", label="Mensaje", visible=False, multiline=True)
    
    def update_inputs(e):
        val = dd_tipo.value
        txt_msg.visible = (val == "WhatsApp")
        if val == "Sitio Web (URL)": txt_1.label = "URL (https://...)"
        elif val == "WhatsApp": txt_1.label = "Número (con código país)"
        elif val == "WiFi": txt_1.label = "Nombre de la Red (SSID)"
        elif val == "Texto Libre": txt_1.label = "Escribe tu texto"
        page.update()
    dd_tipo.on_change = update_inputs

    # Estilos
    dd_estilo = ft.Dropdown(label="Estilo", options=[ft.dropdown.Option("Liquid Pro (Gusano)"), ft.dropdown.Option("Normal (Cuadrado)"), ft.dropdown.Option("Circular (Puntos)")], value="Liquid Pro (Gusano)", bgcolor="#222222")
    dd_modo = ft.Dropdown(label="Color", options=[ft.dropdown.Option("Automático (Logo)"), ft.dropdown.Option("Sólido (Un Color)"), ft.dropdown.Option("Degradado Custom")], value="Automático (Logo)", bgcolor="#222222")
    
    # Botones Color
    btn_c1 = ft.Container(width=40, height=40, bgcolor="#000000", border_radius=20, border=ft.border.all(1,"white"), on_click=lambda _: open_col("c1"))
    btn_c2 = ft.Container(width=40, height=40, bgcolor="#3399ff", border_radius=20, border=ft.border.all(1,"white"), on_click=lambda _: open_col("c2"))
    row_colors = ft.Row([btn_c1, btn_c2], visible=False, alignment="center")

    def upd_modo(e): row_colors.visible = (dd_modo.value != "Automático (Logo)"); page.update()
    dd_modo.on_change = upd_modo

    # Ojos y Fondo
    sw_ojos = ft.Switch(label="Personalizar Ojos", value=False)
    btn_e1 = ft.Container(width=40, height=40, bgcolor="#000000", border_radius=20, border=ft.border.all(1,"white"), on_click=lambda _: open_col("e1"))
    btn_e2 = ft.Container(width=40, height=40, bgcolor="#000000", border_radius=20, border=ft.border.all(1,"white"), on_click=lambda _: open_col("e2"))
    row_ojos = ft.Row([btn_e1, btn_e2], visible=False, alignment="center")
    def upd_ojos(e): row_ojos.visible = sw_ojos.value; page.update()
    sw_ojos.on_change = upd_ojos

    dd_bg = ft.Dropdown(label="Fondo", options=[ft.dropdown.Option("Blanco (Default)"), ft.dropdown.Option("Transparente"), ft.dropdown.Option("Sólido (Color)")], value="Blanco (Default)", bgcolor="#222222")
    btn_b1 = ft.Container(width=40, height=40, bgcolor="#FFFFFF", border_radius=20, border=ft.border.all(1,"white"), on_click=lambda _: open_col("b1"))
    btn_b2 = ft.Container(width=40, height=40, bgcolor="#EEEEEE", border_radius=20, border=ft.border.all(1,"white"), on_click=lambda _: open_col("b2"))
    row_bg = ft.Row([btn_b1, btn_b2], visible=False, alignment="center")
    def upd_bg(e): row_bg.visible = (dd_bg.value != "Blanco (Default)" and dd_bg.value != "Transparente"); page.update()
    dd_bg.on_change = upd_bg

    # Botones Acción
    btn_logo_select = ft.ElevatedButton("Subir Logo (Opcional)", icon=ft.icons.IMAGE, on_click=lambda _: picker_logo.pick_files(), bgcolor="#333333", color="white")
    img_res = ft.Image(src="", width=250, height=250, fit="contain", visible=False, border_radius=10)
    btn_save = ft.ElevatedButton("Descargar PNG", icon=ft.icons.DOWNLOAD, on_click=lambda _: picker_save.save_file(file_name="mi_qr.png"), disabled=True, bgcolor="blue", color="white")

    def generar(e):
        if not txt_1.value:
            page.show_snack_bar(ft.SnackBar(ft.Text("¡Escribe algo primero!"), open=True))
            return

        page.open(dlg_loading); page.update()
        
        # Preparar datos
        data = txt_1.value
        if dd_tipo.value == "WhatsApp": data = f"https://wa.me/{txt_1.value.replace('+','')}?text={txt_msg.value}"
        elif dd_tipo.value == "WiFi": data = f"WIFI:S:{txt_1.value};;"
        
        params = {
            'logo_path': logo_path_ref.current, 'estilo': dd_estilo.value,
            'modo_color_qr': dd_modo.value, 'c1': hex_c1.value, 'c2': hex_c2.value,
            'grad_dir_qr': "Vertical",
            'usar_ojos': sw_ojos.value, 'eye_ext': hex_eye_ext.value, 'eye_int': hex_eye_in.value,
            'modo_fondo': dd_bg.value, 'bg_c1': hex_bg1.value, 'bg_c2': hex_bg2.value, 'grad_dir_bg': "Vertical"
        }

        b64, binary = generar_qr_full_engine(params, data)
        page.close(dlg_loading)

        if b64:
            nonlocal qr_bytes_data; qr_bytes_data = binary
            img_res.src_base64 = b64; img_res.visible = True
            btn_save.disabled = False
            page.update()

    btn_gen = ft.ElevatedButton("CREAR QR AHORA", on_click=generar, height=50, bgcolor="green", color="white")

    # --- ARMADO DE PÁGINA ---
    # Usamos un ListView para evitar problemas de desbordamiento en pantallas pequeñas
    page.add(
        ft.ListView(
            expand=True,
            spacing=20,
            controls=[
                header,
                ft.Text("DATOS", color="green", weight="bold"), dd_tipo, txt_1, txt_msg,
                ft.Divider(),
                ft.Text("DISEÑO", color="blue", weight="bold"), dd_estilo, dd_modo, row_colors,
                sw_ojos, row_ojos,
                dd_bg, row_bg,
                ft.Divider(),
                btn_logo_select,
                ft.Divider(),
                btn_gen,
                ft.Container(content=img_res, alignment=ft.alignment.center, padding=10),
                btn_save
            ]
        )
    )

ft.app(target=main, assets_dir=".")
