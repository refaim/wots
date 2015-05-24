import tools.dict

_SET_ABBREVIATIONS_SOURCE = {
    '10E': ('Tenth Edition', '10th Edition',),
    '2ED': ('Unlimited Edition', '2E', 'Unlimited',),
    '3ED': ('Revised Edition', '3E', 'Revised',),
    '4ED': ('Fourth Edition', '4th Edition', '4E',),
    '5DN': ('Fifth Dawn', 'FD',),
    '5ED': ('Fifth Edition', '5th Edition', '5E',),
    '6ED': ('Sixth Edition', '6th Edition', '6E', 'Classic Sixth Edition',),
    '7ED': ('Seventh Edition', '7th Edition', '7E',),
    '8ED': ('Eighth Edition', '8th Edition', '8E',),
    '9ED': ('Ninth Edition', '9th Edition', '9E',),
    'ALA': ('Shards of Alara', 'SA',),
    'ALL': ('Alliances', 'AL',),
    'APC': ('Apocalypse', 'AP',),
    'ARB': ('Alara Reborn', 'AR',),
    'ARC': ('Archenemy',),
    'ARL': ('Arena League', 'Arena',),
    'ARN': ('Arabian Nights',),
    'ATH': ('Anthologies',),
    'ATQ': ('Antiquities',),
    'AVR': ('Avacyn Restored',),
    'BFZ': ('Battle for Zendikar',),
    'BNG': ('Born of the Gods', 'BOG',),
    'BOK': ('Betrayers of Kamigawa', 'BK',),
    'BRB': ('Battle Royale Box Set', 'Battle Royal',),
    'BTD': ('Beatdown Box Set', 'Beatdown',),
    'C13': ('Commander 2013', 'Commander 2013 Edition', 'Commander2013',),
    'C14': ('Commander 2014', 'Commander 2014 Edition', 'Commander2014',),
    'CHK': ('Champions of Kamigawa', 'CK',),
    'CHP': ('Champs Promos',),
    'CHR': ('Chronicles',),
    'CM1': ("Commander's Arsenal", 'CMA',),
    'CMD': ('Commander',),
    'CNS': ('Conspiracy',),
    'CON': ('Conflux', 'CF', 'CFX',),
    'CP1': ('Magic 2015 Clash Pack',),
    'CP2': ('Fate Reforged Clash Pack',),
    'CSP': ('Coldsnap', 'CS',),
    'CTD': ('Coldsnap Theme Decks', 'Coldsnap Reprints',),
    'DD2': ('Duel Decks: Jace vs. Chandra', 'Jace vs. Chandra',),
    'DD3': ('Duel Decks: Anthology',),
    'DDC': ('Duel Decks: Divine vs. Demonic', 'Divine vs. Demonic',),
    'DDD': ('Duel Decks: Garruk vs. Liliana', 'Garruk vs. Liliana', 'GVL', 'GVL2',),
    'DDE': ('Duel Decks: Phyrexia vs. the Coalition', 'Phyrexia vs. the Coalition',),
    'DDF': ('Duel Decks: Elspeth vs. Tezzeret', 'Elspeth vs. Tezzeret',),
    'DDG': ('Duel Decks: Knights vs. Dragons', 'Knights vs. Dragons',),
    'DDH': ('Duel Decks: Ajani vs. Nicol Bolas', 'Ajani vs. Nicol Bolas',),
    'DDI': ('Duel Decks: Venser vs. Koth', 'Venser vs. Koth',),
    'DDJ': ('Duel Decks: Izzet vs. Golgari', 'Izzet vs. Golgari',),
    'DDK': ('Duel Decks: Sorin vs. Tibalt', 'Sorin vs. Tibalt',),
    'DDL': ('Duel Decks: Heroes vs. Monsters', 'Heroes vs. Monsters',),
    'DDM': ('Duel Decks: Jace vs. Vraska', 'Jace vs. Vraska',),
    'DDN': ('Duel Decks: Speed vs. Cunning', 'Speed vs. Cunning',),
    'DDO': ('Duel Decks: Elspeth vs. Kiora', 'Elspeth vs. Kiora',),
    'DGM': ("Dragon's Maze",),
    'DIS': ('Dissension', 'DI',),
    'DKA': ('Dark Ascension',),
    'DKM': ('Deckmasters',),
    'DLM': ('DCI Legend Membership',),
    'DPA': ('Duels of the Planeswalkers',),
    'DRB': ('From the Vault: Dragons', 'FTV: Dragons',),
    'DRK': ('The Dark', 'DK',),
    'DST': ('Darksteel', 'DS',),
    'DTK': ('Dragons of Tarkir',),
    'EVE': ('Eventide', 'ET',),
    'EVG': ('Duel Decks: Elves vs. Goblins', 'EVG2', 'Elves vs. Goblins'),
    'EXO': ('Exodus', 'EX',),
    'FEM': ('Fallen Empires', 'FE',),
    'FNM': ('Friday Night Magic', 'Friday Night Magic (FNM)',),
    'FRF': ('Fate Reforged',),
    'FUT': ('Future Sight', 'FS',),
    'GPT': ('Guildpact', 'GP',),
    'GPX': ('Grand Prix Promos',),
    'GTC': ('Gatecrash',),
    'H09': ('Premium Deck Series: Slivers',),
    'HHL': ('Happy Holidays Promos',),
    'HJP': ('Hobby Japan Commemorative Cards',),
    'HML': ('Homelands', 'HL',),
    'HOP': ('Planechase',),
    'ICE': ('Ice Age', 'IA',),
    'INP': ('Intro Pack Promos',),
    'INV': ('Invasion', 'IN',),
    'ISD': ('Innistrad',),
    'JOU': ('Journey into Nyx',),
    'JRW': ('Judge Rewards',),
    'JUD': ('Judgment', 'JU',),
    'KTK': ('Khans of Tarkir',),
    'LEA': ('Limited Edition Alpha', 'Alpha',),
    'LEB': ('Limited Edition Beta', 'Beta',),
    'LEG': ('Legends',),
    'LGN': ('Legions',),
    'LND': ('Alternate Art Lands',),
    'LRW': ('Lorwyn', 'LW', 'LOR',),
    'M10': ('Magic 2010', '2010 Core Set',),
    'M11': ('Magic 2011', '2011 Core Set',),
    'M12': ('Magic 2012', '2012 Core Set',),
    'M13': ('Magic 2013', '2013 Core Set',),
    'M14': ('Magic 2014', '2014 Core Set',),
    'M15': ('Magic 2015', '2015 Core Set',),
    'MBP': ('Media Inserts',),
    'MBS': ('Mirrodin Besieged',),
    'MD1': ('Modern Event Deck', 'Modern Event Deck 2014',),
    'MGB': ('Multiverse Gift Box',),
    'MGD': ('Magic Game Day Cards', 'Game Day',),
    'MIR': ('Mirage',),
    'MLP': ('Magic: The Gathering Launch Parties',),
    'MM2': ('Modern Masters 2015',),
    'MMA': ('Modern Masters',),
    'MMQ': ('Mercadian Masques', 'MM',),
    'MOR': ('Morningtide', 'MT',),
    'MPR': ('Magic Player Rewards', 'Reward cards',),
    'MPS': ('Magic Premiere Shop',),
    'MRD': ('Mirrodin',),
    'NEM': ('Nemesis', 'NE',),
    'NPH': ('New Phyrexia',),
    'ODY': ('Odyssey', 'OD',),
    'ONS': ('Onslaught', 'ON',),
    'ORI': ('Magic Origins',),
    'OVS': ('Oversized Cards',),
    'PC2': ('Planechase 2012', 'Planechase 2012 Edition',),
    'PCY': ('Prophecy', 'PY', 'PR',),
    'PD2': ('Premium Deck Series: Fire and Lightning',),
    'PD3': ('Premium Deck Series: Graveborn',),
    'PLC': ('Planar Chaos', 'PC', 'PCH',),
    'PLS': ('Planeshift', 'PS',),
    'PO2': ('Portal: Second Age', 'Portal Second Age',),
    'POR': ('Portal',),
    'PRC': ('Prerelease & Release Cards',),
    'PTK': ('Portal: Three Kingdoms', 'Portal Three Kingdoms',),
    'RAV': ('Ravnica: City of Guilds', 'Ravnica', 'RA',),
    'RED': ('Redemption Program Cards',),
    'ROE': ('Rise of the Eldrazi',),
    'RSM': ('Revised Edition (Summer Magic)',),
    'RTR': ('Return to Ravnica', 'Retun to Ravnica',),
    'S11': ('Salvat 2011',),
    'S99': ('Starter 1999', 'Starter',),
    'SCG': ('Scourge', 'SC',),
    'SHM': ('Shadowmoor', 'SM',),
    'SOK': ('Saviors of Kamigawa', 'SK',),
    'SOM': ('Scars of Mirrodin',),
    'STH': ('Stronghold', 'SH',),
    'SUM': ('Summer of Magic Promos',),
    'THG': ('Two-Headed Giant Promos', '2HG',),
    'THS': ('Theros',),
    'TMP': ('Tempest', 'TE',),
    'TOR': ('Torment', 'TO', 'TR',),
    'TSP': ('Time Spiral', 'TS',),
    'TST': ('Time Spiral Timeshifted', 'TSTS'),
    'UDS': ("Urza's Destiny", 'UD',),
    'UGF': ('Ugin\'s Fate Promos',),
    'UGL': ('Unglued',),
    'ULG': ("Urza's Legacy", 'UL',),
    'UNH': ('Unhinged', 'UH',),
    'URC': ('Ultra Rare Cards',),
    'USG': ("Urza's Saga", 'US',),
    'V09': ('From the Vault: Exiled', 'FTV: Exiled',),
    'V10': ('From the Vault: Relics', 'FTV: Relics',),
    'V11': ('From the Vault: Legends', 'FTV: Legends', 'FVL',),
    'V12': ('From the Vault: Realms', 'FTV: Realms',),
    'V13': ('From the Vault: Twenty', 'FTV: Twenty',),
    'V14': ('From the Vault: Annihilation', 'FTV: Annihilation',),
    'V15': ('From the Vault: Angels', 'FTV: Angels',),
    'VIS': ('Visions', 'VI',),
    'WLD': ('Championships Prizes',),
    'WMC': ('World Magic Cup Qualifiers',),
    'WPN': ('WPN\\Gateway', 'WPN/Gateway',),
    'WTH': ('Weatherlight', 'WL',),
    'WWK': ('Worldwake',),
    'ZEN': ('Zendikar',),
}

