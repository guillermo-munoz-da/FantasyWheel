import json
import random
import os
import PySimpleGUI as sg

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data.json')


def load_data():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def weighted_choice(options):
    total = sum(o.get('weight', 0) for o in options)
    if total <= 0:
        return None
    r = random.uniform(0, total)
    upto = 0
    for o in options:
        w = o.get('weight', 0)
        if upto + w >= r:
            return o
        upto += w
    return options[-1]


class GameState:
    def __init__(self, data):
        self.data = data
        self.selections = {}
        self.stats = {"str": 5, "int": 5, "agi": 5, "cha": 5}
        self.log = []
        self.powers = []
        self.abilities = []

    def spin_race(self):
        # races may be split across 'races' and 'more_races'
        races = list(self.data.get('races', [])) + list(self.data.get('more_races', []))
        race = weighted_choice(races)
        self.selections['Race'] = race['name']
        # apply race stats
        for k, v in race.get('stat_mods', {}).items():
            self.stats[k] = self.stats.get(k, 0) + v
        # set height wheel options dependent on race
        self.selections['height_options'] = race.get('height_options', [])
        # save race object for later (age ranges etc)
        self.selections['_race_obj'] = race
        return race

    def spin_height(self):
        opts = self.selections.get('height_options')
        if not opts:
            # fallback: generic heights
            opts = [
                {"name": "1.60 m", "weight": 50},
                {"name": "1.80 m", "weight": 50}
            ]
        h = weighted_choice(opts)
        self.selections['Height'] = h['name']
        return h

    def spin_class(self):
        cls = weighted_choice(self.data['classes'])
        self.selections['Class'] = cls['name']
        # small bonus for primary stat
        pri = cls.get('stat_priority', [])
        if pri:
            self.stats[pri[0]] += 1
        # assign starter power(s) appropriate to class
        possible = [p for p in self.data.get('powers', []) if cls['name'] in p.get('class_restriction', [])]
        if possible:
            p = weighted_choice(possible)
            if p:
                self.powers.append(p['name'])
                self.log_append(f"Obtienes poder inicial: {p['name']} - {p.get('desc','')}")
        return cls

    def spin_alignment(self):
        al = weighted_choice(self.data['alignments'])
        self.selections['Alignment'] = al['name']
        return al

    def spin_age(self):
        # Prefer race-specific age ranges if present
        race_obj = self.selections.get('_race_obj')
        if race_obj and 'age_range' in race_obj:
            ar = race_obj['age_range']
            # chance for special immortal
            immortal_chance = ar.get('immortal_chance', 0)
            if random.random() < immortal_chance:
                self.selections['Age'] = 'Immortal'
                return {'name': 'Immortal'}
            age = random.randint(ar.get('min', 16), ar.get('max', 60))
            self.selections['Age'] = str(age)
            return {'name': str(age)}
        else:
            a = weighted_choice(self.data['age_brackets'])
            self.selections['Age'] = a['name']
            return a

    def spin_place(self):
        places = self.data.get('places', [])
        if not places:
            return None
        # build options applying race and alignment bias
        opts = []
        race = self.selections.get('Race')
        align = self.selections.get('Alignment')
        for p in places:
            w = p.get('base_weight', 1)
            if race:
                w *= p.get('race_bias', {}).get(race, 1.0)
            if align:
                w *= p.get('alignment_bias', {}).get(align, 1.0)
            if w <= 0:
                continue
            opts.append({'name': p['name'], 'weight': w})
        chosen = weighted_choice(opts)
        if chosen:
            self.selections['Place'] = chosen['name']
        return chosen

    def apply_effects(self, effects):
        for k, v in effects.items():
            if k in self.stats:
                self.stats[k] = self.stats.get(k, 0) + v
            # allow effects to add/remove powers/abilities
            elif k == 'add_power':
                self.powers.append(v)
            elif k == 'remove_power' and v in self.powers:
                self.powers.remove(v)
            elif k == 'add_ability':
                self.abilities.append(v)
            elif k == 'remove_ability' and v in self.abilities:
                self.abilities.remove(v)

    def log_append(self, text):
        self.log.append(text)
        if len(self.log) > 200:
            self.log = self.log[-200:]


def build_layout():
    layout = [
        [sg.Text('Ruleta - Prototipo Dark Fantasy', font=('Any', 16))],
        [sg.Frame('Ruedas', [[
            sg.Column([
                [sg.Text('Race:'), sg.Text('', key='-RACE-', size=(20,1)), sg.Button('Spin Race', key='-SPIN_RACE-')],
                [sg.Text('Class:'), sg.Text('', key='-CLASS-', size=(20,1)), sg.Button('Spin Class', key='-SPIN_CLASS-')],
                [sg.Text('Height:'), sg.Text('', key='-HEIGHT-', size=(20,1)), sg.Button('Spin Height', key='-SPIN_HEIGHT-')],
                [sg.Text('Age:'), sg.Text('', key='-AGE-', size=(20,1)), sg.Button('Spin Age', key='-SPIN_AGE-')],
                [sg.Text('Alignment:'), sg.Text('', key='-ALIGN-', size=(20,1)), sg.Button('Spin Align', key='-SPIN_ALIGN-')],
            ])
        ]])],
        [sg.Frame('Stats', [[sg.Text('', key='-STATS-', size=(60,4))]] )],
        [sg.Button('Auto Generate All', key='-AUTO-'), sg.Button('Trigger Event', key='-EVENT-'), sg.Button('Exit')],
        [sg.Frame('Narrativa', [[sg.Multiline('', key='-LOG-', size=(80,10), disabled=True)]])]
    ]
    return layout


