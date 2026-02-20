using System.Collections.Generic;

namespace DarkWheel.Flow
{
    // ── Data classes ──

    public class ChainOption
    {
        public string Name;
        public float Weight = 5f;
        public string Desc;
        public Dictionary<string, float> StatWeight;
        public Dictionary<string, float> SkillBonus;
        public bool RequiresMagic;
        public string RequiresCondition;
        public string BlockedByCondition;
        public string SuccessTier;
        public string StatCheckInline;
        public string Next;
        public Dictionary<string, object> Effects;
    }

    public class ChainStep
    {
        public string Id;
        public string Label;
        public string StatCheck;
        public string DifficultyKey;
        public List<ChainOption> Options;
    }

    public class ChainDef
    {
        public string BlockedBy;
        public string BlockedMessage;
        public List<ChainStep> Steps;
    }

    public class ChainLimit
    {
        public bool Unique;
        public int MaxRepeats = -1;
    }

    public class DecisionOption
    {
        public string Label;
        public Dictionary<string, float> TagMods;
        public Dictionary<string, int> Rep;
    }

    public class DecisionDef
    {
        public string Prompt;
        public List<DecisionOption> Options;
    }

    // ── Static data ──

    public static class EventChainData
    {
        // ── Compact helpers ──

        static Dictionary<string, int> Rep(params (string f, int v)[] pairs)
        {
            var d = new Dictionary<string, int>();
            foreach (var (f, v) in pairs) d[f] = v;
            return d;
        }

        static Dictionary<string, object> Fx(params (string k, object v)[] pairs)
        {
            var d = new Dictionary<string, object>();
            foreach (var (k, v) in pairs) d[k] = v;
            return d;
        }

        static Dictionary<string, float> Sw(params (string k, float v)[] pairs)
        {
            var d = new Dictionary<string, float>();
            foreach (var (k, v) in pairs) d[k] = v;
            return d;
        }

        static Dictionary<string, float> Sb(params (string k, float v)[] pairs)
        {
            var d = new Dictionary<string, float>();
            foreach (var (k, v) in pairs) d[k] = v;
            return d;
        }

        static ChainOption O(string name, float weight, string desc, string next = null,
            Dictionary<string, float> sw = null, Dictionary<string, float> sb = null,
            bool reqMagic = false, string tier = null, string statInline = null,
            Dictionary<string, object> fx = null) => new()
        {
            Name = name, Weight = weight, Desc = desc, Next = next,
            StatWeight = sw, SkillBonus = sb, RequiresMagic = reqMagic,
            SuccessTier = tier, StatCheckInline = statInline,
            Effects = fx ?? new Dictionary<string, object>()
        };

        static ChainStep S(string id, string label, string statCheck = null,
            string diffKey = null, params ChainOption[] opts) => new()
        {
            Id = id, Label = label, StatCheck = statCheck, DifficultyKey = diffKey,
            Options = new List<ChainOption>(opts)
        };

        // ═══════════════════════════════════════════════════════════
        //  CHAINS
        // ═══════════════════════════════════════════════════════════

        public static readonly Dictionary<string, ChainDef> Chains = new()
        {
            // ── FORGE LEGENDARY GEAR ──
            ["Forge Legendary Gear"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("choose_item", "Elige que forjar", opts:
                        O("Espada Encantada", 5, "Una espada imbuida de poder.",
                            next: "forge_quality",
                            sw: Sw(("Strength", 1.3f)), sb: Sb(("Smithing", 2.0f)),
                            fx: Fx(("_forge_item", "Espada Encantada"))),
                        O("Escudo de Obsidiana", 4, "Un escudo casi indestructible.",
                            next: "forge_quality",
                            sw: Sw(("Durability", 1.3f)), sb: Sb(("Smithing", 2.0f)),
                            fx: Fx(("_forge_item", "Escudo de Obsidiana"))),
                        O("Baston Arcano", 3, "Un baston que canaliza magia.",
                            next: "forge_quality",
                            sw: Sw(("Intelligence", 1.4f)), sb: Sb(("Alchemy", 1.5f)),
                            fx: Fx(("_forge_item", "Baston Arcano"))),
                        O("Anillo de Proteccion", 3, "Un anillo con encantamientos defensivos.",
                            next: "forge_quality",
                            sw: Sw(("Intelligence", 1.2f)), sb: Sb(("Smithing", 1.5f)),
                            fx: Fx(("_forge_item", "Anillo de Proteccion"))),
                        O("Armadura de Dragonskin", 2, "Armadura hecha de escamas de dragon.",
                            next: "forge_quality",
                            sw: Sw(("Strength", 1.2f), ("Durability", 1.2f)), sb: Sb(("Smithing", 2.5f)),
                            fx: Fx(("_forge_item", "Armadura de Dragonskin")))
                    ),
                    S("forge_quality", "Resultado de la Forja", statCheck: "Intelligence", opts:
                        O("Obra Maestra", 2, "Has superado toda expectativa. +2 a stat principal.",
                            tier: "high",
                            fx: Fx(("stat_boost", 2), ("add_item", true), ("rep", Rep(("Merchant Guild", 2))))),
                        O("Buena Calidad", 4, "Un trabajo solido. +1 a stat principal.",
                            tier: "mid",
                            fx: Fx(("stat_boost", 1), ("add_item", true))),
                        O("Calidad Mediocre", 5, "Funcional pero sin brillo.",
                            tier: "low",
                            fx: Fx(("add_item", true))),
                        O("Fallo Catastrofico", 2, "La forja explota. Pierdes materiales y te hieres.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 1), ("rep", Rep(("Merchant Guild", -1)))))
                    )
                }
            },

            // ── PIRATE BLOCKADE ──
            ["Pirate Blockade"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("approach", "Enfrentar el Bloqueo Pirata", opts:
                        O("Negociar con los Piratas", 5, "Intentas dialogar y llegar a un acuerdo.",
                            next: "negotiate_result",
                            sw: Sw(("Charisma", 1.6f)), sb: Sb(("Persuasion", 2.0f))),
                        O("Atacar la Flota", 4, "Lanzas un asalto directo.",
                            next: "combat_result",
                            sw: Sw(("Strength", 1.5f), ("Agility", 1.2f))),
                        O("Infiltracion Nocturna", 4, "Te infiltras de noche para sabotear.",
                            next: "stealth_result",
                            sw: Sw(("Agility", 1.5f)), sb: Sb(("Stealth", 2.0f))),
                        O("Pagar Tributo", 5, "Pagas para que levanten el bloqueo.",
                            next: "tribute_result",
                            sw: Sw(("Charisma", 1.1f))),
                        O("Magia Naval", 2, "Usas magia para destruir o desviar la flota.",
                            next: "magic_result",
                            sw: Sw(("Intelligence", 1.8f)), reqMagic: true)
                    ),
                    S("negotiate_result", "Resultado de la Negociacion", statCheck: "Charisma", opts:
                        O("Acuerdo Comercial", 3, "Los piratas aceptan un pacto. Comercio restaurado.",
                            tier: "high",
                            fx: Fx(("remove_condition", "trade_blocked"), ("rep", Rep(("Merchant Guild", 3), ("Thieves Guild", 1))))),
                        O("Tregua Temporal", 5, "Aceptan pausar el bloqueo, pero volvera.",
                            tier: "mid",
                            fx: Fx(("remove_condition", "trade_blocked"), ("add_condition", "pirate_truce"), ("rep", Rep(("Merchant Guild", 1))))),
                        O("Rechazan Negociar", 4, "Los piratas se rien de tu propuesta.",
                            tier: "low",
                            fx: Fx(("add_condition", "trade_blocked"), ("rep", Rep(("Merchant Guild", -1)))))
                    ),
                    S("combat_result", "Resultado del Combate Naval", statCheck: "Strength", opts:
                        O("Victoria Aplastante", 2, "Destruyes la flota pirata.",
                            tier: "high",
                            fx: Fx(("remove_condition", "trade_blocked"), ("stat_boost", 1), ("rep", Rep(("Hunters Lodge", 2), ("The Crown", 2))))),
                        O("Victoria Ajustada", 4, "Ganas pero con heridas.",
                            tier: "mid",
                            fx: Fx(("remove_condition", "trade_blocked"), ("stat_damage", 1), ("rep", Rep(("Hunters Lodge", 1))))),
                        O("Derrota", 4, "Los piratas te repelen con fuerza.",
                            tier: "low",
                            fx: Fx(("add_condition", "trade_blocked"), ("stat_damage", 2), ("rep", Rep(("Hunters Lodge", -1)))))
                    ),
                    S("stealth_result", "Resultado de la Infiltracion", statCheck: "Agility", opts:
                        O("Sabotaje Perfecto", 3, "Hundes sus barcos sin ser visto.",
                            tier: "high",
                            fx: Fx(("remove_condition", "trade_blocked"), ("rep", Rep(("Thieves Guild", 2))))),
                        O("Parcialmente Exitoso", 4, "Dañas algunos barcos pero te detectan.",
                            tier: "mid",
                            fx: Fx(("remove_condition", "trade_blocked"), ("rep", Rep(("Thieves Guild", 1))))),
                        O("Descubierto", 4, "Te atrapan. Situacion comprometida.",
                            tier: "low",
                            fx: Fx(("add_condition", "trade_blocked"), ("stat_damage", 1)))
                    ),
                    S("tribute_result", "Resultado del Pago", opts:
                        O("Aceptan el Tributo", 6, "Los piratas levantan el bloqueo... por ahora.",
                            fx: Fx(("remove_condition", "trade_blocked"), ("lose_wealth", true), ("add_condition", "pirate_truce"))),
                        O("Exigen Mas", 3, "No es suficiente. Quieren el doble.",
                            fx: Fx(("add_condition", "trade_blocked"), ("lose_wealth", true), ("rep", Rep(("Merchant Guild", -1)))))
                    ),
                    S("magic_result", "Resultado de la Magia Naval", statCheck: "Intelligence", opts:
                        O("Tormenta Arcana", 3, "Invocas una tormenta que destroza la flota.",
                            tier: "high",
                            fx: Fx(("remove_condition", "trade_blocked"), ("rep", Rep(("Mages Circle", 2))), ("stat_boost", 1))),
                        O("Niebla Mistica", 4, "La niebla dispersa a los piratas temporalmente.",
                            tier: "mid",
                            fx: Fx(("remove_condition", "trade_blocked"), ("add_condition", "pirate_truce"))),
                        O("Contrahechizo", 3, "Los piratas tienen un mago que te contrarresta.",
                            tier: "low",
                            fx: Fx(("add_condition", "trade_blocked"), ("stat_damage", 1), ("rep", Rep(("Mages Circle", -1)))))
                    )
                }
            },

            // ── HUNT A BEAST ──
            ["Hunt a Beast"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("choose_prey", "Elige tu Presa", opts:
                        O("Manada de Lobos", 6, "Lobos gigantes asolando aldeas.",
                            next: "hunt_method",
                            sw: Sw(("Strength", 1.2f)), sb: Sb(("Tracking", 1.5f)),
                            fx: Fx(("_prey", "Manada de Lobos"), ("_prey_difficulty", 3))),
                        O("Troll de las Montanas", 4, "Un troll aterroriza los caminos.",
                            next: "hunt_method",
                            sw: Sw(("Strength", 1.4f), ("Durability", 1.3f)),
                            fx: Fx(("_prey", "Troll de las Montanas"), ("_prey_difficulty", 5))),
                        O("Cria de Dragon", 2, "Una cria de dragon cerca de las minas.",
                            next: "hunt_method",
                            sw: Sw(("Strength", 1.5f), ("Intelligence", 1.3f)),
                            fx: Fx(("_prey", "Cria de Dragon"), ("_prey_difficulty", 7))),
                        O("Criatura Sombria", 3, "Un ser de sombra acecha de noche.",
                            next: "hunt_method",
                            sw: Sw(("Intelligence", 1.4f)), sb: Sb(("Tracking", 1.3f)),
                            fx: Fx(("_prey", "Criatura Sombria"), ("_prey_difficulty", 6))),
                        O("Quimera", 1, "La bestia legendaria de tres cabezas.",
                            next: "hunt_method",
                            sw: Sw(("Strength", 1.5f), ("Agility", 1.3f), ("Durability", 1.3f)),
                            fx: Fx(("_prey", "Quimera"), ("_prey_difficulty", 9)))
                    ),
                    S("hunt_method", "Metodo de Caza", opts:
                        O("Rastrear y Emboscar", 5, "Sigues su rastro y tiendes una emboscada.",
                            next: "hunt_result",
                            sw: Sw(("Agility", 1.4f)), sb: Sb(("Tracking", 2.0f), ("Stealth", 1.5f))),
                        O("Combate Directo", 5, "La enfrentas cara a cara.",
                            next: "hunt_result",
                            sw: Sw(("Strength", 1.6f), ("Durability", 1.3f))),
                        O("Trampas", 4, "Preparas trampas en su territorio.",
                            next: "hunt_result",
                            sw: Sw(("Intelligence", 1.4f)), sb: Sb(("Trap Setting", 2.5f))),
                        O("Atraer con Cebo", 3, "Usas un cebo para atraerla a tu terreno.",
                            next: "hunt_result",
                            sw: Sw(("Intelligence", 1.3f)), sb: Sb(("Beast Taming", 1.5f)))
                    ),
                    S("hunt_result", "Resultado de la Caceria", statCheck: "Strength", diffKey: "_prey_difficulty", opts:
                        O("Caza Gloriosa", 3, "Abates a la bestia con maestria. Trofeo legendario.",
                            tier: "high",
                            fx: Fx(("stat_boost", 1), ("add_item_from", "_prey"), ("rep", Rep(("Hunters Lodge", 3))))),
                        O("Caza Exitosa", 5, "La bestia cae, pero no sin lucha.",
                            tier: "mid",
                            fx: Fx(("rep", Rep(("Hunters Lodge", 1))), ("add_item_from", "_prey"))),
                        O("La Bestia Escapa", 4, "No logras atraparla. Regresara mas fuerte.",
                            tier: "low",
                            fx: Fx(("add_condition", "beast_stalking"))),
                        O("Herido Gravemente", 2, "La bestia te ataca y te hiere de gravedad.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 2), ("add_condition", "wounded")))
                    )
                }
            },

