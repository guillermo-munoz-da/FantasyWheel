import tkinter as tk
from tkinter import messagebox, scrolledtext
from PIL import Image, ImageTk
from engine import load_data, GameState
import os
import random
import math


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
    
    def get_color(index, total):
        """Generate distinct colors"""
        from colorsys import hsv_to_rgb
        h = (index / max(1, total)) if total > 0 else 0
        rgb = hsv_to_rgb(h, 0.75, 0.92)
        r, g, b = int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255)
        return '#%02x%02x%02x' % (r, g, b)

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

        # Label - positioned to not rotate
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
        current_wheel_config = get_current_wheel_config()
        current_wheel = current_wheel_config[wheel_index['i']]
        
        # Store selection - handles all cases including multiple powers/skills/magics
        # They'll be stored as "Power 1", "Power 2", etc.
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
            current_lbl.config(text='¡Personaje Completo!')
            spin_btn.config(state='disabled')
            messagebox.showinfo('Éxito', '¡Personaje completamente generado!')

    def show_current_wheel():
        """Display current wheel"""
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
        current_wheel_config = get_current_wheel_config()
        if wheel_index['i'] >= len(current_wheel_config):
            messagebox.showinfo('Completo', '¡Personaje generado!')
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
    show_current_wheel()
    update_char_display()

    root.mainloop()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
