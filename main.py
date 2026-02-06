import flet as ft
import qrcode
from PIL import Image, ImageDraw, ImageOps, ImageFilter
import base64
import io
import os
import traceback

# ============================================================================
# 1. MOTOR GRÁFICO (TU CÓDIGO ORIGINAL - SIN CAMBIOS)
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
        elif direction == "Diagonal":
            steps = w + h
            for i in range(steps):
                r = i / steps
                col = tuple(int(c1[j] * (1 - r) + c2[j] * r) for j in range(3))
                x0, y0 = 0, i; x1, y1 = i, 0
                if y0 > h: x0 = y0 - h; y0 = h
                if x1 > w: y1 = x1 - w; x1 = w
                draw.line([(x0, y0), (x1, y1)], fill=col, width=2)
        return base.convert("RGBA")
    return Image.new("RGBA", (w, h), (255, 255, 255, 255))

def generar_qr_full_engine(params, data_string):
    logo_path = params.get('logo_path')
    estilo = params['estilo']
    modo_color_qr = params['modo_color_qr']
    qr_body_c1 = hex_to_rgb(params['c1']); qr_body_c2 = hex_to_rgb(params['c2'])
    usar_ojos = params['usar_ojos']
    eye_ext = hex_to_rgb(params['eye_ext']); eye_int = hex_to_rgb(params['eye_int'])
    modo_fondo = params['modo_fondo']
    bg_c1 = hex_to_rgb(params['bg_c1']); bg_c2 = hex_to_rgb(params['bg_c2'])
    grad_dir_qr = params['grad_dir_qr']
    grad_dir_bg = params['grad_dir_bg']
    
    usar_logo = False
    if logo_path and os.path.exists(logo_path): 
        usar_logo = True
    elif os.path.exists("assets/icon.png"):
        logo_path = "assets/icon.png"
        usar_logo = True

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
        PAD = 2; RAD_LIQUID = 18

        for r in range(modules):
            for c in range(modules):
                x, y = c * 40, r * 40
                
                if es_ojo_general(r, c):
                    if estilo == "Circular (Puntos)": continue
                    if matrix[r][c]:
                        if es_ojo_interno(r,c): draw_int.rectangle([x, y, x+40, y+40], fill=255)
                        else: draw_ext.rectangle([x, y, x+40, y+40], fill=255)
                    continue

                if es_ojo_interno(r, c): draw = draw_int
                elif es_ojo_externo(r, c): draw = draw_ext
                else: draw = draw_b

                if estilo == "Liquid Pro (Gusano)":
                    if get_m(r, c):
                        draw.rounded_rectangle([x+PAD, y+PAD, x+40-PAD, y+40-PAD], radius=RAD_LIQUID, fill=255)
                        if get_m(r, c+1): draw.rounded_rectangle([x+PAD, y+PAD, x+80-PAD, y+40-PAD], radius=RAD_LIQUID, fill=255)
                        if get_m(r+1, c): draw.rounded_rectangle([x+PAD, y+PAD, x+40-PAD, y+80-PAD], radius=RAD_LIQUID, fill=255)
                        if get_m(r, c+1) and get_m(r+1, c) and get_m(r+1, c+1): draw.rectangle([x+20, y+20, x+60, y+60], fill=255)
                elif estilo == "Normal (Cuadrado)":
                    if get_m(r, c): draw.rectangle([x, y, x+40, y+40], fill=255)
                elif estilo == "Barras (Vertical)":
                    if get_m(r, c):
                        if es_ojo_general(r,c): draw.rectangle([x, y, x+40, y+40], fill=255)
                        else:
                            draw.rounded_rectangle([x+4, y, x+36, y+40], radius=10, fill=255)
                            if get_m(r+1, c) and not es_ojo_general(r+1, c): draw.rectangle([x+4, y+20, x+36, y+60], fill=255)
                elif estilo == "Circular (Puntos)":
                    if get_m(r, c): draw.ellipse([x+1, y+1, x+39, y+39], fill=255)

        if estilo == "Circular (Puntos)":
            def draw_geo_eye(r_start, c_start):
                x = c_start * 40; y = r_start * 40; s = 7 * 40
                draw_ext.ellipse([x, y, x+s, y+s], fill=255)
                draw_ext.ellipse([x+40, y+40, x+s-40, y+s-40], fill=0)
                draw_int.ellipse([x+80, y+80, x+s-80, y+s-80], fill=255)
            draw_geo_eye(0, 0); draw_geo_eye(0, modules-7); draw_geo_eye(modules-7, 0)

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
                elif grad_dir_qr == "Horizontal": draw_grad.line([(i,0),(i,size)], fill=col)
                elif grad_dir_qr == "Diagonal": draw_grad.line([(i,0),(i,size)], fill=col) 

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
        return None, None