_SETS = tools.dict.expandMapping(_SET_ABBREVIATIONS_SOURCE)
_CASE_INSENSITIVE_SET_STRINGS = {}
for key in _SETS:
    _CASE_INSENSITIVE_SET_STRINGS[key.lower()] = key

_SINGLE_LANGUAGE_SETS_DATA = {
    'jp': (
        'Hobby Japan Commemorative Cards',
        'Magic Premiere Shop',
        'Redemption Program Cards',
    ),
    'es': (
        'Salvat 2011',
    ),
    'en': (
        'Alternate Art Lands',
        'Anthologies',
        'Antiquities',
        'Arabian Nights',
        'Archenemy',
        'Battle Royale Box Set',
        'Beatdown Box Set',
        'Championships Prizes',
        'Champs Promos',
        'Commander\'s Arsenal',
        'DCI Legend Membership',
        'Deckmasters',
        'Duel Decks: Anthology',
        'Duel Decks: Divine vs. Demonic',
        'Duel Decks: Elves vs. Goblins',
        'Duel Decks: Garruk vs. Liliana',
        'Duels of the Planeswalkers',
        'Fallen Empires',
        'Fate Reforged Clash Pack',
        'From the Vault: Annihilation',
        'From the Vault: Dragons',
        'From the Vault: Exiled',
        'From the Vault: Legends',
        'From the Vault: Realms',
        'From the Vault: Relics',
        'From the Vault: Twenty',
        'Grand Prix Promos',
        'Happy Holidays Promos',
        'Intro Pack Promos',
        'Limited Edition Alpha',
        'Limited Edition Beta',
        'Magic 2015 Clash Pack',
        'Magic Player Rewards',
        'Modern Event Deck',
        'Modern Masters',
        'Multiverse Gift Box',
        'Planechase',
        'Premium Deck Series: Fire and Lightning',
        'Premium Deck Series: Graveborn',
        'Premium Deck Series: Slivers',
        'Revised Edition (Summer Magic)',
        'Starter 1999',
        'Summer of Magic Promos',
        'Two-Headed Giant Promos',
        'Ugin\'s Fate Promos',
        'Ultra Rare Cards',
        'Unglued',
        'Unhinged',
        'Unlimited Edition',
    )
}


def getAbbreviation(setNameString):
    return _SETS[setNameString]


def getFullName(setAbbrv):
    return _SET_ABBREVIATIONS_SOURCE[setAbbrv][0]


def tryGetAbbreviationCaseInsensitive(setNameString):
    setAbbreviation = None
    caseSensitiveSetString = _CASE_INSENSITIVE_SET_STRINGS.get(setNameString.lower())
    if caseSensitiveSetString is not None:
        setAbbreviation = getAbbreviation(caseSensitiveSetString)
    return setAbbreviation


SINGLE_LANGUAGE_SETS = {}
for language, setStrings in _SINGLE_LANGUAGE_SETS_DATA.iteritems():
    for setId in setStrings:
        abbrv = tryGetAbbreviationCaseInsensitive(setId)
        if abbrv is None:
            print('Unknown card set "{}"'.format(setId))
        SINGLE_LANGUAGE_SETS[abbrv] = language
