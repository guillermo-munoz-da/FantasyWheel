import tkinter as tk
from tkinter import messagebox, scrolledtext
from PIL import Image, ImageTk
from engine import load_data, GameState
import os
import random
import math

# Adventure phase constants
ADVENTURE_STEPS = ['Adventure Activity', 'Adventure Event', 'Adventure Action', 'Adventure Outcome']

# Decision definitions for adventure events
ADVENTURE_DECISIONS = {
    "Cult Whisper": {
        "prompt": "Un culto clandestino te ofrece secretos oscuros. \u00bfQu\u00e9 decides?",
        "options": [
            {"label": "Unirse al Culto", "tag_mods": {"dark": 1.5, "evil": 1.3, "shadow": 1.3}, "rep": {"Shadow Council": 3, "Church of Light": -2}},
            {"label": "Rechazar y Denunciar", "tag_mods": {"good": 1.5, "divine": 1.2}, "rep": {"Church of Light": 2, "Shadow Council": -3}},
            {"label": "Infiltrarse como Esp\u00eda", "tag_mods": {"stealth": 1.4, "investigation": 1.3}, "rep": {"Shadow Council": 1}}
        ]
    },
    "Noble Summons": {
        "prompt": "La nobleza exige tu presencia para una misi\u00f3n. \u00bfC\u00f3mo respondes?",
        "options": [
            {"label": "Aceptar la Misi\u00f3n", "tag_mods": {"honor": 1.3, "leadership": 1.2}, "rep": {"The Crown": 2}},
            {"label": "Negociar T\u00e9rminos", "tag_mods": {"trade": 1.4, "social": 1.3}, "rep": {"The Crown": 1, "Merchant Guild": 1}},
            {"label": "Rechazar", "tag_mods": {"neutral": 1.2}, "rep": {"The Crown": -2}}
        ]
    },
    "Assassination Attempt": {
        "prompt": "\u00a1Han intentado asesinarte! \u00bfC\u00f3mo reaccionas?",
        "options": [
            {"label": "Contraatacar", "tag_mods": {"combat": 1.5, "honor": 1.2}, "rep": {"Hunters Lodge": 1}},
            {"label": "Huir y Esconderse", "tag_mods": {"stealth": 1.4}, "rep": {"Thieves Guild": 1}},
            {"label": "Investigar al Autor", "tag_mods": {"investigation": 1.5, "politics": 1.2}, "rep": {"The Crown": 1}}
        ]
    },
    "Merchant Guild Offer": {
        "prompt": "El Gremio de Mercaderes te propone un trato arriesgado. \u00bfQu\u00e9 haces?",
        "options": [
            {"label": "Aceptar el Trato", "tag_mods": {"trade": 1.5, "merchant": 1.3}, "rep": {"Merchant Guild": 2}},
            {"label": "Pedir M\u00e1s Informaci\u00f3n", "tag_mods": {"investigation": 1.3}, "rep": {"Merchant Guild": 1}},
            {"label": "Rechazar", "tag_mods": {"neutral": 1.1}, "rep": {"Merchant Guild": -1}}
        ]
    },
    "Demonic Rift": {
        "prompt": "Un portal infernal se ha abierto. \u00bfQu\u00e9 decides hacer?",
        "options": [
            {"label": "Cerrar el Portal", "tag_mods": {"magic": 1.4, "good": 1.3, "divine": 1.3}, "rep": {"Church of Light": 3, "Mages Circle": 1}},
            {"label": "Aprovechar su Poder", "tag_mods": {"dark": 1.5, "evil": 1.4}, "rep": {"Shadow Council": 2, "Church of Light": -3}},
            {"label": "Huir de la Zona", "tag_mods": {"neutral": 1.2}, "rep": {}}
        ]
    },
    "Shadow Market": {
        "prompt": "Has descubierto un mercado ilegal. \u00bfQu\u00e9 haces?",
        "options": [
            {"label": "Comerciar", "tag_mods": {"trade": 1.4, "crime": 1.3}, "rep": {"Thieves Guild": 2, "Merchant Guild": -1}},
            {"label": "Denunciar", "tag_mods": {"good": 1.3, "honor": 1.2}, "rep": {"The Crown": 2, "Thieves Guild": -3}},
            {"label": "Buscar Informaci\u00f3n", "tag_mods": {"investigation": 1.3, "stealth": 1.2}, "rep": {"Thieves Guild": 1}}
        ]
    },
    "Trial by Combat": {
        "prompt": "La justicia exige un duelo a muerte. \u00bfC\u00f3mo procedes?",
        "options": [
            {"label": "Aceptar el Duelo", "tag_mods": {"combat": 1.5, "honor": 1.4}, "rep": {"The Crown": 1, "Hunters Lodge": 1}},
            {"label": "Buscar un Campe\u00f3n", "tag_mods": {"social": 1.3, "trade": 1.2}, "rep": {"Merchant Guild": 1}},
            {"label": "Huir antes del Duelo", "tag_mods": {"stealth": 1.4, "crime": 1.2}, "rep": {"The Crown": -2, "Thieves Guild": 1}}
        ]
    },
    "Forbidden Library": {
        "prompt": "Una biblioteca sellada se abre por una noche. \u00bfQu\u00e9 haces?",
        "options": [
            {"label": "Estudiar los Textos", "tag_mods": {"magic": 1.5, "arcane": 1.4, "research": 1.3}, "rep": {"Mages Circle": 2}},
            {"label": "Robar Textos Valiosos", "tag_mods": {"crime": 1.4, "trade": 1.2}, "rep": {"Thieves Guild": 2, "Mages Circle": -2}},
            {"label": "Alertar a las Autoridades", "tag_mods": {"good": 1.2}, "rep": {"The Crown": 1, "Mages Circle": -1}}
        ]
    },
    "Dragon Sighting": {
        "prompt": "Un drag\u00f3n amenaza la regi\u00f3n. \u00bfQu\u00e9 haces?",
        "options": [
            {"label": "Cazar al Drag\u00f3n", "tag_mods": {"combat": 1.6, "hunt": 1.5}, "rep": {"Hunters Lodge": 3}},
            {"label": "Negociar con \u00e9l", "tag_mods": {"social": 1.4, "magic": 1.2}, "rep": {"Mages Circle": 1}},
            {"label": "Evacuar la Zona", "tag_mods": {"leadership": 1.3, "good": 1.2}, "rep": {"The Crown": 1}}
        ]
    },
    "Plague Signs": {
        "prompt": "Se detectan s\u00edntomas de peste. \u00bfC\u00f3mo act\u00faas?",
        "options": [
            {"label": "Curar a los Enfermos", "tag_mods": {"healing": 1.5, "good": 1.3}, "rep": {"Church of Light": 2}},
            {"label": "Buscar la Causa", "tag_mods": {"investigation": 1.4, "research": 1.3}, "rep": {"Mages Circle": 1}},
            {"label": "Huir de la Plaga", "tag_mods": {"neutral": 1.2}, "rep": {"Church of Light": -1}}
        ]
    }
}