def update_stats_display(window, state: GameState):
    s = '\n'.join(f"{k.upper()}: {v}" for k, v in state.stats.items())
    window['-STATS-'].update(s)


def main():
    data = load_data()
    state = GameState(data)

    # Some PySimpleGUI packages may not expose `theme`; guard against that.
    try:
        if hasattr(sg, 'theme'):
            sg.theme('DarkPurple4')
        elif hasattr(sg, 'Theme'):
            # older variants
            sg.Theme('DarkPurple4')
    except Exception:
        pass
    window = sg.Window('Ruleta - Prototipo', build_layout(), finalize=True)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        if event == '-SPIN_RACE-':
            r = state.spin_race()
            window['-RACE-'].update(r['name'])
            update_stats_display(window, state)
        if event == '-SPIN_CLASS-':
            c = state.spin_class()
            window['-CLASS-'].update(c['name'])
            update_stats_display(window, state)
        if event == '-SPIN_HEIGHT-':
            h = state.spin_height()
            window['-HEIGHT-'].update(h['name'])
        if event == '-SPIN_AGE-':
            a = state.spin_age()
            window['-AGE-'].update(a['name'])
        if event == '-SPIN_ALIGN-':
            al = state.spin_alignment()
            window['-ALIGN-'].update(al['name'])
        if event == '-EVENT-':
            ev = weighted_choice(data.get('events', []))
            if not ev:
                state.log_append('No hay eventos disponibles.')
            else:
                # choose outcome with stat-influenced weighting
                outcomes = ev.get('outcomes', [])
                # if GUI present offer interactive choices
                gui_available = hasattr(sg, 'Window')
                if gui_available:
                    # show a popup with buttons for each outcome (simple choice)
                    labels = [o['name'] for o in outcomes]
                    choice = sg.popup_yes_no(*[f"{i+1}. {o['name']}: {o.get('narrative','')}" for i,o in enumerate(outcomes)], title=ev['name'])
                    # popup_yes_no returns 'Yes'/'No' — fallback to weighted selection
                    selected = weighted_choice(outcomes)
                else:
                    # weight outcomes by stat checks
                    weighted_outs = []
                    for o in outcomes:
                        w = o.get('weight', 1)
                        sc = o.get('stat_check')
                        if sc:
                            st = sc.get('stat')
                            diff = sc.get('difficulty', 5)
                            if state.stats.get(st, 0) >= diff:
                                w = w * 3
                            else:
                                w = w * 0.5
                        weighted_outs.append({
                            'name': o['name'], 'weight': w, 'obj': o
                        })
                    # choose
                    sel = weighted_choice(weighted_outs)
                    selected = sel.get('obj') if sel else None
                if selected:
                    effects = selected.get('effects', {})
                    state.apply_effects(effects)
                    text = f"Evento: {ev['name']} - {selected['name']}\n{selected.get('narrative', ev.get('desc',''))}"
                    state.log_append(text)
            # update UI
            window['-LOG-'].update('\n\n'.join(state.log[-30:]))
            update_stats_display(window, state)
        if event == '-AUTO-':
            state.spin_race()
            state.spin_class()
            state.spin_height()
            state.spin_age()
            state.spin_alignment()
            window['-RACE-'].update(state.selections.get('Race',''))
            window['-CLASS-'].update(state.selections.get('Class',''))
            window['-HEIGHT-'].update(state.selections.get('Height',''))
            window['-AGE-'].update(state.selections.get('Age',''))
            window['-ALIGN-'].update(state.selections.get('Alignment',''))
            update_stats_display(window, state)

    window.close()


if __name__ == '__main__':
    # try to run GUI; if PySimpleGUI not usable, run headless simulation for testing
    gui_ok = True
    try:
        import PySimpleGUI as _sg
        if not hasattr(_sg, 'Window'):
            gui_ok = False
    except Exception:
        gui_ok = False

    if gui_ok:
        main()
    else:
        # headless test: auto-generate and run a few events
        data = load_data()
        state = GameState(data)
        state.spin_race()
        state.spin_class()
        state.spin_height()
        state.spin_age()
        state.spin_alignment()
        state.spin_place()
        state.log_append('--- Personaje generado (headless) ---')
        state.log_append(f"Race: {state.selections.get('Race')} | Class: {state.selections.get('Class')} | Place: {state.selections.get('Place')}")
        update_stats_display = lambda win, s: None
        # run 5 events
        for i in range(5):
            ev = weighted_choice(data.get('events', []))
            if not ev:
                state.log_append('No hay eventos disponibles.')
                continue
            outcomes = ev.get('outcomes', [])
            weighted_outs = []
            for o in outcomes:
                w = o.get('weight', 1)
                sc = o.get('stat_check')
                if sc:
                    st = sc.get('stat')
                    diff = sc.get('difficulty', 5)
                    if state.stats.get(st, 0) >= diff:
                        w = w * 3
                    else:
                        w = w * 0.5
                weighted_outs.append({'name': o['name'], 'weight': w, 'obj': o})
            sel = weighted_choice(weighted_outs)
            selected = sel.get('obj') if sel else None
            if selected:
                state.apply_effects(selected.get('effects', {}))
                state.log_append(f"Evento: {ev['name']} - {selected['name']} | {selected.get('narrative','')}")
        # print summary
        print('\n'.join(state.log))
        print('\nStats:')
        print('\n'.join(f"{k}: {v}" for k,v in state.stats.items()))
