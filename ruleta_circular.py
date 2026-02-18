import tkinter as tk
import math
import random
import time
from engine import load_data, GameState
from PIL import Image, ImageTk

# --- Configuración visual ---
BG_COLOR = '#111'
WHEEL_RADIUS = 180
WHEEL_CENTER = (250, 250)
CANVAS_SIZE = 500
SPIN_TIME = 3.5  # segundos
SHOW_RESULT_TIME = 2.0  # segundos

# --- Utilidades de color ---
def color_by_index(idx, total):
    from colorsys import hsv_to_rgb
    h = (idx / max(1, total))
    rgb = hsv_to_rgb(h, 0.45, 0.95)
    r, g, b = int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255)
    return '#%02x%02x%02x' % (r, g, b)

# --- Ruleta circular ---
def draw_wheel(canvas, options, angle_offset=0, highlight_idx=None, bg_img=None):
    canvas.delete('all')
    if bg_img:
        canvas.create_image(0, 0, anchor='nw', image=bg_img)
    cx, cy = WHEEL_CENTER
    n = len(options)
    angle_per = 2*math.pi / n if n else 1
    font_size = max(16, int(WHEEL_RADIUS * 0.15))
    for i, opt in enumerate(options):
        # Rotar la ruleta: sumar angle_offset
        a0 = i * angle_per - math.pi/2 + angle_offset
        a1 = (i+1) * angle_per - math.pi/2 + angle_offset
        color = color_by_index(i, n)
        # sector
        canvas.create_arc(cx-WHEEL_RADIUS, cy-WHEEL_RADIUS, cx+WHEEL_RADIUS, cy+WHEEL_RADIUS,
                          start=math.degrees(a0), extent=math.degrees(angle_per), fill=color, outline='#232946', width=2, style='pieslice')
        # texto girando con la ruleta
        mid_angle = (a0+a1)/2
        tx = cx + math.cos(mid_angle) * (WHEEL_RADIUS*0.7)
        ty = cy + math.sin(mid_angle) * (WHEEL_RADIUS*0.7)
        # Contraste: texto oscuro o claro según fondo
        r,g,b = int(color[1:3],16),int(color[3:5],16),int(color[5:7],16)
        text_color = '#232946' if (r*0.299+g*0.587+b*0.114)>160 else '#fff'
        # Fondo semitransparente para el texto
        text_w = max(80, len(opt['name'])*font_size*0.6)
        text_h = font_size*1.2
        # Coordenadas del rectángulo centrado en (tx, ty)
        rect_x0 = tx - text_w/2
        rect_y0 = ty - text_h/2
        rect_x1 = tx + text_w/2
        rect_y1 = ty + text_h/2
        canvas.create_rectangle(rect_x0, rect_y0, rect_x1, rect_y1, fill='#000a', outline='', width=0)
        # Texto rotado con la ruleta
        canvas.create_text(tx, ty, text=opt['name'], fill=text_color, font=('Segoe UI', font_size, 'bold'), angle=math.degrees(mid_angle)+90)
    # Indicador de selección (flecha arriba)
    canvas.create_polygon(cx-18, cy-WHEEL_RADIUS-10, cx+18, cy-WHEEL_RADIUS-10, cx, cy-WHEEL_RADIUS-40, fill='#FFD700', outline='')

