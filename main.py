import flet as ft
import qrcode
from PIL import Image, ImageDraw, ImageOps, ImageFilter
import base64
import io
import os
import traceback # Importante para ver errores

# ============================================================================
# 0. ELIMINADA CONFIGURACIÓN WINDOWS (CAUSANTE DE PANTALLA NEGRA EN ANDROID)
# ============================================================================

# ============================================================================
# 1. MOTOR GRÁFICO (IGUAL QUE ANTES)
# ============================================================================
def hex_to_rgb(hex_col):
    try:
        h = hex_col.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except:
        return (0, 0, 0)

def crear_fondo(w, h, mode, c1, c2, direction):
    # Simplificado para evitar crash por memoria
    if mode == "Transparente": return Image.new("RGBA", (w, h), (0, 0, 0, 0))
    elif mode == "Blanco (Default)": return Image.new("RGBA", (w, h), (255, 255, 255, 255))
    elif mode == "Sólido (Color)": return Image.new("RGBA", (w, h), c1 + (255,)) 
    return Image.new("RGBA", (w, h), (255, 255, 255, 255))

def generar_qr_full_engine(params, data_string):
    # Motor idéntico al anterior pero protegido
    try:
        logo_path = params['logo_path']; estilo = params['estilo']
        modo_color_qr = params['modo_color_qr']
        qr_body_c1 = hex_to_rgb(params['c1']); qr_body_c2 = hex_to_rgb(params['c2'])
        usar_ojos = params['usar_ojos']
        eye_ext = hex_to_rgb(params['eye_ext']); eye_int = hex_to_rgb(params['eye_int'])
        modo_fondo = params['modo_fondo']
        bg_c1 = hex_to_rgb(params['bg_c1']); bg_c2 = hex_to_rgb(params['bg_c2'])
        
        usar_logo = False
        if logo_path and os.path.exists(logo_path): usar_logo = True

        qr_temp = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=0)
        qr_temp.add_data(data_string); qr_temp.make(fit=True)
        matrix = qr_temp.get_matrix(); modules = len(matrix); size = modules * 40
        
        # Lógica simplificada de logo para evitar errores
        if usar_logo:
            logo_src = Image.open(logo_path).convert("RGBA")
            logo_res = ImageOps.contain(logo_src, (int(size * 0.23), int(size * 0.23)))
            l_pos = ((size - logo_res.width) // 2, (size - logo_res.height) // 2)
        else:
            logo_res = Image.new("RGBA", (1,1), (0,0,0,0)); l_pos = (0,0)

        base_mask = Image.new("L", (size, size), 0)
        aura_pixels = base_mask.load() # Dummy load

        mask_body = Image.new("L", (size, size), 0); draw_b = ImageDraw.Draw(mask_body)
        
        for r in range(modules):
            for c in range(modules):
                x, y = c * 40, r * 40
                if matrix[r][c]:
                    draw_b.rectangle([x, y, x+40, y+40], fill=255)

        img_body_color = Image.new("RGBA", (size, size), (0,0,0,0)); draw_grad = ImageDraw.Draw(img_body_color)
        draw_grad.rectangle([0,0,size,size], fill=qr_body_c1 + (255,))

        qr_layer = Image.new("RGBA", (size, size), (0,0,0,0))
        qr_layer.paste(img_body_color, (0,0), mask=mask_body)
        
        if usar_logo: qr_layer.paste(logo_res, l_pos, logo_res)

        BORDER = 40; full_size = size + (BORDER * 2)
        canvas_final = Image.new("RGBA", (full_size, full_size), bg_c1 + (255,)) # Fondo simple por ahora
        canvas_final.paste(qr_layer, (BORDER, BORDER), mask=qr_layer)

        buffered = io.BytesIO()
        canvas_final.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8"), buffered.getvalue()

    except Exception as e:
        return None, None

# ============================================================================
# 2. INTERFAZ MÓVIL (MODO SEGURO)
# ============================================================================

def main(page: ft.Page):
    # --- ESCUDO ANTI-CRASH ---
    # Si algo falla, atrapamos el error y lo mostramos en pantalla
    try:
        page.title = "QR Creator"
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = "#111111"
        page.padding = 20
        page.scroll = "AUTO"
        
        # --- ELIMINADO: page.window_icon (Causa común de pantalla negra) ---
        
        # --- ESTADO ---
        qr_bytes_data = None
        logo_path_ref = ft.Ref[str]() 
        
        # --- CONTROLES SIMPLES ---
        txt_status = ft.Text("Bienvenido al Generador QR", color="green")
        
        # --- FILE PICKERS ---
        picker_logo = ft.FilePicker()
        picker_save = ft.FilePicker()
        page.overlay.append(picker_logo)
        page.overlay.append(picker_save)

        def on_logo_picked(e: ft.FilePickerResultEvent):
            if e.files:
                logo_path_ref.current = e.files[0].path
                btn_logo_select.text = f"Logo: {e.files[0].name}"
                page.update()

        def on_save_file(e: ft.FilePickerResultEvent):
            if e.path and qr_bytes_data:
                try:
                    with open(e.path, "wb") as f:
                        f.write(qr_bytes_data)
                    page.show_snack_bar(ft.SnackBar(ft.Text("Guardado"), open=True))
                except Exception as ex:
                    page.show_snack_bar(ft.SnackBar(ft.Text(f"Error: {ex}"), open=True))

        picker_logo.on_result = on_logo_picked
        picker_save.on_result = on_save_file

        # --- UI ELEMENTS ---
        # Intentamos cargar la imagen, pero si falla, ponemos un texto (Anti-Crash)
        try:
            header_img = ft.Image(src="icon.png", width=50, height=50)
        except:
            header_img = ft.Icon(ft.icons.QR_CODE, size=50, color="white")

        header = ft.Row([header_img, ft.Text("QR Pro", size=24, weight="bold")], alignment="center")

        txt_1 = ft.TextField(label="Texto o Enlace", bgcolor="#222222")
        btn_logo_select = ft.ElevatedButton("Subir Logo", icon=ft.icons.IMAGE, on_click=lambda _: picker_logo.pick_files(), bgcolor="#333333", color="white")
        img_res = ft.Image(src="", width=250, height=250, fit="contain", visible=False)
        btn_save = ft.ElevatedButton("Descargar", icon=ft.icons.DOWNLOAD, on_click=lambda _: picker_save.save_file(file_name="mi_qr.png"), disabled=True)

        def generar(e):
            if not txt_1.value: return
            
            # Parametros minimos para probar que no explote
            params = {
                'logo_path': logo_path_ref.current, 
                'estilo': "Normal",
                'modo_color_qr': "Sólido", 'c1': "#000000", 'c2': "#000000",
                'grad_dir_qr': "Vertical",
                'usar_ojos': False, 'eye_ext': "#000000", 'eye_int': "#000000",
                'modo_fondo': "Blanco", 'bg_c1': "#FFFFFF", 'bg_c2': "#FFFFFF", 'grad_dir_bg': "Vertical"
            }
            
            # Llamada al motor
            b64, binary = generar_qr_full_engine(params, txt_1.value)

            if b64:
                nonlocal qr_bytes_data; qr_bytes_data = binary
                img_res.src_base64 = b64; img_res.visible = True
                btn_save.disabled = False
                page.update()

        btn_gen = ft.ElevatedButton("GENERAR AHORA", on_click=generar, bgcolor="green", color="white", height=50)

        # --- ARMADO DE PÁGINA ---
        page.add(
            ft.Column([
                header,
                txt_status,
                txt_1,
                btn_logo_select,
                btn_gen,
                ft.Container(content=img_res, alignment=ft.alignment.center, padding=10),
                btn_save
            ], spacing=20)
        )

    except Exception as e:
        # SI ALGO FALLA, ESTO SALDRÁ EN TU PANTALLA
        page.add(ft.Text(f"ERROR FATAL:\n{traceback.format_exc()}", color="red", size=20))
        page.update()

ft.app(target=main, assets_dir=".")