# ============================================================================
# 2. INTERFAZ MÓVIL (CORREGIDA PARA QUE NO FALLE EN ANDROID)
# ============================================================================

def main(page: ft.Page):
    try:
        page.title = "QR + Logo"
        page.theme_mode = "dark" 
        page.bgcolor = "#111111"
        page.padding = 20
        page.scroll = True # CORREGIDO: "AUTO" DA ERROR
        
        # DATOS
        COUNTRY_CODES = ["🇵🇾 +595", "🇦🇷 +54", "🇧🇷 +55", "🇺🇸 +1", "🇪🇸 +34", "🇲🇽 +52"]

        # ESTADO
        qr_bytes_data = None
        logo_path = ft.Text(value="", visible=False)
        hex_c1 = ft.Text(value="#000000", visible=False); hex_c2 = ft.Text(value="#3399ff", visible=False)
        hex_eye_ext = ft.Text(value="#000000", visible=False); hex_eye_in = ft.Text(value="#000000", visible=False)
        hex_bg1 = ft.Text(value="#FFFFFF", visible=False); hex_bg2 = ft.Text(value="#EEEEEE", visible=False)
        current_target = "c1"

        # FILE PICKERS (Agregados uno por uno, sin listas, para seguridad)
        picker_logo = ft.FilePicker(); picker_save = ft.FilePicker()
        page.overlay.append(picker_logo)
        page.overlay.append(picker_save)

        # CORRECCIÓN IMPORTANTE: Quitamos "ft.FilePickerResultEvent"
        def on_logo_picked(e):
            if e.files:
                logo_path.value = e.files[0].path
                btn_logo_select.text = f"Logo: {e.files[0].name}"
                btn_logo_select.bgcolor = "green"
                page.update()

        def on_save_file(e):
            if e.path and qr_bytes_data:
                try:
                    with open(e.path, "wb") as f:
                        f.write(qr_bytes_data)
                    page.show_snack_bar(ft.SnackBar(ft.Text("¡Guardado!"), open=True))
                except: pass

        picker_logo.on_result = on_logo_picked; picker_save.on_result = on_save_file

        # COLOR PICKER
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

        # UI HEADER (CORRECCIÓN IMPORTANTE: ft.Alignment(0,0))
        header = ft.Container(
            content=ft.Row([ft.Image(src="icon.png", width=40, height=40), ft.Text("QR + Logo", size=22, weight="bold")], alignment="center"), 
            padding=15, 
            bgcolor="#1a1a1a",
            alignment=ft.Alignment(0,0) # Aquí fallaba antes con ft.alignment.center
        )

        # 1. CONTENIDO (TU CÓDIGO COMPLETO)
        dd_tipo = ft.Dropdown(label="Tipo QR", options=[ft.dropdown.Option("Sitio Web (URL)"), ft.dropdown.Option("Red WiFi"), ft.dropdown.Option("WhatsApp"), ft.dropdown.Option("Teléfono"), ft.dropdown.Option("E-mail"), ft.dropdown.Option("VCard (Contacto)"), ft.dropdown.Option("SMS (Mensaje)"), ft.dropdown.Option("Texto Libre")], value="Sitio Web (URL)", bgcolor="#222222")
        txt_1 = ft.TextField(bgcolor="#222222"); txt_2 = ft.TextField(bgcolor="#222222", visible=False)
        txt_3 = ft.TextField(bgcolor="#222222", visible=False); txt_4 = ft.TextField(bgcolor="#222222", visible=False)
        txt_5 = ft.TextField(bgcolor="#222222", visible=False); txt_msg = ft.TextField(label="Mensaje", multiline=True, visible=False, bgcolor="#222222")
        dd_pais = ft.Dropdown(options=[ft.dropdown.Option(c) for c in COUNTRY_CODES], value="🇵🇾 +595", width=160, visible=False, bgcolor="#222222")
        row_phone_container = ft.Row([dd_pais, txt_1], alignment="start")

        def update_inputs(e):
            t = dd_tipo.value
            txt_1.visible=False; txt_1.password=False; txt_1.expand=True; txt_2.visible=False; txt_2.password=False
            txt_3.visible=False; txt_4.visible=False; txt_5.visible=False; txt_msg.visible=False; dd_pais.visible=False 
            if t == "Sitio Web (URL)": txt_1.label="Enlace"; txt_1.visible=True
            elif t == "Red WiFi": txt_1.label="SSID"; txt_1.visible=True; txt_1.expand=False; txt_2.label="Pass"; txt_2.visible=True; txt_2.password=True
            elif t == "Texto Libre": txt_msg.label="Texto"; txt_msg.visible=True
            elif t == "VCard (Contacto)": txt_1.label="Nombre"; txt_1.visible=True; txt_1.expand=False; txt_2.label="Apellido"; txt_2.visible=True; txt_3.label="Org"; txt_3.visible=True; txt_4.label="Tel"; txt_4.visible=True; txt_5.label="Email"; txt_5.visible=True
            elif t == "Teléfono": dd_pais.visible=True; txt_1.label="Num"; txt_1.visible=True
            elif t == "WhatsApp": dd_pais.visible=True; txt_1.label="Num"; txt_1.visible=True; txt_msg.label="Msj"; txt_msg.visible=True
            elif t == "SMS (Mensaje)": dd_pais.visible=True; txt_1.label="Num"; txt_1.visible=True; txt_msg.label="Txt"; txt_msg.visible=True
            elif t == "E-mail": txt_1.label="Email"; txt_1.visible=True; txt_1.expand=False; txt_2.label="Asunto"; txt_2.visible=True; txt_msg.label="Cuerpo"; txt_msg.visible=True
            page.update()
        dd_tipo.on_change = update_inputs

        # 2. CUERPO
        dd_estilo = ft.Dropdown(label="Estilo", options=[ft.dropdown.Option("Liquid Pro (Gusano)"), ft.dropdown.Option("Normal (Cuadrado)"), ft.dropdown.Option("Barras (Vertical)"), ft.dropdown.Option("Circular (Puntos)")], value="Liquid Pro (Gusano)", bgcolor="#222222")
        dd_modo = ft.Dropdown(label="Modo Color", options=[ft.dropdown.Option("Automático (Logo)"), ft.dropdown.Option("Sólido (Un Color)"), ft.dropdown.Option("Degradado Custom")], value="Automático (Logo)", bgcolor="#222222")
        dd_dir = ft.Dropdown(label="Dirección", options=[ft.dropdown.Option("Vertical"), ft.dropdown.Option("Horizontal")], value="Vertical", bgcolor="#222222")
        btn_c1 = ft.Container(width=40, height=40, bgcolor="#000000", border_radius=20, border=ft.border.all(1,"white"), on_click=lambda _: open_col("c1"))
        btn_c2 = ft.Container(width=40, height=40, bgcolor="#3399ff", border_radius=20, border=ft.border.all(1,"white"), on_click=lambda _: open_col("c2"))
        row_body_colors = ft.Row([ft.Column([ft.Text("C1"), btn_c1], horizontal_alignment="center"), ft.Column([ft.Text("C2"), btn_c2], horizontal_alignment="center")], alignment="spaceEvenly")

        def upd_body(e):
            m = dd_modo.value
            if m == "Automático (Logo)": row_body_colors.visible=False; dd_dir.visible=False
            elif m == "Sólido (Un Color)": row_body_colors.visible=True; row_body_colors.controls[1].visible=False; dd_dir.visible=False
            elif m == "Degradado Custom": row_body_colors.visible=True; row_body_colors.controls[1].visible=True; dd_dir.visible=True
            page.update()
        dd_modo.on_change = upd_body

        # 3. OJOS
        sw_ojos = ft.Switch(label="Personalizar Ojos", value=False)
        btn_e1 = ft.Container(width=40, height=40, bgcolor="#000000", border_radius=20, border=ft.border.all(1,"white"), on_click=lambda _: open_col("e1"))
        btn_e2 = ft.Container(width=40, height=40, bgcolor="#000000", border_radius=20, border=ft.border.all(1,"white"), on_click=lambda _: open_col("e2"))
        row_ojos = ft.Row([ft.Column([ft.Text("Borde"), btn_e1], horizontal_alignment="center"), ft.Column([ft.Text("Centro"), btn_e2], horizontal_alignment="center")], alignment="spaceEvenly", visible=False)
        def upd_ojos(e): row_ojos.visible = sw_ojos.value; page.update()
        sw_ojos.on_change = upd_ojos

        # 4. FONDO
        dd_bg_mode = ft.Dropdown(label="Fondo", options=[ft.dropdown.Option("Blanco (Default)"), ft.dropdown.Option("Transparente"), ft.dropdown.Option("Sólido (Color)"), ft.dropdown.Option("Degradado")], value="Blanco (Default)", bgcolor="#222222")
        dd_bg_dir = ft.Dropdown(label="Dir Fondo", options=[ft.dropdown.Option("Vertical"), ft.dropdown.Option("Horizontal")], value="Vertical", visible=False, bgcolor="#222222")
        btn_b1 = ft.Container(width=40, height=40, bgcolor="#FFFFFF", border_radius=20, border=ft.border.all(1,"white"), on_click=lambda _: open_col("b1"))
        btn_b2 = ft.Container(width=40, height=40, bgcolor="#EEEEEE", border_radius=20, border=ft.border.all(1,"white"), on_click=lambda _: open_col("b2"))
        row_bg_colors = ft.Row([ft.Column([ft.Text("F1"), btn_b1], horizontal_alignment="center"), ft.Column([ft.Text("F2"), btn_b2], horizontal_alignment="center")], alignment="spaceEvenly", visible=False)
        def upd_bg(e):
            m = dd_bg_mode.value
            if m in ["Blanco (Default)", "Transparente"]: row_bg_colors.visible=False; dd_bg_dir.visible=False
            elif m == "Sólido (Color)": row_bg_colors.visible=True; row_bg_colors.controls[1].visible=False; dd_bg_dir.visible=False
            elif m == "Degradado": row_bg_colors.visible=True; row_bg_colors.controls[1].visible=True; dd_bg_dir.visible=True
            page.update()
        dd_bg_mode.on_change = upd_bg

        # 5. LOGO (CORRECCIÓN: SIN ICONOS GRÁFICOS QUE FALLAN)
        btn_logo_select = ft.ElevatedButton("Seleccionar Logo...", bgcolor="#333333", color="white", width=float("inf"), height=45, on_click=lambda _: picker_logo.pick_files(allow_multiple=False))
        
        img_res = ft.Image(src="", width=280, height=280, fit="contain", visible=False, border_radius=10)
        # CORRECCIÓN: ft.Alignment(0,0) aquí también
        img_container = ft.Container(content=img_res, alignment=ft.Alignment(0,0))
        
        def save_click(e): picker_save.save_file(file_name="qr.png")
        btn_save = ft.ElevatedButton("Guardar Qr", disabled=True, width=float("inf"), height=45, on_click=save_click, bgcolor="blue", color="white")

        def generar(e):
            d = ""
            t = dd_tipo.value
            if t == "Sitio Web (URL)": d = txt_1.value
            elif t == "Texto Libre": d = txt_msg.value
            elif t == "Red WiFi": d = f"WIFI:T:WPA;S:{txt_1.value};P:{txt_2.value};;"
            elif t == "VCard (Contacto)": d = f"BEGIN:VCARD\nVERSION:3.0\nN:{txt_2.value};{txt_1.value}\nFN:{txt_1.value} {txt_2.value}\nORG:{txt_3.value}\nTEL:{txt_4.value}\nEMAIL:{txt_5.value}\nEND:VCARD"
            elif t == "Teléfono": c = dd_pais.value.split(' ')[1]; d = f"tel:{c}{txt_1.value}"
            elif t == "E-mail": d = f"mailto:{txt_1.value}?subject={txt_2.value}&body={txt_msg.value}"
            elif t == "SMS (Mensaje)": c = dd_pais.value.split(' ')[1]; d = f"SMSTO:{c}{txt_1.value}:{txt_msg.value}"
            elif t == "WhatsApp": c = dd_pais.value.split(' ')[1].replace("+",""); d = f"https://wa.me/{c}{txt_1.value}?text={txt_msg.value}"

            if not d and t != "VCard (Contacto)": 
                if not txt_1.value: page.open(ft.SnackBar(ft.Text("Faltan datos"))); return

            btn_gen.text = "PROCESANDO..."
            page.update()

            params = {
                'logo_path': logo_path.value, 'estilo': dd_estilo.value,
                'modo_color_qr': dd_modo.value, 'c1': hex_c1.value, 'c2': hex_c2.value,
                'grad_dir_qr': dd_dir.value,
                'usar_ojos': sw_ojos.value, 'eye_ext': hex_eye_ext.value, 'eye_int': hex_eye_in.value,
                'modo_fondo': dd_bg_mode.value, 'bg_c1': hex_bg1.value, 'bg_c2': hex_bg2.value, 'grad_dir_bg': dd_bg_dir.value
            }
            
            b64, binary = generar_qr_full_engine(params, d)
            
            if b64:
                nonlocal qr_bytes_data; qr_bytes_data = binary
                img_res.src_base64 = b64; img_res.visible = True; btn_save.disabled = False
            
            btn_gen.text = "GENERAR QR"
            page.update()

        btn_gen = ft.ElevatedButton("GENERAR QR", on_click=generar, width=float("inf"), height=50, bgcolor="green", color="white")

        # MAIN COLUMN
        main_column = ft.Column(
            scroll=True, 
            expand=True, 
            spacing=15,
            controls=[
                header,
                ft.Text("1. Contenido", weight="bold", color="green"), dd_tipo, row_phone_container, txt_2, txt_3, txt_4, txt_5, txt_msg,
                ft.Divider(),
                ft.Text("2. Cuerpo", weight="bold", color="blue"), dd_estilo, dd_modo, dd_dir, row_body_colors,
                ft.Divider(),
                ft.Text("3. Ojos", weight="bold", color="blue"), sw_ojos, row_ojos,
                ft.Divider(),
                ft.Text("4. Fondo", weight="bold", color="blue"), dd_bg_mode, dd_bg_dir, row_bg_colors,
                ft.Divider(),
                ft.Text("5. Logo", weight="bold", color="orange"), btn_logo_select,
                ft.Divider(height=20, color="transparent"), btn_gen, img_container, btn_save
            ]
        )
        
        page.add(main_column)
        update_inputs(None); upd_body(None); upd_ojos(None); upd_bg(None)

    except Exception as e:
        page.add(ft.Text(f"ERROR FATAL: {traceback.format_exc()}", color="red"))

ft.app(target=main, assets_dir="assets")