# --- Lógica principal ---
def main():
    data = load_data()
    state = GameState(data)
    wheels = data.get('wheels_order', ['Race', 'Class', 'Height', 'Age', 'Alignment', 'Place'])
    wheel_idx = 0
    results = {}

    root = tk.Tk()
    root.title('Ruleta Circular Minimalista')
    root.configure(bg=BG_COLOR)
    canvas = tk.Canvas(root, width=CANVAS_SIZE, height=CANVAS_SIZE, bg=BG_COLOR, highlightthickness=0)
    canvas.pack()
    spin_btn = tk.Button(root, text='SPIN', font=('Segoe UI', 16, 'bold'), bg='#FFD700', fg='#232946', width=10)
    spin_btn.pack(pady=16)
    msg_var = tk.StringVar(value='')
    msg_lbl = tk.Label(root, textvariable=msg_var, font=('Segoe UI', 16), fg='#FFD700', bg=BG_COLOR)
    msg_lbl.pack(pady=8)

    # --- Opciones dependientes ---
    def get_options_for(wheel):
        opts = []
        if wheel == 'Race':
            races = list(data.get('races', [])) + list(data.get('more_races', []))
            for r in races:
                opts.append({'name': r['name']})
        elif wheel == 'Class':
            race = results.get('Race')
            for c in data.get('classes', []):
                if race == 'Orc' and c['name'] == 'Wizard':
                    continue
                opts.append({'name': c['name']})
        elif wheel == 'Height':
            race = results.get('Race')
            races = list(data.get('races', [])) + list(data.get('more_races', []))
            race_obj = next((r for r in races if r['name'] == race), None)
            heights = race_obj.get('height_options', []) if race_obj else [{'name':'1.75 m'}]
            for h in heights:
                opts.append({'name': h['name']})
        elif wheel == 'Age':
            race = results.get('Race')
            races = list(data.get('races', [])) + list(data.get('more_races', []))
            race_obj = next((r for r in races if r['name'] == race), None)
            if race_obj and 'age_range' in race_obj:
                ar = race_obj['age_range']
                for age in range(ar.get('min', 16), ar.get('max', 60)+1, max(1, int((ar.get('max',60)-ar.get('min',16))/15))):
                    opts.append({'name': str(age)})
                if ar.get('immortal_chance', 0) > 0:
                    opts.append({'name': 'Immortal'})
            else:
                for a in data.get('age_brackets', []):
                    opts.append({'name': a['name']})
        elif wheel == 'Alignment':
            opts = [{'name': a['name']} for a in data.get('alignments',[])]
        elif wheel == 'Place':
            align = results.get('Alignment')
            race = results.get('Race')
            for p in data.get('places', []):
                if race and p.get('race_bias', {}).get(race, 1.0) < 0.5:
                    continue
                if align and p.get('alignment_bias', {}).get(align, 1.0) < 0.5:
                    continue
                opts.append({'name': p['name'], 'bg': p['name']})
        return opts

    # --- Animación de giro ---
    spinning = {'active': False}
    def spin():
        if spinning['active']:
            return
        if wheel_idx >= len(wheels):
            msg_var.set('¡Aventura generada!')
            return
        opts = get_options_for(wheels[wheel_idx])
        if not opts:
            msg_var.set('No hay opciones.')
            return
        n = len(opts)
        final_idx = random.randrange(n)
        total_rot = 8*math.pi  # vueltas totales
        final_angle = (2*math.pi*final_idx/n)
        start_angle = 0
        duration = SPIN_TIME
        steps = int(duration*60)
        # Cargar fondo si es rueda de lugares
        bg_img = None
        if wheels[wheel_idx] == 'Place' and 'bg' in opts[final_idx]:
            try:
                img = Image.open(f'backgrounds/{opts[final_idx]["bg"]}.jpg').resize((CANVAS_SIZE, CANVAS_SIZE))
                bg_img = ImageTk.PhotoImage(img)
            except Exception:
                bg_img = None
        def animate(step=0):
            if step < steps:
                t = step/steps
                # Ease out
                angle = start_angle + (total_rot-final_angle)* (1-t)**2 + final_angle
                draw_wheel(canvas, opts, angle_offset=angle, bg_img=bg_img)
                root.after(int(1000/60), lambda: animate(step+1))
            else:
                draw_wheel(canvas, opts, angle_offset=final_angle, bg_img=bg_img)
                msg_var.set(f'Resultado: {opts[final_idx]["name"]}')
                results[wheels[wheel_idx]] = opts[final_idx]['name']
                spinning['active'] = False
                root.after(int(SHOW_RESULT_TIME*1000), next_wheel)
        spinning['active'] = True
        animate()
    def next_wheel():
        nonlocal wheel_idx
        msg_var.set('')
        wheel_idx += 1
        if wheel_idx < len(wheels):
            opts = get_options_for(wheels[wheel_idx])
            # Cargar fondo si es rueda de lugares
            bg_img = None
            if wheels[wheel_idx] == 'Place' and opts and 'bg' in opts[0]:
                try:
                    img = Image.open(f'backgrounds/{opts[0]["bg"]}.jpg').resize((CANVAS_SIZE, CANVAS_SIZE))
                    bg_img = ImageTk.PhotoImage(img)
                except Exception:
                    bg_img = None
            draw_wheel(canvas, opts, bg_img=bg_img)
        else:
            msg_var.set('¡Aventura generada!')
            draw_wheel(canvas, [{'name':'FIN'}], 0)
    spin_btn.config(command=spin)
    # Inicial
    draw_wheel(canvas, get_options_for(wheels[0]))
    root.mainloop()

def get_bg_image_for_place(place_name):
    # Placeholder: busca un archivo local o genera un fondo sólido
    try:
        img = Image.open(f'backgrounds/{place_name}.jpg').resize((CANVAS_SIZE, CANVAS_SIZE))
        return ImageTk.PhotoImage(img)
    except Exception:
        return None

if __name__ == '__main__':
    main()
