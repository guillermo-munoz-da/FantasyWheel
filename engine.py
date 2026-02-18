import json
import random
import os

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data.json')


def load_data():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def weighted_choice(options):
    if not options:
        return None
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
        races = list(self.data.get('races', [])) + list(self.data.get('more_races', []))
        race = weighted_choice(races)
        if not race:
            return None
        self.selections['Race'] = race['name']
        for k, v in race.get('stat_mods', {}).items():
            self.stats[k] = self.stats.get(k, 0) + v
        self.selections['height_options'] = race.get('height_options', [])
        self.selections['_race_obj'] = race
        return race

    def spin_height(self):
        opts = self.selections.get('height_options')
        if not opts:
            opts = [{"name": "1.60 m", "weight": 50}, {"name": "1.80 m", "weight": 50}]
        h = weighted_choice(opts)
        if h:
            self.selections['Height'] = h['name']
        return h

    def spin_class(self):
        cls = weighted_choice(self.data.get('classes', []))
        if not cls:
            return None
        self.selections['Class'] = cls['name']
        pri = cls.get('stat_priority', [])
        if pri:
            self.stats[pri[0]] += 1
        possible = [p for p in self.data.get('powers', []) if cls['name'] in p.get('class_restriction', [])]
        if possible:
            p = weighted_choice(possible)
            if p:
                self.powers.append(p['name'])
                self.log_append(f"Obtienes poder inicial: {p['name']} - {p.get('desc','')}")
        return cls

    def spin_alignment(self):
        al = weighted_choice(self.data.get('alignments', []))
        if al:
            self.selections['Alignment'] = al['name']
        return al

    def spin_age(self):
        race_obj = self.selections.get('_race_obj')
        if race_obj and 'age_range' in race_obj:
            ar = race_obj['age_range']
            immortal_chance = ar.get('immortal_chance', 0)
            if random.random() < immortal_chance:
                self.selections['Age'] = 'Immortal'
                return {'name': 'Immortal'}
            age = random.randint(ar.get('min', 16), ar.get('max', 60))
            self.selections['Age'] = str(age)
            return {'name': str(age)}
        a = weighted_choice(self.data.get('age_brackets', []))
        if a:
            self.selections['Age'] = a['name']
        return a

    def spin_place(self):
        places = self.data.get('places', [])
        if not places:
            return None
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