            // ── EXPLORE RUINS ──
            ["Explore Ruins"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("choose_depth", "Profundidad de Exploracion", opts:
                        O("Superficie", 6, "Exploras las zonas accesibles y seguras.",
                            next: "surface_find",
                            fx: Fx(("_ruin_depth", 1))),
                        O("Profundidades", 4, "Desciendes a las camaras selladas.",
                            next: "deep_find",
                            sw: Sw(("Agility", 1.2f)), sb: Sb(("Lockpicking", 1.5f)),
                            fx: Fx(("_ruin_depth", 2))),
                        O("El Abismo", 2, "Bajas donde nadie ha regresado con vida.",
                            next: "abyss_find",
                            sw: Sw(("Durability", 1.4f), ("Intelligence", 1.3f)),
                            fx: Fx(("_ruin_depth", 3)))
                    ),
                    S("surface_find", "Hallazgo en Superficie", opts:
                        O("Cofre de Monedas", 5, "Un cofre con riquezas modestas.",
                            fx: Fx(("gain_wealth", true), ("rep", Rep(("Merchant Guild", 1))))),
                        O("Mapa Antiguo", 4, "Un mapa que revela ruinas mas profundas.",
                            fx: Fx(("add_condition", "ancient_map"))),
                        O("Trampa!", 3, "Activas una trampa oculta.",
                            statInline: "Agility",
                            fx: Fx(("stat_damage", 1))),
                        O("Nada Util", 4, "Solo polvo y escombros.")
                    ),
                    S("deep_find", "Hallazgo en Profundidades", opts:
                        O("Artefacto Magico", 3, "Un objeto antiguo vibrando con poder.",
                            fx: Fx(("add_random_item", true), ("stat_boost", 1), ("rep", Rep(("Mages Circle", 1))))),
                        O("Criatura Guardianda", 4, "Un guardian ancestral te ataca.",
                            next: "guardian_fight",
                            statInline: "Strength"),
                        O("Biblioteca Oculta", 3, "Textos antiguos con conocimiento prohibido.",
                            fx: Fx(("stat_boost_specific", "Intelligence"), ("rep", Rep(("Mages Circle", 2))))),
                        O("Maldicion Activada", 3, "Algo oscuro despierta al entrar.",
                            fx: Fx(("add_condition", "cursed"), ("stat_damage", 1)))
                    ),
                    S("abyss_find", "Hallazgo en el Abismo", opts:
                        O("Reliquia Legendaria", 2, "Un artefacto de poder inmenso. +3 stat.",
                            fx: Fx(("stat_boost", 3), ("add_random_item", true), ("rep", Rep(("Mages Circle", 3))))),
                        O("Portal Dimensional", 2, "Un portal a otra dimension se abre.",
                            fx: Fx(("add_condition", "dimensional_rift"))),
                        O("Horror Primordial", 4, "Algo terrible despierta.",
                            statInline: "Durability",
                            fx: Fx(("stat_damage", 3), ("add_condition", "horror_survivor"))),
                        O("Muerte Instantanea", 2, "El abismo te consume.",
                            fx: Fx(("terminal", "death")))
                    ),
                    S("guardian_fight", "Combate contra el Guardian", statCheck: "Strength", opts:
                        O("Derrotas al Guardian", 4, "Vences y reclamas su tesoro.",
                            tier: "high",
                            fx: Fx(("add_random_item", true), ("stat_boost", 1), ("rep", Rep(("Hunters Lodge", 2))))),
                        O("Victoria Pirrica", 4, "Ganas pero malherido.",
                            tier: "mid",
                            fx: Fx(("add_random_item", true), ("stat_damage", 1))),
                        O("Huyes", 3, "Escapas por los pelos.",
                            tier: "low",
                            fx: Fx(("stat_damage", 1)))
                    )
                }
            },

            // ── NEGOTIATE A TRADE ──
            ["Negotiate a Trade"] = new ChainDef
            {
                BlockedBy = "trade_blocked",
                BlockedMessage = "El comercio esta bloqueado por piratas. No puedes comerciar ahora.",
                Steps = new List<ChainStep>
                {
                    S("choose_goods", "Tipo de Mercancia", opts:
                        O("Armas y Armaduras", 5, "Equipo militar de calidad.",
                            next: "haggle",
                            sw: Sw(("Strength", 1.2f)), sb: Sb(("Smithing", 1.5f)),
                            fx: Fx(("_trade_type", "weapons"))),
                        O("Objetos Magicos", 3, "Artefactos y componentes arcanos.",
                            next: "haggle",
                            sw: Sw(("Intelligence", 1.3f)),
                            fx: Fx(("_trade_type", "magic"))),
                        O("Informacion", 4, "Secretos, mapas, y contactos.",
                            next: "haggle",
                            sw: Sw(("Charisma", 1.3f)), sb: Sb(("Investigation", 1.5f)),
                            fx: Fx(("_trade_type", "info"))),
                        O("Materiales Raros", 4, "Componentes para forja y alquimia.",
                            next: "haggle",
                            sb: Sb(("Alchemy", 1.5f), ("Smithing", 1.3f)),
                            fx: Fx(("_trade_type", "materials")))
                    ),
                    S("haggle", "Negociacion del Precio", statCheck: "Charisma", opts:
                        O("Ganga Increible", 2, "Consigues un trato excepcional.",
                            tier: "high",
                            fx: Fx(("gain_wealth", true), ("add_random_item", true), ("rep", Rep(("Merchant Guild", 2))))),
                        O("Buen Trato", 5, "Un intercambio justo y beneficioso.",
                            tier: "mid",
                            fx: Fx(("add_random_item", true), ("rep", Rep(("Merchant Guild", 1))))),
                        O("Precio Justo", 5, "Pagas lo que vale, sin mas.",
                            tier: "mid",
                            fx: Fx(("add_random_item", true))),
                        O("Te Estafan", 3, "El vendedor te engaña vilmente.",
                            tier: "low",
                            fx: Fx(("lose_wealth", true), ("rep", Rep(("Merchant Guild", -1)))))
                    )
                }
            },

