import tkinter as tk
from tkinter import messagebox, scrolledtext
from PIL import Image, ImageTk
from engine import load_data, GameState
import os
import random
import math

# Optional sound support (Windows)
try:
    import winsound
except ImportError:
    winsound = None


def play_sound(name: str):
    """Play a simple Windows beep if available"""
    if not winsound:
        return
    try:
        if name == 'spin':
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        elif name == 'stop':
            winsound.MessageBeep(winsound.MB_OK)
        elif name == 'prize':
            # Short celebratory chirp
            winsound.Beep(1046, 90)
            winsound.Beep(1318, 90)
    except Exception:
        pass

# Lightweight looping background cue state
music_state = {'mood': None, 'timer': None}

# Adventure phase constants
ADVENTURE_STEPS = ['Adventure Activity', 'Adventure Event', 'Adventure Action', 'Adventure Outcome']

# ========== EVENT CHAIN SYSTEM ==========
# Each chain is triggered by an Activity. It replaces the generic Event→Action→Outcome
# with a tree of connected, context-specific wheels.
# Structure:
#   "steps": ordered list of wheel nodes
#   Each step: id, label, options (list of choices)
#   Each option: name, weight, desc, stat_weight (stat→multiplier), skill_bonus (skill→mult),
#                requires_condition, blocked_by_condition, effects, next (step id or None=end)
#   "on_complete": effects applied at chain end