def main():
    data = load_data()
    state = GameState(data)

    # Create main window
    root = tk.Tk()
    root.title('Ruleta de Personaje - Dark Fantasy')
    root.geometry('1600x900')
    root.configure(bg='#000000')

    # Main container
    main_container = tk.Canvas(root, bg='#000000', highlightthickness=0)
    main_container.pack(fill='both', expand=True)

    background_image = {'photo': None}

    def load_background_image(place_name):
        """Load background image for a place"""
        backgrounds_dir = '/workspace/backgrounds'
        
        # Get image filename from mapping, or use place name directly
        image_map = data.get('territory_image_map', {})
        place_file = None
        
        if place_name in image_map:
            place_file = os.path.join(backgrounds_dir, image_map[place_name])
        else:
            # Fallback: search for matching file
            for filename in os.listdir(backgrounds_dir):
                if filename.lower().replace(' ', '').startswith(place_name.lower().replace(' ', '')) and filename.endswith('.jpg'):
                    place_file = os.path.join(backgrounds_dir, filename)
                    break
        
        if place_file and os.path.exists(place_file):
            try:
                img = Image.open(place_file)
                img = img.resize((1600, 900), Image.Resampling.LANCZOS)
                overlay = Image.new('RGBA', img.size, (0, 0, 0, 100))
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                img = Image.alpha_composite(img, overlay)
                img = img.convert('RGB')
                photo = ImageTk.PhotoImage(img)
                main_container.create_image(0, 0, image=photo, anchor='nw', tags='bg_image')
                background_image['photo'] = photo
                main_container.tag_lower('bg_image')
            except Exception as e:
                print(f"Error loading background: {e}")

    # Wheel canvas
    wheel_canvas = tk.Canvas(main_container, width=650, height=650, bg='#000000', 
                             highlightthickness=0)
    main_container.create_window(350, 420, window=wheel_canvas, tags='ui_element')

    # Pointer canvas (arrow at top)
    pointer_canvas = tk.Canvas(main_container, width=650, height=120, bg='#000000',
                              highlightthickness=0)
    main_container.create_window(350, 50, window=pointer_canvas, tags='ui_element')
    
    # Draw golden pointer
    pointer_canvas.create_polygon(325, 100, 350, 120, 375, 100, fill='#eebc1d', outline='#eebc1d', width=2)

    # Title
    title = tk.Label(main_container, text='Ruleta de Personaje - Dark Fantasy', 
                     font=('Segoe UI', 26, 'bold'), fg='#eebc1d', bg='#000000')
    main_container.create_window(900, 50, window=title, tags='ui_element')

    # Info panel
    info_frame = tk.Frame(main_container, bg='#1a1a2e', relief='groove', bd=2)
    main_container.create_window(1350, 200, window=info_frame, tags='ui_element')
    
    tk.Label(info_frame, text='Personaje', font=('Segoe UI', 12, 'bold'), 
             fg='#eebc1d', bg='#1a1a2e').pack(fill='x', padx=5, pady=5)
    
    char_text = scrolledtext.ScrolledText(info_frame, width=28, height=28, 
                                         state='disabled', font=('Consolas', 8), 
                                         bg='#0f3460', fg='#eebc1d', bd=0)
    char_text.pack(fill='both', expand=True, padx=3, pady=3)

    def update_char_display():
        """Update character display"""
        char_text.config(state='normal')
        char_text.delete('1.0', tk.END)
        for key, val in state.selections.items():
            if not key.startswith('_'):
                if isinstance(val, list):
                    char_text.insert(tk.END, f"{key}: {', '.join(val)}\n")
                else:
                    char_text.insert(tk.END, f"{key}: {val}\n")

        # Show reputation during adventure
        if adventure_phase['active'] and any(v != 0 for v in reputation.values()):
            char_text.insert(tk.END, '\n--- REPUTACION ---\n')
            for faction, score in reputation.items():
                if score != 0:
                    bar = '|' * abs(score)
                    symbol = '+' if score > 0 else '-'
                    char_text.insert(tk.END, f"{faction}: {symbol}{abs(score)} {bar}\n")

        # Show adventure log
        if adventure_log:
            char_text.insert(tk.END, '\n--- AVENTURA ---\n')
            for entry in adventure_log[-5:]:  # Show last 5 entries
                char_text.insert(tk.END, f"{entry}\n")

        char_text.config(state='disabled')

    # Current wheel label
    current_lbl = tk.Label(main_container, text='Rueda: Race', 
                           font=('Segoe UI', 14, 'bold'), fg='#eebc1d', bg='#000000')
    main_container.create_window(900, 750, window=current_lbl, tags='ui_element')

    # Spin button
    spin_btn = tk.Button(main_container, text='GIRAR', width=18, font=('Segoe UI', 14, 'bold'), 
                        bg='#eebc1d', fg='#000000', activebackground='#f9d923', 
                        activeforeground='#000000', relief='raised', bd=3)
    main_container.create_window(900, 820, window=spin_btn, tags='ui_element')

    # End Run button (hidden during character creation)
    end_run_btn = tk.Button(main_container, text='FIN DE RUN', width=14, font=('Segoe UI', 11, 'bold'),
                           bg='#ff4444', fg='#ffffff', activebackground='#ff6666',
                           activeforeground='#ffffff', relief='raised', bd=3,
                           state='disabled')
    end_run_window = main_container.create_window(900, 870, window=end_run_btn, tags=('ui_element', 'end_run_tag'))
    main_container.itemconfigure('end_run_tag', state='hidden')

    # Custom wheel configuration - dynamic based on selections
    wheel_config_base = ['Race', 'Gender', 'Age', 'Archetype', 'Class', 'Alignment',
                        'Strength', 'Agility', 'Durability', 'Intelligence', 'Charisma',
                        'Weapon', 'Power Count', 'Magic Count', 'Skill Count', 'Territory', 'Items Count']
    
    def get_current_wheel_config():
        """Get current wheel configuration based on character selections"""
        config = []
        
        for wheel in wheel_config_base:
            config.append(wheel)
            
            # After Weapon, add Weapon Mastery if weapon is not "None"
            if wheel == 'Weapon':
                weapon = state.selections.get('Weapon', 'None')
                if weapon != 'None':
                    config.append('Weapon Mastery')
            
            # After Power Count, add N Power selection wheels + individual mastery for each
            elif wheel == 'Power Count':
                power_count_str = state.selections.get('Power Count', '0 (None)')
                try:
                    power_count = int(power_count_str.split()[0])
                    for i in range(1, power_count + 1):
                        config.append(f'Power {i}')
                        config.append(f'Power Mastery {i}')  # Individual mastery for each power
                except:
                    pass
            
            # After Magic Count, add N Magic Type + Spells + individual Magic Skill for each
            elif wheel == 'Magic Count':
                magic_count_str = state.selections.get('Magic Count', '0 (None)')
                try:
                    magic_count = int(magic_count_str.split()[0])
                    for i in range(1, magic_count + 1):
                        if i == 1:
                            config.append('Magic Type 1')
                        else:
                            config.append(f'Magic Type {i}')
                        # Also add Spell selection after each magic type
                        config.append(f'Spells {i}')
                        # Individual magic skill for each magic type
                        config.append(f'Magic Skill {i}')
                except:
                    pass
            
            # After Skill Count, add N Skill selection wheels + individual mastery for each
            elif wheel == 'Skill Count':
                skill_count_str = state.selections.get('Skill Count', '0 (None)')
                try:
                    skill_count = int(skill_count_str.split()[0])
                    for i in range(1, skill_count + 1):
                        config.append(f'Skill {i}')
                        config.append(f'Skill Mastery {i}')  # Individual mastery for each skill
                    
                    # Only add general Skill Efficiency if there are skills
                    if skill_count > 0:
                        config.append('Skill Efficiency')
                except:
                    pass
            
            # After Items Count, add N Item selection wheels
            elif wheel == 'Items Count':
                items_count_str = state.selections.get('Items Count', '0 (None)')
                try:
                    items_count = int(items_count_str.split()[0])
                    for i in range(1, items_count + 1):
                        config.append(f'Item {i}')
                except:
                    pass
        
        return config
    
    wheel_index = {'i': 0}
    spinning = {'active': False, 'rotation': 0.0}

    # Adventure phase state
    adventure_phase = {'active': False, 'chapter': 1, 'step': 0}
    reputation = {}  # faction_name: score
    adventure_log = []  # chapter summaries
    decision_mods = {}  # temporary tag mods from decisions

    def build_wheel_data(wheel_name):
        """Build wheel segments"""
        segments = []
        
        if wheel_name == 'Race':
            items = data.get('races', [])
            for i, item in enumerate(items):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items)),
                    'desc': f"Raza: {item['name']}"
                })
        
        elif wheel_name == 'Gender':
            items = data.get('genders', [])
            for i, item in enumerate(items):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items)),
                    'desc': f"Género: {item['name']}"
                })
        
        elif wheel_name == 'Age':
            items = data.get('ages', [])
            for i, item in enumerate(items):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items)),
                    'desc': f"Edad: {item['name']}"
                })
        
        elif wheel_name == 'Archetype':
            items = data.get('archetypes', [])
            for i, item in enumerate(items):
                segments.append({
                    'name': item['name'],
                    'weight': 1,
                    'color': get_color(i, len(items)),
                    'desc': f"Arquetipo: {item['name']}"
                })
        
        elif wheel_name == 'Class':
            items = data.get('archetypes', [])
            arch = state.selections.get('Archetype', '')
            arch_obj = next((a for a in items if a['name'] == arch), None)
            if arch_obj:
                classes = arch_obj.get('classes', [])
                for i, cls in enumerate(classes):
                    segments.append({
                        'name': cls,
                        'weight': 1,
                        'color': get_color(i, len(classes)),
                        'desc': f"Clase: {cls}"
                    })
        
        elif wheel_name == 'Alignment':
            items = data.get('alignments', [])
            for i, item in enumerate(items):
                segments.append({
                    'name': item['name'],
                    'weight': 1,
                    'color': get_color(i, len(items)),
                    'desc': f"Alineación: {item['name']}"
                })
        
        elif wheel_name in ['Strength', 'Agility', 'Durability', 'Intelligence', 'Charisma']:
            items = data.get('stat_values', [])
            for i, item in enumerate(items):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items)),
                    'desc': f"{wheel_name}: {item['name']}"
                })
        
        elif wheel_name == 'Weapon':
            items = data.get('weapons', [])
            for i, item in enumerate(items):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items)),
                    'desc': f"Arma: {item['name']}"
                })
        
        elif wheel_name == 'Weapon Mastery':
            items = data.get('weapon_masteries', [])
            for i, item in enumerate(items):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items)),
                    'desc': f"Dominio de Arma: {item['name']} (+{item.get('bonus', 0)})"
                })
        
        elif wheel_name == 'Powers':
            items = data.get('powers', [])
            for i, item in enumerate(items):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items)),
                    'desc': f"Poder: {item['name']}"
                })
        
        elif wheel_name == 'Magic Type':
            # Get magic types with modified weights based on archetype/class/race
            items = data.get('magic_types', [])
            archetype = state.selections.get('Archetype', '')
            char_class = state.selections.get('Class', '')
            race = state.selections.get('Race', '')
            
            # Build magic affinity based on selections
            magic_affinities = build_magic_affinities(archetype, char_class, race)
            
            items_copy = []
            for item in items:
                item_copy = item.copy()
                # Boost weight if magic is compatible
                if item['name'] in magic_affinities:
                    item_copy['weight'] = item.get('weight', 1) * magic_affinities[item['name']]
                items_copy.append(item_copy)
            
            for i, item in enumerate(items_copy):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items_copy)),
                    'desc': f"Tipo Magia: {item['name']}"
                })
        
        elif wheel_name == 'Magic Type 2':
            # Second magic type for special races/classes - same as Magic Type but excludes first selection
            items = data.get('magic_types', [])
            archetype = state.selections.get('Archetype', '')
            char_class = state.selections.get('Class', '')
            race = state.selections.get('Race', '')
            first_magic = state.selections.get('Magic Type', '')
            
            # Build magic affinity based on selections
            magic_affinities = build_magic_affinities(archetype, char_class, race)
            
            items_copy = []
            for item in items:
                # Skip first magic type selection
                if item['name'] == first_magic or item['name'] == 'None':
                    continue
                item_copy = item.copy()
                # Boost weight if magic is compatible
                if item['name'] in magic_affinities:
                    item_copy['weight'] = item.get('weight', 1) * magic_affinities[item['name']]
                items_copy.append(item_copy)
            
            for i, item in enumerate(items_copy):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items_copy)),
                    'desc': f"Magia Secundaria: {item['name']}"
                })
        
        elif wheel_name == 'Skill Efficiency':
            items = data.get('skill_efficiency', [])
            for i, item in enumerate(items):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items)),
                    'desc': f"Eficiencia: {item['name']}"
                })
        
        # Dynamic Power Mastery wheels (Power Mastery 1, 2, etc.)
        elif wheel_name.startswith('Power Mastery '):
            items = data.get('power_skills', [])
            for i, item in enumerate(items):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items)),
                    'desc': f"Dominio: {item['name']} (+{item.get('bonus', 0)})"
                })
        
        # Dynamic Magic Skill wheels (Magic Skill 1, 2, etc.)
        elif wheel_name.startswith('Magic Skill '):
            items = data.get('magic_skills', [])
            for i, item in enumerate(items):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items)),
                    'desc': f"Maestría Mágica: {item['name']} (+{item.get('bonus', 0)})"
                })
        
        # Dynamic Skill Mastery wheels (Skill Mastery 1, 2, etc.)
        elif wheel_name.startswith('Skill Mastery '):
            items = data.get('power_skills', [])  # Use power_skills as default for skill mastery
            for i, item in enumerate(items):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items)),
                    'desc': f"Dominio Habilidad: {item['name']} (+{item.get('bonus', 0)})"
                })
        
        elif wheel_name == 'Power Count':
            items = data.get('power_count', [])
            for i, item in enumerate(items):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items)),
                    'desc': f"Poderes: {item['name']}"
                })
        
        elif wheel_name == 'Magic Count':
            # Check if archetype is magical - if so, make 0 magic almost impossible
            archetype = state.selections.get('Archetype', '')
            magical_archetypes = ['Mage', 'Priest', 'Druid']
            
            items = data.get('magic_count', [])
            
            if archetype in magical_archetypes:
                # For magical archetypes, modify weights to make 0 magic almost impossible
                items_modified = []
                for item in items:
                    item_copy = item.copy()
                    if item['name'] == '0 (None)':
                        # Reduce 0 magic probability drastically for magical archetypes
                        item_copy['weight'] = 1  # 1% or less
                    else:
                        # Boost other probabilities
                        item_copy['weight'] = item.get('weight', 1) * 1.5
                    items_modified.append(item_copy)
                items = items_modified
            
            for i, item in enumerate(items):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items)),
                    'desc': f"Tipos de Magia: {item['name']}"
                })
        
        elif wheel_name == 'Skill Count':
            items = data.get('skills_count', [])
            for i, item in enumerate(items):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items)),
                    'desc': f"Habilidades: {item['name']}"
                })
        
        elif wheel_name == 'Territory':
            # Territory selection with weights influenced by race/class/alignment
            items = data.get('places', [])
            race = state.selections.get('Race', '')
            char_class = state.selections.get('Class', '')
            alignment = state.selections.get('Alignment', '')
            
            # Define territory affinities based on character traits
            territory_affinities = build_territory_affinities(race, char_class, alignment)
            
            items_copy = []
            for item in items:
                item_copy = item.copy()
                # Boost weight if territory is compatible
                if item['name'] in territory_affinities:
                    item_copy['weight'] = item.get('weight', 1) * territory_affinities[item['name']]
                items_copy.append(item_copy)
            
            for i, item in enumerate(items_copy):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items_copy)),
                    'desc': f"Territorio: {item['name']}"
                })
        
        elif wheel_name == 'Items Count':
            items = data.get('items_count', [])
            for i, item in enumerate(items):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items)),
                    'desc': f"Objetos: {item['name']}"
                })
        
        # Dynamic Power wheels (Power 1, Power 2, etc.)
        elif wheel_name.startswith('Power '):
            items = data.get('powers', [])
            for i, item in enumerate(items):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items)),
                    'desc': f"Poder: {item['name']}"
                })
        
        # Dynamic Magic Type wheels (Magic Type 1, Magic Type 2, etc.)
        elif wheel_name.startswith('Magic Type'):
            items = data.get('magic_types', [])
            archetype = state.selections.get('Archetype', '')
            char_class = state.selections.get('Class', '')
            race = state.selections.get('Race', '')
            
            # Get already selected magic types to exclude them
            selected_magics = set()
            for key, val in state.selections.items():
                if key.startswith('Magic Type'):
                    selected_magics.add(val)
            
            magic_affinities = build_magic_affinities(archetype, char_class, race)
            
            items_copy = []
            for item in items:
                # Skip None and already selected magics
                if item['name'] == 'None' or item['name'] in selected_magics:
                    continue
                item_copy = item.copy()
                # Boost weight if magic is compatible
                if item['name'] in magic_affinities:
                    item_copy['weight'] = item.get('weight', 1) * magic_affinities[item['name']]
                items_copy.append(item_copy)
            
            # Add None as option if slots available
            if len(selected_magics) < 5:
                items_copy.append({'name': 'None', 'weight': data.get('magic_types', [{}])[0].get('weight', 1)})
            
            for i, item in enumerate(items_copy):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items_copy)),
                    'desc': f"Magia: {item['name']}"
                })
        
        # Dynamic Spell wheels (Spells 1, Spells 2, etc.)
        elif wheel_name.startswith('Spells '):
            spell_num = wheel_name.split()[-1]
            magic_key = f'Magic Type {spell_num}'
            magic_type = state.selections.get(magic_key, 'None')
            
            all_spells = data.get('spells', [])
            spell_magic_map = get_spell_magic_map()
            
            items = []
            for spell in all_spells:
                allowed_magic = spell_magic_map.get(spell['name'], ['None'])
                if magic_type in allowed_magic or allowed_magic == ['Any']:
                    items.append(spell)
            
            # If no spells match, use all spells
            if not items:
                items = all_spells
            
            for i, item in enumerate(items):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items)),
                    'desc': f"Hechizo: {item['name']}"
                })
        
        # Dynamic Skill wheels (Skill 1, Skill 2, etc.)
        elif wheel_name.startswith('Skill '):
            items = data.get('skills', [])
            
            # Get already selected skills to exclude them
            selected_skills = set()
            for key, val in state.selections.items():
                if key.startswith('Skill '):
                    selected_skills.add(val)
            
            items_filtered = [item for item in items if item['name'] not in selected_skills]
            
            for i, item in enumerate(items_filtered):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items_filtered)),
                    'desc': f"Habilidad: {item['name']}"
                })
        
        # Dynamic Item wheels (Item 1, Item 2, etc.)
        elif wheel_name.startswith('Item '):
            items = data.get('objects', [])
            
            # Get already selected items to exclude them
            selected_items = set()
            for key, val in state.selections.items():
                if key.startswith('Item '):
                    selected_items.add(val)
            
            items_filtered = [item for item in items if item['name'] not in selected_items]
            
            for i, item in enumerate(items_filtered):
                segments.append({
                    'name': item['name'],
                    'weight': item.get('weight', 1),
                    'color': get_color(i, len(items_filtered)),
                    'desc': f"Objeto: {item['name']}"
                })

        # Dynamic Adventure Activity wheels
        elif wheel_name.startswith('Adventure Activity '):
            items = data.get('adventure_activities', [])
            tag_weights = build_adventure_tag_weights()
            # Apply reputation bonuses to tag weights
            for faction_name, score in reputation.items():
                faction_data = next((f for f in data.get('factions', []) if f['name'] == faction_name), None)
                if faction_data and score > 0:
                    for tag in faction_data.get('tags', []):
                        tag_weights[tag] = max(tag_weights.get(tag, 1.0), 1 + score * 0.1)

            for i, item in enumerate(items):
                weight = apply_tag_weights(item, tag_weights)
                for tag in item.get('tags', []):
                    if tag in decision_mods:
                        weight *= decision_mods[tag]
                segments.append({
                    'name': item['name'],
                    'weight': weight,
                    'color': get_color(i, len(items)),
                    'desc': f"Actividad: {item.get('desc', item['name'])}"
                })

        # Dynamic Adventure Event wheels
        elif wheel_name.startswith('Adventure Event '):
            items = data.get('adventure_events', [])
            tag_weights = build_adventure_tag_weights()
            for faction_name, score in reputation.items():
                faction_data = next((f for f in data.get('factions', []) if f['name'] == faction_name), None)
                if faction_data and score > 0:
                    for tag in faction_data.get('tags', []):
                        tag_weights[tag] = max(tag_weights.get(tag, 1.0), 1 + score * 0.1)

            for i, item in enumerate(items):
                weight = apply_tag_weights(item, tag_weights)
                for tag in item.get('tags', []):
                    if tag in decision_mods:
                        weight *= decision_mods[tag]
                segments.append({
                    'name': item['name'],
                    'weight': weight,
                    'color': get_color(i, len(items)),
                    'desc': f"Evento: {item.get('desc', item['name'])}"
                })

        # Dynamic Adventure Action wheels
        elif wheel_name.startswith('Adventure Action '):
            items = data.get('adventure_actions', [])
            tag_weights = build_adventure_tag_weights()
            for faction_name, score in reputation.items():
                faction_data = next((f for f in data.get('factions', []) if f['name'] == faction_name), None)
                if faction_data and score > 0:
                    for tag in faction_data.get('tags', []):
                        tag_weights[tag] = max(tag_weights.get(tag, 1.0), 1 + score * 0.1)

            for i, item in enumerate(items):
                weight = apply_tag_weights(item, tag_weights)
                for tag in item.get('tags', []):
                    if tag in decision_mods:
                        weight *= decision_mods[tag]
                segments.append({
                    'name': item['name'],
                    'weight': weight,
                    'color': get_color(i, len(items)),
                    'desc': f"Accion: {item.get('desc', item['name'])}"
                })

        # Dynamic Adventure Outcome wheels
        elif wheel_name.startswith('Adventure Outcome '):
            items = data.get('adventure_outcomes', [])
            tag_weights = build_adventure_tag_weights()
            chapter = adventure_phase.get('chapter', 1)

            # Get action tags for stat checks
            action_tags = get_action_tags_for_chapter(chapter)
            stat_bonus = compute_stat_bonus_for_tags(action_tags)

            for i, item in enumerate(items):
                weight = apply_tag_weights(item, tag_weights)
                # Apply decision mods
                for tag in item.get('tags', []):
                    if tag in decision_mods:
                        weight *= decision_mods[tag]

                # Stat checks: positive outcomes boosted by good stats
                item_tags = item.get('tags', [])
                if any(t in item_tags for t in ['positive', 'good', 'merchant']):
                    weight *= max(0.3, 1 + stat_bonus)
                elif any(t in item_tags for t in ['negative', 'evil', 'dark']):
                    weight *= max(0.3, 1 - stat_bonus)

                # Dynamic death/victory weights
                terminal = item.get('terminal', None)
                if terminal == 'death':
                    weight = compute_death_weight(chapter)
                elif terminal == 'victory':
                    weight = compute_victory_weight(chapter, item['name'])

                if weight > 0:
                    segments.append({
                        'name': item['name'],
                        'weight': weight,
                        'color': get_color(i, len(items)),
                        'desc': f"Resultado: {item.get('desc', item['name'])}"
                    })
        
        return segments

    def build_magic_affinities(archetype, char_class, race):
        """Build magic type affinities based on character choices"""
        affinities = {}  # spell_name: weight_multiplier
        
        # Archetype-based affinities
        if archetype == 'Mage':
            affinities['Arcane'] = 3.0
            affinities['Divine'] = 0.5
            affinities['Shadow'] = 1.5
        elif archetype == 'Priest':
            affinities['Divine'] = 3.0
            affinities['Nature'] = 2.0
            affinities['Arcane'] = 0.5
        elif archetype == 'Druid':
            affinities['Nature'] = 3.0
            affinities['Earth'] = 2.0
            affinities['Water'] = 1.5
        elif archetype == 'Rogue':
            affinities['Shadow'] = 2.5
            affinities['Blood'] = 1.5
        elif archetype == 'Warrior':
            affinities['Fire'] = 1.5
            affinities['Lightning'] = 1.5
            affinities['Arcane'] = 0.3
        elif archetype == 'Hunter':
            affinities['Nature'] = 2.0
            affinities['Fire'] = 1.5
        elif archetype == 'Bard':
            affinities['Arcane'] = 2.0
            affinities['Divine'] = 1.5
        
        # Race-based affinities
        if race == 'Vampire':
            affinities['Blood'] = 3.0
            affinities['Shadow'] = 2.5
        elif race == 'Werewolf':
            affinities['Blood'] = 2.0
            affinities['Nature'] = 1.5
        elif race == 'Demon':
            affinities['Infernal'] = 3.0
            affinities['Blood'] = 2.0
            affinities['Shadow'] = 1.5
        elif race == 'Dark Elf':
            affinities['Shadow'] = 2.5
            affinities['Arcane'] = 2.0
        elif race == 'Elf':
            affinities['Arcane'] = 2.0
            affinities['Nature'] = 2.0
        
        # Default affinities - boost for non-None
        for magic in ['Arcane', 'Divine', 'Nature', 'Blood', 'Shadow', 'Infernal', 'Fire', 'Water', 'Earth', 'Air', 'Lightning', 'Ice']:
            if magic not in affinities:
                affinities[magic] = 1.0
        
        return affinities
    
    def build_territory_affinities(race, char_class, alignment):
        """Build territory affinities based on race/class/alignment"""
        affinities = {}  # territory_name: weight_multiplier
        
        # Race-based affinities
        if race == 'Elf':
            affinities['Elven Forest'] = 3.0
            affinities['Human City (Good Factions)'] = 2.0
        elif race == 'Dark Elf':
            affinities['Elven Forest'] = 3.0
            affinities['Outlands'] = 2.5
        elif race == 'Dwarf':
            affinities['Dwarven Hold'] = 3.0
            affinities['Dwarven Hold'] = 2.5
        elif race == 'Orc':
            affinities['Human Slums'] = 2.5
            affinities['Outlands'] = 2.0
        elif race in ['Vampire', 'Werewolf', 'Demon']:
            affinities['Outlands'] = 3.0
            affinities['Human Slums'] = 2.0
        elif race == 'Gnome':
            affinities['Human City (Good Factions)'] = 2.5
        
        # Class-based affinities
        if char_class == 'Thief':
            affinities['Human City (Good Factions)'] = 2.5
            affinities['Elven Forest'] = 1.5
        elif char_class == 'Knight':
            affinities['Dwarven Hold'] = 2.5
            affinities['Human City (Good Factions)'] = 1.5
        elif char_class in ['Cleric', 'Priest']:
            affinities['Human City (Good Factions)'] = 3.0
            affinities['Dwarven Hold'] = 2.0
        elif char_class in ['Mage', 'Sorcerer', 'Enchanter']:
            affinities['Outlands'] = 3.0
            affinities['Human City (Good Factions)'] = 1.5
        elif char_class == 'Beast Hunter':
            affinities['Elven Forest'] = 2.5
            affinities['Human Slums'] = 2.0
        
        # Alignment-based affinities
        if 'Good' in alignment:
            affinities['Human City (Good Factions)'] = 2.0
            affinities['Dwarven Hold'] = 1.5
        elif 'Evil' in alignment:
            affinities['Outlands'] = 2.5
            affinities['Human Slums'] = 2.0
            affinities['Human Slums'] = 1.5
        
        # Default affinities for all territories
        default_territories = ['Elven Forest', 'Human City (Good Factions)', 'Dwarven Hold', 'Human Slums', 'Outlands']
        
        for territory in default_territories:
            if territory not in affinities:
                affinities[territory] = 1.0
        
        return affinities
    
    def get_spell_magic_map():
        """Map spells to their allowed magic types"""
        return {
            'Chain Lightning': ['Lightning', 'Arcane'],
            'Frost Nova': ['Ice', 'Arcane'],
            'Arcane Missile': ['Arcane'],
            'Shadow Veil': ['Shadow'],
            'Curse of Weakness': ['Shadow', 'Blood'],
            'Sanctuary': ['Divine'],
            'Wind Walk': ['Air', 'Divine'],
            'Earthquake': ['Earth', 'Nature'],
            'Fireball': ['Fire', 'Arcane'],
            'Dark Flame': ['Infernal', 'Shadow'],
            'Nature Blessing': ['Nature', 'Divine'],
            'Beast Call': ['Nature'],
            'Blood Curse': ['Blood'],
            'Blood Drain': ['Blood', 'Infernal']
        }

    def apply_tag_weights(item, tag_weights):
        """Apply weight multipliers based on item tags"""
        weight = item.get('weight', 1)
        for tag in item.get('tags', []):
            if tag in tag_weights:
                weight *= tag_weights[tag]
        return weight

    def build_adventure_tag_weights():
        """Build adventure tag weights from character selections"""
        tag_weights = {}

        def add_tag(tag, mult):
            tag_weights[tag] = max(tag_weights.get(tag, 1.0), mult)

        archetype = state.selections.get('Archetype', '')
        char_class = state.selections.get('Class', '')
        race = state.selections.get('Race', '')
        alignment = state.selections.get('Alignment', '')

        if archetype == 'Merchant':
            add_tag('merchant', 2.0)
            add_tag('trade', 2.0)
            add_tag('commerce', 1.8)
            add_tag('social', 1.4)
        elif archetype == 'Warrior':
            add_tag('combat', 1.8)
            add_tag('honor', 1.4)
        elif archetype == 'Mage':
            add_tag('magic', 1.8)
            add_tag('arcane', 1.5)
            add_tag('research', 1.3)
        elif archetype == 'Rogue':
            add_tag('crime', 1.8)
            add_tag('stealth', 1.8)
        elif archetype == 'Priest':
            add_tag('divine', 1.8)
            add_tag('faith', 1.6)
            add_tag('healing', 1.4)
        elif archetype == 'Hunter':
            add_tag('hunt', 1.8)
            add_tag('tracking', 1.6)
        elif archetype == 'Druid':
            add_tag('nature', 1.8)
            add_tag('ritual', 1.4)
        elif archetype == 'Noble':
            add_tag('politics', 1.8)
            add_tag('leadership', 1.6)
            add_tag('social', 1.4)
        elif archetype == 'Beast':
            add_tag('beast', 1.8)
            add_tag('hunt', 1.4)

        if char_class in ['Trader', 'Smuggler', 'Black Market Dealer', 'Banker', 'Artisan', 'Caravan Master', 'Fence', 'Relic Seller']:
            add_tag('merchant', 2.0)
            add_tag('trade', 1.8)
        if char_class in ['Assassin', 'Spy', 'Saboteur', 'Shadow Dancer', 'Poisoner']:
            add_tag('crime', 2.0)
            add_tag('stealth', 1.6)
        if char_class in ['Knight', 'Bodyguard', 'Duelist', 'Warlord', 'Gladiator']:
            add_tag('combat', 1.8)
            add_tag('honor', 1.3)
        if char_class in ['Cleric', 'Inquisitor', 'Exorcist', 'Healer', 'Oracle', 'Prophet']:
            add_tag('divine', 1.7)
            add_tag('healing', 1.5)
        if char_class in ['Elementalist', 'Illusionist', 'Necromancer', 'Enchanter', 'Sorcerer', 'Alchemist', 'Blood Mage', 'Chronomancer']:
            add_tag('magic', 1.8)
            add_tag('arcane', 1.4)

        if 'Good' in alignment:
            add_tag('good', 1.4)
        elif 'Evil' in alignment:
            add_tag('evil', 1.6)
        else:
            add_tag('neutral', 1.2)

        if race in ['Vampire', 'Demon', 'Werewolf']:
            add_tag('dark', 1.7)
        if race == 'Elf':
            add_tag('elven', 1.3)
        if race == 'Dwarf':
            add_tag('dwarf', 1.3)
        if race == 'Orc':
            add_tag('orc', 1.3)

        magic_types = []
        for key, val in state.selections.items():
            if key.startswith('Magic Type') and val not in ['None', '', None]:
                magic_types.append(val)

        for mtype in magic_types:
            add_tag('magic', 1.4)
            add_tag(f"magic_{mtype.lower()}", 1.5)

        for key, val in state.selections.items():
            if key.startswith('Skill '):
                if val == 'Persuasion':
                    add_tag('social', 1.6)
                    add_tag('trade', 1.4)
                elif val == 'Stealth':
                    add_tag('stealth', 1.8)
                elif val == 'Tracking':
                    add_tag('tracking', 1.6)
                    add_tag('hunt', 1.4)
                elif val == 'Smithing':
                    add_tag('craft', 1.7)
                elif val == 'Alchemy':
                    add_tag('alchemy', 1.6)
                    add_tag('magic', 1.2)
                elif val == 'Leadership':
                    add_tag('leadership', 1.6)
                elif val == 'Investigation':
                    add_tag('investigation', 1.6)
                elif val == 'Lockpicking':
                    add_tag('crime', 1.5)
                elif val == 'Medicine':
                    add_tag('healing', 1.5)

        for key, val in state.selections.items():
            if key.startswith('Power '):
                if 'Blood' in val:
                    add_tag('blood', 1.6)
                    add_tag('dark', 1.3)
                if 'Shadow' in val:
                    add_tag('shadow', 1.6)
                    add_tag('dark', 1.3)
                if 'Wings' in val:
                    add_tag('flight', 1.4)
                if 'Mind Control' in val:
                    add_tag('domination', 1.6)
                if 'Regeneration' in val:
                    add_tag('survival', 1.3)
                if 'Animal' in val:
                    add_tag('beast', 1.4)

        return tag_weights
    
    def get_color(index, total):
        """Generate distinct colors"""
        from colorsys import hsv_to_rgb
        h = (index / max(1, total)) if total > 0 else 0
        rgb = hsv_to_rgb(h, 0.75, 0.92)
        r, g, b = int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255)
        return '#%02x%02x%02x' % (r, g, b)

    # ===== ADVENTURE HELPER FUNCTIONS =====

    def get_stat_value(stat_name):
        """Extract numeric stat value from selection string like '5 (Good)'"""
        val_str = state.selections.get(stat_name, '5 (Good)')
        try:
            return int(val_str.split()[0])
        except:
            return 5

    def compute_stat_bonus_for_tags(tags):
        """Compute a stat-based bonus/penalty based on relevant action tags"""
        bonus = 0.0
        if any(t in tags for t in ['combat', 'honor']):
            bonus += (get_stat_value('Strength') - 5) * 0.12
            bonus += (get_stat_value('Agility') - 5) * 0.08
            bonus += (get_stat_value('Durability') - 5) * 0.05
        if any(t in tags for t in ['magic', 'arcane', 'ritual', 'divine', 'research']):
            bonus += (get_stat_value('Intelligence') - 5) * 0.15
        if any(t in tags for t in ['social', 'trade', 'politics', 'merchant', 'leadership']):
            bonus += (get_stat_value('Charisma') - 5) * 0.15
        if any(t in tags for t in ['stealth', 'crime']):
            bonus += (get_stat_value('Agility') - 5) * 0.15
        if any(t in tags for t in ['tracking', 'hunt', 'exploration']):
            bonus += (get_stat_value('Agility') - 5) * 0.08
            bonus += (get_stat_value('Intelligence') - 5) * 0.07
        if any(t in tags for t in ['healing']):
            bonus += (get_stat_value('Intelligence') - 5) * 0.1
            bonus += (get_stat_value('Charisma') - 5) * 0.05
        return bonus

    def get_action_tags_for_chapter(chapter):
        """Get tags from the current chapter's action for stat checks"""
        action_key = f'Adventure Action {chapter}'
        action_name = state.selections.get(action_key, '')
        all_actions = data.get('adventure_actions', [])
        action_data = next((a for a in all_actions if a['name'] == action_name), None)
        if action_data:
            return action_data.get('tags', [])
        return []

    def compute_death_weight(chapter):
        """Compute dynamic death probability based on chapter and state"""
        base = 0.5
        # Increase danger after chapter 3
        if chapter > 3:
            base += (chapter - 3) * 0.4
        # Recent catastrophes increase death chance
        for i in range(max(1, chapter - 2), chapter):
            outcome = state.selections.get(f'Adventure Outcome {i}', '')
            if outcome in ['Catastrophe', 'Curse']:
                base *= 1.8
            if outcome == 'Make Enemy':
                base *= 1.3
        # Durability influence
        durability = get_stat_value('Durability')
        if durability <= 2:
            base *= 2.0
        elif durability <= 4:
            base *= 1.3
        elif durability >= 8:
            base *= 0.5
        # Powers influence
        for key, val in state.selections.items():
            if key.startswith('Power ') and not key.startswith('Power Count') and not key.startswith('Power Mastery'):
                if val == 'Regeneration':
                    base *= 0.6
                if val == 'Unbreakable':
                    base *= 0.7
        return max(0.3, base)

    def compute_victory_weight(chapter, victory_type):
        """Compute dynamic victory probability based on chapter, character, and history"""
        if chapter < 3:
            return 0  # Can't win too early

        base = 0.5

        if victory_type == 'Retire Wealthy':
            if chapter < 4:
                return 0
            wealth_count = sum(1 for k, v in state.selections.items()
                              if k.startswith('Adventure Outcome') and v == 'Gain Wealth')
            archetype = state.selections.get('Archetype', '')
            if archetype == 'Merchant':
                base *= 2.0
            base += wealth_count * 0.8
            if chapter >= 6:
                base *= 1.5

        elif victory_type == 'Ascend to Godhood':
            if chapter < 5:
                return 0
            magic_count_str = state.selections.get('Magic Count', '0')
            try:
                magic_count = int(magic_count_str.split()[0])
            except:
                magic_count = 0
            if magic_count == 0:
                return 0  # Need magic
            intelligence = get_stat_value('Intelligence')
            base += (intelligence - 5) * 0.3
            base += magic_count * 0.5
            ascension_attempts = sum(1 for k, v in state.selections.items()
                                    if k.startswith('Adventure Outcome') and v == 'Ascension Attempt')
            base += ascension_attempts * 1.5
            if chapter >= 8:
                base *= 1.5

        elif victory_type == 'Found a Dynasty':
            if chapter < 4:
                return 0
            archetype = state.selections.get('Archetype', '')
            if archetype in ['Noble', 'Merchant']:
                base *= 2.0
            charisma = get_stat_value('Charisma')
            base += (charisma - 5) * 0.3
            ally_count = sum(1 for k, v in state.selections.items()
                            if k.startswith('Adventure Outcome') and v == 'Gain Ally')
            base += ally_count * 0.6

        elif victory_type == 'Legendary Hero':
            if chapter < 5:
                return 0
            successes = sum(1 for k, v in state.selections.items()
                           if k.startswith('Adventure Outcome') and v in ['Great Success', 'Costly Victory'])
            strength = get_stat_value('Strength')
            base += successes * 0.5
            base += (strength - 5) * 0.2
            alignment = state.selections.get('Alignment', '')
            if 'Good' in alignment:
                base *= 1.5

        return max(0, base)

    def update_reputation_from_outcome(outcome_name, action_tags):
        """Update faction reputation based on adventure outcome and action context"""
        factions = data.get('factions', [])
        for faction in factions:
            faction_tags = faction.get('tags', [])
            faction_name = faction['name']
            if faction_name not in reputation:
                reputation[faction_name] = 0
            # Positive outcomes with matching tags boost rep
            if outcome_name in ['Great Success', 'Gain Ally', 'Gain Wealth', 'Gain Relic']:
                for tag in action_tags:
                    if tag in faction_tags:
                        reputation[faction_name] += 1
                        break
            # Negative outcomes with matching tags hurt rep
            elif outcome_name in ['Catastrophe', 'Failure', 'Lose Wealth']:
                for tag in action_tags:
                    if tag in faction_tags:
                        reputation[faction_name] -= 1
                        break

    def start_adventure_phase():
        """Transition from character creation to adventure phase"""
        adventure_phase['active'] = True
        adventure_phase['chapter'] = 1
        adventure_phase['step'] = 0

        # Initialize faction reputation
        factions = data.get('factions', [])
        for faction in factions:
            reputation[faction['name']] = 0

        # Show End Run button
        end_run_btn.config(state='normal')
        main_container.itemconfigure('end_run_tag', state='normal')

        current_lbl.config(text='--- FASE DE AVENTURA ---')
        messagebox.showinfo('Aventura',
            'Personaje creado! Comienza tu aventura.\n\n'
            'La aventura continua hasta:\n'
            '- Morir sin posibilidad de resurreccion\n'
            '- Lograr un objetivo vital\n'
            '- Pulsar "FIN DE RUN"')

        show_adventure_wheel()

    def get_adventure_wheel_name():
        """Get current adventure wheel name"""
        step = adventure_phase['step']
        chapter = adventure_phase['chapter']
        return f"{ADVENTURE_STEPS[step]} {chapter}"

    def show_adventure_wheel():
        """Display current adventure wheel"""
        wheel_name = get_adventure_wheel_name()
        step = adventure_phase['step']
        chapter = adventure_phase['chapter']

        step_labels = ['Actividad', 'Evento', 'Accion', 'Resultado']
        current_lbl.config(text=f'Cap. {chapter} - {step_labels[step]}')

        segments = build_wheel_data(wheel_name)
        if segments:
            draw_wheel(segments, 0)
            spinning['rotation'] = 0

    def handle_adventure_result(selected_name):
        """Handle a spin result during adventure phase"""
        step = adventure_phase['step']
        chapter = adventure_phase['chapter']
        wheel_key = get_adventure_wheel_name()

        state.selections[wheel_key] = selected_name

        # After event step, check for decisions
        if step == 1:  # Event
            if selected_name in ADVENTURE_DECISIONS:
                update_char_display()
                show_decision_popup(selected_name)
                return  # Decision popup will advance the adventure

        # After outcome step, process chapter end
        if step == 3:  # Outcome
            # Check for terminal outcomes
            all_outcomes = data.get('adventure_outcomes', [])
            outcome_data = next((o for o in all_outcomes if o['name'] == selected_name), None)

            if outcome_data and outcome_data.get('terminal') == 'death':
                update_char_display()
                end_run('death', selected_name)
                return
            elif outcome_data and outcome_data.get('terminal') == 'victory':
                update_char_display()
                end_run('victory', selected_name)
                return

            # Update reputation
            action_tags = get_action_tags_for_chapter(chapter)
            update_reputation_from_outcome(selected_name, action_tags)

            # Log chapter summary
            activity = state.selections.get(f'Adventure Activity {chapter}', '?')
            event = state.selections.get(f'Adventure Event {chapter}', '?')
            action = state.selections.get(f'Adventure Action {chapter}', '?')
            adventure_log.append(f"Cap.{chapter}: {activity} > {event} > {action} > {selected_name}")

            # Clear temporary decision mods
            decision_mods.clear()

        update_char_display()
        advance_adventure()

    def advance_adventure():
        """Move to next adventure step or chapter"""
        adventure_phase['step'] += 1
        if adventure_phase['step'] > 3:
            adventure_phase['step'] = 0
            adventure_phase['chapter'] += 1
        show_adventure_wheel()

    def show_decision_popup(event_name):
        """Show decision popup for an adventure event"""
        decision = ADVENTURE_DECISIONS[event_name]

        popup = tk.Toplevel(root)
        popup.title('Decision')
        popup.geometry('550x400')
        popup.configure(bg='#1a1a2e')
        popup.transient(root)
        popup.grab_set()
        popup.geometry('+{}+{}'.format(root.winfo_x() + 525, root.winfo_y() + 250))

        tk.Label(popup, text='DECISION', font=('Segoe UI', 18, 'bold'),
                fg='#ff6b6b', bg='#1a1a2e').pack(pady=10)

        tk.Label(popup, text=decision['prompt'], font=('Segoe UI', 12),
                fg='#eebc1d', bg='#1a1a2e', wraplength=500).pack(pady=10)

        def on_decision(option):
            # Apply tag mods
            for tag, mult in option.get('tag_mods', {}).items():
                decision_mods[tag] = max(decision_mods.get(tag, 1.0), mult)
            # Apply reputation changes
            for faction, change in option.get('rep', {}).items():
                if faction not in reputation:
                    reputation[faction] = 0
                reputation[faction] += change
            popup.destroy()
            update_char_display()
            advance_adventure()

        for option in decision['options']:
            btn = tk.Button(popup, text=option['label'], font=('Segoe UI', 11, 'bold'),
                           bg='#2a2a4e', fg='#eebc1d', activebackground='#3a3a6e',
                           activeforeground='#eebc1d', width=35, relief='ridge', bd=2,
                           command=lambda o=option: on_decision(o))
            btn.pack(pady=8)

    def end_run(reason, detail=''):
        """End the adventure"""
        adventure_phase['active'] = False
        spin_btn.config(state='disabled')
        end_run_btn.config(state='disabled')

        chapter = adventure_phase['chapter']

        if reason == 'death':
            title = 'MUERTE'
            msg = f'Tu aventura termina en el capitulo {chapter}.\n\n{detail}\n\nHas caido sin posibilidad de resurreccion.'
            color = '#ff4444'
        elif reason == 'victory':
            title = 'VICTORIA'
            msg = f'Has logrado tu objetivo vital en el capitulo {chapter}!\n\n{detail}\n\nTu leyenda perdurara por siempre.'
            color = '#44ff44'
        else:  # manual end run
            title = 'FIN DE RUN'
            msg = f'Has decidido terminar tu aventura en el capitulo {chapter}.\n\nTu historia queda inconclusa, pero vives para contarla.'
            color = '#eebc1d'

        # Show end popup
        popup = tk.Toplevel(root)
        popup.title(title)
        popup.geometry('600x500')
        popup.configure(bg='#1a1a2e')
        popup.transient(root)
        popup.grab_set()
        popup.geometry('+{}+{}'.format(root.winfo_x() + 500, root.winfo_y() + 200))

        tk.Label(popup, text=title, font=('Segoe UI', 22, 'bold'),
                fg=color, bg='#1a1a2e').pack(pady=15)

        tk.Label(popup, text=msg, font=('Segoe UI', 12),
                fg='#eebc1d', bg='#1a1a2e', wraplength=550).pack(pady=10)

        # Show adventure log
        if adventure_log:
            log_frame = tk.Frame(popup, bg='#0f3460')
            log_frame.pack(fill='both', expand=True, padx=10, pady=10)
            tk.Label(log_frame, text='Registro de Aventura:', font=('Segoe UI', 10, 'bold'),
                    fg='#eebc1d', bg='#0f3460').pack(anchor='w', padx=5, pady=2)
            log_text = scrolledtext.ScrolledText(log_frame, height=8, width=65,
                                                font=('Consolas', 8), bg='#0f3460', fg='#eebc1d', bd=0)
            log_text.pack(fill='both', expand=True, padx=5, pady=2)
            for entry in adventure_log:
                log_text.insert(tk.END, entry + '\n')
            log_text.config(state='disabled')

        # Show reputation
        if any(v != 0 for v in reputation.values()):
            rep_text = '\nReputacion Final:\n'
            for faction, score in reputation.items():
                if score != 0:
                    symbol = '+' if score > 0 else ''
                    rep_text += f"  {faction}: {symbol}{score}\n"
            tk.Label(popup, text=rep_text, font=('Consolas', 9),
                    fg='#eebc1d', bg='#1a1a2e', justify='left').pack(pady=5)

        tk.Button(popup, text='Cerrar', font=('Segoe UI', 12, 'bold'),
                 bg='#eebc1d', fg='#000000', width=15,
                 command=popup.destroy).pack(pady=10)

        current_lbl.config(text=title)

    # ===== END ADVENTURE HELPERS =====

    def draw_wheel(segments, rotation_angle=0.0):
        """Draw the circular wheel"""
        wheel_canvas.delete('all')
        
        if not segments:
            wheel_canvas.create_text(325, 325, text='No options', 
                                    fill='#eebc1d', font=('Segoe UI', 16))
            return

        total_weight = sum(s['weight'] for s in segments)
        if total_weight == 0:
            total_weight = 1

        center_x, center_y = 325, 325
        radius = 300
        start_angle = rotation_angle

        # Draw segments
        for segment in segments:
            segment_angle = (segment['weight'] / total_weight) * 360
            end_angle = start_angle + segment_angle
            draw_segment(center_x, center_y, radius, start_angle, end_angle, 
                        segment['color'], segment['name'])
            start_angle = end_angle

        # Center circle
        wheel_canvas.create_oval(center_x - 50, center_y - 50, 
                               center_x + 50, center_y + 50, 
                               fill='#000000', outline='#eebc1d', width=4)
        wheel_canvas.create_text(center_x, center_y, text='SPIN', 
                               fill='#eebc1d', font=('Segoe UI', 14, 'bold'))

    def draw_segment(center_x, center_y, radius, start_angle, end_angle, color, label):
        """Draw segment"""
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)

        points = [center_x, center_y]
        num_points = max(3, int((end_angle - start_angle) / 5))
        for i in range(num_points + 1):
            angle = start_angle + (end_angle - start_angle) * (i / num_points)
            angle_rad = math.radians(angle)
            px = center_x + radius * math.cos(angle_rad)
            py = center_y + radius * math.sin(angle_rad)
            points.extend([px, py])
        points.extend([center_x, center_y])
        
        wheel_canvas.create_polygon(points, fill=color, outline='#1a1a1a', width=1)

        # Label - horizontal text for prototype stability
        mid_angle = (start_angle + end_angle) / 2
        label_radius = radius * 0.65
        label_rad = math.radians(mid_angle)
        label_x = center_x + label_radius * math.cos(label_rad)
        label_y = center_y + label_radius * math.sin(label_rad)
        
        wheel_canvas.create_text(label_x, label_y, text=label, 
                               fill='#000000', font=('Segoe UI', 11, 'bold'),
                               width=80)

    def animate_spin(segments, final_idx, duration=3500):
        """Spin animation"""
        if spinning['active']:
            return
        
        spinning['active'] = True
        total_weight = sum(s['weight'] for s in segments)
        
        # Calculate target angle (segment under pointer at top = 270 degrees in trig coords)
        current_angle = 0
        target_angle = 0
        for i, seg in enumerate(segments):
            seg_angle = (seg['weight'] / total_weight) * 360
            if i == final_idx:
                # Stop in the middle of this segment
                target_angle = current_angle + seg_angle / 2
                break
            current_angle += seg_angle
        
        # Normalize angle properly for wheel rotation
        target_angle = target_angle % 360
        
        # The pointer (arrow) is at 270 degrees (top of canvas)
        # Rotate so the selected segment ends at the pointer (270°)
        final_rotation = (270 - target_angle) % 360
        
        # Spin with multiple rotations + target
        total_rotation = 360 * 5 + final_rotation
        start_rot = spinning['rotation']
        
        steps = 80
        
        def step(n):
            if n >= steps:
                spinning['rotation'] = final_rotation
                draw_wheel(segments, final_rotation)
                spinning['active'] = False
                root.after(500, lambda: show_result_popup(segments[final_idx]))
                return
            
            t = n / steps
            ease = 1 - (1 - t) ** 2.5  # Better deceleration
            current_rot = start_rot + (total_rotation - start_rot) * ease
            spinning['rotation'] = current_rot % 360
            
            draw_wheel(segments, spinning['rotation'])
            root.after(int(duration / steps), lambda: step(n + 1))
        
        step(0)

    def show_result_popup(result_segment):
        """Show result in popup"""
        popup = tk.Toplevel(root)
        popup.title('Resultado')
        popup.geometry('500x350')
        popup.configure(bg='#1a1a2e')
        popup.transient(root)
        popup.grab_set()
        
        # Center the popup
        popup.geometry('+{}+{}'.format(root.winfo_x() + 550, root.winfo_y() + 275))
        
        tk.Label(popup, text=result_segment['name'], font=('Segoe UI', 24, 'bold'),
                fg='#eebc1d', bg='#1a1a2e').pack(pady=20)
        
        tk.Label(popup, text=result_segment['desc'], font=('Segoe UI', 14),
                fg='#eebc1d', bg='#1a1a2e', wraplength=450).pack(pady=15)
        
        tk.Button(popup, text='Aceptar', font=('Segoe UI', 12, 'bold'),
                 bg='#eebc1d', fg='#000000', width=15,
                 command=lambda: on_accept(popup, result_segment['name'])).pack(pady=20)

    def on_accept(popup, selected_name):
        """Accept result and proceed"""
        popup.destroy()
        on_spin_result(selected_name)

    def on_spin_result(selected_name):
        """Handle spin result"""
        if adventure_phase['active']:
            handle_adventure_result(selected_name)
            return

        # Character creation flow
        current_wheel_config = get_current_wheel_config()
        current_wheel = current_wheel_config[wheel_index['i']]

        # Store selection
        state.selections[current_wheel] = selected_name

        # Load background image if territory is selected
        if current_wheel == 'Territory':
            root.after(100, lambda: load_background_image(selected_name))

        update_char_display()

        wheel_index['i'] += 1
        current_wheel_config = get_current_wheel_config()
        if wheel_index['i'] < len(current_wheel_config):
            current_lbl.config(text=f'Rueda: {current_wheel_config[wheel_index["i"]]}')
            show_current_wheel()
        else:
            # Character creation complete - start adventure!
            start_adventure_phase()

    def show_current_wheel():
        """Display current wheel"""
        if adventure_phase['active']:
            show_adventure_wheel()
            return
        current_wheel_config = get_current_wheel_config()
        if wheel_index['i'] < len(current_wheel_config):
            wheel_name = current_wheel_config[wheel_index['i']]
            segments = build_wheel_data(wheel_name)
            if segments:
                draw_wheel(segments, 0)
                spinning['rotation'] = 0

    def spin_action():
        """Spin button"""
        if spinning['active']:
            return

        if adventure_phase['active']:
            wheel_name = get_adventure_wheel_name()
        else:
            current_wheel_config = get_current_wheel_config()
            if wheel_index['i'] >= len(current_wheel_config):
                return
            wheel_name = current_wheel_config[wheel_index['i']]

        segments = build_wheel_data(wheel_name)

        if not segments:
            messagebox.showwarning('Error', f'No hay opciones para {wheel_name}')
            return

        # Weighted random
        total_weight = sum(s['weight'] for s in segments)
        choice = random.uniform(0, total_weight)
        current = 0
        final_idx = 0

        for i, seg in enumerate(segments):
            current += seg['weight']
            if choice <= current:
                final_idx = i
                break

        animate_spin(segments, final_idx)

    spin_btn.config(command=spin_action)
    end_run_btn.config(command=lambda: end_run('manual'))
    show_current_wheel()
    update_char_display()

    root.mainloop()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