            // ── INVESTIGATE A MYSTERY ──
            ["Investigate a Mystery"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("choose_approach", "Metodo de Investigacion", opts:
                        O("Interrogar Testigos", 5, "Hablas con quienes vieron algo.",
                            next: "investigate_result",
                            sw: Sw(("Charisma", 1.5f)), sb: Sb(("Persuasion", 1.5f), ("Intimidation", 1.3f))),
                        O("Buscar Pistas Fisicas", 5, "Examinas la escena del crimen.",
                            next: "investigate_result",
                            sw: Sw(("Intelligence", 1.4f)), sb: Sb(("Investigation", 2.0f))),
                        O("Consultar Archivos", 4, "Revisas registros y documentos.",
                            next: "investigate_result",
                            sw: Sw(("Intelligence", 1.4f)), sb: Sb(("Investigation", 1.5f))),
                        O("Espionaje Nocturno", 3, "Vigilas a los sospechosos de noche.",
                            next: "investigate_result",
                            sw: Sw(("Agility", 1.4f)), sb: Sb(("Stealth", 2.0f)))
                    ),
                    S("investigate_result", "Resultado de la Investigacion", statCheck: "Intelligence", opts:
                        O("Caso Resuelto!", 3, "Descubres la verdad y al culpable.",
                            tier: "high",
                            fx: Fx(("stat_boost_specific", "Intelligence"), ("rep", Rep(("The Crown", 2))), ("gain_wealth", true))),
                        O("Pista Importante", 5, "No resuelves todo, pero avanzas mucho.",
                            tier: "mid",
                            fx: Fx(("add_condition", "clue_found"), ("rep", Rep(("The Crown", 1))))),
                        O("Callejon Sin Salida", 4, "Las pistas no llevan a nada concreto.",
                            tier: "low"),
                        O("Descubierto por el Culpable", 2, "El criminal sabe que lo investigas.",
                            tier: "fail",
                            fx: Fx(("add_condition", "enemy_alerted"), ("stat_damage", 1)))
                    )
                }
            },

            // ── HEAL THE SICK ──
            ["Heal the Sick"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("diagnose", "Diagnostico", opts:
                        O("Plaga Comun", 5, "Una enfermedad conocida pero grave.",
                            next: "treatment",
                            sw: Sw(("Intelligence", 1.2f)), sb: Sb(("Medicine", 1.5f)),
                            fx: Fx(("_disease", "common"), ("_cure_difficulty", 3))),
                        O("Maldicion Arcana", 3, "No es enfermedad, es magia oscura.",
                            next: "treatment",
                            sw: Sw(("Intelligence", 1.4f)), reqMagic: true,
                            fx: Fx(("_disease", "curse"), ("_cure_difficulty", 6))),
                        O("Veneno Raro", 4, "Han sido envenenados intencionalmente.",
                            next: "treatment",
                            sw: Sw(("Intelligence", 1.3f)), sb: Sb(("Alchemy", 2.0f)),
                            fx: Fx(("_disease", "poison"), ("_cure_difficulty", 4)))
                    ),
                    S("treatment", "Tratamiento", statCheck: "Intelligence", diffKey: "_cure_difficulty", opts:
                        O("Cura Milagrosa", 3, "Todos se salvan. Eres un heroe.",
                            tier: "high",
                            fx: Fx(("rep", Rep(("Church of Light", 3))), ("stat_boost_specific", "Charisma"))),
                        O("Mayoria Salvados", 5, "Salvas a la mayoria de los afectados.",
                            tier: "mid",
                            fx: Fx(("rep", Rep(("Church of Light", 1))))),
                        O("Pocos Sobreviven", 4, "A pesar de tu esfuerzo, muchos mueren.",
                            tier: "low",
                            fx: Fx(("rep", Rep(("Church of Light", -1))))),
                        O("Contagiado", 2, "Tu mismo caes enfermo.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 2), ("add_condition", "sick")))
                    )
                }
            },

            // ── TALK WITH A STRANGER ──
            ["Talk with a Stranger"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("stranger_type", "Tipo de Desconocido", opts:
                        O("Mercader Errante", 5, "Un comerciante con mercancias exoticas.",
                            next: "conversation_result",
                            sw: Sw(("Charisma", 1.2f)),
                            fx: Fx(("_stranger", "mercader"), ("_talk_difficulty", 3))),
                        O("Veterano de Guerra", 5, "Un soldado retirado con cicatrices y experiencia.",
                            next: "conversation_result",
                            sw: Sw(("Strength", 1.2f)),
                            fx: Fx(("_stranger", "veterano"), ("_talk_difficulty", 4))),
                        O("Hechicero Misterioso", 3, "Un mago encapuchado que susurra conjuros.",
                            next: "conversation_result",
                            sw: Sw(("Intelligence", 1.4f)),
                            fx: Fx(("_stranger", "mago"), ("_talk_difficulty", 5))),
                        O("Ladron Disfrazado", 4, "Alguien cuya sonrisa oculta intenciones oscuras.",
                            next: "conversation_result",
                            sw: Sw(("Agility", 1.2f)), sb: Sb(("Perception", 1.5f)),
                            fx: Fx(("_stranger", "ladron"), ("_talk_difficulty", 5))),
                        O("Noble de Incognito", 3, "Un aristocrata viajando sin escolta.",
                            next: "conversation_result",
                            sw: Sw(("Charisma", 1.3f)), sb: Sb(("Persuasion", 1.3f)),
                            fx: Fx(("_stranger", "noble"), ("_talk_difficulty", 4)))
                    ),
                    S("conversation_result", "Resultado de la Conversacion", statCheck: "Charisma", diffKey: "_talk_difficulty", opts:
                        O("Nuevo Aliado", 3, "Ganas un aliado valioso para el futuro.",
                            tier: "high",
                            fx: Fx(("stat_boost_specific", "Charisma"), ("add_condition", "has_ally"), ("rep", Rep(("Merchant Guild", 1))))),
                        O("Informacion Valiosa", 5, "Compartes secretos utiles.",
                            tier: "mid",
                            fx: Fx(("add_condition", "clue_found"), ("stat_boost", 1))),
                        O("Conversacion Vacia", 4, "No sacas nada en limpio.",
                            tier: "low"),
                        O("Te Roban!", 3, "El desconocido te roba mientras hablas.",
                            tier: "fail",
                            fx: Fx(("lose_wealth", true), ("rep", Rep(("Thieves Guild", -1)))))
                    )
                }
            },

            // ── SEARCH FOR RARE GOODS ──
            ["Search for Rare Goods"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("search_location", "Donde Buscar", opts:
                        O("Mercado Negro", 5, "Bienes prohibidos a precios elevados.",
                            next: "search_result",
                            sw: Sw(("Charisma", 1.2f)), sb: Sb(("Stealth", 1.3f)),
                            fx: Fx(("_search_type", "black_market"), ("_search_difficulty", 4))),
                        O("Caravana Lejana", 5, "Una caravana de tierras exoticas.",
                            next: "search_result",
                            sw: Sw(("Charisma", 1.2f)),
                            fx: Fx(("_search_type", "caravan"), ("_search_difficulty", 3))),
                        O("Ruinas Comerciales", 3, "Restos de un antiguo emporio.",
                            next: "search_result",
                            sw: Sw(("Intelligence", 1.3f), ("Agility", 1.2f)),
                            fx: Fx(("_search_type", "ruins"), ("_search_difficulty", 5))),
                        O("Contacto Secreto", 4, "Un informante con conexiones exclusivas.",
                            next: "search_result",
                            sw: Sw(("Charisma", 1.4f)), sb: Sb(("Persuasion", 1.5f)),
                            fx: Fx(("_search_type", "contact"), ("_search_difficulty", 4)))
                    ),
                    S("search_result", "Resultado de la Busqueda", statCheck: "Intelligence", diffKey: "_search_difficulty", opts:
                        O("Hallazgo Excepcional", 2, "Encuentras bienes unicos e invaluables.",
                            tier: "high",
                            fx: Fx(("add_random_item", true), ("gain_wealth", true), ("rep", Rep(("Merchant Guild", 2))))),
                        O("Buenos Bienes", 5, "Encuentras mercancia de calidad.",
                            tier: "mid",
                            fx: Fx(("add_random_item", true), ("rep", Rep(("Merchant Guild", 1))))),
                        O("Nada Interesante", 4, "No encuentras nada que valga la pena.",
                            tier: "low"),
                        O("Trampa de Contrabandistas", 3, "Caes en una trampa de criminales.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 1), ("lose_wealth", true), ("rep", Rep(("Thieves Guild", -1)))))
                    )
                }
            },

            // ── ESTABLISH A BUSINESS ──
            ["Establish a Business"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("business_type", "Tipo de Negocio", opts:
                        O("Taberna", 5, "Un lugar de bebida y rumores.",
                            next: "business_result",
                            sw: Sw(("Charisma", 1.4f)),
                            fx: Fx(("_business", "taberna"), ("_biz_difficulty", 3))),
                        O("Forja", 4, "Un taller para crear armas y armaduras.",
                            next: "business_result",
                            sw: Sw(("Strength", 1.3f)), sb: Sb(("Smithing", 2.0f)),
                            fx: Fx(("_business", "forja"), ("_biz_difficulty", 4))),
                        O("Tienda de Magia", 3, "Venta de componentes y hechizos.",
                            next: "business_result",
                            sw: Sw(("Intelligence", 1.4f)), reqMagic: true,
                            fx: Fx(("_business", "magia"), ("_biz_difficulty", 5))),
                        O("Red de Informantes", 3, "Un negocio de secretos y espionaje.",
                            next: "business_result",
                            sw: Sw(("Charisma", 1.3f), ("Intelligence", 1.2f)), sb: Sb(("Stealth", 1.3f)),
                            fx: Fx(("_business", "espionaje"), ("_biz_difficulty", 6))),
                        O("Casa de Apuestas", 4, "Ganancias rapidas con mucho riesgo.",
                            next: "business_result",
                            sw: Sw(("Charisma", 1.2f)),
                            fx: Fx(("_business", "apuestas"), ("_biz_difficulty", 4)))
                    ),
                    S("business_result", "Resultado del Negocio", statCheck: "Charisma", diffKey: "_biz_difficulty", opts:
                        O("Negocio Prospero", 3, "Tu negocio florece rapidamente.",
                            tier: "high",
                            fx: Fx(("gain_wealth", true), ("stat_boost_specific", "Charisma"), ("add_condition", "business_owner"), ("rep", Rep(("Merchant Guild", 3))))),
                        O("Beneficios Moderados", 5, "Funciona, pero sin grandes ganancias.",
                            tier: "mid",
                            fx: Fx(("gain_wealth", true), ("add_condition", "business_owner"), ("rep", Rep(("Merchant Guild", 1))))),
                        O("Negocio Fallido", 4, "Los costos superan los ingresos.",
                            tier: "low",
                            fx: Fx(("lose_wealth", true))),
                        O("Robado por Competidores", 2, "Tu negocio es saboteado y saqueado.",
                            tier: "fail",
                            fx: Fx(("lose_wealth", true), ("stat_damage", 1), ("rep", Rep(("Merchant Guild", -2)))))
                    )
                }
            },

            // ── GUARD A CARAVAN ──
            ["Guard a Caravan"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("threat_type", "Tipo de Amenaza", opts:
                        O("Emboscada de Bandidos", 5, "Un grupo de bandidos ataca la caravana.",
                            next: "defense_strategy",
                            sw: Sw(("Strength", 1.3f)),
                            fx: Fx(("_threat", "bandidos"), ("_threat_difficulty", 4))),
                        O("Bestias Salvajes", 5, "Criaturas hambrientas acechan la ruta.",
                            next: "defense_strategy",
                            sw: Sw(("Agility", 1.2f)), sb: Sb(("Tracking", 1.5f)),
                            fx: Fx(("_threat", "bestias"), ("_threat_difficulty", 5))),
                        O("Clima Extremo", 4, "Una tormenta devastadora azota el camino.",
                            next: "defense_strategy",
                            sw: Sw(("Durability", 1.4f)),
                            fx: Fx(("_threat", "clima"), ("_threat_difficulty", 4))),
                        O("Ejercito Hostil", 2, "Soldados enemigos bloquean el paso.",
                            next: "defense_strategy",
                            sw: Sw(("Strength", 1.3f), ("Intelligence", 1.2f)),
                            fx: Fx(("_threat", "ejercito"), ("_threat_difficulty", 7)))
                    ),
                    S("defense_strategy", "Estrategia de Defensa", opts:
                        O("Contraemboscada", 4, "Preparas tu propia emboscada.",
                            next: "caravan_result",
                            sw: Sw(("Intelligence", 1.4f)), sb: Sb(("Tracking", 1.5f), ("Stealth", 1.3f))),
                        O("Combate Frontal", 5, "Enfrentas la amenaza cara a cara.",
                            next: "caravan_result",
                            sw: Sw(("Strength", 1.5f), ("Durability", 1.3f))),
                        O("Evasion Rapida", 4, "Intentas esquivar la amenaza por rutas alternas.",
                            next: "caravan_result",
                            sw: Sw(("Agility", 1.5f)), sb: Sb(("Tracking", 1.3f))),
                        O("Negociar Paso", 3, "Intentas dialogar o sobornar.",
                            next: "caravan_result",
                            sw: Sw(("Charisma", 1.6f)), sb: Sb(("Persuasion", 1.5f)))
                    ),
                    S("caravan_result", "Resultado de la Escolta", statCheck: "Strength", diffKey: "_threat_difficulty", opts:
                        O("Caravana Intacta", 3, "Proteges la caravana sin perdidas. Gran recompensa.",
                            tier: "high",
                            fx: Fx(("gain_wealth", true), ("stat_boost", 1), ("rep", Rep(("Merchant Guild", 3), ("Hunters Lodge", 1))))),
                        O("Danos Menores", 5, "La caravana llega con algunos danos.",
                            tier: "mid",
                            fx: Fx(("gain_wealth", true), ("rep", Rep(("Merchant Guild", 1))))),
                        O("Perdidas Graves", 4, "Gran parte de la mercancia se pierde.",
                            tier: "low",
                            fx: Fx(("rep", Rep(("Merchant Guild", -1))))),
                        O("Caravana Destruida", 2, "La caravana es arrasada. Apenas escapas.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 2), ("lose_wealth", true), ("rep", Rep(("Merchant Guild", -3)))))
                    )
                }
            },

            // ── TRACK A FUGITIVE ──
            ["Track a Fugitive"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("fugitive_type", "Tipo de Fugitivo", opts:
                        O("Criminal Peligroso", 5, "Un asesino en serie buscado por la corona.",
                            next: "tracking_method",
                            sw: Sw(("Strength", 1.2f), ("Agility", 1.2f)),
                            fx: Fx(("_fugitive", "criminal"), ("_fugitive_difficulty", 5))),
                        O("Noble Desertor", 4, "Un noble que huye con secretos de estado.",
                            next: "tracking_method",
                            sw: Sw(("Intelligence", 1.3f)), sb: Sb(("Investigation", 1.5f)),
                            fx: Fx(("_fugitive", "noble"), ("_fugitive_difficulty", 4))),
                        O("Mago Renegado", 3, "Un hechicero que rompio sus juramentos.",
                            next: "tracking_method",
                            sw: Sw(("Intelligence", 1.4f)),
                            fx: Fx(("_fugitive", "mago"), ("_fugitive_difficulty", 7))),
                        O("Espia Enemigo", 3, "Un infiltrado de una faccion rival.",
                            next: "tracking_method",
                            sw: Sw(("Agility", 1.3f)), sb: Sb(("Stealth", 1.5f), ("Tracking", 1.3f)),
                            fx: Fx(("_fugitive", "espia"), ("_fugitive_difficulty", 6)))
                    ),
                    S("tracking_method", "Metodo de Rastreo", opts:
                        O("Interrogar Contactos", 5, "Presionas a conocidos del fugitivo.",
                            next: "capture_result",
                            sw: Sw(("Charisma", 1.4f)), sb: Sb(("Persuasion", 1.5f), ("Intimidation", 2.0f))),
                        O("Rastrear Huellas", 5, "Sigues su rastro fisico.",
                            next: "capture_result",
                            sw: Sw(("Agility", 1.3f)), sb: Sb(("Tracking", 2.5f))),
                        O("Magia de Localizacion", 3, "Usas hechizos para encontrarlo.",
                            next: "capture_result",
                            sw: Sw(("Intelligence", 1.5f)), reqMagic: true),
                        O("Pagar Informantes", 4, "Compras informacion a la red criminal.",
                            next: "capture_result",
                            sw: Sw(("Charisma", 1.2f)),
                            fx: Fx(("lose_wealth", true), ("rep", Rep(("Thieves Guild", 1)))))
                    ),
                    S("capture_result", "Resultado de la Captura", statCheck: "Agility", diffKey: "_fugitive_difficulty", opts:
                        O("Captura Limpia", 3, "Atrapas al fugitivo sin incidentes.",
                            tier: "high",
                            fx: Fx(("gain_wealth", true), ("stat_boost", 1), ("rep", Rep(("The Crown", 3), ("Hunters Lodge", 1))))),
                        O("Captura Violenta", 4, "Lo atrapas pero con una pelea dura.",
                            tier: "mid",
                            fx: Fx(("gain_wealth", true), ("stat_damage", 1), ("rep", Rep(("The Crown", 1))))),
                        O("El Fugitivo Escapa", 4, "Se te escurre entre los dedos.",
                            tier: "low",
                            fx: Fx(("add_condition", "fugitive_loose"), ("rep", Rep(("The Crown", -1))))),
                        O("Emboscada del Fugitivo", 3, "Te tiende una trampa y te hiere gravemente.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 2), ("add_condition", "wounded")))
                    )
                }
            },

            // ── STUDY AN ANCIENT TOME ──
            ["Study an Ancient Tome"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("tome_type", "Tipo de Tomo", opts:
                        O("Grimorio de Conjuros", 4, "Un libro de hechizos poderosos.",
                            next: "study_result",
                            sw: Sw(("Intelligence", 1.5f)), reqMagic: true,
                            fx: Fx(("_tome", "grimorio"), ("_study_difficulty", 5))),
                        O("Tratado Alquimico", 5, "Formulas para pociones y transmutaciones.",
                            next: "study_result",
                            sw: Sw(("Intelligence", 1.3f)), sb: Sb(("Alchemy", 2.0f)),
                            fx: Fx(("_tome", "alquimia"), ("_study_difficulty", 4))),
                        O("Profecia Antigua", 3, "Un texto profetico sobre el fin de los tiempos.",
                            next: "study_result",
                            sw: Sw(("Intelligence", 1.4f)),
                            fx: Fx(("_tome", "profecia"), ("_study_difficulty", 6))),
                        O("Diario de Archimago", 3, "Las memorias de un mago legendario.",
                            next: "study_result",
                            sw: Sw(("Intelligence", 1.4f)), sb: Sb(("Investigation", 1.5f)),
                            fx: Fx(("_tome", "diario"), ("_study_difficulty", 5))),
                        O("Textos Prohibidos", 2, "Conocimiento sellado por la iglesia.",
                            next: "study_result",
                            sw: Sw(("Intelligence", 1.3f)),
                            fx: Fx(("_tome", "prohibido"), ("_study_difficulty", 7)))
                    ),
                    S("study_result", "Resultado del Estudio", statCheck: "Intelligence", diffKey: "_study_difficulty", opts:
                        O("Conocimiento Profundo", 3, "Comprendes secretos ocultos del universo.",
                            tier: "high",
                            fx: Fx(("stat_boost_specific", "Intelligence"), ("stat_boost", 1), ("rep", Rep(("Mages Circle", 3))))),
                        O("Algo Aprendido", 5, "Ganas conocimiento util, aunque fragmentario.",
                            tier: "mid",
                            fx: Fx(("stat_boost_specific", "Intelligence"), ("rep", Rep(("Mages Circle", 1))))),
                        O("Incomprensible", 4, "El texto es demasiado complejo para ti.",
                            tier: "low"),
                        O("Maldicion del Conocimiento", 2, "El tomo estaba maldito. Tu mente sufre.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 2), ("add_condition", "cursed"), ("rep", Rep(("Mages Circle", -1)))))
                    )
                }
            },

            // ── PERFORM A DARK RITUAL ──
            ["Perform a Dark Ritual"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("ritual_type", "Tipo de Ritual", opts:
                        O("Invocacion Demoniaca", 4, "Invocas a un demonio para negociar.",
                            next: "ritual_result",
                            sw: Sw(("Intelligence", 1.5f)),
                            fx: Fx(("_ritual", "demonio"), ("_ritual_difficulty", 7))),
                        O("Resurreccion", 3, "Intentas devolver un alma del mas alla.",
                            next: "ritual_result",
                            sw: Sw(("Intelligence", 1.4f)),
                            fx: Fx(("_ritual", "resurreccion"), ("_ritual_difficulty", 8))),
                        O("Pacto de Sangre", 4, "Sellas un pacto con tu propia sangre.",
                            next: "ritual_result",
                            sw: Sw(("Durability", 1.3f)),
                            fx: Fx(("_ritual", "pacto"), ("_ritual_difficulty", 5))),
                        O("Maldicion Dirigida", 4, "Lanzas una maldicion sobre tu enemigo.",
                            next: "ritual_result",
                            sw: Sw(("Intelligence", 1.3f), ("Charisma", 1.2f)),
                            fx: Fx(("_ritual", "maldicion"), ("_ritual_difficulty", 5))),
                        O("Ascension Oscura", 1, "Intentas absorber poder de las sombras.",
                            next: "ritual_result",
                            sw: Sw(("Intelligence", 1.5f), ("Durability", 1.3f)),
                            fx: Fx(("_ritual", "ascension"), ("_ritual_difficulty", 9)))
                    ),
                    S("ritual_result", "Resultado del Ritual", statCheck: "Intelligence", diffKey: "_ritual_difficulty", opts:
                        O("Ritual Perfecto", 2, "El ritual funciona a la perfeccion. Poder inmenso.",
                            tier: "high",
                            fx: Fx(("stat_boost", 2), ("add_condition", "dark_empowered"), ("rep", Rep(("Shadow Council", 3), ("Church of Light", -2))))),
                        O("Exito Parcial", 4, "Funciona, pero algo salio diferente a lo esperado.",
                            tier: "mid",
                            fx: Fx(("stat_boost", 1), ("rep", Rep(("Shadow Council", 1), ("Church of Light", -1))))),
                        O("Fallo Contenido", 4, "El ritual falla pero contienes el dano.",
                            tier: "low",
                            fx: Fx(("stat_damage", 1))),
                        O("Catastrofe Ritual", 3, "La energia descontrolada te devasta.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 3), ("add_condition", "cursed"), ("rep", Rep(("Shadow Council", -1))))),
                        O("Posesion Demoniaca", 1, "Algo oscuro toma control de tu cuerpo.",
                            tier: "fail",
                            fx: Fx(("terminal", "death")))
                    )
                }
            },

            // ── INFILTRATE A STRONGHOLD ──
            ["Infiltrate a Stronghold"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("entry_method", "Metodo de Entrada", opts:
                        O("Disfraz", 5, "Te haces pasar por alguien autorizado.",
                            next: "infiltrate_objective",
                            sw: Sw(("Charisma", 1.5f)), sb: Sb(("Disguise", 2.0f))),
                        O("Tuneles Subterraneos", 4, "Encuentras pasadizos secretos.",
                            next: "infiltrate_objective",
                            sw: Sw(("Intelligence", 1.3f)), sb: Sb(("Investigation", 1.5f))),
                        O("Soborno a Guardias", 4, "Pagas para que miren a otro lado.",
                            next: "infiltrate_objective",
                            sw: Sw(("Charisma", 1.3f)),
                            fx: Fx(("lose_wealth", true))),
                        O("Escalada Nocturna", 4, "Escalas los muros bajo el amparo de la noche.",
                            next: "infiltrate_objective",
                            sw: Sw(("Agility", 1.6f)), sb: Sb(("Stealth", 2.0f))),
                        O("Magia de Invisibilidad", 2, "Te vuelves invisible magicamente.",
                            next: "infiltrate_objective",
                            sw: Sw(("Intelligence", 1.5f)), reqMagic: true)
                    ),
                    S("infiltrate_objective", "Objetivo en el Interior", opts:
                        O("Robar un Tesoro", 5, "Buscas la camara del tesoro.",
                            next: "infiltrate_result",
                            sw: Sw(("Agility", 1.3f)), sb: Sb(("Lockpicking", 2.0f)),
                            fx: Fx(("_objective", "tesoro"), ("_infil_difficulty", 5))),
                        O("Liberar un Prisionero", 4, "Rescatas a alguien de las mazmorras.",
                            next: "infiltrate_result",
                            sw: Sw(("Strength", 1.2f), ("Agility", 1.2f)),
                            fx: Fx(("_objective", "prisionero"), ("_infil_difficulty", 5))),
                        O("Sabotear Defensas", 3, "Destruyes fortificaciones desde dentro.",
                            next: "infiltrate_result",
                            sw: Sw(("Intelligence", 1.3f)),
                            fx: Fx(("_objective", "sabotaje"), ("_infil_difficulty", 6))),
                        O("Espiar al Enemigo", 4, "Recoges informacion vital.",
                            next: "infiltrate_result",
                            sw: Sw(("Intelligence", 1.3f), ("Agility", 1.2f)), sb: Sb(("Stealth", 1.5f)),
                            fx: Fx(("_objective", "espionaje"), ("_infil_difficulty", 4)))
                    ),
                    S("infiltrate_result", "Resultado de la Infiltracion", statCheck: "Agility", diffKey: "_infil_difficulty", opts:
                        O("Mision Perfecta", 3, "Completas el objetivo sin ser detectado.",
                            tier: "high",
                            fx: Fx(("stat_boost", 1), ("gain_wealth", true), ("rep", Rep(("Thieves Guild", 3))))),
                        O("Exito con Complicaciones", 4, "Lo logras pero te detectan al salir.",
                            tier: "mid",
                            fx: Fx(("gain_wealth", true), ("add_condition", "enemy_alerted"), ("rep", Rep(("Thieves Guild", 1))))),
                        O("Descubierto y Perseguido", 4, "Te detectan y debes huir.",
                            tier: "low",
                            fx: Fx(("stat_damage", 1), ("add_condition", "enemy_alerted"))),
                        O("Capturado", 3, "Te atrapan y te encierran.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 2), ("add_condition", "imprisoned"), ("rep", Rep(("The Crown", -2)))))
                    )
                }
            },

            // ── COMPETE IN A TOURNAMENT ──
            ["Compete in a Tournament"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("tournament_type", "Tipo de Torneo", opts:
                        O("Combate Cuerpo a Cuerpo", 5, "Lucha sin armas en la arena.",
                            next: "tournament_round",
                            sw: Sw(("Strength", 1.5f), ("Durability", 1.3f)),
                            fx: Fx(("_tournament", "melee"), ("_tourn_difficulty", 5))),
                        O("Duelo de Espadas", 5, "Enfrentamientos uno contra uno con armas.",
                            next: "tournament_round",
                            sw: Sw(("Strength", 1.3f), ("Agility", 1.3f)),
                            fx: Fx(("_tournament", "swords"), ("_tourn_difficulty", 5))),
                        O("Tiro con Arco", 4, "Competencia de precision a distancia.",
                            next: "tournament_round",
                            sw: Sw(("Agility", 1.6f)), sb: Sb(("Archery", 2.5f)),
                            fx: Fx(("_tournament", "archery"), ("_tourn_difficulty", 4))),
                        O("Justa a Caballo", 3, "Cargas a caballo con lanza.",
                            next: "tournament_round",
                            sw: Sw(("Strength", 1.4f), ("Agility", 1.2f)),
                            fx: Fx(("_tournament", "joust"), ("_tourn_difficulty", 6))),
                        O("Duelo de Magia", 2, "Un torneo de hechiceros.",
                            next: "tournament_round",
                            sw: Sw(("Intelligence", 1.6f)), reqMagic: true,
                            fx: Fx(("_tournament", "magic"), ("_tourn_difficulty", 6)))
                    ),
                    S("tournament_round", "Ronda Final", statCheck: "Strength", diffKey: "_tourn_difficulty", opts:
                        O("Campeon!", 3, "Vences a todos los rivales. Eres el campeon!",
                            tier: "high",
                            fx: Fx(("stat_boost", 2), ("gain_wealth", true), ("add_condition", "tournament_champion"), ("rep", Rep(("Hunters Lodge", 3), ("The Crown", 2))))),
                        O("Finalista", 4, "Llegas a la final pero pierdes el ultimo combate.",
                            tier: "mid",
                            fx: Fx(("stat_boost", 1), ("rep", Rep(("Hunters Lodge", 1))))),
                        O("Eliminado en Semifinal", 4, "Un rival fuerte te derrota antes de la final.",
                            tier: "low",
                            fx: Fx(("rep", Rep(("Hunters Lodge", -1))))),
                        O("Descalificado", 2, "Te acusan de hacer trampa. Humillacion publica.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 1), ("rep", Rep(("Hunters Lodge", -2), ("The Crown", -1))))),
                        O("Herido Gravemente", 2, "Un golpe brutal te deja malherido.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 2), ("add_condition", "wounded")))
                    )
                }
            },

            // ── LEAD A REBELLION ──
            ["Lead a Rebellion"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("rebellion_strategy", "Estrategia de Rebelion", opts:
                        O("Asalto Directo", 4, "Atacas el centro de poder directamente.",
                            next: "rebellion_result",
                            sw: Sw(("Strength", 1.5f), ("Durability", 1.3f)),
                            fx: Fx(("_strategy", "asalto"), ("_rebel_difficulty", 7))),
                        O("Subversion Interna", 4, "Corroes el poder desde dentro.",
                            next: "rebellion_result",
                            sw: Sw(("Intelligence", 1.4f), ("Charisma", 1.3f)), sb: Sb(("Persuasion", 1.5f)),
                            fx: Fx(("_strategy", "subversion"), ("_rebel_difficulty", 6))),
                        O("Alianza con Bandidos", 3, "Te alias con elementos criminales.",
                            next: "rebellion_result",
                            sw: Sw(("Charisma", 1.3f)),
                            fx: Fx(("_strategy", "bandidos"), ("_rebel_difficulty", 5), ("rep", Rep(("Thieves Guild", 1))))),
                        O("Propaganda Popular", 4, "Ganas al pueblo con discursos y promesas.",
                            next: "rebellion_result",
                            sw: Sw(("Charisma", 1.6f)), sb: Sb(("Persuasion", 2.0f)),
                            fx: Fx(("_strategy", "propaganda"), ("_rebel_difficulty", 5))),
                        O("Asesinato Politico", 2, "Eliminas al lider enemigo directamente.",
                            next: "rebellion_result",
                            sw: Sw(("Agility", 1.5f)), sb: Sb(("Stealth", 2.0f)),
                            fx: Fx(("_strategy", "asesinato"), ("_rebel_difficulty", 8)))
                    ),
                    S("rebellion_result", "Resultado de la Rebelion", statCheck: "Charisma", diffKey: "_rebel_difficulty", opts:
                        O("Victoria Revolucionaria", 2, "El regimen cae. Eres el nuevo lider.",
                            tier: "high",
                            fx: Fx(("stat_boost", 2), ("gain_wealth", true), ("add_condition", "rebel_leader"), ("rep", Rep(("The Crown", -3), ("Shadow Council", 2))))),
                        O("Control Parcial", 4, "Ganas terreno pero el conflicto continua.",
                            tier: "mid",
                            fx: Fx(("stat_boost", 1), ("add_condition", "rebellion_ongoing"), ("rep", Rep(("The Crown", -2))))),
                        O("Represion Brutal", 4, "El poder contraataca con fuerza.",
                            tier: "low",
                            fx: Fx(("stat_damage", 1), ("add_condition", "wanted_rebel"), ("rep", Rep(("The Crown", -1))))),
                        O("Aplastados", 3, "La rebelion es destruida sin piedad.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 3), ("add_condition", "wanted_rebel"), ("rep", Rep(("The Crown", -3))))),
                        O("Ejecutado!", 1, "Te capturan y te ejecutan publicamente.",
                            tier: "fail",
                            fx: Fx(("terminal", "death")))
                    )
                }
            },

            // ── SERVE AT COURT ──
            ["Serve at Court"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("court_role", "Tu Rol en la Corte", opts:
                        O("Consejero del Rey", 4, "Asesoras al monarca en decisiones criticas.",
                            next: "court_intrigue",
                            sw: Sw(("Intelligence", 1.5f), ("Charisma", 1.3f)),
                            fx: Fx(("_role", "consejero"), ("_court_difficulty", 5))),
                        O("Embajador Diplomatico", 4, "Representas la corona ante facciones extranjeras.",
                            next: "court_intrigue",
                            sw: Sw(("Charisma", 1.6f)), sb: Sb(("Persuasion", 2.0f)),
                            fx: Fx(("_role", "embajador"), ("_court_difficulty", 5))),
                        O("Espia de la Corte", 3, "Vigilas y descubres conspiraciones.",
                            next: "court_intrigue",
                            sw: Sw(("Agility", 1.3f), ("Intelligence", 1.3f)), sb: Sb(("Stealth", 1.5f)),
                            fx: Fx(("_role", "espia"), ("_court_difficulty", 6))),
                        O("Organizador de Eventos", 4, "Planificas banquetes y ceremonias.",
                            next: "court_intrigue",
                            sw: Sw(("Charisma", 1.4f)),
                            fx: Fx(("_role", "organizador"), ("_court_difficulty", 3))),
                        O("Guardia Personal", 3, "Proteges la vida del monarca.",
                            next: "court_intrigue",
                            sw: Sw(("Strength", 1.4f), ("Agility", 1.3f)),
                            fx: Fx(("_role", "guardia"), ("_court_difficulty", 5)))
                    ),
                    S("court_intrigue", "Intrigas de la Corte", opts:
                        O("Conspiracion Descubierta", 4, "Descubres un complot contra el rey.",
                            next: "court_result",
                            sw: Sw(("Intelligence", 1.4f)), sb: Sb(("Investigation", 1.5f)),
                            fx: Fx(("_intrigue", "conspiracion"))),
                        O("Rival Politico", 5, "Un noble poderoso te desafia.",
                            next: "court_result",
                            sw: Sw(("Charisma", 1.3f)),
                            fx: Fx(("_intrigue", "rival"))),
                        O("Oferta de Soborno", 4, "Te ofrecen oro a cambio de traicion.",
                            next: "court_result",
                            sw: Sw(("Charisma", 1.2f)),
                            fx: Fx(("_intrigue", "soborno"))),
                        O("Romance Prohibido", 3, "Te involucras emocionalmente con alguien poderoso.",
                            next: "court_result",
                            sw: Sw(("Charisma", 1.5f)),
                            fx: Fx(("_intrigue", "romance")))
                    ),
                    S("court_result", "Resultado en la Corte", statCheck: "Charisma", diffKey: "_court_difficulty", opts:
                        O("Favor del Rey", 3, "El monarca te recompensa con poder y tierras.",
                            tier: "high",
                            fx: Fx(("stat_boost_specific", "Charisma"), ("gain_wealth", true), ("rep", Rep(("The Crown", 4))))),
                        O("Reconocimiento Publico", 5, "Tu trabajo es reconocido positivamente.",
                            tier: "mid",
                            fx: Fx(("rep", Rep(("The Crown", 2))), ("gain_wealth", true))),
                        O("Pasas Desapercibido", 4, "Tu servicio no impresiona a nadie.",
                            tier: "low"),
                        O("Caida en Desgracia", 2, "Caes en una trampa politica y pierdes todo.",
                            tier: "fail",
                            fx: Fx(("lose_wealth", true), ("stat_damage", 1), ("rep", Rep(("The Crown", -3))), ("add_condition", "disgraced")))
                    )
                }
            },

            // ── ATTEMPT APOTHEOSIS ──
            ["Attempt Apotheosis"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("path_to_godhood", "Camino a la Divinidad", opts:
                        O("Ritual Supremo", 4, "Un ritual milenario para ascender.",
                            next: "apotheosis_trial",
                            sw: Sw(("Intelligence", 1.6f)),
                            fx: Fx(("_path", "ritual"), ("_apo_difficulty", 8))),
                        O("Absorber Poder Divino", 3, "Intentas robar poder a un dios menor.",
                            next: "apotheosis_trial",
                            sw: Sw(("Strength", 1.3f), ("Intelligence", 1.4f)),
                            fx: Fx(("_path", "absorcion"), ("_apo_difficulty", 9))),
                        O("Sacrificio de Seguidores", 3, "El poder de las almas como combustible.",
                            next: "apotheosis_trial",
                            sw: Sw(("Charisma", 1.3f)),
                            fx: Fx(("_path", "sacrificio"), ("_apo_difficulty", 7), ("rep", Rep(("Church of Light", -3))))),
                        O("Prueba de los Dioses", 2, "Los dioses mismos te someten a pruebas.",
                            next: "apotheosis_trial",
                            sw: Sw(("Durability", 1.4f), ("Intelligence", 1.3f)),
                            fx: Fx(("_path", "prueba"), ("_apo_difficulty", 10)))
                    ),
                    S("apotheosis_trial", "Prueba Final de Ascension", statCheck: "Intelligence", diffKey: "_apo_difficulty", opts:
                        O("Ascendes a la Divinidad!", 1, "Te conviertes en un nuevo dios. Tu leyenda es eterna.",
                            tier: "high",
                            fx: Fx(("terminal", "victory"))),
                        O("Semidivinidad", 3, "No llegas a dios, pero ganas poder inmenso.",
                            tier: "mid",
                            fx: Fx(("stat_boost", 3), ("add_condition", "semidivine"), ("rep", Rep(("Mages Circle", 3), ("Church of Light", -2))))),
                        O("Fallo Monumental", 4, "Tu cuerpo no puede contener tanto poder.",
                            tier: "low",
                            fx: Fx(("stat_damage", 3), ("add_condition", "cursed"))),
                        O("Destruccion Total", 3, "El intento te consume completamente.",
                            tier: "fail",
                            fx: Fx(("terminal", "death")))
                    )
                }
            },

            // ── BANDIT RAID ──
            ["Bandit Raid"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("raid_response", "Respuesta al Asalto", opts:
                        O("Defender la Posicion", 5, "Te atrincheras y luchas.",
                            next: "raid_result",
                            sw: Sw(("Strength", 1.4f), ("Durability", 1.3f)),
                            fx: Fx(("_response", "defender"))),
                        O("Contraataque Sorpresa", 4, "Les das la vuelta con un ataque inesperado.",
                            next: "raid_result",
                            sw: Sw(("Agility", 1.4f), ("Intelligence", 1.2f)), sb: Sb(("Stealth", 1.5f)),
                            fx: Fx(("_response", "contraataque"))),
                        O("Negociar con el Lider", 3, "Intentas hablar con el jefe bandido.",
                            next: "raid_result",
                            sw: Sw(("Charisma", 1.6f)), sb: Sb(("Persuasion", 1.5f)),
                            fx: Fx(("_response", "negociar"))),
                        O("Organizar a los Civiles", 4, "Organizas la defensa del pueblo.",
                            next: "raid_result",
                            sw: Sw(("Charisma", 1.3f), ("Intelligence", 1.2f)),
                            fx: Fx(("_response", "organizar")))
                    ),
                    S("raid_result", "Resultado del Asalto", statCheck: "Strength", opts:
                        O("Bandidos Derrotados", 3, "Los bandidos huyen derrotados.",
                            tier: "high",
                            fx: Fx(("stat_boost", 1), ("gain_wealth", true), ("rep", Rep(("The Crown", 2), ("Hunters Lodge", 1))))),
                        O("Victoria con Bajas", 5, "Ganas, pero hay perdidas considerables.",
                            tier: "mid",
                            fx: Fx(("stat_damage", 1), ("rep", Rep(("The Crown", 1))))),
                        O("Empate Sangriento", 4, "Ambos bandos sufren, nadie gana claramente.",
                            tier: "low",
                            fx: Fx(("stat_damage", 1))),
                        O("Saqueo Total", 2, "Los bandidos arrasan con todo.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 2), ("lose_wealth", true), ("rep", Rep(("The Crown", -1)))))
                    )
                }
            },

            // ── DRAGON SIGHTING ──
            ["Dragon Sighting"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("dragon_approach", "Como Enfrentar al Dragon", opts:
                        O("Cazar al Dragon", 4, "Intentas abatir a la bestia legendaria.",
                            next: "dragon_result",
                            sw: Sw(("Strength", 1.5f), ("Durability", 1.3f)),
                            fx: Fx(("_approach", "cazar"), ("_dragon_difficulty", 9))),
                        O("Negociar con el Dragon", 3, "Los dragones son inteligentes. Intentas hablar.",
                            next: "dragon_result",
                            sw: Sw(("Charisma", 1.4f), ("Intelligence", 1.3f)),
                            fx: Fx(("_approach", "negociar"), ("_dragon_difficulty", 7))),
                        O("Evacuar la Zona", 5, "Organizas la evacuacion de la region.",
                            next: "dragon_result",
                            sw: Sw(("Charisma", 1.3f), ("Intelligence", 1.2f)),
                            fx: Fx(("_approach", "evacuar"), ("_dragon_difficulty", 4))),
                        O("Buscar su Guarida", 3, "Buscas su nido para encontrar tesoros.",
                            next: "dragon_result",
                            sw: Sw(("Agility", 1.4f), ("Intelligence", 1.3f)), sb: Sb(("Tracking", 2.0f), ("Stealth", 1.5f)),
                            fx: Fx(("_approach", "guarida"), ("_dragon_difficulty", 8)))
                    ),
                    S("dragon_result", "Resultado del Encuentro", statCheck: "Strength", diffKey: "_dragon_difficulty", opts:
                        O("Triunfo Legendario", 2, "Logras lo imposible. Tu nombre sera recordado.",
                            tier: "high",
                            fx: Fx(("stat_boost", 3), ("add_random_item", true), ("rep", Rep(("Hunters Lodge", 4), ("The Crown", 2))))),
                        O("Exito Parcial", 4, "No es perfecto, pero sobrevives con ganancias.",
                            tier: "mid",
                            fx: Fx(("stat_boost", 1), ("rep", Rep(("Hunters Lodge", 1))))),
                        O("Retirada Necesaria", 4, "El dragon es demasiado. Apenas escapas.",
                            tier: "low",
                            fx: Fx(("stat_damage", 1), ("add_condition", "dragon_fear"))),
                        O("Calcinado", 2, "El fuego del dragon te alcanza de lleno.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 3), ("add_condition", "burned"))),
                        O("Devorado", 1, "El dragon te consume entero.",
                            tier: "fail",
                            fx: Fx(("terminal", "death")))
                    )
                }
            },

            // ── DEMONIC RIFT ──
            ["Demonic Rift"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("rift_response", "Respuesta al Portal", opts:
                        O("Cerrar el Portal", 4, "Intentas sellar la grieta dimensional.",
                            next: "rift_result",
                            sw: Sw(("Intelligence", 1.5f)), reqMagic: true,
                            fx: Fx(("_response", "cerrar"), ("_rift_difficulty", 7))),
                        O("Combatir Demonios", 5, "Luchas contra las criaturas que emergen.",
                            next: "rift_result",
                            sw: Sw(("Strength", 1.5f), ("Durability", 1.3f)),
                            fx: Fx(("_response", "combatir"), ("_rift_difficulty", 6))),
                        O("Aprovechar su Poder", 3, "Absorbes energia del portal.",
                            next: "rift_result",
                            sw: Sw(("Intelligence", 1.4f)),
                            fx: Fx(("_response", "absorber"), ("_rift_difficulty", 8))),
                        O("Evacuar y Vigilar", 4, "Alejas a la gente y observas.",
                            next: "rift_result",
                            sw: Sw(("Intelligence", 1.2f), ("Charisma", 1.2f)),
                            fx: Fx(("_response", "vigilar"), ("_rift_difficulty", 3)))
                    ),
                    S("rift_result", "Resultado del Portal", statCheck: "Intelligence", diffKey: "_rift_difficulty", opts:
                        O("Portal Sellado", 3, "El portal se cierra. La amenaza termina.",
                            tier: "high",
                            fx: Fx(("stat_boost", 2), ("rep", Rep(("Church of Light", 3), ("Mages Circle", 2))))),
                        O("Contencion Parcial", 4, "Reduces la amenaza pero el portal persiste.",
                            tier: "mid",
                            fx: Fx(("stat_boost", 1), ("add_condition", "rift_unstable"), ("rep", Rep(("Church of Light", 1))))),
                        O("Contaminacion Oscura", 3, "La energia demoniaca te afecta.",
                            tier: "low",
                            fx: Fx(("stat_damage", 1), ("add_condition", "corrupted"))),
                        O("Explosion Infernal", 2, "El portal explota en energia caosica.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 3), ("rep", Rep(("Church of Light", -2)))))
                    )
                }
            },

            // ── MERCHANT GUILD OFFER ──
            ["Merchant Guild Offer"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("offer_type", "Tipo de Oferta", opts:
                        O("Contrato Comercial", 5, "Una ruta comercial lucrativa.",
                            next: "offer_result",
                            sw: Sw(("Charisma", 1.3f)),
                            fx: Fx(("_offer", "contrato"), ("_offer_difficulty", 4))),
                        O("Mision de Escolta", 4, "Proteger un envio valioso.",
                            next: "offer_result",
                            sw: Sw(("Strength", 1.3f)),
                            fx: Fx(("_offer", "escolta"), ("_offer_difficulty", 5))),
                        O("Inversion Arriesgada", 3, "Una apuesta financiera con grandes retornos.",
                            next: "offer_result",
                            sw: Sw(("Intelligence", 1.3f)),
                            fx: Fx(("_offer", "inversion"), ("_offer_difficulty", 5))),
                        O("Eliminar Competencia", 3, "Trabajo sucio contra rivales del gremio.",
                            next: "offer_result",
                            sw: Sw(("Agility", 1.3f)), sb: Sb(("Stealth", 1.5f)),
                            fx: Fx(("_offer", "eliminar"), ("_offer_difficulty", 6)))
                    ),
                    S("offer_result", "Resultado de la Oferta", statCheck: "Charisma", diffKey: "_offer_difficulty", opts:
                        O("Gran Beneficio", 3, "El negocio sale redondo. Ganancias excelentes.",
                            tier: "high",
                            fx: Fx(("gain_wealth", true), ("stat_boost", 1), ("rep", Rep(("Merchant Guild", 3))))),
                        O("Beneficio Moderado", 5, "Ganas algo, pero no tanto como esperabas.",
                            tier: "mid",
                            fx: Fx(("gain_wealth", true), ("rep", Rep(("Merchant Guild", 1))))),
                        O("Sin Ganancias", 4, "El trato no lleva a nada concreto.",
                            tier: "low"),
                        O("Estafa del Gremio", 2, "Te usan como peon desechable.",
                            tier: "fail",
                            fx: Fx(("lose_wealth", true), ("stat_damage", 1), ("rep", Rep(("Merchant Guild", -2)))))
                    )
                }
            },

            // ── NOBLE SUMMONS ──
            ["Noble Summons"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("summons_mission", "Mision de la Nobleza", opts:
                        O("Escoltar al Heredero", 4, "Proteger al heredero en un viaje peligroso.",
                            next: "summons_result",
                            sw: Sw(("Strength", 1.3f), ("Agility", 1.2f)),
                            fx: Fx(("_mission", "escolta"), ("_summons_difficulty", 5))),
                        O("Negociacion Diplomatica", 4, "Representar la casa noble en negociaciones.",
                            next: "summons_result",
                            sw: Sw(("Charisma", 1.5f)), sb: Sb(("Persuasion", 2.0f)),
                            fx: Fx(("_mission", "diplomacia"), ("_summons_difficulty", 5))),
                        O("Investigar Traicion", 3, "Descubrir un traidor entre la nobleza.",
                            next: "summons_result",
                            sw: Sw(("Intelligence", 1.4f)), sb: Sb(("Investigation", 1.5f)),
                            fx: Fx(("_mission", "traicion"), ("_summons_difficulty", 6))),
                        O("Recuperar Reliquia Familiar", 3, "Encontrar un tesoro ancestral robado.",
                            next: "summons_result",
                            sw: Sw(("Agility", 1.3f), ("Intelligence", 1.2f)),
                            fx: Fx(("_mission", "reliquia"), ("_summons_difficulty", 6)))
                    ),
                    S("summons_result", "Resultado de la Mision", statCheck: "Charisma", diffKey: "_summons_difficulty", opts:
                        O("Recompensa Real", 3, "La nobleza te recompensa generosamente.",
                            tier: "high",
                            fx: Fx(("gain_wealth", true), ("stat_boost", 1), ("rep", Rep(("The Crown", 3))))),
                        O("Mision Cumplida", 5, "Completas la tarea satisfactoriamente.",
                            tier: "mid",
                            fx: Fx(("rep", Rep(("The Crown", 2))))),
                        O("Resultado Mediocre", 4, "La nobleza no esta impresionada.",
                            tier: "low",
                            fx: Fx(("rep", Rep(("The Crown", -1))))),
                        O("Fracaso Deshonroso", 2, "Fallas y la nobleza te castiga.",
                            tier: "fail",
                            fx: Fx(("lose_wealth", true), ("stat_damage", 1), ("rep", Rep(("The Crown", -3)))))
                    )
                }
            },

            // ── CULT WHISPER ──
            ["Cult Whisper"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("cult_response", "Respuesta al Culto", opts:
                        O("Unirse al Culto", 4, "Aceptas sus ense\u00f1anzas oscuras.",
                            next: "cult_result",
                            sw: Sw(("Intelligence", 1.3f)),
                            fx: Fx(("_response", "unirse"), ("_cult_difficulty", 4))),
                        O("Infiltrarse como Espia", 4, "Finges unirte para descubrir sus planes.",
                            next: "cult_result",
                            sw: Sw(("Charisma", 1.4f), ("Agility", 1.2f)), sb: Sb(("Stealth", 1.5f)),
                            fx: Fx(("_response", "infiltrar"), ("_cult_difficulty", 6))),
                        O("Denunciar al Culto", 3, "Alertas a las autoridades.",
                            next: "cult_result",
                            sw: Sw(("Charisma", 1.2f)),
                            fx: Fx(("_response", "denunciar"), ("_cult_difficulty", 3))),
                        O("Robar sus Secretos", 3, "Tomas sus textos y huyes.",
                            next: "cult_result",
                            sw: Sw(("Agility", 1.5f)), sb: Sb(("Stealth", 2.0f), ("Lockpicking", 1.5f)),
                            fx: Fx(("_response", "robar"), ("_cult_difficulty", 5)))
                    ),
                    S("cult_result", "Resultado con el Culto", statCheck: "Intelligence", diffKey: "_cult_difficulty", opts:
                        O("Poder Oscuro Obtenido", 3, "Ganas conocimiento y poder prohibido.",
                            tier: "high",
                            fx: Fx(("stat_boost", 2), ("rep", Rep(("Shadow Council", 3), ("Church of Light", -2))))),
                        O("Secretos Revelados", 4, "Descubres informacion importante.",
                            tier: "mid",
                            fx: Fx(("stat_boost", 1), ("add_condition", "cult_knowledge"), ("rep", Rep(("Shadow Council", 1))))),
                        O("Nada Util", 4, "El culto resulta ser un fraude.",
                            tier: "low"),
                        O("Maldicion del Culto", 3, "El culto te maldice por inmiscuirte.",
                            tier: "fail",
                            fx: Fx(("add_condition", "cursed"), ("stat_damage", 1), ("rep", Rep(("Shadow Council", -2)))))
                    )
                }
            },

            // ── ASSASSINATION ATTEMPT ──
            ["Assassination Attempt"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("attack_response", "Reaccion al Ataque", opts:
                        O("Contraatacar", 5, "Te defiendes y atacas al asesino.",
                            next: "assassination_result",
                            sw: Sw(("Strength", 1.5f), ("Agility", 1.3f)),
                            fx: Fx(("_response", "contraatacar"))),
                        O("Esquivar y Huir", 4, "Te alejas del peligro rapidamente.",
                            next: "assassination_result",
                            sw: Sw(("Agility", 1.6f)), sb: Sb(("Stealth", 1.5f)),
                            fx: Fx(("_response", "huir"))),
                        O("Usar Magia Defensiva", 3, "Invocas proteccion magica.",
                            next: "assassination_result",
                            sw: Sw(("Intelligence", 1.5f)), reqMagic: true,
                            fx: Fx(("_response", "magia"))),
                        O("Negociar con el Asesino", 3, "Intentas comprar tu vida.",
                            next: "assassination_result",
                            sw: Sw(("Charisma", 1.5f)),
                            fx: Fx(("_response", "negociar")))
                    ),
                    S("assassination_result", "Resultado del Atentado", statCheck: "Agility", opts:
                        O("Asesino Capturado", 3, "Capturas al asesino y descubres quien lo envio.",
                            tier: "high",
                            fx: Fx(("stat_boost", 1), ("add_condition", "knows_enemy"), ("rep", Rep(("The Crown", 2))))),
                        O("Sobrevives Ileso", 4, "Escapas sin heridas graves.",
                            tier: "mid",
                            fx: Fx(("add_condition", "assassination_survivor"))),
                        O("Herido pero Vivo", 4, "El ataque te deja herido.",
                            tier: "low",
                            fx: Fx(("stat_damage", 1), ("add_condition", "wounded"))),
                        O("Herida Mortal", 2, "El veneno del asesino es letal.",
                            tier: "fail",
                            fx: Fx(("terminal", "death")))
                    )
                }
            },

            // ── SHADOW MARKET ──
            ["Shadow Market"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("market_action", "Accion en el Mercado Negro", opts:
                        O("Comprar Artefactos", 5, "Buscas objetos raros y prohibidos.",
                            next: "market_result",
                            sw: Sw(("Intelligence", 1.3f)), sb: Sb(("Investigation", 1.3f)),
                            fx: Fx(("_action", "comprar"))),
                        O("Vender Informacion", 4, "Vendes secretos al mejor postor.",
                            next: "market_result",
                            sw: Sw(("Charisma", 1.4f)),
                            fx: Fx(("_action", "vender"))),
                        O("Buscar Contactos", 4, "Amplias tu red de informantes.",
                            next: "market_result",
                            sw: Sw(("Charisma", 1.3f)), sb: Sb(("Persuasion", 1.5f)),
                            fx: Fx(("_action", "contactos"))),
                        O("Robar a los Vendedores", 3, "Intentas robar mercancia.",
                            next: "market_result",
                            sw: Sw(("Agility", 1.5f)), sb: Sb(("Stealth", 2.0f), ("Lockpicking", 1.5f)),
                            fx: Fx(("_action", "robar")))
                    ),
                    S("market_result", "Resultado del Mercado Negro", statCheck: "Charisma", opts:
                        O("Gran Negocio", 3, "Consigues exactamente lo que buscabas.",
                            tier: "high",
                            fx: Fx(("add_random_item", true), ("gain_wealth", true), ("rep", Rep(("Thieves Guild", 2))))),
                        O("Trato Aceptable", 5, "No es perfecto pero sirve.",
                            tier: "mid",
                            fx: Fx(("add_random_item", true), ("rep", Rep(("Thieves Guild", 1))))),
                        O("Sin Suerte", 4, "No encuentras nada interesante.",
                            tier: "low"),
                        O("Trampa!", 2, "Era una trampa de la guardia o de criminales.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 1), ("lose_wealth", true), ("rep", Rep(("Thieves Guild", -2)))))
                    )
                }
            },

            // ── TRIAL BY COMBAT ──
            ["Trial by Combat"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("trial_preparation", "Preparacion para el Duelo", opts:
                        O("Aceptar el Desafio", 5, "Luchas tu mismo con honor.",
                            next: "trial_result",
                            sw: Sw(("Strength", 1.5f), ("Durability", 1.3f)),
                            fx: Fx(("_prep", "personal"), ("_trial_difficulty", 5))),
                        O("Buscar un Campeon", 4, "Contratas a un luchador profesional.",
                            next: "trial_result",
                            sw: Sw(("Charisma", 1.3f)),
                            fx: Fx(("_prep", "campeon"), ("_trial_difficulty", 4), ("lose_wealth", true))),
                        O("Entrenar Intensamente", 4, "Dedicas tiempo a prepararte.",
                            next: "trial_result",
                            sw: Sw(("Strength", 1.3f), ("Agility", 1.2f)),
                            fx: Fx(("_prep", "entrenar"), ("_trial_difficulty", 4))),
                        O("Trucos Sucios", 3, "Envenenas el arma o sobornas al juez.",
                            next: "trial_result",
                            sw: Sw(("Intelligence", 1.3f)), sb: Sb(("Stealth", 1.5f)),
                            fx: Fx(("_prep", "truco"), ("_trial_difficulty", 3)))
                    ),
                    S("trial_result", "Resultado del Juicio", statCheck: "Strength", diffKey: "_trial_difficulty", opts:
                        O("Victoria Heroica", 3, "Ganas el duelo con honor y gloria.",
                            tier: "high",
                            fx: Fx(("stat_boost", 1), ("rep", Rep(("Hunters Lodge", 2), ("The Crown", 2))))),
                        O("Victoria Ajustada", 5, "Ganas por poco. Mantenes tu honor.",
                            tier: "mid",
                            fx: Fx(("rep", Rep(("The Crown", 1))))),
                        O("Derrota Honrosa", 4, "Pierdes pero con dignidad.",
                            tier: "low",
                            fx: Fx(("stat_damage", 1), ("rep", Rep(("The Crown", -1))))),
                        O("Derrota Humillante", 2, "Pierdes vergonzosamente.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 2), ("rep", Rep(("Hunters Lodge", -2), ("The Crown", -2))))),
                        O("Muerte en el Duelo", 1, "Tu oponente te asesta un golpe mortal.",
                            tier: "fail",
                            fx: Fx(("terminal", "death")))
                    )
                }
            },

            // ── FORBIDDEN LIBRARY ──
            ["Forbidden Library"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("library_action", "Accion en la Biblioteca", opts:
                        O("Estudiar Textos Arcanos", 5, "Lees los textos prohibidos.",
                            next: "library_result",
                            sw: Sw(("Intelligence", 1.5f)), sb: Sb(("Investigation", 1.5f)),
                            fx: Fx(("_action", "estudiar"), ("_lib_difficulty", 5))),
                        O("Robar Grimorios", 4, "Te llevas los libros mas valiosos.",
                            next: "library_result",
                            sw: Sw(("Agility", 1.4f)), sb: Sb(("Stealth", 1.5f), ("Lockpicking", 1.5f)),
                            fx: Fx(("_action", "robar"), ("_lib_difficulty", 5))),
                        O("Buscar Hechizo Especifico", 4, "Buscas un conjuro concreto.",
                            next: "library_result",
                            sw: Sw(("Intelligence", 1.5f)), reqMagic: true,
                            fx: Fx(("_action", "buscar"), ("_lib_difficulty", 6))),
                        O("Copiar Mapas Antiguos", 3, "Copias cartografia secreta.",
                            next: "library_result",
                            sw: Sw(("Intelligence", 1.3f)),
                            fx: Fx(("_action", "copiar"), ("_lib_difficulty", 3)))
                    ),
                    S("library_result", "Resultado en la Biblioteca", statCheck: "Intelligence", diffKey: "_lib_difficulty", opts:
                        O("Conocimiento Supremo", 3, "Descubres secretos que cambian todo.",
                            tier: "high",
                            fx: Fx(("stat_boost_specific", "Intelligence"), ("stat_boost", 1), ("add_random_item", true), ("rep", Rep(("Mages Circle", 3))))),
                        O("Buenos Hallazgos", 5, "Encuentras informacion valiosa.",
                            tier: "mid",
                            fx: Fx(("stat_boost_specific", "Intelligence"), ("rep", Rep(("Mages Circle", 1))))),
                        O("Textos Ilegibles", 4, "No logras descifrar los textos.",
                            tier: "low"),
                        O("Guardian de la Biblioteca", 2, "Un guardian magico te ataca.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 2), ("rep", Rep(("Mages Circle", -1)))))
                    )
                }
            },

            // ── ELVEN ENVOY ──
            ["Elven Envoy"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("envoy_request", "Peticion del Emisario", opts:
                        O("Alianza Militar", 4, "Los elfos buscan aliados contra una amenaza.",
                            next: "envoy_result",
                            sw: Sw(("Charisma", 1.3f), ("Strength", 1.2f)),
                            fx: Fx(("_request", "alianza"))),
                        O("Intercambio de Conocimiento", 4, "Ofrecen sabiduria a cambio de ayuda.",
                            next: "envoy_result",
                            sw: Sw(("Intelligence", 1.4f)),
                            fx: Fx(("_request", "conocimiento"))),
                        O("Recuperar Reliquia Elfica", 3, "Un artefacto elfico fue robado.",
                            next: "envoy_result",
                            sw: Sw(("Agility", 1.3f)), sb: Sb(("Tracking", 1.5f)),
                            fx: Fx(("_request", "reliquia"))),
                        O("Rechazar al Emisario", 3, "No te interesan los asuntos elficos.",
                            fx: Fx(("rep", Rep(("Mages Circle", -1)))))
                    ),
                    S("envoy_result", "Resultado con los Elfos", statCheck: "Charisma", opts:
                        O("Alianza Sellada", 3, "Los elfos se convierten en aliados fieles.",
                            tier: "high",
                            fx: Fx(("stat_boost", 1), ("add_condition", "elven_ally"), ("rep", Rep(("Mages Circle", 2))))),
                        O("Cooperacion Limitada", 5, "Ayudan pero con reservas.",
                            tier: "mid",
                            fx: Fx(("rep", Rep(("Mages Circle", 1))))),
                        O("Desconfianza Mutua", 4, "No se llega a ningun acuerdo.",
                            tier: "low"),
                        O("Ofensa Diplomatica", 2, "Insultas a los elfos sin querer.",
                            tier: "fail",
                            fx: Fx(("rep", Rep(("Mages Circle", -2)))))
                    )
                }
            },

            // ── DWARVEN FORGE FIRE ──
            ["Dwarven Forge Fire"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("forge_help", "Ayuda en la Forja", opts:
                        O("Ayudar con la Forja", 5, "Trabajas junto a los enanos.",
                            next: "forge_result",
                            sw: Sw(("Strength", 1.4f)), sb: Sb(("Smithing", 2.5f)),
                            fx: Fx(("_help", "forjar"))),
                        O("Conseguir Materiales", 4, "Buscas materiales raros que necesitan.",
                            next: "forge_result",
                            sw: Sw(("Agility", 1.3f)), sb: Sb(("Tracking", 1.5f)),
                            fx: Fx(("_help", "materiales"))),
                        O("Proteger la Forja", 4, "Defiendes la forja de saboteadores.",
                            next: "forge_result",
                            sw: Sw(("Strength", 1.3f), ("Durability", 1.2f)),
                            fx: Fx(("_help", "proteger"))),
                        O("Aportar Magia", 3, "Usas magia para potenciar la forja.",
                            next: "forge_result",
                            sw: Sw(("Intelligence", 1.5f)), reqMagic: true,
                            fx: Fx(("_help", "magia")))
                    ),
                    S("forge_result", "Resultado en la Forja Enana", statCheck: "Strength", opts:
                        O("Arma Legendaria", 3, "Los enanos te regalan una obra maestra.",
                            tier: "high",
                            fx: Fx(("add_random_item", true), ("stat_boost", 1), ("rep", Rep(("Merchant Guild", 2), ("Hunters Lodge", 1))))),
                        O("Buen Trabajo", 5, "Los enanos estan satisfechos.",
                            tier: "mid",
                            fx: Fx(("add_random_item", true), ("rep", Rep(("Merchant Guild", 1))))),
                        O("Trabajo Mediocre", 4, "No cumples las expectativas enanas.",
                            tier: "low"),
                        O("Desastre en la Forja", 2, "Causas un accidente que da\u00f1a la forja.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 1), ("rep", Rep(("Merchant Guild", -2)))))
                    )
                }
            },

            // ── PLAGUE SIGNS ──
            ["Plague Signs"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("plague_response", "Respuesta a la Plaga", opts:
                        O("Curar a los Enfermos", 5, "Dedicas tu esfuerzo a sanar.",
                            next: "plague_result",
                            sw: Sw(("Intelligence", 1.3f)), sb: Sb(("Medicine", 2.0f)),
                            fx: Fx(("_response", "curar"), ("_plague_difficulty", 5))),
                        O("Buscar el Origen", 4, "Investigas la causa de la plaga.",
                            next: "plague_result",
                            sw: Sw(("Intelligence", 1.5f)), sb: Sb(("Investigation", 1.5f), ("Alchemy", 1.5f)),
                            fx: Fx(("_response", "investigar"), ("_plague_difficulty", 6))),
                        O("Cuarentena Estricta", 4, "Impones aislamiento total.",
                            next: "plague_result",
                            sw: Sw(("Charisma", 1.3f), ("Intelligence", 1.2f)),
                            fx: Fx(("_response", "cuarentena"), ("_plague_difficulty", 4))),
                        O("Huir de la Zona", 3, "Escapas antes de contagiarte.",
                            fx: Fx(("rep", Rep(("Church of Light", -2)))))
                    ),
                    S("plague_result", "Resultado de la Plaga", statCheck: "Intelligence", diffKey: "_plague_difficulty", opts:
                        O("Plaga Erradicada", 3, "Tu intervencion salva a cientos de vidas.",
                            tier: "high",
                            fx: Fx(("stat_boost_specific", "Charisma"), ("rep", Rep(("Church of Light", 4))))),
                        O("Plaga Contenida", 5, "Reduces el impacto significativamente.",
                            tier: "mid",
                            fx: Fx(("rep", Rep(("Church of Light", 2))))),
                        O("Plaga Persiste", 4, "Tus esfuerzos no son suficientes.",
                            tier: "low",
                            fx: Fx(("add_condition", "plague_active"), ("rep", Rep(("Church of Light", -1))))),
                        O("Te Contagias", 2, "La plaga te alcanza a ti.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 2), ("add_condition", "sick")))
                    )
                }
            },

            // ── MYSTIC ECLIPSE ──
            ["Mystic Eclipse"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("eclipse_action", "Accion durante el Eclipse", opts:
                        O("Realizar un Ritual", 4, "Aprovechas el eclipse para un hechizo poderoso.",
                            next: "eclipse_result",
                            sw: Sw(("Intelligence", 1.6f)), reqMagic: true,
                            fx: Fx(("_action", "ritual"), ("_eclipse_difficulty", 6))),
                        O("Meditar y Absorber", 4, "Absorbes la energia cosmica del eclipse.",
                            next: "eclipse_result",
                            sw: Sw(("Intelligence", 1.3f), ("Durability", 1.2f)),
                            fx: Fx(("_action", "meditar"), ("_eclipse_difficulty", 4))),
                        O("Estudiar el Fenomeno", 5, "Observas y documentas el evento.",
                            next: "eclipse_result",
                            sw: Sw(("Intelligence", 1.4f)),
                            fx: Fx(("_action", "estudiar"), ("_eclipse_difficulty", 3))),
                        O("Proteger a los Demas", 3, "Algunos enloquecen. Los proteges.",
                            next: "eclipse_result",
                            sw: Sw(("Charisma", 1.3f), ("Strength", 1.2f)),
                            fx: Fx(("_action", "proteger"), ("_eclipse_difficulty", 4)))
                    ),
                    S("eclipse_result", "Resultado del Eclipse", statCheck: "Intelligence", diffKey: "_eclipse_difficulty", opts:
                        O("Poder Cosmico", 3, "El eclipse te otorga poder increible.",
                            tier: "high",
                            fx: Fx(("stat_boost", 2), ("rep", Rep(("Mages Circle", 3))))),
                        O("Iluminacion Parcial", 5, "Ganas algo de poder y conocimiento.",
                            tier: "mid",
                            fx: Fx(("stat_boost", 1), ("rep", Rep(("Mages Circle", 1))))),
                        O("Nada Especial", 4, "El eclipse pasa sin efecto para ti.",
                            tier: "low"),
                        O("Locura Temporal", 2, "La energia te afecta mentalmente.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 1), ("add_condition", "mentally_unstable")))
                    )
                }
            },

            // ── LOST HEIR ──
            ["Lost Heir"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("heir_decision", "Decision sobre el Heredero", opts:
                        O("Proteger al Heredero", 5, "Lo escoltas y proteges.",
                            next: "heir_result",
                            sw: Sw(("Strength", 1.3f), ("Charisma", 1.2f)),
                            fx: Fx(("_decision", "proteger"))),
                        O("Vender al Heredero", 3, "Lo entregas al mejor postor.",
                            next: "heir_result",
                            sw: Sw(("Charisma", 1.3f)),
                            fx: Fx(("_decision", "vender"))),
                        O("Usar como Peon Politico", 4, "Lo usas para tus propios fines.",
                            next: "heir_result",
                            sw: Sw(("Intelligence", 1.4f), ("Charisma", 1.3f)),
                            fx: Fx(("_decision", "peon"))),
                        O("Ignorar al Heredero", 3, "No es tu problema.")
                    ),
                    S("heir_result", "Resultado del Heredero", statCheck: "Charisma", opts:
                        O("Recompensa Real", 3, "Tu decision te trae grandes beneficios.",
                            tier: "high",
                            fx: Fx(("gain_wealth", true), ("stat_boost", 1), ("rep", Rep(("The Crown", 3))))),
                        O("Reconocimiento", 5, "Tu accion es reconocida por la nobleza.",
                            tier: "mid",
                            fx: Fx(("rep", Rep(("The Crown", 1))))),
                        O("Complicaciones", 4, "Tu decision trae consecuencias inesperadas.",
                            tier: "low",
                            fx: Fx(("add_condition", "political_trouble"))),
                        O("Traicion del Heredero", 2, "El heredero te traiciona.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 1), ("rep", Rep(("The Crown", -2)))))
                    )
                }
            },

            // ── ANCIENT MAP ──
            ["Ancient Map"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("map_destination", "Destino del Mapa", opts:
                        O("Tumba Olvidada", 5, "El mapa lleva a una tumba llena de tesoros.",
                            next: "map_result",
                            sw: Sw(("Intelligence", 1.3f)),
                            fx: Fx(("_dest", "tumba"), ("_map_difficulty", 5))),
                        O("Ciudad Perdida", 3, "Una ciudad antigua oculta en la selva.",
                            next: "map_result",
                            sw: Sw(("Intelligence", 1.4f), ("Agility", 1.2f)),
                            fx: Fx(("_dest", "ciudad"), ("_map_difficulty", 7))),
                        O("Mina Abandonada", 4, "Una mina con minerales raros.",
                            next: "map_result",
                            sw: Sw(("Strength", 1.2f)),
                            fx: Fx(("_dest", "mina"), ("_map_difficulty", 4))),
                        O("Santuario Secreto", 3, "Un templo oculto con poder arcano.",
                            next: "map_result",
                            sw: Sw(("Intelligence", 1.4f)), reqMagic: true,
                            fx: Fx(("_dest", "santuario"), ("_map_difficulty", 6)))
                    ),
                    S("map_result", "Resultado de la Expedicion", statCheck: "Intelligence", diffKey: "_map_difficulty", opts:
                        O("Tesoro Legendario", 2, "Encuentras riquezas inimaginables.",
                            tier: "high",
                            fx: Fx(("add_random_item", true), ("gain_wealth", true), ("stat_boost", 2), ("rep", Rep(("Mages Circle", 2))))),
                        O("Buen Botin", 5, "Encuentras objetos valiosos.",
                            tier: "mid",
                            fx: Fx(("add_random_item", true), ("rep", Rep(("Mages Circle", 1))))),
                        O("Lugar Saqueado", 4, "Alguien llego antes que tu.",
                            tier: "low"),
                        O("Trampa Mortal", 3, "El mapa era una trampa elaborada.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 2), ("add_condition", "wounded")))
                    )
                }
            },

            // ── HERETICAL SERMON ──
            ["Heretical Sermon"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("sermon_response", "Respuesta al Sermon", opts:
                        O("Apoyar al Hereje", 4, "Sus palabras resuenan contigo.",
                            next: "sermon_result",
                            sw: Sw(("Charisma", 1.3f)),
                            fx: Fx(("_response", "apoyar"))),
                        O("Denunciar al Hereje", 4, "Alertas a la Iglesia.",
                            next: "sermon_result",
                            sw: Sw(("Charisma", 1.2f)),
                            fx: Fx(("_response", "denunciar"))),
                        O("Debatir Publicamente", 3, "Lo desafias intelectualmente.",
                            next: "sermon_result",
                            sw: Sw(("Intelligence", 1.4f), ("Charisma", 1.4f)),
                            fx: Fx(("_response", "debatir"))),
                        O("Escuchar en Secreto", 4, "Observas desde las sombras.",
                            next: "sermon_result",
                            sw: Sw(("Agility", 1.2f)), sb: Sb(("Stealth", 1.3f)),
                            fx: Fx(("_response", "escuchar")))
                    ),
                    S("sermon_result", "Resultado del Sermon", statCheck: "Charisma", opts:
                        O("Influencia Ganada", 3, "Tu posicion te gana seguidores.",
                            tier: "high",
                            fx: Fx(("stat_boost_specific", "Charisma"), ("rep", Rep(("Church of Light", 2))))),
                        O("Reconocimiento", 5, "La gente nota tu intervencion.",
                            tier: "mid",
                            fx: Fx(("rep", Rep(("Church of Light", 1))))),
                        O("Ignorado", 4, "Nadie presta atencion.",
                            tier: "low"),
                        O("Acusado de Hereje", 2, "Te acusan de herejia a ti tambien.",
                            tier: "fail",
                            fx: Fx(("rep", Rep(("Church of Light", -3))), ("add_condition", "heretic_accused")))
                    )
                }
            },

            // ── BEAST STAMPEDE ──
            ["Beast Stampede"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("stampede_action", "Accion ante la Estampida", opts:
                        O("Desviar la Estampida", 4, "Intentas redirigir a las bestias.",
                            next: "stampede_result",
                            sw: Sw(("Intelligence", 1.3f), ("Agility", 1.3f)), sb: Sb(("Beast Taming", 2.0f)),
                            fx: Fx(("_action", "desviar"))),
                        O("Cazar las Bestias", 4, "Abates a las criaturas mas peligrosas.",
                            next: "stampede_result",
                            sw: Sw(("Strength", 1.5f)), sb: Sb(("Tracking", 1.5f)),
                            fx: Fx(("_action", "cazar"))),
                        O("Proteger al Pueblo", 5, "Organizas la defensa del asentamiento.",
                            next: "stampede_result",
                            sw: Sw(("Charisma", 1.3f), ("Strength", 1.2f)),
                            fx: Fx(("_action", "proteger"))),
                        O("Huir a Terreno Alto", 4, "Escapas a un lugar seguro.",
                            next: "stampede_result",
                            sw: Sw(("Agility", 1.4f)),
                            fx: Fx(("_action", "huir")))
                    ),
                    S("stampede_result", "Resultado de la Estampida", statCheck: "Strength", opts:
                        O("Bestias Controladas", 3, "Logras detener la estampida.",
                            tier: "high",
                            fx: Fx(("stat_boost", 1), ("rep", Rep(("Hunters Lodge", 3))))),
                        O("Danos Minimizados", 5, "Reduces el impacto considerablemente.",
                            tier: "mid",
                            fx: Fx(("rep", Rep(("Hunters Lodge", 1))))),
                        O("Danos Severos", 4, "La estampida causa destruccion.",
                            tier: "low",
                            fx: Fx(("stat_damage", 1))),
                        O("Arrasado", 2, "Las bestias te pasan por encima.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 3), ("add_condition", "wounded")))
                    )
                }
            },

            // ── ORACLE VISION ──
            ["Oracle Vision"] = new ChainDef
            {
                Steps = new List<ChainStep>
                {
                    S("vision_interpretation", "Interpretacion de la Vision", opts:
                        O("Aceptar el Destino", 4, "Sigues lo que la vision muestra.",
                            next: "vision_result",
                            sw: Sw(("Intelligence", 1.3f)),
                            fx: Fx(("_interpretation", "aceptar"))),
                        O("Desafiar la Profecia", 4, "Intentas cambiar lo que fue visto.",
                            next: "vision_result",
                            sw: Sw(("Charisma", 1.3f), ("Durability", 1.2f)),
                            fx: Fx(("_interpretation", "desafiar"))),
                        O("Buscar Mas Respuestas", 4, "Investigas el significado profundo.",
                            next: "vision_result",
                            sw: Sw(("Intelligence", 1.5f)), sb: Sb(("Investigation", 1.5f)),
                            fx: Fx(("_interpretation", "investigar"))),
                        O("Compartir la Vision", 3, "Cuentas lo visto a tus aliados.",
                            next: "vision_result",
                            sw: Sw(("Charisma", 1.4f)),
                            fx: Fx(("_interpretation", "compartir")))
                    ),
                    S("vision_result", "Resultado de la Vision", statCheck: "Intelligence", opts:
                        O("Profecia Cumplida", 3, "La vision se cumple a tu favor.",
                            tier: "high",
                            fx: Fx(("stat_boost", 2), ("add_condition", "destiny_touched"), ("rep", Rep(("Church of Light", 2), ("Mages Circle", 2))))),
                        O("Pistas del Futuro", 5, "Ganas perspectiva sobre lo que viene.",
                            tier: "mid",
                            fx: Fx(("stat_boost", 1), ("rep", Rep(("Mages Circle", 1))))),
                        O("Vision Confusa", 4, "No logras interpretar la vision correctamente.",
                            tier: "low"),
                        O("Vision Corruptora", 2, "La vision te afecta psicologicamente.",
                            tier: "fail",
                            fx: Fx(("stat_damage", 1), ("add_condition", "mentally_unstable")))
                    )
                }
            }
        };

        // ═══════════════════════════════════════════════════════════
        //  CHAIN LIMITS
        // ═══════════════════════════════════════════════════════════

        public static readonly Dictionary<string, ChainLimit> ChainLimits = new()
        {
            // Unique (one-time events)
            ["Attempt Apotheosis"]    = new ChainLimit { Unique = true },
            ["Dragon Sighting"]      = new ChainLimit { Unique = true },
            ["Demonic Rift"]         = new ChainLimit { Unique = true },
            ["Mystic Eclipse"]       = new ChainLimit { Unique = true },
            ["Lost Heir"]            = new ChainLimit { Unique = true },
            ["Oracle Vision"]        = new ChainLimit { Unique = true },
            ["Assassination Attempt"]= new ChainLimit { Unique = true },
            ["Trial by Combat"]      = new ChainLimit { Unique = true },
            ["Pirate Blockade"]      = new ChainLimit { Unique = true },
            ["Ancient Map"]          = new ChainLimit { Unique = true },
            ["Forbidden Library"]    = new ChainLimit { Unique = true },
            // Limited repeats
            ["Lead a Rebellion"]       = new ChainLimit { MaxRepeats = 2 },
            ["Compete in a Tournament"]= new ChainLimit { MaxRepeats = 2 },
            ["Serve at Court"]         = new ChainLimit { MaxRepeats = 2 },
            ["Establish a Business"]   = new ChainLimit { MaxRepeats = 1 },
            ["Perform a Dark Ritual"]  = new ChainLimit { MaxRepeats = 2 },
            ["Study an Ancient Tome"]  = new ChainLimit { MaxRepeats = 3 },
            ["Infiltrate a Stronghold"]= new ChainLimit { MaxRepeats = 2 },
            ["Track a Fugitive"]       = new ChainLimit { MaxRepeats = 3 },
            ["Forge Legendary Gear"]   = new ChainLimit { MaxRepeats = 2 },
            ["Heretical Sermon"]       = new ChainLimit { MaxRepeats = 1 },
            ["Beast Stampede"]         = new ChainLimit { MaxRepeats = 2 },
            ["Cult Whisper"]           = new ChainLimit { MaxRepeats = 2 },
            ["Elven Envoy"]            = new ChainLimit { MaxRepeats = 2 },
            ["Dwarven Forge Fire"]     = new ChainLimit { MaxRepeats = 2 },
            ["Noble Summons"]          = new ChainLimit { MaxRepeats = 3 },
            ["Plague Signs"]           = new ChainLimit { MaxRepeats = 2 },
        };

        // ═══════════════════════════════════════════════════════════
        //  CHAIN TITLES  (chain_name, option_name) → title
        // ═══════════════════════════════════════════════════════════

        public static readonly Dictionary<(string Chain, string Option), string> ChainTitles = new()
        {
            [("Dragon Sighting",        "Triunfo Legendario")]     = "Mata-Dragones",
            [("Compete in a Tournament", "Campeon!")]               = "Campeon del Torneo",
            [("Demonic Rift",           "Portal Sellado")]          = "Sellador de Portales",
            [("Assassination Attempt",  "Asesino Capturado")]       = "El Intocable",
            [("Lead a Rebellion",       "Victoria Revolucionaria")] = "El Libertador",
            [("Attempt Apotheosis",     "Semidivinidad")]           = "Semidios",
            [("Pirate Blockade",        "Victoria Aplastante")]     = "Terror de los Mares",
            [("Hunt a Beast",           "Caza Gloriosa")]           = "Gran Cazador",
            [("Investigate a Mystery",  "Caso Resuelto!")]          = "Detective Supremo",
            [("Serve at Court",         "Favor del Rey")]           = "Favorito del Rey",
            [("Forge Legendary Gear",   "Obra Maestra")]            = "Maestro Forjador",
            [("Heal the Sick",          "Cura Milagrosa")]          = "El Sanador",
            [("Explore Ruins",          "Reliquia Legendaria")]     = "Explorador Legendario",
            [("Infiltrate a Stronghold","Mision Perfecta")]         = "La Sombra",
            [("Perform a Dark Ritual",  "Ritual Perfecto")]         = "Senor Oscuro",
            [("Trial by Combat",        "Victoria Heroica")]        = "Campeon del Juicio",
            [("Plague Signs",           "Plaga Erradicada")]        = "Salvador de la Plaga",
            [("Negotiate a Trade",      "Ganga Increible")]         = "Negociador Supremo",
            [("Guard a Caravan",        "Caravana Intacta")]        = "Guardia de Honor",
            [("Track a Fugitive",       "Captura Limpia")]          = "Cazarrecompensas",
            [("Study an Ancient Tome",  "Conocimiento Profundo")]   = "Erudito",
            [("Establish a Business",   "Negocio Prospero")]        = "Magnate",
        };

        // ═══════════════════════════════════════════════════════════
        //  CONDITION DESCRIPTIONS
        // ═══════════════════════════════════════════════════════════

        public static readonly Dictionary<string, string> ConditionDescriptions = new()
        {
            ["trade_blocked"]        = "Comercio bloqueado por piratas",
            ["pirate_truce"]         = "Tregua temporal con piratas",
            ["wounded"]              = "Herido gravemente",
            ["cursed"]               = "Maldito por fuerzas oscuras",
            ["sick"]                 = "Enfermo/contagiado",
            ["beast_stalking"]       = "Una bestia te acecha",
            ["ancient_map"]          = "Posees un mapa antiguo",
            ["dimensional_rift"]     = "Portal dimensional abierto",
            ["horror_survivor"]      = "Marcado por un horror primordial",
            ["business_owner"]       = "Propietario de un negocio",
            ["fugitive_loose"]       = "Un fugitivo sigue suelto",
            ["enemy_alerted"]        = "Tu enemigo conoce tus movimientos",
            ["imprisoned"]           = "Has estado preso recientemente",
            ["disgraced"]            = "Caido en desgracia publica",
            ["tournament_champion"]  = "Campeon de torneo",
            ["rebel_leader"]         = "Lider de la rebelion",
            ["rebellion_ongoing"]    = "Rebelion activa",
            ["wanted_rebel"]         = "Buscado como rebelde",
            ["dark_empowered"]       = "Imbuido de poder oscuro",
            ["semidivine"]           = "Semidivino",
            ["clue_found"]           = "Pista importante descubierta",
            ["has_ally"]             = "Tienes un aliado valioso",
            ["knows_enemy"]          = "Sabes quien es tu enemigo",
            ["assassination_survivor"] = "Sobreviviste un atentado",
            ["elven_ally"]           = "Aliado de los elfos",
            ["plague_active"]        = "Plaga activa en la region",
            ["mentally_unstable"]    = "Inestabilidad mental",
            ["cult_knowledge"]       = "Conocimiento oculto del culto",
            ["corrupted"]            = "Corrupcion demoniaca",
            ["rift_unstable"]        = "Portal dimensional inestable",
            ["political_trouble"]    = "Problemas politicos",
            ["heretic_accused"]      = "Acusado de herejia",
            ["destiny_touched"]      = "Tocado por el destino",
            ["dragon_fear"]          = "Terror al dragon",
            ["burned"]               = "Quemaduras graves",
        };

        // ═══════════════════════════════════════════════════════════
        //  ADVENTURE DECISIONS
        // ═══════════════════════════════════════════════════════════

        static Dictionary<string, float> Tm(params (string k, float v)[] pairs)
        {
            var d = new Dictionary<string, float>();
            foreach (var (k, v) in pairs) d[k] = v;
            return d;
        }

        static DecisionOption DO(string label, Dictionary<string, float> tagMods,
            Dictionary<string, int> rep = null) => new()
        {
            Label = label, TagMods = tagMods, Rep = rep ?? new Dictionary<string, int>()
        };

        public static readonly Dictionary<string, DecisionDef> AdventureDecisions = new()
        {
            ["Cult Whisper"] = new DecisionDef
            {
                Prompt = "Un culto clandestino te ofrece secretos oscuros. \u00bfQu\u00e9 decides?",
                Options = new List<DecisionOption>
                {
                    DO("Unirse al Culto", Tm(("dark", 1.5f), ("evil", 1.3f), ("shadow", 1.3f)),
                        Rep(("Shadow Council", 3), ("Church of Light", -2))),
                    DO("Rechazar y Denunciar", Tm(("good", 1.5f), ("divine", 1.2f)),
                        Rep(("Church of Light", 2), ("Shadow Council", -3))),
                    DO("Infiltrarse como Esp\u00eda", Tm(("stealth", 1.4f), ("investigation", 1.3f)),
                        Rep(("Shadow Council", 1)))
                }
            },
            ["Noble Summons"] = new DecisionDef
            {
                Prompt = "La nobleza exige tu presencia para una misi\u00f3n. \u00bfC\u00f3mo respondes?",
                Options = new List<DecisionOption>
                {
                    DO("Aceptar la Misi\u00f3n", Tm(("honor", 1.3f), ("leadership", 1.2f)),
                        Rep(("The Crown", 2))),
                    DO("Negociar T\u00e9rminos", Tm(("trade", 1.4f), ("social", 1.3f)),
                        Rep(("The Crown", 1), ("Merchant Guild", 1))),
                    DO("Rechazar", Tm(("neutral", 1.2f)),
                        Rep(("The Crown", -2)))
                }
            },
            ["Assassination Attempt"] = new DecisionDef
            {
                Prompt = "\u00a1Han intentado asesinarte! \u00bfC\u00f3mo reaccionas?",
                Options = new List<DecisionOption>
                {
                    DO("Contraatacar", Tm(("combat", 1.5f), ("honor", 1.2f)),
                        Rep(("Hunters Lodge", 1))),
                    DO("Huir y Esconderse", Tm(("stealth", 1.4f)),
                        Rep(("Thieves Guild", 1))),
                    DO("Investigar al Autor", Tm(("investigation", 1.5f), ("politics", 1.2f)),
                        Rep(("The Crown", 1)))
                }
            },
            ["Merchant Guild Offer"] = new DecisionDef
            {
                Prompt = "El Gremio de Mercaderes te propone un trato arriesgado. \u00bfQu\u00e9 haces?",
                Options = new List<DecisionOption>
                {
                    DO("Aceptar el Trato", Tm(("trade", 1.5f), ("merchant", 1.3f)),
                        Rep(("Merchant Guild", 2))),
                    DO("Pedir M\u00e1s Informaci\u00f3n", Tm(("investigation", 1.3f)),
                        Rep(("Merchant Guild", 1))),
                    DO("Rechazar", Tm(("neutral", 1.1f)),
                        Rep(("Merchant Guild", -1)))
                }
            },
            ["Demonic Rift"] = new DecisionDef
            {
                Prompt = "Un portal infernal se ha abierto. \u00bfQu\u00e9 decides hacer?",
                Options = new List<DecisionOption>
                {
                    DO("Cerrar el Portal", Tm(("magic", 1.4f), ("good", 1.3f), ("divine", 1.3f)),
                        Rep(("Church of Light", 3), ("Mages Circle", 1))),
                    DO("Aprovechar su Poder", Tm(("dark", 1.5f), ("evil", 1.4f)),
                        Rep(("Shadow Council", 2), ("Church of Light", -3))),
                    DO("Huir de la Zona", Tm(("neutral", 1.2f)))
                }
            },
            ["Shadow Market"] = new DecisionDef
            {
                Prompt = "Has descubierto un mercado ilegal. \u00bfQu\u00e9 haces?",
                Options = new List<DecisionOption>
                {
                    DO("Comerciar", Tm(("trade", 1.4f), ("crime", 1.3f)),
                        Rep(("Thieves Guild", 2), ("Merchant Guild", -1))),
                    DO("Denunciar", Tm(("good", 1.3f), ("honor", 1.2f)),
                        Rep(("The Crown", 2), ("Thieves Guild", -3))),
                    DO("Buscar Informaci\u00f3n", Tm(("investigation", 1.3f), ("stealth", 1.2f)),
                        Rep(("Thieves Guild", 1)))
                }
            },
            ["Trial by Combat"] = new DecisionDef
            {
                Prompt = "La justicia exige un duelo a muerte. \u00bfC\u00f3mo procedes?",
                Options = new List<DecisionOption>
                {
                    DO("Aceptar el Duelo", Tm(("combat", 1.5f), ("honor", 1.4f)),
                        Rep(("The Crown", 1), ("Hunters Lodge", 1))),
                    DO("Buscar un Campe\u00f3n", Tm(("social", 1.3f), ("trade", 1.2f)),
                        Rep(("Merchant Guild", 1))),
                    DO("Huir antes del Duelo", Tm(("stealth", 1.4f), ("crime", 1.2f)),
                        Rep(("The Crown", -2), ("Thieves Guild", 1)))
                }
            },
            ["Forbidden Library"] = new DecisionDef
            {
                Prompt = "Una biblioteca sellada se abre por una noche. \u00bfQu\u00e9 haces?",
                Options = new List<DecisionOption>
                {
                    DO("Estudiar los Textos", Tm(("magic", 1.5f), ("arcane", 1.4f), ("research", 1.3f)),
                        Rep(("Mages Circle", 2))),
                    DO("Robar Textos Valiosos", Tm(("crime", 1.4f), ("trade", 1.2f)),
                        Rep(("Thieves Guild", 2), ("Mages Circle", -2))),
                    DO("Alertar a las Autoridades", Tm(("good", 1.2f)),
                        Rep(("The Crown", 1), ("Mages Circle", -1)))
                }
            },
            ["Dragon Sighting"] = new DecisionDef
            {
                Prompt = "Un drag\u00f3n amenaza la regi\u00f3n. \u00bfQu\u00e9 haces?",
                Options = new List<DecisionOption>
                {
                    DO("Cazar al Drag\u00f3n", Tm(("combat", 1.6f), ("hunt", 1.5f)),
                        Rep(("Hunters Lodge", 3))),
                    DO("Negociar con \u00e9l", Tm(("social", 1.4f), ("magic", 1.2f)),
                        Rep(("Mages Circle", 1))),
                    DO("Evacuar la Zona", Tm(("leadership", 1.3f), ("good", 1.2f)),
                        Rep(("The Crown", 1)))
                }
            },
            ["Plague Signs"] = new DecisionDef
            {
                Prompt = "Se detectan s\u00edntomas de peste. \u00bfC\u00f3mo act\u00faas?",
                Options = new List<DecisionOption>
                {
                    DO("Curar a los Enfermos", Tm(("healing", 1.5f), ("good", 1.3f)),
                        Rep(("Church of Light", 2))),
                    DO("Buscar la Causa", Tm(("investigation", 1.4f), ("research", 1.3f)),
                        Rep(("Mages Circle", 1))),
                    DO("Huir de la Plaga", Tm(("neutral", 1.2f)),
                        Rep(("Church of Light", -1)))
                }
            },
        };

        // ═══════════════════════════════════════════════════════════
        //  SUBLOCATIONS
        // ═══════════════════════════════════════════════════════════

        public static readonly Dictionary<string, string[]> Sublocations = new()
        {
            ["Human City (Good Factions)"] = new[] { "Distrito Mercante", "Catedral", "Casa de Gremios" },
            ["Human Slums"]                = new[] { "Callejones", "Puertos", "Foso de Lucha" },
            ["Elven Forest"]               = new[] { "Arboleda Antigua", "Canopia", "Claro Lunar" },
            ["Dwarven Hold"]               = new[] { "Gran Forja", "Minas Profundas", "Bazar de Piedra" },
            ["Outlands"]                   = new[] { "Fortin en Ruinas", "Pantano Sangriento", "Campamento Bandido" },
        };
    }
}