EVENT_CHAINS = {
    # ---- FORGE LEGENDARY GEAR ----
    "Forge Legendary Gear": {
        "steps": [
            {
                "id": "choose_item",
                "label": "Elige que forjar",
                "options": [
                    {"name": "Espada Encantada", "weight": 5, "desc": "Una espada imbuida de poder.",
                     "stat_weight": {"Strength": 1.3}, "skill_bonus": {"Smithing": 2.0},
                     "next": "forge_quality",
                     "effects": {"_forge_item": "Espada Encantada"}},
                    {"name": "Escudo de Obsidiana", "weight": 4, "desc": "Un escudo casi indestructible.",
                     "stat_weight": {"Durability": 1.3}, "skill_bonus": {"Smithing": 2.0},
                     "next": "forge_quality",
                     "effects": {"_forge_item": "Escudo de Obsidiana"}},
                    {"name": "Baston Arcano", "weight": 3, "desc": "Un baston que canaliza magia.",
                     "stat_weight": {"Intelligence": 1.4}, "skill_bonus": {"Alchemy": 1.5},
                     "next": "forge_quality",
                     "effects": {"_forge_item": "Baston Arcano"}},
                    {"name": "Anillo de Proteccion", "weight": 3, "desc": "Un anillo con encantamientos defensivos.",
                     "stat_weight": {"Intelligence": 1.2}, "skill_bonus": {"Smithing": 1.5},
                     "next": "forge_quality",
                     "effects": {"_forge_item": "Anillo de Proteccion"}},
                    {"name": "Armadura de Dragonskin", "weight": 2, "desc": "Armadura hecha de escamas de dragon.",
                     "stat_weight": {"Strength": 1.2, "Durability": 1.2}, "skill_bonus": {"Smithing": 2.5},
                     "next": "forge_quality",
                     "effects": {"_forge_item": "Armadura de Dragonskin"}}
                ]
            },
            {
                "id": "forge_quality",
                "label": "Resultado de la Forja",
                "stat_check": "Intelligence",
                "options": [
                    {"name": "Obra Maestra", "weight": 2, "desc": "Has superado toda expectativa. +2 a stat principal.",
                     "success_tier": "high",
                     "effects": {"stat_boost": 2, "add_item": True, "rep": {"Merchant Guild": 2}}},
                    {"name": "Buena Calidad", "weight": 4, "desc": "Un trabajo solido. +1 a stat principal.",
                     "success_tier": "mid",
                     "effects": {"stat_boost": 1, "add_item": True}},
                    {"name": "Calidad Mediocre", "weight": 5, "desc": "Funcional pero sin brillo.",
                     "success_tier": "low",
                     "effects": {"add_item": True}},
                    {"name": "Fallo Catastrofico", "weight": 2, "desc": "La forja explota. Pierdes materiales y te hieres.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 1, "rep": {"Merchant Guild": -1}}}
                ]
            }
        ]
    },

    # ---- PIRATE BLOCKADE ----
    "Pirate Blockade": {
        "steps": [
            {
                "id": "approach",
                "label": "Enfrentar el Bloqueo Pirata",
                "options": [
                    {"name": "Negociar con los Piratas", "weight": 5, "desc": "Intentas dialogar y llegar a un acuerdo.",
                     "stat_weight": {"Charisma": 1.6}, "skill_bonus": {"Persuasion": 2.0},
                     "next": "negotiate_result"},
                    {"name": "Atacar la Flota", "weight": 4, "desc": "Lanzas un asalto directo.",
                     "stat_weight": {"Strength": 1.5, "Agility": 1.2},
                     "next": "combat_result"},
                    {"name": "Infiltracion Nocturna", "weight": 4, "desc": "Te infiltras de noche para sabotear.",
                     "stat_weight": {"Agility": 1.5}, "skill_bonus": {"Stealth": 2.0},
                     "next": "stealth_result"},
                    {"name": "Pagar Tributo", "weight": 5, "desc": "Pagas para que levanten el bloqueo.",
                     "stat_weight": {"Charisma": 1.1},
                     "next": "tribute_result"},
                    {"name": "Magia Naval", "weight": 2, "desc": "Usas magia para destruir o desviar la flota.",
                     "stat_weight": {"Intelligence": 1.8},
                     "requires_magic": True,
                     "next": "magic_result"}
                ]
            },
            {
                "id": "negotiate_result",
                "label": "Resultado de la Negociacion",
                "stat_check": "Charisma",
                "options": [
                    {"name": "Acuerdo Comercial", "weight": 3, "desc": "Los piratas aceptan un pacto. Comercio restaurado.",
                     "success_tier": "high",
                     "effects": {"remove_condition": "trade_blocked", "rep": {"Merchant Guild": 3, "Thieves Guild": 1}}},
                    {"name": "Tregua Temporal", "weight": 5, "desc": "Aceptan pausar el bloqueo, pero volvera.",
                     "success_tier": "mid",
                     "effects": {"remove_condition": "trade_blocked", "add_condition": "pirate_truce", "rep": {"Merchant Guild": 1}}},
                    {"name": "Rechazan Negociar", "weight": 4, "desc": "Los piratas se rien de tu propuesta.",
                     "success_tier": "low",
                     "effects": {"add_condition": "trade_blocked", "rep": {"Merchant Guild": -1}}}
                ]
            },
            {
                "id": "combat_result",
                "label": "Resultado del Combate Naval",
                "stat_check": "Strength",
                "options": [
                    {"name": "Victoria Aplastante", "weight": 2, "desc": "Destruyes la flota pirata.",
                     "success_tier": "high",
                     "effects": {"remove_condition": "trade_blocked", "stat_boost": 1, "rep": {"Hunters Lodge": 2, "The Crown": 2}}},
                    {"name": "Victoria Ajustada", "weight": 4, "desc": "Ganas pero con heridas.",
                     "success_tier": "mid",
                     "effects": {"remove_condition": "trade_blocked", "stat_damage": 1, "rep": {"Hunters Lodge": 1}}},
                    {"name": "Derrota", "weight": 4, "desc": "Los piratas te repelen con fuerza.",
                     "success_tier": "low",
                     "effects": {"add_condition": "trade_blocked", "stat_damage": 2, "rep": {"Hunters Lodge": -1}}}
                ]
            },
            {
                "id": "stealth_result",
                "label": "Resultado de la Infiltracion",
                "stat_check": "Agility",
                "options": [
                    {"name": "Sabotaje Perfecto", "weight": 3, "desc": "Hundes sus barcos sin ser visto.",
                     "success_tier": "high",
                     "effects": {"remove_condition": "trade_blocked", "rep": {"Thieves Guild": 2}}},
                    {"name": "Parcialmente Exitoso", "weight": 4, "desc": "Dañas algunos barcos pero te detectan.",
                     "success_tier": "mid",
                     "effects": {"remove_condition": "trade_blocked", "rep": {"Thieves Guild": 1}}},
                    {"name": "Descubierto", "weight": 4, "desc": "Te atrapan. Situacion comprometida.",
                     "success_tier": "low",
                     "effects": {"add_condition": "trade_blocked", "stat_damage": 1}}
                ]
            },
            {
                "id": "tribute_result",
                "label": "Resultado del Pago",
                "options": [
                    {"name": "Aceptan el Tributo", "weight": 6, "desc": "Los piratas levantan el bloqueo... por ahora.",
                     "effects": {"remove_condition": "trade_blocked", "lose_wealth": True, "add_condition": "pirate_truce"}},
                    {"name": "Exigen Mas", "weight": 3, "desc": "No es suficiente. Quieren el doble.",
                     "effects": {"add_condition": "trade_blocked", "lose_wealth": True, "rep": {"Merchant Guild": -1}}}
                ]
            },
            {
                "id": "magic_result",
                "label": "Resultado de la Magia Naval",
                "stat_check": "Intelligence",
                "options": [
                    {"name": "Tormenta Arcana", "weight": 3, "desc": "Invocas una tormenta que destroza la flota.",
                     "success_tier": "high",
                     "effects": {"remove_condition": "trade_blocked", "rep": {"Mages Circle": 2}, "stat_boost": 1}},
                    {"name": "Niebla Mistica", "weight": 4, "desc": "La niebla dispersa a los piratas temporalmente.",
                     "success_tier": "mid",
                     "effects": {"remove_condition": "trade_blocked", "add_condition": "pirate_truce"}},
                    {"name": "Contrahechizo", "weight": 3, "desc": "Los piratas tienen un mago que te contrarresta.",
                     "success_tier": "low",
                     "effects": {"add_condition": "trade_blocked", "stat_damage": 1, "rep": {"Mages Circle": -1}}}
                ]
            }
        ]
    },

    # ---- HUNT A BEAST ----
    "Hunt a Beast": {
        "steps": [
            {
                "id": "choose_prey",
                "label": "Elige tu Presa",
                "options": [
                    {"name": "Manada de Lobos", "weight": 6, "desc": "Lobos gigantes asolando aldeas.",
                     "stat_weight": {"Strength": 1.2}, "skill_bonus": {"Tracking": 1.5},
                     "next": "hunt_method", "effects": {"_prey": "Manada de Lobos", "_prey_difficulty": 3}},
                    {"name": "Troll de las Montanas", "weight": 4, "desc": "Un troll aterroriza los caminos.",
                     "stat_weight": {"Strength": 1.4, "Durability": 1.3},
                     "next": "hunt_method", "effects": {"_prey": "Troll de las Montanas", "_prey_difficulty": 5}},
                    {"name": "Cria de Dragon", "weight": 2, "desc": "Una cria de dragon cerca de las minas.",
                     "stat_weight": {"Strength": 1.5, "Intelligence": 1.3},
                     "next": "hunt_method", "effects": {"_prey": "Cria de Dragon", "_prey_difficulty": 7}},
                    {"name": "Criatura Sombria", "weight": 3, "desc": "Un ser de sombra acecha de noche.",
                     "stat_weight": {"Intelligence": 1.4}, "skill_bonus": {"Tracking": 1.3},
                     "next": "hunt_method", "effects": {"_prey": "Criatura Sombria", "_prey_difficulty": 6}},
                    {"name": "Quimera", "weight": 1, "desc": "La bestia legendaria de tres cabezas.",
                     "stat_weight": {"Strength": 1.5, "Agility": 1.3, "Durability": 1.3},
                     "next": "hunt_method", "effects": {"_prey": "Quimera", "_prey_difficulty": 9}}
                ]
            },
            {
                "id": "hunt_method",
                "label": "Metodo de Caza",
                "options": [
                    {"name": "Rastrear y Emboscar", "weight": 5, "desc": "Sigues su rastro y tiendes una emboscada.",
                     "stat_weight": {"Agility": 1.4}, "skill_bonus": {"Tracking": 2.0, "Stealth": 1.5},
                     "next": "hunt_result"},
                    {"name": "Combate Directo", "weight": 5, "desc": "La enfrentas cara a cara.",
                     "stat_weight": {"Strength": 1.6, "Durability": 1.3},
                     "next": "hunt_result"},
                    {"name": "Trampas", "weight": 4, "desc": "Preparas trampas en su territorio.",
                     "stat_weight": {"Intelligence": 1.4}, "skill_bonus": {"Trap Setting": 2.5},
                     "next": "hunt_result"},
                    {"name": "Atraer con Cebo", "weight": 3, "desc": "Usas un cebo para atraerla a tu terreno.",
                     "stat_weight": {"Intelligence": 1.3}, "skill_bonus": {"Beast Taming": 1.5},
                     "next": "hunt_result"}
                ]
            },
            {
                "id": "hunt_result",
                "label": "Resultado de la Caceria",
                "stat_check": "Strength",
                "difficulty_key": "_prey_difficulty",
                "options": [
                    {"name": "Caza Gloriosa", "weight": 3, "desc": "Abates a la bestia con maestria. Trofeo legendario.",
                     "success_tier": "high",
                     "effects": {"stat_boost": 1, "add_item_from": "_prey", "rep": {"Hunters Lodge": 3}}},
                    {"name": "Caza Exitosa", "weight": 5, "desc": "La bestia cae, pero no sin lucha.",
                     "success_tier": "mid",
                     "effects": {"rep": {"Hunters Lodge": 1}, "add_item_from": "_prey"}},
                    {"name": "La Bestia Escapa", "weight": 4, "desc": "No logras atraparla. Regresara mas fuerte.",
                     "success_tier": "low",
                     "effects": {"add_condition": "beast_stalking"}},
                    {"name": "Herido Gravemente", "weight": 2, "desc": "La bestia te ataca y te hiere de gravedad.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 2, "add_condition": "wounded"}}
                ]
            }
        ]
    },

    # ---- EXPLORE RUINS ----
    "Explore Ruins": {
        "steps": [
            {
                "id": "choose_depth",
                "label": "Profundidad de Exploracion",
                "options": [
                    {"name": "Superficie", "weight": 6, "desc": "Exploras las zonas accesibles y seguras.",
                     "next": "surface_find", "effects": {"_ruin_depth": 1}},
                    {"name": "Profundidades", "weight": 4, "desc": "Desciendes a las camaras selladas.",
                     "stat_weight": {"Agility": 1.2}, "skill_bonus": {"Lockpicking": 1.5},
                     "next": "deep_find", "effects": {"_ruin_depth": 2}},
                    {"name": "El Abismo", "weight": 2, "desc": "Bajas donde nadie ha regresado con vida.",
                     "stat_weight": {"Durability": 1.4, "Intelligence": 1.3},
                     "next": "abyss_find", "effects": {"_ruin_depth": 3}}
                ]
            },
            {
                "id": "surface_find",
                "label": "Hallazgo en Superficie",
                "options": [
                    {"name": "Cofre de Monedas", "weight": 5, "desc": "Un cofre con riquezas modestas.",
                     "effects": {"gain_wealth": True, "rep": {"Merchant Guild": 1}}},
                    {"name": "Mapa Antiguo", "weight": 4, "desc": "Un mapa que revela ruinas mas profundas.",
                     "effects": {"add_condition": "ancient_map"}},
                    {"name": "Trampa!", "weight": 3, "desc": "Activas una trampa oculta.",
                     "stat_check_inline": "Agility",
                     "effects": {"stat_damage": 1}},
                    {"name": "Nada Util", "weight": 4, "desc": "Solo polvo y escombros."}
                ]
            },
            {
                "id": "deep_find",
                "label": "Hallazgo en Profundidades",
                "options": [
                    {"name": "Artefacto Magico", "weight": 3, "desc": "Un objeto antiguo vibrando con poder.",
                     "effects": {"add_random_item": True, "stat_boost": 1, "rep": {"Mages Circle": 1}}},
                    {"name": "Criatura Guardianda", "weight": 4, "desc": "Un guardian ancestral te ataca.",
                     "stat_check_inline": "Strength",
                     "next": "guardian_fight"},
                    {"name": "Biblioteca Oculta", "weight": 3, "desc": "Textos antiguos con conocimiento prohibido.",
                     "effects": {"stat_boost_specific": "Intelligence", "rep": {"Mages Circle": 2}}},
                    {"name": "Maldicion Activada", "weight": 3, "desc": "Algo oscuro despierta al entrar.",
                     "effects": {"add_condition": "cursed", "stat_damage": 1}}
                ]
            },
            {
                "id": "abyss_find",
                "label": "Hallazgo en el Abismo",
                "options": [
                    {"name": "Reliquia Legendaria", "weight": 2, "desc": "Un artefacto de poder inmenso. +3 stat.",
                     "effects": {"stat_boost": 3, "add_random_item": True, "rep": {"Mages Circle": 3}}},
                    {"name": "Portal Dimensional", "weight": 2, "desc": "Un portal a otra dimension se abre.",
                     "effects": {"add_condition": "dimensional_rift"}},
                    {"name": "Horror Primordial", "weight": 4, "desc": "Algo terrible despierta.",
                     "stat_check_inline": "Durability",
                     "effects": {"stat_damage": 3, "add_condition": "horror_survivor"}},
                    {"name": "Muerte Instantanea", "weight": 2, "desc": "El abismo te consume.",
                     "effects": {"terminal": "death"}}
                ]
            },
            {
                "id": "guardian_fight",
                "label": "Combate contra el Guardian",
                "stat_check": "Strength",
                "options": [
                    {"name": "Derrotas al Guardian", "weight": 4, "desc": "Vences y reclamas su tesoro.",
                     "success_tier": "high",
                     "effects": {"add_random_item": True, "stat_boost": 1, "rep": {"Hunters Lodge": 2}}},
                    {"name": "Victoria Pirrica", "weight": 4, "desc": "Ganas pero malherido.",
                     "success_tier": "mid",
                     "effects": {"add_random_item": True, "stat_damage": 1}},
                    {"name": "Huyes", "weight": 3, "desc": "Escapas por los pelos.",
                     "success_tier": "low",
                     "effects": {"stat_damage": 1}}
                ]
            }
        ]
    },

    # ---- NEGOTIATE A TRADE ----
    "Negotiate a Trade": {
        "blocked_by": "trade_blocked",
        "blocked_message": "El comercio esta bloqueado por piratas. No puedes comerciar ahora.",
        "steps": [
            {
                "id": "choose_goods",
                "label": "Tipo de Mercancia",
                "options": [
                    {"name": "Armas y Armaduras", "weight": 5, "desc": "Equipo militar de calidad.",
                     "stat_weight": {"Strength": 1.2}, "skill_bonus": {"Smithing": 1.5},
                     "next": "haggle", "effects": {"_trade_type": "weapons"}},
                    {"name": "Objetos Magicos", "weight": 3, "desc": "Artefactos y componentes arcanos.",
                     "stat_weight": {"Intelligence": 1.3},
                     "next": "haggle", "effects": {"_trade_type": "magic"}},
                    {"name": "Informacion", "weight": 4, "desc": "Secretos, mapas, y contactos.",
                     "stat_weight": {"Charisma": 1.3}, "skill_bonus": {"Investigation": 1.5},
                     "next": "haggle", "effects": {"_trade_type": "info"}},
                    {"name": "Materiales Raros", "weight": 4, "desc": "Componentes para forja y alquimia.",
                     "skill_bonus": {"Alchemy": 1.5, "Smithing": 1.3},
                     "next": "haggle", "effects": {"_trade_type": "materials"}}
                ]
            },
            {
                "id": "haggle",
                "label": "Negociacion del Precio",
                "stat_check": "Charisma",
                "options": [
                    {"name": "Ganga Increible", "weight": 2, "desc": "Consigues un trato excepcional.",
                     "success_tier": "high",
                     "effects": {"gain_wealth": True, "add_random_item": True, "rep": {"Merchant Guild": 2}}},
                    {"name": "Buen Trato", "weight": 5, "desc": "Un intercambio justo y beneficioso.",
                     "success_tier": "mid",
                     "effects": {"add_random_item": True, "rep": {"Merchant Guild": 1}}},
                    {"name": "Precio Justo", "weight": 5, "desc": "Pagas lo que vale, sin mas.",
                     "success_tier": "mid",
                     "effects": {"add_random_item": True}},
                    {"name": "Te Estafan", "weight": 3, "desc": "El vendedor te engaña vilmente.",
                     "success_tier": "low",
                     "effects": {"lose_wealth": True, "rep": {"Merchant Guild": -1}}}
                ]
            }
        ]
    },

    # ---- INVESTIGATE A MYSTERY ----
    "Investigate a Mystery": {
        "steps": [
            {
                "id": "choose_approach",
                "label": "Metodo de Investigacion",
                "options": [
                    {"name": "Interrogar Testigos", "weight": 5, "desc": "Hablas con quienes vieron algo.",
                     "stat_weight": {"Charisma": 1.5}, "skill_bonus": {"Persuasion": 1.5, "Intimidation": 1.3},
                     "next": "investigate_result"},
                    {"name": "Buscar Pistas Fisicas", "weight": 5, "desc": "Examinas la escena del crimen.",
                     "stat_weight": {"Intelligence": 1.4}, "skill_bonus": {"Investigation": 2.0},
                     "next": "investigate_result"},
                    {"name": "Consultar Archivos", "weight": 4, "desc": "Revisas registros y documentos.",
                     "stat_weight": {"Intelligence": 1.4}, "skill_bonus": {"Investigation": 1.5},
                     "next": "investigate_result"},
                    {"name": "Espionaje Nocturno", "weight": 3, "desc": "Vigilas a los sospechosos de noche.",
                     "stat_weight": {"Agility": 1.4}, "skill_bonus": {"Stealth": 2.0},
                     "next": "investigate_result"}
                ]
            },
            {
                "id": "investigate_result",
                "label": "Resultado de la Investigacion",
                "stat_check": "Intelligence",
                "options": [
                    {"name": "Caso Resuelto!", "weight": 3, "desc": "Descubres la verdad y al culpable.",
                     "success_tier": "high",
                     "effects": {"stat_boost_specific": "Intelligence", "rep": {"The Crown": 2}, "gain_wealth": True}},
                    {"name": "Pista Importante", "weight": 5, "desc": "No resuelves todo, pero avanzas mucho.",
                     "success_tier": "mid",
                     "effects": {"add_condition": "clue_found", "rep": {"The Crown": 1}}},
                    {"name": "Callejon Sin Salida", "weight": 4, "desc": "Las pistas no llevan a nada concreto.",
                     "success_tier": "low",
                     "effects": {}},
                    {"name": "Descubierto por el Culpable", "weight": 2, "desc": "El criminal sabe que lo investigas.",
                     "success_tier": "fail",
                     "effects": {"add_condition": "enemy_alerted", "stat_damage": 1}}
                ]
            }
        ]
    },

    # ---- HEAL THE SICK ----
    "Heal the Sick": {
        "steps": [
            {
                "id": "diagnose",
                "label": "Diagnostico",
                "options": [
                    {"name": "Plaga Comun", "weight": 5, "desc": "Una enfermedad conocida pero grave.",
                     "stat_weight": {"Intelligence": 1.2}, "skill_bonus": {"Medicine": 1.5},
                     "next": "treatment", "effects": {"_disease": "common", "_cure_difficulty": 3}},
                    {"name": "Maldicion Arcana", "weight": 3, "desc": "No es enfermedad, es magia oscura.",
                     "stat_weight": {"Intelligence": 1.4},
                     "requires_magic": True,
                     "next": "treatment", "effects": {"_disease": "curse", "_cure_difficulty": 6}},
                    {"name": "Veneno Raro", "weight": 4, "desc": "Han sido envenenados intencionalmente.",
                     "stat_weight": {"Intelligence": 1.3}, "skill_bonus": {"Alchemy": 2.0},
                     "next": "treatment", "effects": {"_disease": "poison", "_cure_difficulty": 4}}
                ]
            },
            {
                "id": "treatment",
                "label": "Tratamiento",
                "stat_check": "Intelligence",
                "difficulty_key": "_cure_difficulty",
                "options": [
                    {"name": "Cura Milagrosa", "weight": 3, "desc": "Todos se salvan. Eres un heroe.",
                     "success_tier": "high",
                     "effects": {"rep": {"Church of Light": 3}, "stat_boost_specific": "Charisma"}},
                    {"name": "Mayoria Salvados", "weight": 5, "desc": "Salvas a la mayoria de los afectados.",
                     "success_tier": "mid",
                     "effects": {"rep": {"Church of Light": 1}}},
                    {"name": "Pocos Sobreviven", "weight": 4, "desc": "A pesar de tu esfuerzo, muchos mueren.",
                     "success_tier": "low",
                     "effects": {"rep": {"Church of Light": -1}}},
                    {"name": "Contagiado", "weight": 2, "desc": "Tu mismo caes enfermo.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 2, "add_condition": "sick"}}
                ]
            }
        ]
    },

    # ---- TALK WITH A STRANGER ----
    "Talk with a Stranger": {
        "steps": [
            {
                "id": "stranger_type",
                "label": "Tipo de Desconocido",
                "options": [
                    {"name": "Mercader Errante", "weight": 5, "desc": "Un comerciante con mercancias exoticas.",
                     "stat_weight": {"Charisma": 1.2},
                     "next": "conversation_result", "effects": {"_stranger": "mercader", "_talk_difficulty": 3}},
                    {"name": "Veterano de Guerra", "weight": 5, "desc": "Un soldado retirado con cicatrices y experiencia.",
                     "stat_weight": {"Strength": 1.2},
                     "next": "conversation_result", "effects": {"_stranger": "veterano", "_talk_difficulty": 4}},
                    {"name": "Hechicero Misterioso", "weight": 3, "desc": "Un mago encapuchado que susurra conjuros.",
                     "stat_weight": {"Intelligence": 1.4},
                     "next": "conversation_result", "effects": {"_stranger": "mago", "_talk_difficulty": 5}},
                    {"name": "Ladron Disfrazado", "weight": 4, "desc": "Alguien cuya sonrisa oculta intenciones oscuras.",
                     "stat_weight": {"Agility": 1.2}, "skill_bonus": {"Perception": 1.5},
                     "next": "conversation_result", "effects": {"_stranger": "ladron", "_talk_difficulty": 5}},
                    {"name": "Noble de Incognito", "weight": 3, "desc": "Un aristocrata viajando sin escolta.",
                     "stat_weight": {"Charisma": 1.3}, "skill_bonus": {"Persuasion": 1.3},
                     "next": "conversation_result", "effects": {"_stranger": "noble", "_talk_difficulty": 4}}
                ]
            },
            {
                "id": "conversation_result",
                "label": "Resultado de la Conversacion",
                "stat_check": "Charisma",
                "difficulty_key": "_talk_difficulty",
                "options": [
                    {"name": "Nuevo Aliado", "weight": 3, "desc": "Ganas un aliado valioso para el futuro.",
                     "success_tier": "high",
                     "effects": {"stat_boost_specific": "Charisma", "add_condition": "has_ally", "rep": {"Merchant Guild": 1}}},
                    {"name": "Informacion Valiosa", "weight": 5, "desc": "Compartes secretos utiles.",
                     "success_tier": "mid",
                     "effects": {"add_condition": "clue_found", "stat_boost": 1}},
                    {"name": "Conversacion Vacia", "weight": 4, "desc": "No sacas nada en limpio.",
                     "success_tier": "low",
                     "effects": {}},
                    {"name": "Te Roban!", "weight": 3, "desc": "El desconocido te roba mientras hablas.",
                     "success_tier": "fail",
                     "effects": {"lose_wealth": True, "rep": {"Thieves Guild": -1}}}
                ]
            }
        ]
    },

    # ---- SEARCH FOR RARE GOODS ----
    "Search for Rare Goods": {
        "steps": [
            {
                "id": "search_location",
                "label": "Donde Buscar",
                "options": [
                    {"name": "Mercado Negro", "weight": 5, "desc": "Bienes prohibidos a precios elevados.",
                     "stat_weight": {"Charisma": 1.2}, "skill_bonus": {"Stealth": 1.3},
                     "next": "search_result", "effects": {"_search_type": "black_market", "_search_difficulty": 4}},
                    {"name": "Caravana Lejana", "weight": 5, "desc": "Una caravana de tierras exoticas.",
                     "stat_weight": {"Charisma": 1.2},
                     "next": "search_result", "effects": {"_search_type": "caravan", "_search_difficulty": 3}},
                    {"name": "Ruinas Comerciales", "weight": 3, "desc": "Restos de un antiguo emporio.",
                     "stat_weight": {"Intelligence": 1.3, "Agility": 1.2},
                     "next": "search_result", "effects": {"_search_type": "ruins", "_search_difficulty": 5}},
                    {"name": "Contacto Secreto", "weight": 4, "desc": "Un informante con conexiones exclusivas.",
                     "stat_weight": {"Charisma": 1.4}, "skill_bonus": {"Persuasion": 1.5},
                     "next": "search_result", "effects": {"_search_type": "contact", "_search_difficulty": 4}}
                ]
            },
            {
                "id": "search_result",
                "label": "Resultado de la Busqueda",
                "stat_check": "Intelligence",
                "difficulty_key": "_search_difficulty",
                "options": [
                    {"name": "Hallazgo Excepcional", "weight": 2, "desc": "Encuentras bienes unicos e invaluables.",
                     "success_tier": "high",
                     "effects": {"add_random_item": True, "gain_wealth": True, "rep": {"Merchant Guild": 2}}},
                    {"name": "Buenos Bienes", "weight": 5, "desc": "Encuentras mercancia de calidad.",
                     "success_tier": "mid",
                     "effects": {"add_random_item": True, "rep": {"Merchant Guild": 1}}},
                    {"name": "Nada Interesante", "weight": 4, "desc": "No encuentras nada que valga la pena.",
                     "success_tier": "low",
                     "effects": {}},
                    {"name": "Trampa de Contrabandistas", "weight": 3, "desc": "Caes en una trampa de criminales.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 1, "lose_wealth": True, "rep": {"Thieves Guild": -1}}}
                ]
            }
        ]
    },

    # ---- ESTABLISH A BUSINESS ----
    "Establish a Business": {
        "steps": [
            {
                "id": "business_type",
                "label": "Tipo de Negocio",
                "options": [
                    {"name": "Taberna", "weight": 5, "desc": "Un lugar de bebida y rumores.",
                     "stat_weight": {"Charisma": 1.4},
                     "next": "business_result", "effects": {"_business": "taberna", "_biz_difficulty": 3}},
                    {"name": "Forja", "weight": 4, "desc": "Un taller para crear armas y armaduras.",
                     "stat_weight": {"Strength": 1.3}, "skill_bonus": {"Smithing": 2.0},
                     "next": "business_result", "effects": {"_business": "forja", "_biz_difficulty": 4}},
                    {"name": "Tienda de Magia", "weight": 3, "desc": "Venta de componentes y hechizos.",
                     "stat_weight": {"Intelligence": 1.4}, "requires_magic": True,
                     "next": "business_result", "effects": {"_business": "magia", "_biz_difficulty": 5}},
                    {"name": "Red de Informantes", "weight": 3, "desc": "Un negocio de secretos y espionaje.",
                     "stat_weight": {"Charisma": 1.3, "Intelligence": 1.2}, "skill_bonus": {"Stealth": 1.3},
                     "next": "business_result", "effects": {"_business": "espionaje", "_biz_difficulty": 6}},
                    {"name": "Casa de Apuestas", "weight": 4, "desc": "Ganancias rapidas con mucho riesgo.",
                     "stat_weight": {"Charisma": 1.2},
                     "next": "business_result", "effects": {"_business": "apuestas", "_biz_difficulty": 4}}
                ]
            },
            {
                "id": "business_result",
                "label": "Resultado del Negocio",
                "stat_check": "Charisma",
                "difficulty_key": "_biz_difficulty",
                "options": [
                    {"name": "Negocio Prospero", "weight": 3, "desc": "Tu negocio florece rapidamente.",
                     "success_tier": "high",
                     "effects": {"gain_wealth": True, "stat_boost_specific": "Charisma", "add_condition": "business_owner", "rep": {"Merchant Guild": 3}}},
                    {"name": "Beneficios Moderados", "weight": 5, "desc": "Funciona, pero sin grandes ganancias.",
                     "success_tier": "mid",
                     "effects": {"gain_wealth": True, "add_condition": "business_owner", "rep": {"Merchant Guild": 1}}},
                    {"name": "Negocio Fallido", "weight": 4, "desc": "Los costos superan los ingresos.",
                     "success_tier": "low",
                     "effects": {"lose_wealth": True}},
                    {"name": "Robado por Competidores", "weight": 2, "desc": "Tu negocio es saboteado y saqueado.",
                     "success_tier": "fail",
                     "effects": {"lose_wealth": True, "stat_damage": 1, "rep": {"Merchant Guild": -2}}}
                ]
            }
        ]
    },

    # ---- GUARD A CARAVAN ----
    "Guard a Caravan": {
        "steps": [
            {
                "id": "threat_type",
                "label": "Tipo de Amenaza",
                "options": [
                    {"name": "Emboscada de Bandidos", "weight": 5, "desc": "Un grupo de bandidos ataca la caravana.",
                     "stat_weight": {"Strength": 1.3},
                     "next": "defense_strategy", "effects": {"_threat": "bandidos", "_threat_difficulty": 4}},
                    {"name": "Bestias Salvajes", "weight": 5, "desc": "Criaturas hambrientas acechan la ruta.",
                     "stat_weight": {"Agility": 1.2}, "skill_bonus": {"Tracking": 1.5},
                     "next": "defense_strategy", "effects": {"_threat": "bestias", "_threat_difficulty": 5}},
                    {"name": "Clima Extremo", "weight": 4, "desc": "Una tormenta devastadora azota el camino.",
                     "stat_weight": {"Durability": 1.4},
                     "next": "defense_strategy", "effects": {"_threat": "clima", "_threat_difficulty": 4}},
                    {"name": "Ejercito Hostil", "weight": 2, "desc": "Soldados enemigos bloquean el paso.",
                     "stat_weight": {"Strength": 1.3, "Intelligence": 1.2},
                     "next": "defense_strategy", "effects": {"_threat": "ejercito", "_threat_difficulty": 7}}
                ]
            },
            {
                "id": "defense_strategy",
                "label": "Estrategia de Defensa",
                "options": [
                    {"name": "Contraemboscada", "weight": 4, "desc": "Preparas tu propia emboscada.",
                     "stat_weight": {"Intelligence": 1.4}, "skill_bonus": {"Tracking": 1.5, "Stealth": 1.3},
                     "next": "caravan_result"},
                    {"name": "Combate Frontal", "weight": 5, "desc": "Enfrentas la amenaza cara a cara.",
                     "stat_weight": {"Strength": 1.5, "Durability": 1.3},
                     "next": "caravan_result"},
                    {"name": "Evasion Rapida", "weight": 4, "desc": "Intentas esquivar la amenaza por rutas alternas.",
                     "stat_weight": {"Agility": 1.5}, "skill_bonus": {"Tracking": 1.3},
                     "next": "caravan_result"},
                    {"name": "Negociar Paso", "weight": 3, "desc": "Intentas dialogar o sobornar.",
                     "stat_weight": {"Charisma": 1.6}, "skill_bonus": {"Persuasion": 1.5},
                     "next": "caravan_result"}
                ]
            },
            {
                "id": "caravan_result",
                "label": "Resultado de la Escolta",
                "stat_check": "Strength",
                "difficulty_key": "_threat_difficulty",
                "options": [
                    {"name": "Caravana Intacta", "weight": 3, "desc": "Proteges la caravana sin perdidas. Gran recompensa.",
                     "success_tier": "high",
                     "effects": {"gain_wealth": True, "stat_boost": 1, "rep": {"Merchant Guild": 3, "Hunters Lodge": 1}}},
                    {"name": "Danos Menores", "weight": 5, "desc": "La caravana llega con algunos danos.",
                     "success_tier": "mid",
                     "effects": {"gain_wealth": True, "rep": {"Merchant Guild": 1}}},
                    {"name": "Perdidas Graves", "weight": 4, "desc": "Gran parte de la mercancia se pierde.",
                     "success_tier": "low",
                     "effects": {"rep": {"Merchant Guild": -1}}},
                    {"name": "Caravana Destruida", "weight": 2, "desc": "La caravana es arrasada. Apenas escapas.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 2, "lose_wealth": True, "rep": {"Merchant Guild": -3}}}
                ]
            }
        ]
    },

    # ---- TRACK A FUGITIVE ----
    "Track a Fugitive": {
        "steps": [
            {
                "id": "fugitive_type",
                "label": "Tipo de Fugitivo",
                "options": [
                    {"name": "Criminal Peligroso", "weight": 5, "desc": "Un asesino en serie buscado por la corona.",
                     "stat_weight": {"Strength": 1.2, "Agility": 1.2},
                     "next": "tracking_method", "effects": {"_fugitive": "criminal", "_fugitive_difficulty": 5}},
                    {"name": "Noble Desertor", "weight": 4, "desc": "Un noble que huye con secretos de estado.",
                     "stat_weight": {"Intelligence": 1.3}, "skill_bonus": {"Investigation": 1.5},
                     "next": "tracking_method", "effects": {"_fugitive": "noble", "_fugitive_difficulty": 4}},
                    {"name": "Mago Renegado", "weight": 3, "desc": "Un hechicero que rompio sus juramentos.",
                     "stat_weight": {"Intelligence": 1.4},
                     "next": "tracking_method", "effects": {"_fugitive": "mago", "_fugitive_difficulty": 7}},
                    {"name": "Espia Enemigo", "weight": 3, "desc": "Un infiltrado de una faccion rival.",
                     "stat_weight": {"Agility": 1.3}, "skill_bonus": {"Stealth": 1.5, "Tracking": 1.3},
                     "next": "tracking_method", "effects": {"_fugitive": "espia", "_fugitive_difficulty": 6}}
                ]
            },
            {
                "id": "tracking_method",
                "label": "Metodo de Rastreo",
                "options": [
                    {"name": "Interrogar Contactos", "weight": 5, "desc": "Presionas a conocidos del fugitivo.",
                     "stat_weight": {"Charisma": 1.4}, "skill_bonus": {"Persuasion": 1.5, "Intimidation": 2.0},
                     "next": "capture_result"},
                    {"name": "Rastrear Huellas", "weight": 5, "desc": "Sigues su rastro fisico.",
                     "stat_weight": {"Agility": 1.3}, "skill_bonus": {"Tracking": 2.5},
                     "next": "capture_result"},
                    {"name": "Magia de Localizacion", "weight": 3, "desc": "Usas hechizos para encontrarlo.",
                     "stat_weight": {"Intelligence": 1.5}, "requires_magic": True,
                     "next": "capture_result"},
                    {"name": "Pagar Informantes", "weight": 4, "desc": "Compras informacion a la red criminal.",
                     "stat_weight": {"Charisma": 1.2},
                     "next": "capture_result", "effects": {"lose_wealth": True, "rep": {"Thieves Guild": 1}}}
                ]
            },
            {
                "id": "capture_result",
                "label": "Resultado de la Captura",
                "stat_check": "Agility",
                "difficulty_key": "_fugitive_difficulty",
                "options": [
                    {"name": "Captura Limpia", "weight": 3, "desc": "Atrapas al fugitivo sin incidentes.",
                     "success_tier": "high",
                     "effects": {"gain_wealth": True, "stat_boost": 1, "rep": {"The Crown": 3, "Hunters Lodge": 1}}},
                    {"name": "Captura Violenta", "weight": 4, "desc": "Lo atrapas pero con una pelea dura.",
                     "success_tier": "mid",
                     "effects": {"gain_wealth": True, "stat_damage": 1, "rep": {"The Crown": 1}}},
                    {"name": "El Fugitivo Escapa", "weight": 4, "desc": "Se te escurre entre los dedos.",
                     "success_tier": "low",
                     "effects": {"add_condition": "fugitive_loose", "rep": {"The Crown": -1}}},
                    {"name": "Emboscada del Fugitivo", "weight": 3, "desc": "Te tiende una trampa y te hiere gravemente.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 2, "add_condition": "wounded"}}
                ]
            }
        ]
    },

    # ---- STUDY AN ANCIENT TOME ----
    "Study an Ancient Tome": {
        "steps": [
            {
                "id": "tome_type",
                "label": "Tipo de Tomo",
                "options": [
                    {"name": "Grimorio de Conjuros", "weight": 4, "desc": "Un libro de hechizos poderosos.",
                     "stat_weight": {"Intelligence": 1.5}, "requires_magic": True,
                     "next": "study_result", "effects": {"_tome": "grimorio", "_study_difficulty": 5}},
                    {"name": "Tratado Alquimico", "weight": 5, "desc": "Formulas para pociones y transmutaciones.",
                     "stat_weight": {"Intelligence": 1.3}, "skill_bonus": {"Alchemy": 2.0},
                     "next": "study_result", "effects": {"_tome": "alquimia", "_study_difficulty": 4}},
                    {"name": "Profecia Antigua", "weight": 3, "desc": "Un texto profetico sobre el fin de los tiempos.",
                     "stat_weight": {"Intelligence": 1.4},
                     "next": "study_result", "effects": {"_tome": "profecia", "_study_difficulty": 6}},
                    {"name": "Diario de Archimago", "weight": 3, "desc": "Las memorias de un mago legendario.",
                     "stat_weight": {"Intelligence": 1.4}, "skill_bonus": {"Investigation": 1.5},
                     "next": "study_result", "effects": {"_tome": "diario", "_study_difficulty": 5}},
                    {"name": "Textos Prohibidos", "weight": 2, "desc": "Conocimiento sellado por la iglesia.",
                     "stat_weight": {"Intelligence": 1.3},
                     "next": "study_result", "effects": {"_tome": "prohibido", "_study_difficulty": 7}}
                ]
            },
            {
                "id": "study_result",
                "label": "Resultado del Estudio",
                "stat_check": "Intelligence",
                "difficulty_key": "_study_difficulty",
                "options": [
                    {"name": "Conocimiento Profundo", "weight": 3, "desc": "Comprendes secretos ocultos del universo.",
                     "success_tier": "high",
                     "effects": {"stat_boost_specific": "Intelligence", "stat_boost": 1, "rep": {"Mages Circle": 3}}},
                    {"name": "Algo Aprendido", "weight": 5, "desc": "Ganas conocimiento util, aunque fragmentario.",
                     "success_tier": "mid",
                     "effects": {"stat_boost_specific": "Intelligence", "rep": {"Mages Circle": 1}}},
                    {"name": "Incomprensible", "weight": 4, "desc": "El texto es demasiado complejo para ti.",
                     "success_tier": "low",
                     "effects": {}},
                    {"name": "Maldicion del Conocimiento", "weight": 2, "desc": "El tomo estaba maldito. Tu mente sufre.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 2, "add_condition": "cursed", "rep": {"Mages Circle": -1}}}
                ]
            }
        ]
    },

    # ---- PERFORM A DARK RITUAL ----
    "Perform a Dark Ritual": {
        "steps": [
            {
                "id": "ritual_type",
                "label": "Tipo de Ritual",
                "options": [
                    {"name": "Invocacion Demoniaca", "weight": 4, "desc": "Invocas a un demonio para negociar.",
                     "stat_weight": {"Intelligence": 1.5},
                     "next": "ritual_result", "effects": {"_ritual": "demonio", "_ritual_difficulty": 7}},
                    {"name": "Resurreccion", "weight": 3, "desc": "Intentas devolver un alma del mas alla.",
                     "stat_weight": {"Intelligence": 1.4},
                     "next": "ritual_result", "effects": {"_ritual": "resurreccion", "_ritual_difficulty": 8}},
                    {"name": "Pacto de Sangre", "weight": 4, "desc": "Sellas un pacto con tu propia sangre.",
                     "stat_weight": {"Durability": 1.3},
                     "next": "ritual_result", "effects": {"_ritual": "pacto", "_ritual_difficulty": 5}},
                    {"name": "Maldicion Dirigida", "weight": 4, "desc": "Lanzas una maldicion sobre tu enemigo.",
                     "stat_weight": {"Intelligence": 1.3, "Charisma": 1.2},
                     "next": "ritual_result", "effects": {"_ritual": "maldicion", "_ritual_difficulty": 5}},
                    {"name": "Ascension Oscura", "weight": 1, "desc": "Intentas absorber poder de las sombras.",
                     "stat_weight": {"Intelligence": 1.5, "Durability": 1.3},
                     "next": "ritual_result", "effects": {"_ritual": "ascension", "_ritual_difficulty": 9}}
                ]
            },
            {
                "id": "ritual_result",
                "label": "Resultado del Ritual",
                "stat_check": "Intelligence",
                "difficulty_key": "_ritual_difficulty",
                "options": [
                    {"name": "Ritual Perfecto", "weight": 2, "desc": "El ritual funciona a la perfeccion. Poder inmenso.",
                     "success_tier": "high",
                     "effects": {"stat_boost": 2, "add_condition": "dark_empowered", "rep": {"Shadow Council": 3, "Church of Light": -2}}},
                    {"name": "Exito Parcial", "weight": 4, "desc": "Funciona, pero algo salio diferente a lo esperado.",
                     "success_tier": "mid",
                     "effects": {"stat_boost": 1, "rep": {"Shadow Council": 1, "Church of Light": -1}}},
                    {"name": "Fallo Contenido", "weight": 4, "desc": "El ritual falla pero contienes el dano.",
                     "success_tier": "low",
                     "effects": {"stat_damage": 1}},
                    {"name": "Catastrofe Ritual", "weight": 3, "desc": "La energia descontrolada te devasta.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 3, "add_condition": "cursed", "rep": {"Shadow Council": -1}}},
                    {"name": "Posesion Demoniaca", "weight": 1, "desc": "Algo oscuro toma control de tu cuerpo.",
                     "success_tier": "fail",
                     "effects": {"terminal": "death"}}
                ]
            }
        ]
    },

    # ---- INFILTRATE A STRONGHOLD ----
    "Infiltrate a Stronghold": {
        "steps": [
            {
                "id": "entry_method",
                "label": "Metodo de Entrada",
                "options": [
                    {"name": "Disfraz", "weight": 5, "desc": "Te haces pasar por alguien autorizado.",
                     "stat_weight": {"Charisma": 1.5}, "skill_bonus": {"Disguise": 2.0},
                     "next": "infiltrate_objective"},
                    {"name": "Tuneles Subterraneos", "weight": 4, "desc": "Encuentras pasadizos secretos.",
                     "stat_weight": {"Intelligence": 1.3}, "skill_bonus": {"Investigation": 1.5},
                     "next": "infiltrate_objective"},
                    {"name": "Soborno a Guardias", "weight": 4, "desc": "Pagas para que miren a otro lado.",
                     "stat_weight": {"Charisma": 1.3},
                     "next": "infiltrate_objective", "effects": {"lose_wealth": True}},
                    {"name": "Escalada Nocturna", "weight": 4, "desc": "Escalas los muros bajo el amparo de la noche.",
                     "stat_weight": {"Agility": 1.6}, "skill_bonus": {"Stealth": 2.0},
                     "next": "infiltrate_objective"},
                    {"name": "Magia de Invisibilidad", "weight": 2, "desc": "Te vuelves invisible magicamente.",
                     "stat_weight": {"Intelligence": 1.5}, "requires_magic": True,
                     "next": "infiltrate_objective"}
                ]
            },
            {
                "id": "infiltrate_objective",
                "label": "Objetivo en el Interior",
                "options": [
                    {"name": "Robar un Tesoro", "weight": 5, "desc": "Buscas la camara del tesoro.",
                     "stat_weight": {"Agility": 1.3}, "skill_bonus": {"Lockpicking": 2.0},
                     "next": "infiltrate_result", "effects": {"_objective": "tesoro", "_infil_difficulty": 5}},
                    {"name": "Liberar un Prisionero", "weight": 4, "desc": "Rescatas a alguien de las mazmorras.",
                     "stat_weight": {"Strength": 1.2, "Agility": 1.2},
                     "next": "infiltrate_result", "effects": {"_objective": "prisionero", "_infil_difficulty": 5}},
                    {"name": "Sabotear Defensas", "weight": 3, "desc": "Destruyes fortificaciones desde dentro.",
                     "stat_weight": {"Intelligence": 1.3},
                     "next": "infiltrate_result", "effects": {"_objective": "sabotaje", "_infil_difficulty": 6}},
                    {"name": "Espiar al Enemigo", "weight": 4, "desc": "Recoges informacion vital.",
                     "stat_weight": {"Intelligence": 1.3, "Agility": 1.2}, "skill_bonus": {"Stealth": 1.5},
                     "next": "infiltrate_result", "effects": {"_objective": "espionaje", "_infil_difficulty": 4}}
                ]
            },
            {
                "id": "infiltrate_result",
                "label": "Resultado de la Infiltracion",
                "stat_check": "Agility",
                "difficulty_key": "_infil_difficulty",
                "options": [
                    {"name": "Mision Perfecta", "weight": 3, "desc": "Completas el objetivo sin ser detectado.",
                     "success_tier": "high",
                     "effects": {"stat_boost": 1, "gain_wealth": True, "rep": {"Thieves Guild": 3}}},
                    {"name": "Exito con Complicaciones", "weight": 4, "desc": "Lo logras pero te detectan al salir.",
                     "success_tier": "mid",
                     "effects": {"gain_wealth": True, "add_condition": "enemy_alerted", "rep": {"Thieves Guild": 1}}},
                    {"name": "Descubierto y Perseguido", "weight": 4, "desc": "Te detectan y debes huir.",
                     "success_tier": "low",
                     "effects": {"stat_damage": 1, "add_condition": "enemy_alerted"}},
                    {"name": "Capturado", "weight": 3, "desc": "Te atrapan y te encierran.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 2, "add_condition": "imprisoned", "rep": {"The Crown": -2}}}
                ]
            }
        ]
    },

    # ---- COMPETE IN A TOURNAMENT ----
    "Compete in a Tournament": {
        "steps": [
            {
                "id": "tournament_type",
                "label": "Tipo de Torneo",
                "options": [
                    {"name": "Combate Cuerpo a Cuerpo", "weight": 5, "desc": "Lucha sin armas en la arena.",
                     "stat_weight": {"Strength": 1.5, "Durability": 1.3},
                     "next": "tournament_round", "effects": {"_tournament": "melee", "_tourn_difficulty": 5}},
                    {"name": "Duelo de Espadas", "weight": 5, "desc": "Enfrentamientos uno contra uno con armas.",
                     "stat_weight": {"Strength": 1.3, "Agility": 1.3},
                     "next": "tournament_round", "effects": {"_tournament": "swords", "_tourn_difficulty": 5}},
                    {"name": "Tiro con Arco", "weight": 4, "desc": "Competencia de precision a distancia.",
                     "stat_weight": {"Agility": 1.6}, "skill_bonus": {"Archery": 2.5},
                     "next": "tournament_round", "effects": {"_tournament": "archery", "_tourn_difficulty": 4}},
                    {"name": "Justa a Caballo", "weight": 3, "desc": "Cargas a caballo con lanza.",
                     "stat_weight": {"Strength": 1.4, "Agility": 1.2},
                     "next": "tournament_round", "effects": {"_tournament": "joust", "_tourn_difficulty": 6}},
                    {"name": "Duelo de Magia", "weight": 2, "desc": "Un torneo de hechiceros.",
                     "stat_weight": {"Intelligence": 1.6}, "requires_magic": True,
                     "next": "tournament_round", "effects": {"_tournament": "magic", "_tourn_difficulty": 6}}
                ]
            },
            {
                "id": "tournament_round",
                "label": "Ronda Final",
                "stat_check": "Strength",
                "difficulty_key": "_tourn_difficulty",
                "options": [
                    {"name": "Campeon!", "weight": 3, "desc": "Vences a todos los rivales. Eres el campeon!",
                     "success_tier": "high",
                     "effects": {"stat_boost": 2, "gain_wealth": True, "add_condition": "tournament_champion", "rep": {"Hunters Lodge": 3, "The Crown": 2}}},
                    {"name": "Finalista", "weight": 4, "desc": "Llegas a la final pero pierdes el ultimo combate.",
                     "success_tier": "mid",
                     "effects": {"stat_boost": 1, "rep": {"Hunters Lodge": 1}}},
                    {"name": "Eliminado en Semifinal", "weight": 4, "desc": "Un rival fuerte te derrota antes de la final.",
                     "success_tier": "low",
                     "effects": {"rep": {"Hunters Lodge": -1}}},
                    {"name": "Descalificado", "weight": 2, "desc": "Te acusan de hacer trampa. Humillacion publica.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 1, "rep": {"Hunters Lodge": -2, "The Crown": -1}}},
                    {"name": "Herido Gravemente", "weight": 2, "desc": "Un golpe brutal te deja malherido.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 2, "add_condition": "wounded"}}
                ]
            }
        ]
    },

    # ---- LEAD A REBELLION ----
    "Lead a Rebellion": {
        "steps": [
            {
                "id": "rebellion_strategy",
                "label": "Estrategia de Rebelion",
                "options": [
                    {"name": "Asalto Directo", "weight": 4, "desc": "Atacas el centro de poder directamente.",
                     "stat_weight": {"Strength": 1.5, "Durability": 1.3},
                     "next": "rebellion_result", "effects": {"_strategy": "asalto", "_rebel_difficulty": 7}},
                    {"name": "Subversion Interna", "weight": 4, "desc": "Corroes el poder desde dentro.",
                     "stat_weight": {"Intelligence": 1.4, "Charisma": 1.3}, "skill_bonus": {"Persuasion": 1.5},
                     "next": "rebellion_result", "effects": {"_strategy": "subversion", "_rebel_difficulty": 6}},
                    {"name": "Alianza con Bandidos", "weight": 3, "desc": "Te alias con elementos criminales.",
                     "stat_weight": {"Charisma": 1.3},
                     "next": "rebellion_result", "effects": {"_strategy": "bandidos", "_rebel_difficulty": 5, "rep": {"Thieves Guild": 1}}},
                    {"name": "Propaganda Popular", "weight": 4, "desc": "Ganas al pueblo con discursos y promesas.",
                     "stat_weight": {"Charisma": 1.6}, "skill_bonus": {"Persuasion": 2.0},
                     "next": "rebellion_result", "effects": {"_strategy": "propaganda", "_rebel_difficulty": 5}},
                    {"name": "Asesinato Politico", "weight": 2, "desc": "Eliminas al lider enemigo directamente.",
                     "stat_weight": {"Agility": 1.5}, "skill_bonus": {"Stealth": 2.0},
                     "next": "rebellion_result", "effects": {"_strategy": "asesinato", "_rebel_difficulty": 8}}
                ]
            },
            {
                "id": "rebellion_result",
                "label": "Resultado de la Rebelion",
                "stat_check": "Charisma",
                "difficulty_key": "_rebel_difficulty",
                "options": [
                    {"name": "Victoria Revolucionaria", "weight": 2, "desc": "El regimen cae. Eres el nuevo lider.",
                     "success_tier": "high",
                     "effects": {"stat_boost": 2, "gain_wealth": True, "add_condition": "rebel_leader", "rep": {"The Crown": -3, "Shadow Council": 2}}},
                    {"name": "Control Parcial", "weight": 4, "desc": "Ganas terreno pero el conflicto continua.",
                     "success_tier": "mid",
                     "effects": {"stat_boost": 1, "add_condition": "rebellion_ongoing", "rep": {"The Crown": -2}}},
                    {"name": "Represion Brutal", "weight": 4, "desc": "El poder contraataca con fuerza.",
                     "success_tier": "low",
                     "effects": {"stat_damage": 1, "add_condition": "wanted_rebel", "rep": {"The Crown": -1}}},
                    {"name": "Aplastados", "weight": 3, "desc": "La rebelion es destruida sin piedad.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 3, "add_condition": "wanted_rebel", "rep": {"The Crown": -3}}},
                    {"name": "Ejecutado!", "weight": 1, "desc": "Te capturan y te ejecutan publicamente.",
                     "success_tier": "fail",
                     "effects": {"terminal": "death"}}
                ]
            }
        ]
    },

    # ---- SERVE AT COURT ----
    "Serve at Court": {
        "steps": [
            {
                "id": "court_role",
                "label": "Tu Rol en la Corte",
                "options": [
                    {"name": "Consejero del Rey", "weight": 4, "desc": "Asesoras al monarca en decisiones criticas.",
                     "stat_weight": {"Intelligence": 1.5, "Charisma": 1.3},
                     "next": "court_intrigue", "effects": {"_role": "consejero", "_court_difficulty": 5}},
                    {"name": "Embajador Diplomatico", "weight": 4, "desc": "Representas la corona ante facciones extranjeras.",
                     "stat_weight": {"Charisma": 1.6}, "skill_bonus": {"Persuasion": 2.0},
                     "next": "court_intrigue", "effects": {"_role": "embajador", "_court_difficulty": 5}},
                    {"name": "Espia de la Corte", "weight": 3, "desc": "Vigilas y descubres conspiraciones.",
                     "stat_weight": {"Agility": 1.3, "Intelligence": 1.3}, "skill_bonus": {"Stealth": 1.5},
                     "next": "court_intrigue", "effects": {"_role": "espia", "_court_difficulty": 6}},
                    {"name": "Organizador de Eventos", "weight": 4, "desc": "Planificas banquetes y ceremonias.",
                     "stat_weight": {"Charisma": 1.4},
                     "next": "court_intrigue", "effects": {"_role": "organizador", "_court_difficulty": 3}},
                    {"name": "Guardia Personal", "weight": 3, "desc": "Proteges la vida del monarca.",
                     "stat_weight": {"Strength": 1.4, "Agility": 1.3},
                     "next": "court_intrigue", "effects": {"_role": "guardia", "_court_difficulty": 5}}
                ]
            },
            {
                "id": "court_intrigue",
                "label": "Intrigas de la Corte",
                "options": [
                    {"name": "Conspiracion Descubierta", "weight": 4, "desc": "Descubres un complot contra el rey.",
                     "stat_weight": {"Intelligence": 1.4}, "skill_bonus": {"Investigation": 1.5},
                     "next": "court_result", "effects": {"_intrigue": "conspiracion"}},
                    {"name": "Rival Politico", "weight": 5, "desc": "Un noble poderoso te desafia.",
                     "stat_weight": {"Charisma": 1.3},
                     "next": "court_result", "effects": {"_intrigue": "rival"}},
                    {"name": "Oferta de Soborno", "weight": 4, "desc": "Te ofrecen oro a cambio de traicion.",
                     "stat_weight": {"Charisma": 1.2},
                     "next": "court_result", "effects": {"_intrigue": "soborno"}},
                    {"name": "Romance Prohibido", "weight": 3, "desc": "Te involucras emocionalmente con alguien poderoso.",
                     "stat_weight": {"Charisma": 1.5},
                     "next": "court_result", "effects": {"_intrigue": "romance"}}
                ]
            },
            {
                "id": "court_result",
                "label": "Resultado en la Corte",
                "stat_check": "Charisma",
                "difficulty_key": "_court_difficulty",
                "options": [
                    {"name": "Favor del Rey", "weight": 3, "desc": "El monarca te recompensa con poder y tierras.",
                     "success_tier": "high",
                     "effects": {"stat_boost_specific": "Charisma", "gain_wealth": True, "rep": {"The Crown": 4}}},
                    {"name": "Reconocimiento Publico", "weight": 5, "desc": "Tu trabajo es reconocido positivamente.",
                     "success_tier": "mid",
                     "effects": {"rep": {"The Crown": 2}, "gain_wealth": True}},
                    {"name": "Pasas Desapercibido", "weight": 4, "desc": "Tu servicio no impresiona a nadie.",
                     "success_tier": "low",
                     "effects": {}},
                    {"name": "Caida en Desgracia", "weight": 2, "desc": "Caes en una trampa politica y pierdes todo.",
                     "success_tier": "fail",
                     "effects": {"lose_wealth": True, "stat_damage": 1, "rep": {"The Crown": -3}, "add_condition": "disgraced"}}
                ]
            }
        ]
    },

    # ---- ATTEMPT APOTHEOSIS ----
    "Attempt Apotheosis": {
        "steps": [
            {
                "id": "path_to_godhood",
                "label": "Camino a la Divinidad",
                "options": [
                    {"name": "Ritual Supremo", "weight": 4, "desc": "Un ritual milenario para ascender.",
                     "stat_weight": {"Intelligence": 1.6},
                     "next": "apotheosis_trial", "effects": {"_path": "ritual", "_apo_difficulty": 8}},
                    {"name": "Absorber Poder Divino", "weight": 3, "desc": "Intentas robar poder a un dios menor.",
                     "stat_weight": {"Strength": 1.3, "Intelligence": 1.4},
                     "next": "apotheosis_trial", "effects": {"_path": "absorcion", "_apo_difficulty": 9}},
                    {"name": "Sacrificio de Seguidores", "weight": 3, "desc": "El poder de las almas como combustible.",
                     "stat_weight": {"Charisma": 1.3},
                     "next": "apotheosis_trial", "effects": {"_path": "sacrificio", "_apo_difficulty": 7, "rep": {"Church of Light": -3}}},
                    {"name": "Prueba de los Dioses", "weight": 2, "desc": "Los dioses mismos te someten a pruebas.",
                     "stat_weight": {"Durability": 1.4, "Intelligence": 1.3},
                     "next": "apotheosis_trial", "effects": {"_path": "prueba", "_apo_difficulty": 10}}
                ]
            },
            {
                "id": "apotheosis_trial",
                "label": "Prueba Final de Ascension",
                "stat_check": "Intelligence",
                "difficulty_key": "_apo_difficulty",
                "options": [
                    {"name": "Ascendes a la Divinidad!", "weight": 1, "desc": "Te conviertes en un nuevo dios. Tu leyenda es eterna.",
                     "success_tier": "high",
                     "effects": {"terminal": "victory"}},
                    {"name": "Semidivinidad", "weight": 3, "desc": "No llegas a dios, pero ganas poder inmenso.",
                     "success_tier": "mid",
                     "effects": {"stat_boost": 3, "add_condition": "semidivine", "rep": {"Mages Circle": 3, "Church of Light": -2}}},
                    {"name": "Fallo Monumental", "weight": 4, "desc": "Tu cuerpo no puede contener tanto poder.",
                     "success_tier": "low",
                     "effects": {"stat_damage": 3, "add_condition": "cursed"}},
                    {"name": "Destruccion Total", "weight": 3, "desc": "El intento te consume completamente.",
                     "success_tier": "fail",
                     "effects": {"terminal": "death"}}
                ]
            }
        ]
    },

    # ---- EVENT CHAINS ----

    # ---- BANDIT RAID ----
    "Bandit Raid": {
        "steps": [
            {
                "id": "raid_response",
                "label": "Respuesta al Asalto",
                "options": [
                    {"name": "Defender la Posicion", "weight": 5, "desc": "Te atrincheras y luchas.",
                     "stat_weight": {"Strength": 1.4, "Durability": 1.3},
                     "next": "raid_result", "effects": {"_response": "defender"}},
                    {"name": "Contraataque Sorpresa", "weight": 4, "desc": "Les das la vuelta con un ataque inesperado.",
                     "stat_weight": {"Agility": 1.4, "Intelligence": 1.2}, "skill_bonus": {"Stealth": 1.5},
                     "next": "raid_result", "effects": {"_response": "contraataque"}},
                    {"name": "Negociar con el Lider", "weight": 3, "desc": "Intentas hablar con el jefe bandido.",
                     "stat_weight": {"Charisma": 1.6}, "skill_bonus": {"Persuasion": 1.5},
                     "next": "raid_result", "effects": {"_response": "negociar"}},
                    {"name": "Organizar a los Civiles", "weight": 4, "desc": "Organizas la defensa del pueblo.",
                     "stat_weight": {"Charisma": 1.3, "Intelligence": 1.2},
                     "next": "raid_result", "effects": {"_response": "organizar"}}
                ]
            },
            {
                "id": "raid_result",
                "label": "Resultado del Asalto",
                "stat_check": "Strength",
                "options": [
                    {"name": "Bandidos Derrotados", "weight": 3, "desc": "Los bandidos huyen derrotados.",
                     "success_tier": "high",
                     "effects": {"stat_boost": 1, "gain_wealth": True, "rep": {"The Crown": 2, "Hunters Lodge": 1}}},
                    {"name": "Victoria con Bajas", "weight": 5, "desc": "Ganas, pero hay perdidas considerables.",
                     "success_tier": "mid",
                     "effects": {"stat_damage": 1, "rep": {"The Crown": 1}}},
                    {"name": "Empate Sangriento", "weight": 4, "desc": "Ambos bandos sufren, nadie gana claramente.",
                     "success_tier": "low",
                     "effects": {"stat_damage": 1}},
                    {"name": "Saqueo Total", "weight": 2, "desc": "Los bandidos arrasan con todo.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 2, "lose_wealth": True, "rep": {"The Crown": -1}}}
                ]
            }
        ]
    },

    # ---- DRAGON SIGHTING ----
    "Dragon Sighting": {
        "steps": [
            {
                "id": "dragon_approach",
                "label": "Como Enfrentar al Dragon",
                "options": [
                    {"name": "Cazar al Dragon", "weight": 4, "desc": "Intentas abatir a la bestia legendaria.",
                     "stat_weight": {"Strength": 1.5, "Durability": 1.3},
                     "next": "dragon_result", "effects": {"_approach": "cazar", "_dragon_difficulty": 9}},
                    {"name": "Negociar con el Dragon", "weight": 3, "desc": "Los dragones son inteligentes. Intentas hablar.",
                     "stat_weight": {"Charisma": 1.4, "Intelligence": 1.3},
                     "next": "dragon_result", "effects": {"_approach": "negociar", "_dragon_difficulty": 7}},
                    {"name": "Evacuar la Zona", "weight": 5, "desc": "Organizas la evacuacion de la region.",
                     "stat_weight": {"Charisma": 1.3, "Intelligence": 1.2},
                     "next": "dragon_result", "effects": {"_approach": "evacuar", "_dragon_difficulty": 4}},
                    {"name": "Buscar su Guarida", "weight": 3, "desc": "Buscas su nido para encontrar tesoros.",
                     "stat_weight": {"Agility": 1.4, "Intelligence": 1.3}, "skill_bonus": {"Tracking": 2.0, "Stealth": 1.5},
                     "next": "dragon_result", "effects": {"_approach": "guarida", "_dragon_difficulty": 8}}
                ]
            },
            {
                "id": "dragon_result",
                "label": "Resultado del Encuentro",
                "stat_check": "Strength",
                "difficulty_key": "_dragon_difficulty",
                "options": [
                    {"name": "Triunfo Legendario", "weight": 2, "desc": "Logras lo imposible. Tu nombre sera recordado.",
                     "success_tier": "high",
                     "effects": {"stat_boost": 3, "add_random_item": True, "rep": {"Hunters Lodge": 4, "The Crown": 2}}},
                    {"name": "Exito Parcial", "weight": 4, "desc": "No es perfecto, pero sobrevives con ganancias.",
                     "success_tier": "mid",
                     "effects": {"stat_boost": 1, "rep": {"Hunters Lodge": 1}}},
                    {"name": "Retirada Necesaria", "weight": 4, "desc": "El dragon es demasiado. Apenas escapas.",
                     "success_tier": "low",
                     "effects": {"stat_damage": 1, "add_condition": "dragon_fear"}},
                    {"name": "Calcinado", "weight": 2, "desc": "El fuego del dragon te alcanza de lleno.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 3, "add_condition": "burned"}},
                    {"name": "Devorado", "weight": 1, "desc": "El dragon te consume entero.",
                     "success_tier": "fail",
                     "effects": {"terminal": "death"}}
                ]
            }
        ]
    },

    # ---- DEMONIC RIFT ----
    "Demonic Rift": {
        "steps": [
            {
                "id": "rift_response",
                "label": "Respuesta al Portal",
                "options": [
                    {"name": "Cerrar el Portal", "weight": 4, "desc": "Intentas sellar la grieta dimensional.",
                     "stat_weight": {"Intelligence": 1.5}, "requires_magic": True,
                     "next": "rift_result", "effects": {"_response": "cerrar", "_rift_difficulty": 7}},
                    {"name": "Combatir Demonios", "weight": 5, "desc": "Luchas contra las criaturas que emergen.",
                     "stat_weight": {"Strength": 1.5, "Durability": 1.3},
                     "next": "rift_result", "effects": {"_response": "combatir", "_rift_difficulty": 6}},
                    {"name": "Aprovechar su Poder", "weight": 3, "desc": "Absorbes energia del portal.",
                     "stat_weight": {"Intelligence": 1.4},
                     "next": "rift_result", "effects": {"_response": "absorber", "_rift_difficulty": 8}},
                    {"name": "Evacuar y Vigilar", "weight": 4, "desc": "Alejas a la gente y observas.",
                     "stat_weight": {"Intelligence": 1.2, "Charisma": 1.2},
                     "next": "rift_result", "effects": {"_response": "vigilar", "_rift_difficulty": 3}}
                ]
            },
            {
                "id": "rift_result",
                "label": "Resultado del Portal",
                "stat_check": "Intelligence",
                "difficulty_key": "_rift_difficulty",
                "options": [
                    {"name": "Portal Sellado", "weight": 3, "desc": "El portal se cierra. La amenaza termina.",
                     "success_tier": "high",
                     "effects": {"stat_boost": 2, "rep": {"Church of Light": 3, "Mages Circle": 2}}},
                    {"name": "Contencion Parcial", "weight": 4, "desc": "Reduces la amenaza pero el portal persiste.",
                     "success_tier": "mid",
                     "effects": {"stat_boost": 1, "add_condition": "rift_unstable", "rep": {"Church of Light": 1}}},
                    {"name": "Contaminacion Oscura", "weight": 3, "desc": "La energia demoniaca te afecta.",
                     "success_tier": "low",
                     "effects": {"stat_damage": 1, "add_condition": "corrupted"}},
                    {"name": "Explosion Infernal", "weight": 2, "desc": "El portal explota en energia caosica.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 3, "rep": {"Church of Light": -2}}}
                ]
            }
        ]
    },

    # ---- MERCHANT GUILD OFFER ----
    "Merchant Guild Offer": {
        "steps": [
            {
                "id": "offer_type",
                "label": "Tipo de Oferta",
                "options": [
                    {"name": "Contrato Comercial", "weight": 5, "desc": "Una ruta comercial lucrativa.",
                     "stat_weight": {"Charisma": 1.3},
                     "next": "offer_result", "effects": {"_offer": "contrato", "_offer_difficulty": 4}},
                    {"name": "Mision de Escolta", "weight": 4, "desc": "Proteger un envio valioso.",
                     "stat_weight": {"Strength": 1.3},
                     "next": "offer_result", "effects": {"_offer": "escolta", "_offer_difficulty": 5}},
                    {"name": "Inversion Arriesgada", "weight": 3, "desc": "Una apuesta financiera con grandes retornos.",
                     "stat_weight": {"Intelligence": 1.3},
                     "next": "offer_result", "effects": {"_offer": "inversion", "_offer_difficulty": 5}},
                    {"name": "Eliminar Competencia", "weight": 3, "desc": "Trabajo sucio contra rivales del gremio.",
                     "stat_weight": {"Agility": 1.3}, "skill_bonus": {"Stealth": 1.5},
                     "next": "offer_result", "effects": {"_offer": "eliminar", "_offer_difficulty": 6}}
                ]
            },
            {
                "id": "offer_result",
                "label": "Resultado de la Oferta",
                "stat_check": "Charisma",
                "difficulty_key": "_offer_difficulty",
                "options": [
                    {"name": "Gran Beneficio", "weight": 3, "desc": "El negocio sale redondo. Ganancias excelentes.",
                     "success_tier": "high",
                     "effects": {"gain_wealth": True, "stat_boost": 1, "rep": {"Merchant Guild": 3}}},
                    {"name": "Beneficio Moderado", "weight": 5, "desc": "Ganas algo, pero no tanto como esperabas.",
                     "success_tier": "mid",
                     "effects": {"gain_wealth": True, "rep": {"Merchant Guild": 1}}},
                    {"name": "Sin Ganancias", "weight": 4, "desc": "El trato no lleva a nada concreto.",
                     "success_tier": "low",
                     "effects": {}},
                    {"name": "Estafa del Gremio", "weight": 2, "desc": "Te usan como peon desechable.",
                     "success_tier": "fail",
                     "effects": {"lose_wealth": True, "stat_damage": 1, "rep": {"Merchant Guild": -2}}}
                ]
            }
        ]
    },

    # ---- NOBLE SUMMONS ----
    "Noble Summons": {
        "steps": [
            {
                "id": "summons_mission",
                "label": "Mision de la Nobleza",
                "options": [
                    {"name": "Escoltar al Heredero", "weight": 4, "desc": "Proteger al heredero en un viaje peligroso.",
                     "stat_weight": {"Strength": 1.3, "Agility": 1.2},
                     "next": "summons_result", "effects": {"_mission": "escolta", "_summons_difficulty": 5}},
                    {"name": "Negociacion Diplomatica", "weight": 4, "desc": "Representar la casa noble en negociaciones.",
                     "stat_weight": {"Charisma": 1.5}, "skill_bonus": {"Persuasion": 2.0},
                     "next": "summons_result", "effects": {"_mission": "diplomacia", "_summons_difficulty": 5}},
                    {"name": "Investigar Traicion", "weight": 3, "desc": "Descubrir un traidor entre la nobleza.",
                     "stat_weight": {"Intelligence": 1.4}, "skill_bonus": {"Investigation": 1.5},
                     "next": "summons_result", "effects": {"_mission": "traicion", "_summons_difficulty": 6}},
                    {"name": "Recuperar Reliquia Familiar", "weight": 3, "desc": "Encontrar un tesoro ancestral robado.",
                     "stat_weight": {"Agility": 1.3, "Intelligence": 1.2},
                     "next": "summons_result", "effects": {"_mission": "reliquia", "_summons_difficulty": 6}}
                ]
            },
            {
                "id": "summons_result",
                "label": "Resultado de la Mision",
                "stat_check": "Charisma",
                "difficulty_key": "_summons_difficulty",
                "options": [
                    {"name": "Recompensa Real", "weight": 3, "desc": "La nobleza te recompensa generosamente.",
                     "success_tier": "high",
                     "effects": {"gain_wealth": True, "stat_boost": 1, "rep": {"The Crown": 3}}},
                    {"name": "Mision Cumplida", "weight": 5, "desc": "Completas la tarea satisfactoriamente.",
                     "success_tier": "mid",
                     "effects": {"rep": {"The Crown": 2}}},
                    {"name": "Resultado Mediocre", "weight": 4, "desc": "La nobleza no esta impresionada.",
                     "success_tier": "low",
                     "effects": {"rep": {"The Crown": -1}}},
                    {"name": "Fracaso Deshonroso", "weight": 2, "desc": "Fallas y la nobleza te castiga.",
                     "success_tier": "fail",
                     "effects": {"lose_wealth": True, "stat_damage": 1, "rep": {"The Crown": -3}}}
                ]
            }
        ]
    },

    # ---- CULT WHISPER ----
    "Cult Whisper": {
        "steps": [
            {
                "id": "cult_response",
                "label": "Respuesta al Culto",
                "options": [
                    {"name": "Unirse al Culto", "weight": 4, "desc": "Aceptas sus enseñanzas oscuras.",
                     "stat_weight": {"Intelligence": 1.3},
                     "next": "cult_result", "effects": {"_response": "unirse", "_cult_difficulty": 4}},
                    {"name": "Infiltrarse como Espia", "weight": 4, "desc": "Finges unirte para descubrir sus planes.",
                     "stat_weight": {"Charisma": 1.4, "Agility": 1.2}, "skill_bonus": {"Stealth": 1.5},
                     "next": "cult_result", "effects": {"_response": "infiltrar", "_cult_difficulty": 6}},
                    {"name": "Denunciar al Culto", "weight": 3, "desc": "Alertas a las autoridades.",
                     "stat_weight": {"Charisma": 1.2},
                     "next": "cult_result", "effects": {"_response": "denunciar", "_cult_difficulty": 3}},
                    {"name": "Robar sus Secretos", "weight": 3, "desc": "Tomas sus textos y huyes.",
                     "stat_weight": {"Agility": 1.5}, "skill_bonus": {"Stealth": 2.0, "Lockpicking": 1.5},
                     "next": "cult_result", "effects": {"_response": "robar", "_cult_difficulty": 5}}
                ]
            },
            {
                "id": "cult_result",
                "label": "Resultado con el Culto",
                "stat_check": "Intelligence",
                "difficulty_key": "_cult_difficulty",
                "options": [
                    {"name": "Poder Oscuro Obtenido", "weight": 3, "desc": "Ganas conocimiento y poder prohibido.",
                     "success_tier": "high",
                     "effects": {"stat_boost": 2, "rep": {"Shadow Council": 3, "Church of Light": -2}}},
                    {"name": "Secretos Revelados", "weight": 4, "desc": "Descubres informacion importante.",
                     "success_tier": "mid",
                     "effects": {"stat_boost": 1, "add_condition": "cult_knowledge", "rep": {"Shadow Council": 1}}},
                    {"name": "Nada Util", "weight": 4, "desc": "El culto resulta ser un fraude.",
                     "success_tier": "low",
                     "effects": {}},
                    {"name": "Maldicion del Culto", "weight": 3, "desc": "El culto te maldice por inmiscuirte.",
                     "success_tier": "fail",
                     "effects": {"add_condition": "cursed", "stat_damage": 1, "rep": {"Shadow Council": -2}}}
                ]
            }
        ]
    },

    # ---- ASSASSINATION ATTEMPT ----
    "Assassination Attempt": {
        "steps": [
            {
                "id": "attack_response",
                "label": "Reaccion al Ataque",
                "options": [
                    {"name": "Contraatacar", "weight": 5, "desc": "Te defiendes y atacas al asesino.",
                     "stat_weight": {"Strength": 1.5, "Agility": 1.3},
                     "next": "assassination_result", "effects": {"_response": "contraatacar"}},
                    {"name": "Esquivar y Huir", "weight": 4, "desc": "Te alejas del peligro rapidamente.",
                     "stat_weight": {"Agility": 1.6}, "skill_bonus": {"Stealth": 1.5},
                     "next": "assassination_result", "effects": {"_response": "huir"}},
                    {"name": "Usar Magia Defensiva", "weight": 3, "desc": "Invocas proteccion magica.",
                     "stat_weight": {"Intelligence": 1.5}, "requires_magic": True,
                     "next": "assassination_result", "effects": {"_response": "magia"}},
                    {"name": "Negociar con el Asesino", "weight": 3, "desc": "Intentas comprar tu vida.",
                     "stat_weight": {"Charisma": 1.5},
                     "next": "assassination_result", "effects": {"_response": "negociar"}}
                ]
            },
            {
                "id": "assassination_result",
                "label": "Resultado del Atentado",
                "stat_check": "Agility",
                "options": [
                    {"name": "Asesino Capturado", "weight": 3, "desc": "Capturas al asesino y descubres quien lo envio.",
                     "success_tier": "high",
                     "effects": {"stat_boost": 1, "add_condition": "knows_enemy", "rep": {"The Crown": 2}}},
                    {"name": "Sobrevives Ileso", "weight": 4, "desc": "Escapas sin heridas graves.",
                     "success_tier": "mid",
                     "effects": {"add_condition": "assassination_survivor"}},
                    {"name": "Herido pero Vivo", "weight": 4, "desc": "El ataque te deja herido.",
                     "success_tier": "low",
                     "effects": {"stat_damage": 1, "add_condition": "wounded"}},
                    {"name": "Herida Mortal", "weight": 2, "desc": "El veneno del asesino es letal.",
                     "success_tier": "fail",
                     "effects": {"terminal": "death"}}
                ]
            }
        ]
    },

    # ---- SHADOW MARKET ----
    "Shadow Market": {
        "steps": [
            {
                "id": "market_action",
                "label": "Accion en el Mercado Negro",
                "options": [
                    {"name": "Comprar Artefactos", "weight": 5, "desc": "Buscas objetos raros y prohibidos.",
                     "stat_weight": {"Intelligence": 1.3}, "skill_bonus": {"Investigation": 1.3},
                     "next": "market_result", "effects": {"_action": "comprar"}},
                    {"name": "Vender Informacion", "weight": 4, "desc": "Vendes secretos al mejor postor.",
                     "stat_weight": {"Charisma": 1.4},
                     "next": "market_result", "effects": {"_action": "vender"}},
                    {"name": "Buscar Contactos", "weight": 4, "desc": "Amplias tu red de informantes.",
                     "stat_weight": {"Charisma": 1.3}, "skill_bonus": {"Persuasion": 1.5},
                     "next": "market_result", "effects": {"_action": "contactos"}},
                    {"name": "Robar a los Vendedores", "weight": 3, "desc": "Intentas robar mercancia.",
                     "stat_weight": {"Agility": 1.5}, "skill_bonus": {"Stealth": 2.0, "Lockpicking": 1.5},
                     "next": "market_result", "effects": {"_action": "robar"}}
                ]
            },
            {
                "id": "market_result",
                "label": "Resultado del Mercado Negro",
                "stat_check": "Charisma",
                "options": [
                    {"name": "Gran Negocio", "weight": 3, "desc": "Consigues exactamente lo que buscabas.",
                     "success_tier": "high",
                     "effects": {"add_random_item": True, "gain_wealth": True, "rep": {"Thieves Guild": 2}}},
                    {"name": "Trato Aceptable", "weight": 5, "desc": "No es perfecto pero sirve.",
                     "success_tier": "mid",
                     "effects": {"add_random_item": True, "rep": {"Thieves Guild": 1}}},
                    {"name": "Sin Suerte", "weight": 4, "desc": "No encuentras nada interesante.",
                     "success_tier": "low",
                     "effects": {}},
                    {"name": "Trampa!", "weight": 2, "desc": "Era una trampa de la guardia o de criminales.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 1, "lose_wealth": True, "rep": {"Thieves Guild": -2}}}
                ]
            }
        ]
    },

    # ---- TRIAL BY COMBAT ----
    "Trial by Combat": {
        "steps": [
            {
                "id": "trial_preparation",
                "label": "Preparacion para el Duelo",
                "options": [
                    {"name": "Aceptar el Desafio", "weight": 5, "desc": "Luchas tu mismo con honor.",
                     "stat_weight": {"Strength": 1.5, "Durability": 1.3},
                     "next": "trial_result", "effects": {"_prep": "personal", "_trial_difficulty": 5}},
                    {"name": "Buscar un Campeon", "weight": 4, "desc": "Contratas a un luchador profesional.",
                     "stat_weight": {"Charisma": 1.3},
                     "next": "trial_result", "effects": {"_prep": "campeon", "_trial_difficulty": 4, "lose_wealth": True}},
                    {"name": "Entrenar Intensamente", "weight": 4, "desc": "Dedicas tiempo a prepararte.",
                     "stat_weight": {"Strength": 1.3, "Agility": 1.2},
                     "next": "trial_result", "effects": {"_prep": "entrenar", "_trial_difficulty": 4}},
                    {"name": "Trucos Sucios", "weight": 3, "desc": "Envenenas el arma o sobornas al juez.",
                     "stat_weight": {"Intelligence": 1.3}, "skill_bonus": {"Stealth": 1.5},
                     "next": "trial_result", "effects": {"_prep": "truco", "_trial_difficulty": 3}}
                ]
            },
            {
                "id": "trial_result",
                "label": "Resultado del Juicio",
                "stat_check": "Strength",
                "difficulty_key": "_trial_difficulty",
                "options": [
                    {"name": "Victoria Heroica", "weight": 3, "desc": "Ganas el duelo con honor y gloria.",
                     "success_tier": "high",
                     "effects": {"stat_boost": 1, "rep": {"Hunters Lodge": 2, "The Crown": 2}}},
                    {"name": "Victoria Ajustada", "weight": 5, "desc": "Ganas por poco. Mantenes tu honor.",
                     "success_tier": "mid",
                     "effects": {"rep": {"The Crown": 1}}},
                    {"name": "Derrota Honrosa", "weight": 4, "desc": "Pierdes pero con dignidad.",
                     "success_tier": "low",
                     "effects": {"stat_damage": 1, "rep": {"The Crown": -1}}},
                    {"name": "Derrota Humillante", "weight": 2, "desc": "Pierdes vergonzosamente.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 2, "rep": {"Hunters Lodge": -2, "The Crown": -2}}},
                    {"name": "Muerte en el Duelo", "weight": 1, "desc": "Tu oponente te asesta un golpe mortal.",
                     "success_tier": "fail",
                     "effects": {"terminal": "death"}}
                ]
            }
        ]
    },

    # ---- FORBIDDEN LIBRARY ----
    "Forbidden Library": {
        "steps": [
            {
                "id": "library_action",
                "label": "Accion en la Biblioteca",
                "options": [
                    {"name": "Estudiar Textos Arcanos", "weight": 5, "desc": "Lees los textos prohibidos.",
                     "stat_weight": {"Intelligence": 1.5}, "skill_bonus": {"Investigation": 1.5},
                     "next": "library_result", "effects": {"_action": "estudiar", "_lib_difficulty": 5}},
                    {"name": "Robar Grimorios", "weight": 4, "desc": "Te llevas los libros mas valiosos.",
                     "stat_weight": {"Agility": 1.4}, "skill_bonus": {"Stealth": 1.5, "Lockpicking": 1.5},
                     "next": "library_result", "effects": {"_action": "robar", "_lib_difficulty": 5}},
                    {"name": "Buscar Hechizo Especifico", "weight": 4, "desc": "Buscas un conjuro concreto.",
                     "stat_weight": {"Intelligence": 1.5}, "requires_magic": True,
                     "next": "library_result", "effects": {"_action": "buscar", "_lib_difficulty": 6}},
                    {"name": "Copiar Mapas Antiguos", "weight": 3, "desc": "Copias cartografia secreta.",
                     "stat_weight": {"Intelligence": 1.3},
                     "next": "library_result", "effects": {"_action": "copiar", "_lib_difficulty": 3}}
                ]
            },
            {
                "id": "library_result",
                "label": "Resultado en la Biblioteca",
                "stat_check": "Intelligence",
                "difficulty_key": "_lib_difficulty",
                "options": [
                    {"name": "Conocimiento Supremo", "weight": 3, "desc": "Descubres secretos que cambian todo.",
                     "success_tier": "high",
                     "effects": {"stat_boost_specific": "Intelligence", "stat_boost": 1, "add_random_item": True, "rep": {"Mages Circle": 3}}},
                    {"name": "Buenos Hallazgos", "weight": 5, "desc": "Encuentras informacion valiosa.",
                     "success_tier": "mid",
                     "effects": {"stat_boost_specific": "Intelligence", "rep": {"Mages Circle": 1}}},
                    {"name": "Textos Ilegibles", "weight": 4, "desc": "No logras descifrar los textos.",
                     "success_tier": "low",
                     "effects": {}},
                    {"name": "Guardian de la Biblioteca", "weight": 2, "desc": "Un guardian magico te ataca.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 2, "rep": {"Mages Circle": -1}}}
                ]
            }
        ]
    },

    # ---- ELVEN ENVOY ----
    "Elven Envoy": {
        "steps": [
            {
                "id": "envoy_request",
                "label": "Peticion del Emisario",
                "options": [
                    {"name": "Alianza Militar", "weight": 4, "desc": "Los elfos buscan aliados contra una amenaza.",
                     "stat_weight": {"Charisma": 1.3, "Strength": 1.2},
                     "next": "envoy_result", "effects": {"_request": "alianza"}},
                    {"name": "Intercambio de Conocimiento", "weight": 4, "desc": "Ofrecen sabiduria a cambio de ayuda.",
                     "stat_weight": {"Intelligence": 1.4},
                     "next": "envoy_result", "effects": {"_request": "conocimiento"}},
                    {"name": "Recuperar Reliquia Elfica", "weight": 3, "desc": "Un artefacto elfico fue robado.",
                     "stat_weight": {"Agility": 1.3}, "skill_bonus": {"Tracking": 1.5},
                     "next": "envoy_result", "effects": {"_request": "reliquia"}},
                    {"name": "Rechazar al Emisario", "weight": 3, "desc": "No te interesan los asuntos elficos.",
                     "effects": {"rep": {"Mages Circle": -1}}}
                ]
            },
            {
                "id": "envoy_result",
                "label": "Resultado con los Elfos",
                "stat_check": "Charisma",
                "options": [
                    {"name": "Alianza Sellada", "weight": 3, "desc": "Los elfos se convierten en aliados fieles.",
                     "success_tier": "high",
                     "effects": {"stat_boost": 1, "add_condition": "elven_ally", "rep": {"Mages Circle": 2}}},
                    {"name": "Cooperacion Limitada", "weight": 5, "desc": "Ayudan pero con reservas.",
                     "success_tier": "mid",
                     "effects": {"rep": {"Mages Circle": 1}}},
                    {"name": "Desconfianza Mutua", "weight": 4, "desc": "No se llega a ningun acuerdo.",
                     "success_tier": "low",
                     "effects": {}},
                    {"name": "Ofensa Diplomatica", "weight": 2, "desc": "Insultas a los elfos sin querer.",
                     "success_tier": "fail",
                     "effects": {"rep": {"Mages Circle": -2}}}
                ]
            }
        ]
    },

    # ---- DWARVEN FORGE FIRE ----
    "Dwarven Forge Fire": {
        "steps": [
            {
                "id": "forge_help",
                "label": "Ayuda en la Forja",
                "options": [
                    {"name": "Ayudar con la Forja", "weight": 5, "desc": "Trabajas junto a los enanos.",
                     "stat_weight": {"Strength": 1.4}, "skill_bonus": {"Smithing": 2.5},
                     "next": "forge_result", "effects": {"_help": "forjar"}},
                    {"name": "Conseguir Materiales", "weight": 4, "desc": "Buscas materiales raros que necesitan.",
                     "stat_weight": {"Agility": 1.3}, "skill_bonus": {"Tracking": 1.5},
                     "next": "forge_result", "effects": {"_help": "materiales"}},
                    {"name": "Proteger la Forja", "weight": 4, "desc": "Defiendes la forja de saboteadores.",
                     "stat_weight": {"Strength": 1.3, "Durability": 1.2},
                     "next": "forge_result", "effects": {"_help": "proteger"}},
                    {"name": "Aportar Magia", "weight": 3, "desc": "Usas magia para potenciar la forja.",
                     "stat_weight": {"Intelligence": 1.5}, "requires_magic": True,
                     "next": "forge_result", "effects": {"_help": "magia"}}
                ]
            },
            {
                "id": "forge_result",
                "label": "Resultado en la Forja Enana",
                "stat_check": "Strength",
                "options": [
                    {"name": "Arma Legendaria", "weight": 3, "desc": "Los enanos te regalan una obra maestra.",
                     "success_tier": "high",
                     "effects": {"add_random_item": True, "stat_boost": 1, "rep": {"Merchant Guild": 2, "Hunters Lodge": 1}}},
                    {"name": "Buen Trabajo", "weight": 5, "desc": "Los enanos estan satisfechos.",
                     "success_tier": "mid",
                     "effects": {"add_random_item": True, "rep": {"Merchant Guild": 1}}},
                    {"name": "Trabajo Mediocre", "weight": 4, "desc": "No cumples las expectativas enanas.",
                     "success_tier": "low",
                     "effects": {}},
                    {"name": "Desastre en la Forja", "weight": 2, "desc": "Causas un accidente que daña la forja.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 1, "rep": {"Merchant Guild": -2}}}
                ]
            }
        ]
    },

    # ---- PLAGUE SIGNS ----
    "Plague Signs": {
        "steps": [
            {
                "id": "plague_response",
                "label": "Respuesta a la Plaga",
                "options": [
                    {"name": "Curar a los Enfermos", "weight": 5, "desc": "Dedicas tu esfuerzo a sanar.",
                     "stat_weight": {"Intelligence": 1.3}, "skill_bonus": {"Medicine": 2.0},
                     "next": "plague_result", "effects": {"_response": "curar", "_plague_difficulty": 5}},
                    {"name": "Buscar el Origen", "weight": 4, "desc": "Investigas la causa de la plaga.",
                     "stat_weight": {"Intelligence": 1.5}, "skill_bonus": {"Investigation": 1.5, "Alchemy": 1.5},
                     "next": "plague_result", "effects": {"_response": "investigar", "_plague_difficulty": 6}},
                    {"name": "Cuarentena Estricta", "weight": 4, "desc": "Impones aislamiento total.",
                     "stat_weight": {"Charisma": 1.3, "Intelligence": 1.2},
                     "next": "plague_result", "effects": {"_response": "cuarentena", "_plague_difficulty": 4}},
                    {"name": "Huir de la Zona", "weight": 3, "desc": "Escapas antes de contagiarte.",
                     "effects": {"rep": {"Church of Light": -2}}}
                ]
            },
            {
                "id": "plague_result",
                "label": "Resultado de la Plaga",
                "stat_check": "Intelligence",
                "difficulty_key": "_plague_difficulty",
                "options": [
                    {"name": "Plaga Erradicada", "weight": 3, "desc": "Tu intervencion salva a cientos de vidas.",
                     "success_tier": "high",
                     "effects": {"stat_boost_specific": "Charisma", "rep": {"Church of Light": 4}}},
                    {"name": "Plaga Contenida", "weight": 5, "desc": "Reduces el impacto significativamente.",
                     "success_tier": "mid",
                     "effects": {"rep": {"Church of Light": 2}}},
                    {"name": "Plaga Persiste", "weight": 4, "desc": "Tus esfuerzos no son suficientes.",
                     "success_tier": "low",
                     "effects": {"add_condition": "plague_active", "rep": {"Church of Light": -1}}},
                    {"name": "Te Contagias", "weight": 2, "desc": "La plaga te alcanza a ti.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 2, "add_condition": "sick"}}
                ]
            }
        ]
    },

    # ---- MYSTIC ECLIPSE ----
    "Mystic Eclipse": {
        "steps": [
            {
                "id": "eclipse_action",
                "label": "Accion durante el Eclipse",
                "options": [
                    {"name": "Realizar un Ritual", "weight": 4, "desc": "Aprovechas el eclipse para un hechizo poderoso.",
                     "stat_weight": {"Intelligence": 1.6}, "requires_magic": True,
                     "next": "eclipse_result", "effects": {"_action": "ritual", "_eclipse_difficulty": 6}},
                    {"name": "Meditar y Absorber", "weight": 4, "desc": "Absorbes la energia cosmica del eclipse.",
                     "stat_weight": {"Intelligence": 1.3, "Durability": 1.2},
                     "next": "eclipse_result", "effects": {"_action": "meditar", "_eclipse_difficulty": 4}},
                    {"name": "Estudiar el Fenomeno", "weight": 5, "desc": "Observas y documentas el evento.",
                     "stat_weight": {"Intelligence": 1.4},
                     "next": "eclipse_result", "effects": {"_action": "estudiar", "_eclipse_difficulty": 3}},
                    {"name": "Proteger a los Demas", "weight": 3, "desc": "Algunos enloquecen. Los proteges.",
                     "stat_weight": {"Charisma": 1.3, "Strength": 1.2},
                     "next": "eclipse_result", "effects": {"_action": "proteger", "_eclipse_difficulty": 4}}
                ]
            },
            {
                "id": "eclipse_result",
                "label": "Resultado del Eclipse",
                "stat_check": "Intelligence",
                "difficulty_key": "_eclipse_difficulty",
                "options": [
                    {"name": "Poder Cosmico", "weight": 3, "desc": "El eclipse te otorga poder increible.",
                     "success_tier": "high",
                     "effects": {"stat_boost": 2, "rep": {"Mages Circle": 3}}},
                    {"name": "Iluminacion Parcial", "weight": 5, "desc": "Ganas algo de poder y conocimiento.",
                     "success_tier": "mid",
                     "effects": {"stat_boost": 1, "rep": {"Mages Circle": 1}}},
                    {"name": "Nada Especial", "weight": 4, "desc": "El eclipse pasa sin efecto para ti.",
                     "success_tier": "low",
                     "effects": {}},
                    {"name": "Locura Temporal", "weight": 2, "desc": "La energia te afecta mentalmente.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 1, "add_condition": "mentally_unstable"}}
                ]
            }
        ]
    },

    # ---- LOST HEIR ----
    "Lost Heir": {
        "steps": [
            {
                "id": "heir_decision",
                "label": "Decision sobre el Heredero",
                "options": [
                    {"name": "Proteger al Heredero", "weight": 5, "desc": "Lo escoltas y proteges.",
                     "stat_weight": {"Strength": 1.3, "Charisma": 1.2},
                     "next": "heir_result", "effects": {"_decision": "proteger"}},
                    {"name": "Vender al Heredero", "weight": 3, "desc": "Lo entregas al mejor postor.",
                     "stat_weight": {"Charisma": 1.3},
                     "next": "heir_result", "effects": {"_decision": "vender"}},
                    {"name": "Usar como Peon Politico", "weight": 4, "desc": "Lo usas para tus propios fines.",
                     "stat_weight": {"Intelligence": 1.4, "Charisma": 1.3},
                     "next": "heir_result", "effects": {"_decision": "peon"}},
                    {"name": "Ignorar al Heredero", "weight": 3, "desc": "No es tu problema.",
                     "effects": {}}
                ]
            },
            {
                "id": "heir_result",
                "label": "Resultado del Heredero",
                "stat_check": "Charisma",
                "options": [
                    {"name": "Recompensa Real", "weight": 3, "desc": "Tu decision te trae grandes beneficios.",
                     "success_tier": "high",
                     "effects": {"gain_wealth": True, "stat_boost": 1, "rep": {"The Crown": 3}}},
                    {"name": "Reconocimiento", "weight": 5, "desc": "Tu accion es reconocida por la nobleza.",
                     "success_tier": "mid",
                     "effects": {"rep": {"The Crown": 1}}},
                    {"name": "Complicaciones", "weight": 4, "desc": "Tu decision trae consecuencias inesperadas.",
                     "success_tier": "low",
                     "effects": {"add_condition": "political_trouble"}},
                    {"name": "Traicion del Heredero", "weight": 2, "desc": "El heredero te traiciona.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 1, "rep": {"The Crown": -2}}}
                ]
            }
        ]
    },

    # ---- ANCIENT MAP ----
    "Ancient Map": {
        "steps": [
            {
                "id": "map_destination",
                "label": "Destino del Mapa",
                "options": [
                    {"name": "Tumba Olvidada", "weight": 5, "desc": "El mapa lleva a una tumba llena de tesoros.",
                     "stat_weight": {"Intelligence": 1.3},
                     "next": "map_result", "effects": {"_dest": "tumba", "_map_difficulty": 5}},
                    {"name": "Ciudad Perdida", "weight": 3, "desc": "Una ciudad antigua oculta en la selva.",
                     "stat_weight": {"Intelligence": 1.4, "Agility": 1.2},
                     "next": "map_result", "effects": {"_dest": "ciudad", "_map_difficulty": 7}},
                    {"name": "Mina Abandonada", "weight": 4, "desc": "Una mina con minerales raros.",
                     "stat_weight": {"Strength": 1.2},
                     "next": "map_result", "effects": {"_dest": "mina", "_map_difficulty": 4}},
                    {"name": "Santuario Secreto", "weight": 3, "desc": "Un templo oculto con poder arcano.",
                     "stat_weight": {"Intelligence": 1.4}, "requires_magic": True,
                     "next": "map_result", "effects": {"_dest": "santuario", "_map_difficulty": 6}}
                ]
            },
            {
                "id": "map_result",
                "label": "Resultado de la Expedicion",
                "stat_check": "Intelligence",
                "difficulty_key": "_map_difficulty",
                "options": [
                    {"name": "Tesoro Legendario", "weight": 2, "desc": "Encuentras riquezas inimaginables.",
                     "success_tier": "high",
                     "effects": {"add_random_item": True, "gain_wealth": True, "stat_boost": 2, "rep": {"Mages Circle": 2}}},
                    {"name": "Buen Botin", "weight": 5, "desc": "Encuentras objetos valiosos.",
                     "success_tier": "mid",
                     "effects": {"add_random_item": True, "rep": {"Mages Circle": 1}}},
                    {"name": "Lugar Saqueado", "weight": 4, "desc": "Alguien llego antes que tu.",
                     "success_tier": "low",
                     "effects": {}},
                    {"name": "Trampa Mortal", "weight": 3, "desc": "El mapa era una trampa elaborada.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 2, "add_condition": "wounded"}}
                ]
            }
        ]
    },

    # ---- HERETICAL SERMON ----
    "Heretical Sermon": {
        "steps": [
            {
                "id": "sermon_response",
                "label": "Respuesta al Sermon",
                "options": [
                    {"name": "Apoyar al Hereje", "weight": 4, "desc": "Sus palabras resuenan contigo.",
                     "stat_weight": {"Charisma": 1.3},
                     "next": "sermon_result", "effects": {"_response": "apoyar"}},
                    {"name": "Denunciar al Hereje", "weight": 4, "desc": "Alertas a la Iglesia.",
                     "stat_weight": {"Charisma": 1.2},
                     "next": "sermon_result", "effects": {"_response": "denunciar"}},
                    {"name": "Debatir Publicamente", "weight": 3, "desc": "Lo desafias intelectualmente.",
                     "stat_weight": {"Intelligence": 1.4, "Charisma": 1.4},
                     "next": "sermon_result", "effects": {"_response": "debatir"}},
                    {"name": "Escuchar en Secreto", "weight": 4, "desc": "Observas desde las sombras.",
                     "stat_weight": {"Agility": 1.2}, "skill_bonus": {"Stealth": 1.3},
                     "next": "sermon_result", "effects": {"_response": "escuchar"}}
                ]
            },
            {
                "id": "sermon_result",
                "label": "Resultado del Sermon",
                "stat_check": "Charisma",
                "options": [
                    {"name": "Influencia Ganada", "weight": 3, "desc": "Tu posicion te gana seguidores.",
                     "success_tier": "high",
                     "effects": {"stat_boost_specific": "Charisma", "rep": {"Church of Light": 2}}},
                    {"name": "Reconocimiento", "weight": 5, "desc": "La gente nota tu intervencion.",
                     "success_tier": "mid",
                     "effects": {"rep": {"Church of Light": 1}}},
                    {"name": "Ignorado", "weight": 4, "desc": "Nadie presta atencion.",
                     "success_tier": "low",
                     "effects": {}},
                    {"name": "Acusado de Hereje", "weight": 2, "desc": "Te acusan de herejia a ti tambien.",
                     "success_tier": "fail",
                     "effects": {"rep": {"Church of Light": -3}, "add_condition": "heretic_accused"}}
                ]
            }
        ]
    },

    # ---- BEAST STAMPEDE ----
    "Beast Stampede": {
        "steps": [
            {
                "id": "stampede_action",
                "label": "Accion ante la Estampida",
                "options": [
                    {"name": "Desviar la Estampida", "weight": 4, "desc": "Intentas redirigir a las bestias.",
                     "stat_weight": {"Intelligence": 1.3, "Agility": 1.3}, "skill_bonus": {"Beast Taming": 2.0},
                     "next": "stampede_result", "effects": {"_action": "desviar"}},
                    {"name": "Cazar las Bestias", "weight": 4, "desc": "Abates a las criaturas mas peligrosas.",
                     "stat_weight": {"Strength": 1.5}, "skill_bonus": {"Tracking": 1.5},
                     "next": "stampede_result", "effects": {"_action": "cazar"}},
                    {"name": "Proteger al Pueblo", "weight": 5, "desc": "Organizas la defensa del asentamiento.",
                     "stat_weight": {"Charisma": 1.3, "Strength": 1.2},
                     "next": "stampede_result", "effects": {"_action": "proteger"}},
                    {"name": "Huir a Terreno Alto", "weight": 4, "desc": "Escapas a un lugar seguro.",
                     "stat_weight": {"Agility": 1.4},
                     "next": "stampede_result", "effects": {"_action": "huir"}}
                ]
            },
            {
                "id": "stampede_result",
                "label": "Resultado de la Estampida",
                "stat_check": "Strength",
                "options": [
                    {"name": "Bestias Controladas", "weight": 3, "desc": "Logras detener la estampida.",
                     "success_tier": "high",
                     "effects": {"stat_boost": 1, "rep": {"Hunters Lodge": 3}}},
                    {"name": "Danos Minimizados", "weight": 5, "desc": "Reduces el impacto considerablemente.",
                     "success_tier": "mid",
                     "effects": {"rep": {"Hunters Lodge": 1}}},
                    {"name": "Danos Severos", "weight": 4, "desc": "La estampida causa destruccion.",
                     "success_tier": "low",
                     "effects": {"stat_damage": 1}},
                    {"name": "Arrasado", "weight": 2, "desc": "Las bestias te pasan por encima.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 3, "add_condition": "wounded"}}
                ]
            }
        ]
    },

    # ---- ORACLE VISION ----
    "Oracle Vision": {
        "steps": [
            {
                "id": "vision_interpretation",
                "label": "Interpretacion de la Vision",
                "options": [
                    {"name": "Aceptar el Destino", "weight": 4, "desc": "Sigues lo que la vision muestra.",
                     "stat_weight": {"Intelligence": 1.3},
                     "next": "vision_result", "effects": {"_interpretation": "aceptar"}},
                    {"name": "Desafiar la Profecia", "weight": 4, "desc": "Intentas cambiar lo que fue visto.",
                     "stat_weight": {"Charisma": 1.3, "Durability": 1.2},
                     "next": "vision_result", "effects": {"_interpretation": "desafiar"}},
                    {"name": "Buscar Mas Respuestas", "weight": 4, "desc": "Investigas el significado profundo.",
                     "stat_weight": {"Intelligence": 1.5}, "skill_bonus": {"Investigation": 1.5},
                     "next": "vision_result", "effects": {"_interpretation": "investigar"}},
                    {"name": "Compartir la Vision", "weight": 3, "desc": "Cuentas lo visto a tus aliados.",
                     "stat_weight": {"Charisma": 1.4},
                     "next": "vision_result", "effects": {"_interpretation": "compartir"}}
                ]
            },
            {
                "id": "vision_result",
                "label": "Resultado de la Vision",
                "stat_check": "Intelligence",
                "options": [
                    {"name": "Profecia Cumplida", "weight": 3, "desc": "La vision se cumple a tu favor.",
                     "success_tier": "high",
                     "effects": {"stat_boost": 2, "add_condition": "destiny_touched", "rep": {"Church of Light": 2, "Mages Circle": 2}}},
                    {"name": "Pistas del Futuro", "weight": 5, "desc": "Ganas perspectiva sobre lo que viene.",
                     "success_tier": "mid",
                     "effects": {"stat_boost": 1, "rep": {"Mages Circle": 1}}},
                    {"name": "Vision Confusa", "weight": 4, "desc": "No logras interpretar la vision correctamente.",
                     "success_tier": "low",
                     "effects": {}},
                    {"name": "Vision Corruptora", "weight": 2, "desc": "La vision te afecta psicologicamente.",
                     "success_tier": "fail",
                     "effects": {"stat_damage": 1, "add_condition": "mentally_unstable"}}
                ]
            }
        ]
    }
}

# ========== CHAIN REPETITION LIMITS ==========
CHAIN_LIMITS = {
    # Unique: only once per run (major one-time events)
    "Attempt Apotheosis": {"unique": True},
    "Dragon Sighting": {"unique": True},
    "Demonic Rift": {"unique": True},
    "Mystic Eclipse": {"unique": True},
    "Lost Heir": {"unique": True},
    "Oracle Vision": {"unique": True},
    "Assassination Attempt": {"unique": True},
    "Trial by Combat": {"unique": True},
    "Pirate Blockade": {"unique": True},
    "Ancient Map": {"unique": True},
    "Forbidden Library": {"unique": True},
    # Limited repeats
    "Lead a Rebellion": {"max_repeats": 2},
    "Compete in a Tournament": {"max_repeats": 2},
    "Serve at Court": {"max_repeats": 2},
    "Establish a Business": {"max_repeats": 1},
    "Perform a Dark Ritual": {"max_repeats": 2},
    "Study an Ancient Tome": {"max_repeats": 3},
    "Infiltrate a Stronghold": {"max_repeats": 2},
    "Track a Fugitive": {"max_repeats": 3},
    "Forge Legendary Gear": {"max_repeats": 2},
    "Heretical Sermon": {"max_repeats": 1},
    "Beast Stampede": {"max_repeats": 2},
    "Cult Whisper": {"max_repeats": 2},
    "Elven Envoy": {"max_repeats": 2},
    "Dwarven Forge Fire": {"max_repeats": 2},
    "Noble Summons": {"max_repeats": 3},
    "Plague Signs": {"max_repeats": 2},
}

# ========== CONDITION DESCRIPTIONS ==========
CONDITION_DESCRIPTIONS = {
    "trade_blocked": "Comercio bloqueado por piratas",
    "pirate_truce": "Tregua temporal con piratas",
    "wounded": "Herido gravemente",
    "cursed": "Maldito por fuerzas oscuras",
    "sick": "Enfermo/contagiado",
    "beast_stalking": "Una bestia te acecha",
    "ancient_map": "Posees un mapa antiguo",
    "dimensional_rift": "Portal dimensional abierto",
    "horror_survivor": "Marcado por un horror primordial",
    "business_owner": "Propietario de un negocio",
    "fugitive_loose": "Un fugitivo sigue suelto",
    "enemy_alerted": "Tu enemigo conoce tus movimientos",
    "imprisoned": "Has estado preso recientemente",
    "disgraced": "Caido en desgracia publica",
    "tournament_champion": "Campeon de torneo",
    "rebel_leader": "Lider de la rebelion",
    "rebellion_ongoing": "Rebelion activa",
    "wanted_rebel": "Buscado como rebelde",
    "dark_empowered": "Imbuido de poder oscuro",
    "semidivine": "Semidivino",
    "clue_found": "Pista importante descubierta",
    "has_ally": "Tienes un aliado valioso",
    "knows_enemy": "Sabes quien es tu enemigo",
    "assassination_survivor": "Sobreviviste un atentado",
    "elven_ally": "Aliado de los elfos",
    "plague_active": "Plaga activa en la region",
    "mentally_unstable": "Inestabilidad mental",
    "cult_knowledge": "Conocimiento oculto del culto",
    "corrupted": "Corrupcion demoniaca",
    "rift_unstable": "Portal dimensional inestable",
    "political_trouble": "Problemas politicos",
    "heretic_accused": "Acusado de herejia",
    "destiny_touched": "Tocado por el destino",
    "dragon_fear": "Terror al dragon",
    "burned": "Quemaduras graves",
}

# ========== CHAIN TITLES (achievements) ==========
CHAIN_TITLES = {
    ("Dragon Sighting", "Triunfo Legendario"): "Mata-Dragones",
    ("Compete in a Tournament", "Campeon!"): "Campeon del Torneo",
    ("Demonic Rift", "Portal Sellado"): "Sellador de Portales",
    ("Assassination Attempt", "Asesino Capturado"): "El Intocable",
    ("Lead a Rebellion", "Victoria Revolucionaria"): "El Libertador",
    ("Attempt Apotheosis", "Semidivinidad"): "Semidios",
    ("Pirate Blockade", "Victoria Aplastante"): "Terror de los Mares",
    ("Hunt a Beast", "Caza Gloriosa"): "Gran Cazador",
    ("Investigate a Mystery", "Caso Resuelto!"): "Detective Supremo",
    ("Serve at Court", "Favor del Rey"): "Favorito del Rey",
    ("Forge Legendary Gear", "Obra Maestra"): "Maestro Forjador",
    ("Heal the Sick", "Cura Milagrosa"): "El Sanador",
    ("Explore Ruins", "Reliquia Legendaria"): "Explorador Legendario",
    ("Infiltrate a Stronghold", "Mision Perfecta"): "La Sombra",
    ("Perform a Dark Ritual", "Ritual Perfecto"): "Senor Oscuro",
    ("Trial by Combat", "Victoria Heroica"): "Campeon del Juicio",
    ("Plague Signs", "Plaga Erradicada"): "Salvador de la Plaga",
    ("Negotiate a Trade", "Ganga Increible"): "Negociador Supremo",
    ("Guard a Caravan", "Caravana Intacta"): "Guardia de Honor",
    ("Track a Fugitive", "Captura Limpia"): "Cazarrecompensas",
    ("Study an Ancient Tome", "Conocimiento Profundo"): "Erudito",
    ("Establish a Business", "Negocio Prospero"): "Magnate",
}

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
    resources = {'gold': 50}
    last_random_event = {'chapter': 0, 'name': None}

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

    # Info panel with separate areas
    info_frame = tk.Frame(main_container, bg='#1a1a2e', relief='groove', bd=2)
    main_container.create_window(1350, 200, window=info_frame, tags='ui_element')

    # Character panel
    tk.Label(info_frame, text='Personaje', font=('Segoe UI', 12, 'bold'),
             fg='#eebc1d', bg='#1a1a2e').pack(fill='x', padx=5, pady=4)
    char_text = scrolledtext.ScrolledText(info_frame, width=28, height=12,
                                         state='disabled', font=('Consolas', 8),
                                         bg='#0f3460', fg='#eebc1d', bd=0)
    char_text.pack(fill='x', padx=3, pady=(0,6))

    # World/Status panel
    tk.Label(info_frame, text='Estado del Mundo', font=('Segoe UI', 12, 'bold'),
             fg='#eebc1d', bg='#1a1a2e').pack(fill='x', padx=5, pady=4)
    world_text = scrolledtext.ScrolledText(info_frame, width=28, height=10,
                                          state='disabled', font=('Consolas', 8),
                                          bg='#0f3460', fg='#eebc1d', bd=0)
    world_text.pack(fill='x', padx=3, pady=(0,6))

    # Log panel
    tk.Label(info_frame, text='Registro', font=('Segoe UI', 12, 'bold'),
             fg='#eebc1d', bg='#1a1a2e').pack(fill='x', padx=5, pady=4)
    log_text = scrolledtext.ScrolledText(info_frame, width=28, height=8,
                                        state='disabled', font=('Consolas', 8),
                                        bg='#0f3460', fg='#eebc1d', bd=0)
    log_text.pack(fill='x', padx=3, pady=(0,6))

    # Money label
    money_var = tk.StringVar(value=f"Oro: {resources['gold']}")
    money_lbl = tk.Label(main_container, textvariable=money_var,
                         font=('Segoe UI', 12, 'bold'), fg='#eebc1d', bg='#000000')
    main_container.create_window(900, 690, window=money_lbl, tags='ui_element')

    def update_panels():
        """Update character, world, and log panels"""
        char_text.config(state='normal')
        char_text.delete('1.0', tk.END)
        for key, val in state.selections.items():
            if not key.startswith('_'):
                if isinstance(val, list):
                    char_text.insert(tk.END, f"{key}: {', '.join(val)}\n")
                else:
                    char_text.insert(tk.END, f"{key}: {val}\n")
        char_text.config(state='disabled')

        world_text.config(state='normal')
        world_text.delete('1.0', tk.END)
        # Location
        world_text.insert(tk.END, f"Lugar: {current_location['territory']}\n")
        if current_location['sublocation']:
            world_text.insert(tk.END, f" - {current_location['sublocation']}\n")
        # Money
        world_text.insert(tk.END, f"Oro: {resources['gold']}\n")
        # Reputation
        if adventure_phase['active'] and any(v != 0 for v in reputation.values()):
            world_text.insert(tk.END, '\nREPUTACION\n')
            for faction, score in reputation.items():
                if score != 0:
                    symbol = '+' if score > 0 else ''
                    bar = '|' * abs(score)
                    world_text.insert(tk.END, f"{faction}: {symbol}{score} {bar}\n")
        # Conditions
        if conditions:
            world_text.insert(tk.END, '\nCONDICIONES\n')
            for cond in sorted(conditions):
                desc = CONDITION_DESCRIPTIONS.get(cond, cond.replace('_', ' ').title())
                world_text.insert(tk.END, f"- {desc}\n")
        # Titles
        if titles:
            world_text.insert(tk.END, '\nTITULOS\n')
            for t in titles:
                world_text.insert(tk.END, f"* {t}\n")
        world_text.config(state='disabled')

        log_text.config(state='normal')
        log_text.delete('1.0', tk.END)
        if adventure_log:
            for entry in adventure_log[-8:]:
                log_text.insert(tk.END, f"{entry}\n")
        log_text.config(state='disabled')

        money_var.set(f"Oro: {resources['gold']}")

    # Backward compatibility for existing calls
    def update_char_display():
        update_panels()

    # Current wheel labels
    current_lbl = tk.Label(main_container, text='Rueda: Race', 
                           font=('Segoe UI', 14, 'bold'), fg='#eebc1d', bg='#000000')
    main_container.create_window(900, 730, window=current_lbl, tags='ui_element')
    context_lbl = tk.Label(main_container, text='',
                           font=('Segoe UI', 11, 'italic'), fg='#f0e6d2', bg='#000000', wraplength=500, justify='left')
    main_container.create_window(900, 760, window=context_lbl, tags='ui_element')

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
    travel_phase = {'active': False, 'done_for_chapter': False}
    current_location = {'territory': state.selections.get('Territory', 'Human City (Good Factions)'), 'sublocation': None}
    reputation = {}  # faction_name: score
    adventure_log = []  # chapter summaries
    decision_mods = {}  # temporary tag mods from decisions
    conditions = set()  # persistent world conditions (e.g. "trade_blocked")
    completed_chains = {}  # chain_name -> completion count
    titles = []  # earned titles/achievements
    chain_state = {
        'active': False,     # is a chain currently running?
        'chain_name': None,  # name of the chain (key in EVENT_CHAINS)
        'step_id': None,     # current step id within the chain
        'choices': {},       # choices made during this chain: step_id -> option name
        'temp_vars': {},     # temp variables (_forge_item, _prey, etc.)
    }

    def build_wheel_data(wheel_name):
        """Build wheel segments"""
        segments = []

        if wheel_name == 'Travel':
            segments = build_travel_segments()
            return segments
        
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

        elif wheel_name == 'Travel':
            segments = build_travel_segments()
        
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
                # Check if this activity is blocked by a condition
                chain_def = EVENT_CHAINS.get(item['name'])
                if chain_def and chain_def.get('blocked_by'):
                    if chain_def['blocked_by'] in conditions:
                        continue  # skip blocked activities

                # Check chain repeat limits
                chain_name = item['name']
                if chain_name in completed_chains:
                    count = completed_chains[chain_name]
                    limits = CHAIN_LIMITS.get(chain_name, {})
                    if limits.get('unique') and count > 0:
                        continue  # skip unique chains already done
                    if 'max_repeats' in limits and count >= limits['max_repeats']:
                        continue  # skip chains at max repeats

                weight = apply_tag_weights(item, tag_weights)
                for tag in item.get('tags', []):
                    if tag in decision_mods:
                        weight *= decision_mods[tag]

                # Boost activities that have chains (more interesting)
                if item['name'] in EVENT_CHAINS:
                    weight *= 1.3

                # Diminishing returns for repeated chains
                if chain_name in completed_chains and completed_chains[chain_name] > 0:
                    weight *= max(0.15, 1.0 / (1 + completed_chains[chain_name] * 0.6))

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
                # Check if this event is blocked by a condition
                chain_def = EVENT_CHAINS.get(item['name'])
                if chain_def and chain_def.get('blocked_by'):
                    if chain_def['blocked_by'] in conditions:
                        continue

                # Check chain repeat limits
                chain_name = item['name']
                if chain_name in completed_chains:
                    count = completed_chains[chain_name]
                    limits = CHAIN_LIMITS.get(chain_name, {})
                    if limits.get('unique') and count > 0:
                        continue  # skip unique events already done
                    if 'max_repeats' in limits and count >= limits['max_repeats']:
                        continue  # skip events at max repeats

                weight = apply_tag_weights(item, tag_weights)
                for tag in item.get('tags', []):
                    if tag in decision_mods:
                        weight *= decision_mods[tag]

                # Boost events that have chains
                if item['name'] in EVENT_CHAINS:
                    weight *= 1.3

                # Diminishing returns for repeated events
                if chain_name in completed_chains and completed_chains[chain_name] > 0:
                    weight *= max(0.15, 1.0 / (1 + completed_chains[chain_name] * 0.6))

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

    # Sublocations per territory for travel flavor
    SUBLOCATIONS = {
        'Human City (Good Factions)': ['Distrito Mercante', 'Catedral', 'Casa de Gremios'],
        'Human Slums': ['Callejones', 'Puertos', 'Foso de Lucha'],
        'Elven Forest': ['Arboleda Antigua', 'Canopia', 'Claro Lunar'],
        'Dwarven Hold': ['Gran Forja', 'Minas Profundas', 'Bazar de Piedra'],
        'Outlands': ['Fortin en Ruinas', 'Pantano Sangriento', 'Campamento Bandido']
    }

    def get_mood_for_territory(territory):
        mapping = {
            'Human City (Good Factions)': 'calm',
            'Human Slums': 'gritty',
            'Elven Forest': 'mystic',
            'Dwarven Hold': 'forge',
            'Outlands': 'tense'
        }
        return mapping.get(territory, 'calm')

    def play_music_theme(mood):
        """Looping lightweight background cue per mood using short beeps (non-blocking)"""
        if not winsound:
            return

        # Cancel previous loop if mood changes
        if music_state['timer']:
            try:
                root.after_cancel(music_state['timer'])
            except Exception:
                pass
            music_state['timer'] = None

        music_state['mood'] = mood

        tones = {
            'calm': [(440, 90), (523, 90)],
            'mystic': [(392, 110), (622, 110)],
            'forge': [(262, 110), (196, 110)],
            'gritty': [(330, 90), (247, 90)],
            'tense': [(554, 80), (659, 80)]
        }
        seq = tones.get(mood, tones['calm'])

        def loop():
            if music_state['mood'] != mood:
                return
            try:
                for freq, dur in seq:
                    winsound.Beep(freq, dur)
            except Exception:
                pass
            finally:
                # repeat every ~4 seconds
                music_state['timer'] = root.after(4000, loop)

        # start shortly to avoid blocking UI thread during call
        music_state['timer'] = root.after(200, loop)

    def pick_sublocation(territory):
        options = SUBLOCATIONS.get(territory, [])
        return random.choice(options) if options else None

    def build_travel_segments():
        """Build travel wheel segments weighted by territory affinities"""
        items = data.get('territories') or data.get('places', [])
        affinities = build_territory_affinities(
            state.selections.get('Race', ''),
            state.selections.get('Class', ''),
            state.selections.get('Alignment', '')
        )
        segments = []
        for i, item in enumerate(items):
            territory = item['name']
            weight = item.get('weight', 1) * affinities.get(territory, 1.0)
            segments.append({
                'name': territory,
                'weight': weight,
                'color': get_color(i, len(items)),
                'desc': f"Viajar a {territory}"
            })
        return segments

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

    def get_wheel_context(wheel_name):
        """One-line narration for the current wheel"""
        if wheel_name == 'Travel':
            return f"Cap. {adventure_phase['chapter']}: Elige tu destino antes de la accion."
        if wheel_name.startswith('Adventure Activity'):
            loc = current_location['territory']
            sub = current_location.get('sublocation')
            if sub:
                return f"En {loc} ({sub}), rumores de oportunidades circulan."
            return f"En {loc}, buscas tu proxima aventura."
        if wheel_name.startswith('Adventure Event'):
            return "Un giro del destino se acerca."
        if wheel_name.startswith('Adventure Action'):
            return "Decide tu enfoque frente al desafio."
        if wheel_name.startswith('Adventure Outcome'):
            return "Las consecuencias de tus actos se revelan."
        if wheel_name.startswith('Adventure'):
            return "Progreso de aventura."
        if wheel_name.startswith('Magic') or wheel_name.startswith('Spells'):
            return "Elige el camino arcano que te define."
        if wheel_name.startswith('Power'):
            return "Poderes despiertan en tu sangre."
        if wheel_name.startswith('Skill'):
            return "Talentos mortales afinan tu oficio."
        if wheel_name.startswith('Territory'):
            return "Donde empezara tu historia."
        return "Forja tu leyenda."

    def should_trigger_travel(event_name):
        """Decide if an event selection should prompt travel"""
        name_lower = event_name.lower()
        ev = next((e for e in data.get('adventure_events', []) if e['name'] == event_name), None)
        tags = ev.get('tags', []) if ev else []
        travel_tags = {'explore', 'travel', 'caravan', 'escort', 'escort_caravan', 'guard_caravan'}
        if any(t in travel_tags for t in tags):
            return True
        keywords = ['explor', 'caravan', 'caravana', 'escolta', 'escoltar']
        return any(k in name_lower for k in keywords)

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

        # Reset travel state for the new run
        travel_phase['done_for_chapter'] = False
        travel_phase['active'] = False

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

    def show_travel_wheel():
        """Display travel wheel before adventure activity"""
        travel_phase['active'] = True
        current_lbl.config(text=f'Cap. {adventure_phase["chapter"]} - Viajar')
        context_lbl.config(text=get_wheel_context('Travel'))
        segments = build_wheel_data('Travel')
        if segments:
            draw_wheel(segments, 0)
            spinning['rotation'] = 0
        else:
            # If no travel options, skip travel to avoid getting stuck
            travel_phase['active'] = False
            travel_phase['done_for_chapter'] = True
            show_adventure_wheel()

    def show_adventure_wheel():
        """Display current adventure wheel"""
        # If a chain is active, show the chain wheel instead
        if chain_state['active']:
            show_chain_wheel()
            return

        wheel_name = get_adventure_wheel_name()
        step = adventure_phase['step']
        chapter = adventure_phase['chapter']

        step_labels = ['Actividad', 'Evento', 'Accion', 'Resultado']
        current_lbl.config(text=f'Cap. {chapter} - {step_labels[step]}')
        context_lbl.config(text=get_wheel_context(wheel_name))

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

        # After Activity step (step 0): check if this triggers a chain
        if step == 0:
            if selected_name in EVENT_CHAINS:
                update_char_display()
                start_chain(selected_name)
                return

        # After event step, check for decisions
        if step == 1:  # Event
            if selected_name in ADVENTURE_DECISIONS:
                update_char_display()
                show_decision_popup(selected_name)
                return  # Decision popup will advance the adventure
            # Events can also trigger chains
            if selected_name in EVENT_CHAINS:
                update_char_display()
                start_chain(selected_name)
                return
            # Certain events trigger travel before action
            if should_trigger_travel(selected_name):
                travel_phase['active'] = True
                travel_phase['done_for_chapter'] = False
                update_char_display()
                show_travel_wheel()
                return

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
            travel_phase['done_for_chapter'] = False
            travel_phase['active'] = False
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
        # Stop background music loop
        music_state['mood'] = None
        if music_state['timer']:
            try:
                root.after_cancel(music_state['timer'])
            except Exception:
                pass
            music_state['timer'] = None
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
        popup.geometry('650x700')
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

        # Show titles earned
        if titles:
            titles_text = '\nTitulos Obtenidos:\n'
            for t in titles:
                titles_text += f"  * {t}\n"
            tk.Label(popup, text=titles_text, font=('Consolas', 9),
                    fg='#44ff44', bg='#1a1a2e', justify='left').pack(pady=5)

        # Show final world state
        if conditions:
            cond_text = '\nEstado del Mundo:\n'
            for cond in sorted(conditions):
                desc = CONDITION_DESCRIPTIONS.get(cond, cond.replace('_', ' ').title())
                cond_text += f"  * {desc}\n"
            tk.Label(popup, text=cond_text, font=('Consolas', 9),
                    fg='#ff9999', bg='#1a1a2e', justify='left').pack(pady=5)

        tk.Button(popup, text='Cerrar', font=('Segoe UI', 12, 'bold'),
                 bg='#eebc1d', fg='#000000', width=15,
                 command=popup.destroy).pack(pady=10)

        current_lbl.config(text=title)

    # ===== CHAIN SYSTEM HELPERS =====

    def get_chain_step(chain_name, step_id):
        """Get a specific step from a chain by its id"""
        chain = EVENT_CHAINS.get(chain_name)
        if not chain:
            return None
        for step in chain['steps']:
            if step['id'] == step_id:
                return step
        return None

    def build_chain_wheel_segments(chain_name, step_id):
        """Build wheel segments for a specific chain step"""
        step = get_chain_step(chain_name, step_id)
        if not step:
            return []

        segments = []
        stat_check = step.get('stat_check')
        # If step has a difficulty key, get it from temp_vars
        difficulty = 5  # default
        diff_key = step.get('difficulty_key')
        if diff_key and diff_key in chain_state['temp_vars']:
            difficulty = chain_state['temp_vars'][diff_key]

        for i, opt in enumerate(step['options']):
            weight = opt.get('weight', 5)

            # Check requires_magic
            if opt.get('requires_magic'):
                magic_count_str = state.selections.get('Magic Count', '0 (None)')
                try:
                    mc = int(magic_count_str.split()[0])
                except:
                    mc = 0
                if mc == 0:
                    continue  # skip option if no magic

            # Check requires_condition
            req_cond = opt.get('requires_condition')
            if req_cond and req_cond not in conditions:
                continue

            # Check blocked_by_condition
            block_cond = opt.get('blocked_by_condition')
            if block_cond and block_cond in conditions:
                continue

            # Apply stat_weight: multiply weight by (stat_value / 5)
            for stat_name, multiplier in opt.get('stat_weight', {}).items():
                stat_val = get_stat_value(stat_name)
                weight *= (stat_val / 5.0) * multiplier

            # Apply skill_bonus: if character has that skill, multiply weight
            for skill_name, multiplier in opt.get('skill_bonus', {}).items():
                has_skill = False
                for key, val in state.selections.items():
                    if key.startswith('Skill ') and not key.startswith('Skill Count') and not key.startswith('Skill Mastery') and not key.startswith('Skill Efficiency'):
                        if val == skill_name:
                            has_skill = True
                            break
                if has_skill:
                    weight *= multiplier

            # Apply power bonuses
            for key, val in state.selections.items():
                if key.startswith('Power ') and not key.startswith('Power Count') and not key.startswith('Power Mastery'):
                    pname = val.lower()
                    opt_name = opt['name'].lower()
                    if 'shadow' in pname and ('infiltra' in opt_name or 'sigilo' in opt_name or 'nocturna' in opt_name):
                        weight *= 1.4

            # For stat-checked results, modify by stat and difficulty
            if stat_check and opt.get('success_tier'):
                check_val = get_stat_value(stat_check)
                tier = opt['success_tier']
                ratio = check_val / max(1, difficulty)

                if tier == 'high':
                    weight *= max(0.3, ratio * 1.5)
                elif tier == 'mid':
                    weight *= max(0.5, 0.8 + ratio * 0.3)
                elif tier == 'low':
                    weight *= max(0.3, 1.5 - ratio * 0.5)
                elif tier == 'fail':
                    weight *= max(0.2, 1.8 - ratio * 0.8)

            # Inline stat check (for options that are partially stat-dependent)
            inline_check = opt.get('stat_check_inline')
            if inline_check:
                check_val = get_stat_value(inline_check)
                if check_val >= 7:
                    weight *= 0.5  # less likely to be bad if high stat
                elif check_val <= 3:
                    weight *= 1.5  # more likely to be bad if low stat

            weight = max(0.1, weight)
            segments.append({
                'name': opt['name'],
                'weight': weight,
                'color': get_color(i, len(step['options'])),
                'desc': opt.get('desc', opt['name']),
                '_option_data': opt  # stash full option data for later
            })

        return segments

    def start_chain(chain_name):
        """Start an event chain"""
        chain = EVENT_CHAINS.get(chain_name)
        if not chain:
            return False

        # Check if chain is blocked by condition
        blocked_by = chain.get('blocked_by')
        if blocked_by and blocked_by in conditions:
            msg = chain.get('blocked_message', f'Esta accion esta bloqueada ({blocked_by}).')
            messagebox.showinfo('Bloqueado', msg)
            # Fall back to generic adventure
            advance_adventure()
            return True

        chain_state['active'] = True
        chain_state['chain_name'] = chain_name
        chain_state['step_id'] = chain['steps'][0]['id']
        chain_state['choices'] = {}
        chain_state['temp_vars'] = {}
        show_chain_wheel()
        return True

    def show_chain_wheel():
        """Display current chain step wheel"""
        chain_name = chain_state['chain_name']
        step_id = chain_state['step_id']
        step = get_chain_step(chain_name, step_id)

        if not step:
            end_chain()
            return

        chapter = adventure_phase['chapter']
        current_lbl.config(text=f'Cap. {chapter} - {step["label"]}')
        context_lbl.config(text=f"{chain_name}: {step['label']}")

        segments = build_chain_wheel_segments(chain_name, step_id)
        if segments:
            draw_wheel(segments, 0)
            spinning['rotation'] = 0
        else:
            # No valid options, skip
            end_chain()

    def handle_travel_result(selected_name):
        """Apply travel choice: set territory and sublocation"""
        travel_phase['active'] = False
        travel_phase['done_for_chapter'] = True

        current_location['territory'] = selected_name
        subloc = pick_sublocation(selected_name)
        current_location['sublocation'] = subloc
        state.selections['Territory'] = selected_name
        if subloc:
            state.selections['_Sublocation'] = subloc
        else:
            state.selections.pop('_Sublocation', None)

        adventure_log.append(f"Viajas a {selected_name}" + (f" ({subloc})" if subloc else ''))
        play_music_theme(get_mood_for_territory(selected_name))
        root.after(100, lambda: load_background_image(selected_name))
        update_char_display()

        # After travel, proceed with adventure flow
        if adventure_phase['active'] and adventure_phase['step'] == 1:
            advance_adventure()
        else:
            show_adventure_wheel()

    def handle_chain_result(selected_name):
        """Handle the result of spinning a chain wheel"""
        chain_name = chain_state['chain_name']
        step_id = chain_state['step_id']
        step = get_chain_step(chain_name, step_id)

        if not step:
            end_chain()
            return

        # Find the selected option
        selected_opt = None
        for opt in step['options']:
            if opt['name'] == selected_name:
                selected_opt = opt
                break

        if not selected_opt:
            end_chain()
            return

        # Store choice
        chain_state['choices'][step_id] = selected_name

        # Apply immediate effects from the option
        effects = selected_opt.get('effects', {})
        context_stat = step.get('stat_check')  # pass stat context for targeted effects
        apply_chain_effects(effects, context_stat)

        # Store temp vars (keys starting with _)
        for k, v in effects.items():
            if k.startswith('_'):
                chain_state['temp_vars'][k] = v

        # Store in state.selections for display
        chapter = adventure_phase['chapter']
        sel_key = f'{step["label"]} (Cap.{chapter})'
        state.selections[sel_key] = selected_name
        update_char_display()

        # Check for terminal death
        if effects.get('terminal') == 'death':
            end_run('death', selected_opt.get('desc', selected_name))
            return

        # Move to next step
        next_id = selected_opt.get('next')
        if next_id:
            chain_state['step_id'] = next_id
            show_chain_wheel()
        else:
            # Chain complete
            end_chain()

    def change_gold(amount, source=''):
        """Adjust gold and log the change"""
        resources['gold'] = max(0, resources['gold'] + amount)
        sign = '+' if amount >= 0 else ''
        entry = f"  [ORO] {sign}{amount}"
        if source:
            entry += f" {source}"
        adventure_log.append(entry)

    def apply_chain_effects(effects, context_stat=None):
        """Apply effects from a chain option with narrative feedback"""
        chapter = adventure_phase['chapter']
        stat_labels = {1: 'Abysmal', 2: 'Poor', 3: 'Below Average', 4: 'Average',
                      5: 'Good', 6: 'Excellent', 7: 'Great', 8: 'Outstanding',
                      9: 'Superhuman', 10: 'Legendary'}

        # Stat boost - targeted to context stat or related stat
        stat_boost = effects.get('stat_boost', 0)
        if stat_boost > 0:
            if context_stat and context_stat in ['Strength', 'Agility', 'Durability', 'Intelligence', 'Charisma']:
                stat = context_stat
            else:
                stats = ['Strength', 'Agility', 'Durability', 'Intelligence', 'Charisma']
                stat = random.choice(stats)
            old_val = get_stat_value(stat)
            new_val = min(10, old_val + stat_boost)
            state.selections[stat] = f'{new_val} ({stat_labels.get(new_val, "Good")})'
            adventure_log.append(f'  [+{stat_boost}] {stat}: {old_val} -> {new_val}')

        # Stat boost to specific stat
        stat_spec = effects.get('stat_boost_specific')
        if stat_spec:
            old_val = get_stat_value(stat_spec)
            new_val = min(10, old_val + 1)
            state.selections[stat_spec] = f'{new_val} ({stat_labels.get(new_val, "Good")})'
            adventure_log.append(f'  [+1] {stat_spec}: {old_val} -> {new_val}')

        # Stat damage - targeted to context stat (you fail at what you tried)
        stat_dmg = effects.get('stat_damage', 0)
        if stat_dmg > 0:
            if context_stat and context_stat in ['Strength', 'Agility', 'Durability', 'Intelligence', 'Charisma']:
                # Damage the stat you were using (failed attempt hurts relevant ability)
                stat = context_stat
            else:
                # Damage weakest stat (injury exploits weakness)
                stats = ['Strength', 'Agility', 'Durability', 'Intelligence', 'Charisma']
                stat = min(stats, key=lambda s: get_stat_value(s))
            old_val = get_stat_value(stat)
            new_val = max(1, old_val - stat_dmg)
            state.selections[stat] = f'{new_val} ({stat_labels.get(new_val, "Good")})'
            adventure_log.append(f'  [-{stat_dmg}] {stat}: {old_val} -> {new_val}')

        # Add condition with narrative
        cond = effects.get('add_condition')
        if cond:
            conditions.add(cond)
            cond_desc = CONDITION_DESCRIPTIONS.get(cond, cond)
            adventure_log.append(f'  [ESTADO] {cond_desc}')

        # Remove condition with narrative
        rm_cond = effects.get('remove_condition')
        if rm_cond and rm_cond in conditions:
            conditions.discard(rm_cond)
            cond_desc = CONDITION_DESCRIPTIONS.get(rm_cond, rm_cond)
            adventure_log.append(f'  [CURADO] {cond_desc}')

        # Add random item
        if effects.get('add_random_item'):
            objects = data.get('objects', [])
            if objects:
                item = random.choice(objects)
                item_idx = 1
                while f'Item {item_idx}' in state.selections:
                    item_idx += 1
                state.selections[f'Item {item_idx}'] = item['name']
                adventure_log.append(f'  [ITEM] Obtienes: {item["name"]}')

        # Add item from prey/forge (named item)
        if effects.get('add_item'):
            forge_item = chain_state['temp_vars'].get('_forge_item', 'Artefacto')
            item_idx = 1
            while f'Item {item_idx}' in state.selections:
                item_idx += 1
            state.selections[f'Item {item_idx}'] = forge_item
            adventure_log.append(f'  [ITEM] Forjado: {forge_item}')

        if effects.get('add_item_from'):
            source_key = effects['add_item_from']
            source_name = chain_state['temp_vars'].get(source_key, 'Trofeo')
            trophy_name = f'Trofeo: {source_name}'
            item_idx = 1
            while f'Item {item_idx}' in state.selections:
                item_idx += 1
            state.selections[f'Item {item_idx}'] = trophy_name
            adventure_log.append(f'  [ITEM] Trofeo: {source_name}')

        # Wealth changes
        if effects.get('gain_wealth'):
            change_gold(25, 'ganas riqueza')
        if effects.get('lose_wealth'):
            change_gold(-20, 'pierdes riqueza')

        # Reputation changes with narrative
        for faction, change in effects.get('rep', {}).items():
            if faction not in reputation:
                reputation[faction] = 0
            reputation[faction] += change
            symbol = '+' if change > 0 else ''
            adventure_log.append(f'  [REP] {faction}: {symbol}{change}')

    def end_chain():
        """End the current chain and advance to next chapter"""
        chapter = adventure_phase['chapter']
        chain_name = chain_state['chain_name'] or '?'

        # Track chain completion
        completed_chains[chain_name] = completed_chains.get(chain_name, 0) + 1

        # Check for title awards based on chain outcomes
        for step_id, choice_name in chain_state['choices'].items():
            title_key = (chain_name, choice_name)
            if title_key in CHAIN_TITLES:
                new_title = CHAIN_TITLES[title_key]
                if new_title not in titles:
                    titles.append(new_title)
                    adventure_log.append(f'  [TITULO] Obtienes: {new_title}')

        # Build log entry from chain choices
        choices_str = ' > '.join(chain_state['choices'].values())
        adventure_log.append(f'Cap.{chapter}: {chain_name} > {choices_str}')

        # Reset chain state
        chain_state['active'] = False
        chain_state['chain_name'] = None
        chain_state['step_id'] = None
        chain_state['choices'] = {}
        chain_state['temp_vars'] = {}

        # Clear decision mods
        decision_mods.clear()
        update_char_display()

        # Random event chance (30%) - avoid immediate repeats
        if random.random() < 0.3:
            event_chain = pick_random_event_chain()
            if event_chain:
                last_random_event['chapter'] = adventure_phase['chapter']
                last_random_event['name'] = event_chain
                adventure_phase['chapter'] += 1
                adventure_phase['step'] = 0
                travel_phase['done_for_chapter'] = False
                travel_phase['active'] = False
                start_chain(event_chain)
                return

        # Advance chapter
        adventure_phase['chapter'] += 1
        adventure_phase['step'] = 0
        travel_phase['done_for_chapter'] = False
        travel_phase['active'] = False
        show_adventure_wheel()

    def pick_random_event_chain():
        """Pick a random event that has a chain, weighted by tags and conditions"""
        events = data.get('adventure_events', [])
        current_chapter = adventure_phase['chapter']
        tag_weights = build_adventure_tag_weights()

        candidates = []
        for item in events:
            # Only pick events that have chains
            if item['name'] not in EVENT_CHAINS:
                continue
            # Skip if event fired too recently
            if last_random_event['name'] == item['name'] and current_chapter - last_random_event['chapter'] < 2:
                continue
            # Check if blocked
            chain_def = EVENT_CHAINS[item['name']]
            if chain_def.get('blocked_by') and chain_def['blocked_by'] in conditions:
                continue

            # Check chain repeat limits
            if item['name'] in completed_chains:
                count = completed_chains[item['name']]
                limits = CHAIN_LIMITS.get(item['name'], {})
                if limits.get('unique') and count > 0:
                    continue
                if 'max_repeats' in limits and count >= limits['max_repeats']:
                    continue

            weight = apply_tag_weights(item, tag_weights)
            # Diminishing returns for repeated chains
            if item['name'] in completed_chains and completed_chains[item['name']] > 0:
                weight *= max(0.15, 1.0 / (1 + completed_chains[item['name']] * 0.6))
            # Apply reputation bonuses
            for faction_name, score in reputation.items():
                faction_data = next((f for f in data.get('factions', []) if f['name'] == faction_name), None)
                if faction_data and score > 0:
                    item_tags = item.get('tags', [])
                    for tag in faction_data.get('tags', []):
                        if tag in item_tags:
                            weight *= 1 + score * 0.1

            if weight > 0:
                candidates.append((item['name'], weight))

        if not candidates:
            return None

        total = sum(w for _, w in candidates)
        choice = random.uniform(0, total)
        current = 0
        for name, w in candidates:
            current += w
            if choice <= current:
                return name
        return candidates[-1][0]

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
                play_sound('stop')
                play_sound('prize')
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
        if travel_phase['active']:
            handle_travel_result(selected_name)
            return
        if adventure_phase['active']:
            if chain_state['active']:
                handle_chain_result(selected_name)
            else:
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
            context_lbl.config(text=get_wheel_context(wheel_name))
            segments = build_wheel_data(wheel_name)
            if segments:
                draw_wheel(segments, 0)
                spinning['rotation'] = 0

    def spin_action():
        """Spin button"""
        if spinning['active']:
            return

        if adventure_phase['active'] and chain_state['active']:
            # Build chain wheel segments
            chain_name = chain_state['chain_name']
            step_id = chain_state['step_id']
            segments = build_chain_wheel_segments(chain_name, step_id)
            wheel_name = chain_name
        elif adventure_phase['active']:
            if travel_phase['active']:
                wheel_name = 'Travel'
                segments = build_wheel_data(wheel_name)
            else:
                wheel_name = get_adventure_wheel_name()
                segments = build_wheel_data(wheel_name)
        else:
            current_wheel_config = get_current_wheel_config()
            if wheel_index['i'] >= len(current_wheel_config):
                return
            wheel_name = current_wheel_config[wheel_index['i']]
            segments = build_wheel_data(wheel_name)

        if not segments:
            messagebox.showwarning('Error', f'No hay opciones para {wheel_name}')
            if wheel_name == 'Travel' and adventure_phase['active']:
                # Skip travel and continue adventure to avoid blocking
                travel_phase['active'] = False
                travel_phase['done_for_chapter'] = True
                show_adventure_wheel()
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

        play_sound('spin')
        animate_spin(segments, final_idx)

    spin_btn.config(command=spin_action)
    end_run_btn.config(command=lambda: end_run('manual'))

    # === TEST MODE: Skip character creation ===
    def skip_to_adventure():
        """Pre-fill a test character and jump to adventure phase"""
        test_char = {
            'Race': 'Human',
            'Gender': 'Female',
            'Age': 'Adult (36-60)',
            'Archetype': 'Merchant',
            'Class': 'Trader',
            'Alignment': 'Neutral Good',
            'Strength': '4 (Average)',
            'Agility': '5 (Good)',
            'Durability': '5 (Good)',
            'Intelligence': '7 (Great)',
            'Charisma': '8 (Outstanding)',
            'Weapon': 'Rapier',
            'Weapon Mastery': 'Expert',
            'Power Count': '1 (Single)',
            'Power 1': 'Mind Control (innate)',
            'Power Mastery 1': 'Advanced',
            'Magic Count': '1 (Single)',
            'Magic Type 1': 'Arcane',
            'Spells 1': 'Arcane Missile',
            'Magic Skill 1': 'Adept',
            'Skill Count': '3 (Triple)',
            'Skill 1': 'Persuasion',
            'Skill Mastery 1': 'Expert',
            'Skill 2': 'Stealth',
            'Skill Mastery 2': 'Skilled',
            'Skill 3': 'Investigation',
            'Skill Mastery 3': 'Skilled',
            'Skill Efficiency': 'Great (115%)',
            'Territory': 'Human City (Good Factions)',
            'Items Count': '2 (Dual)',
            'Item 1': 'Guild Signet',
            'Item 2': 'Ledger',
        }
        for k, v in test_char.items():
            state.selections[k] = v
        resources['gold'] = 120
        # Load territory background
        root.after(100, lambda: load_background_image(test_char['Territory']))
        update_char_display()
        start_adventure_phase()

    skip_btn = tk.Button(main_container, text='TEST: SKIP', width=12, font=('Segoe UI', 9, 'bold'),
                        bg='#444444', fg='#ffffff', activebackground='#666666',
                        activeforeground='#ffffff', relief='raised', bd=2,
                        command=skip_to_adventure)
    main_container.create_window(1350, 870, window=skip_btn, tags='ui_element')
    # === END TEST MODE ===

    show_current_wheel()
    update_char_display()

    root.mainloop()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
