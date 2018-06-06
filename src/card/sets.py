import string
import traceback

import core.language
import core.logger
import tools.dict

_logger = core.logger.Logger('Sets')
_SET_ABBREVIATIONS_SOURCE = {
    '2ED': ('Unlimited Edition', '2E', 'Unlimited',),
    '3ED': ('Revised Edition', '3E', 'Revised',),
    '3FB': ('Revised Edition (FBB)', '3rd Edition (FBB)',),
    '3WB': ('Revised Edition (FWB)', '3rd Edition (FWB)',),
    '4ED': ('Fourth Edition', '4th Edition', '4E',),
    '4FB': ('Fourth Edition (FBB)', '4th Edition (FBB)', '4EF'),
    '4WB': ('Fourth Edition (FWB)', '4th Edition (FWB)',),
    '5DN': ('Fifth Dawn', 'FD',),
    '5ED': ('Fifth Edition', '5th Edition', '5E',),
    '6ED': ('Sixth Edition', '6th Edition', '6E', 'Classic Sixth Edition',),
    '7ED': ('Seventh Edition', '7th Edition', '7E',),
    '8EB': ('Eighth Edition Box Set',),
    '8ED': ('Eighth Edition', '8th Edition', '8E',),
    '9EB': ('Ninth Edition Box Set',),
    '9ED': ('Ninth Edition', '9th Edition', '9E',),
    '10E': ('Tenth Edition', '10th Edition',),
    'A25': ('Masters 25',),
    'AER': ('Aether Revolt',),
    'AKH': ('Amonkhet',),
    'ALA': ('Shards of Alara', 'SA',),
    'ALL': ('Alliances', 'AL',),
    'APA': ('APAC Lands', 'APAC',),
    'APC': ('Apocalypse', 'AP',),
    'ARB': ('Alara Reborn', 'AR',),
    'ARC': ('Archenemy',),
    'ARL': ('Arena League', 'Arena', 'Arena/Colosseo Leagues Promos', 'Arena Promo',),
    'ARN': ('Arabian Nights',),
    'AST': ('Astral',),
    'ATH': ('Anthologies',),
    'ATQ': ('Antiquities',),
    'AVR': ('Avacyn Restored',),
    'BFZ': ('Battle for Zendikar',),
    'BNG': ('Born of the Gods', 'BOG',),
    'BOK': ('Betrayers of Kamigawa', 'BK',),
    'BRB': ('Battle Royale Box Set', 'Battle Royal', 'Battle Royale',),
    'BTD': ('Beatdown Box Set', 'Beatdown',),
    'C13': ('Commander 2013', 'Commander 2013 Edition',),
    'C14': ('Commander 2014', 'Commander 2014 Edition',),
    'C15': ('Commander 2015', 'Commander 2015 Edition',),
    'C16': ('Commander 2016', 'Commander 2016 Edition',),
    'C17': ('Commander 2017', 'Commander 2017 Edition',),
    'CD1': ('Challenge Deck: Face the Hydra',),
    'CD2': ('Challenge Deck: Battle the Horde',),
    'CD3': ('Challenge Deck: Defeat a God',),
    'CED': ('Collectors Edition (Domestic)',),
    'CEI': ('Collectors Edition (International)',),
    'CHK': ('Champions of Kamigawa', 'CK',),
    'CHP': ('Champs Promos', 'Champs Promo', 'Champs', 'Tournament Promos',),
    'CHR': ('Chronicles',),
    'CM1': ("Commander's Arsenal",),
    'CMA': ('Commander Anthology',),
    'CMD': ('Commander', 'Magic: The Gathering Commander',),
    'CN2': ('Conspiracy: Take the Crown',),
    'CNS': ('Conspiracy',),
    'CON': ('Conflux', 'CF', 'CFX',),
    'CP1': ('Magic 2015 Clash Pack',),
    'CP2': ('Fate Reforged Clash Pack',),
    'CP3': ('Magic Origins Clash Pack',),
    'CPP': ('Clash Pack Promos', 'Clash Pack',),
    'CSP': ('Coldsnap', 'CS',),
    'CTD': ('Coldsnap Theme Decks', 'Coldsnap Reprints',),
    'DD2': ('Duel Decks: Jace vs. Chandra', 'Jace vs. Chandra', 'DD3_JVC',),
    'DD3': ('Duel Decks: Anthology',),
    'DDADVD': ('Duel Decks Anthology: Divine vs. Demonic', 'Duel Decks: Divine vs. Demonic (Anthology)',),
    'DDAEVG': ('Duel Decks Anthology: Elves vs. Goblins', 'Duel Decks: Elves vs. Goblins (Anthology)',),
    'DDAGVL': ('Duel Decks Anthology: Garruk vs. Liliana', 'Duel Decks: Garruk vs. Liliana (Anthology)',),
    'DDAJVC': ('Duel Decks Anthology: Jace vs. Chandra', 'Duel Decks: Jace vs. Chandra (Anthology)',),
    'DDC': ('Duel Decks: Divine vs. Demonic', 'Divine vs. Demonic', 'DD3_DVD',),
    'DDD': ('Duel Decks: Garruk vs. Liliana', 'Garruk vs. Liliana', 'GVL', 'GVL2', 'DD3_GVL',),
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
    'DDO': ('Duel Decks: Elspeth vs. Kiora', 'Elspeth vs. Kiora', 'Duel Decks: Kiora vs. Elspeth',),
    'DDP': ('Duel Decks: Zendikar vs. Eldrazi', 'Zendikar vs. Eldrazi',),
    'DDQ': ('Duel Decks: Blessed vs. Cursed', 'Blessed vs. Cursed',),
    'DDR': ('Duel Decks: Nissa vs. Ob Nixilis', 'Nissa vs. Ob Nixilis',),
    'DDS': ('Duel Decks: Mind vs. Might', 'Mind vs. Might'),
    'DDT': ('Duel Decks: Merfolk vs. Goblins', 'Merfolk vs. Goblins'),
    'DDU': ('Duel Decks: Elves vs. Inventors', 'Elves vs. Inventors',),
    'DGM': ("Dragon's Maze",),
    'DIS': ('Dissension', 'DI',),
    'DKA': ('Dark Ascension',),
    'DKM': ('Deckmasters',),
    'DLM': ('DCI Legend Membership',),
    'DOM': ('Dominaria',),
    'DPA': ('Duels of the Planeswalkers',),
    'DRB': ('From the Vault: Dragons', 'FTV: Dragons',),
    'DRK': ('The Dark', 'DK',),
    'DST': ('Darksteel', 'DS',),
    'DTK': ('Dragons of Tarkir',),
    'E01': ('Archenemy: Nicol Bolas',),
    'E02': ('Explorers of Ixalan',),
    'EMA': ('Eternal Masters',),
    'EMN': ('Eldritch Moon',),
    'EUL': ('European Lands',),
    'EVE': ('Eventide', 'ET',),
    'EVG': ('Duel Decks: Elves vs. Goblins', 'EVG2', 'Elves vs. Goblins', 'DD3_EVG',),
    'EXO': ('Exodus', 'EX',),
    'EXP': ('Zendikar Expeditions', 'Zendikar Expedition',),
    'FEM': ('Fallen Empires', 'FE',),
    'FNM': ('Friday Night Magic', 'Friday Night Magic Promos', 'Friday Night Magic (FNM)', 'pFNM', 'FNM Promos',),
    'FRF': ('Fate Reforged',),
    'FUT': ('Future Sight', 'FS',),
    'GPT': ('Guildpact', 'GP',),
    'GPX': ('Grand Prix Promos', 'Grand Prix Promo', 'Grand Prix',),
    'GRL': ('Guru Lands',),
    'GTC': ('Gatecrash',),
    'H09': ('Premium Deck Series: Slivers',),
    'HGB': ('Holiday Gift Box Promos',),
    'HHL': ('Happy Holidays Promos', 'Happy Holidays',),
    'HJP': ('Hobby Japan Commemorative Cards',),
    'HML': ('Homelands', 'HL',),
    'HOP': ('Planechase',),
    'HOU': ('Hour of Devastation',),
    'HPP': ("Hero's Path Promos",),
    'ICE': ('Ice Age', 'IA',),
    'IMA': ('Iconic Masters',),
    'INP': ('Intro Pack Promos',),
    'INV': ('Invasion', 'IN',),
    'ISD': ('Innistrad',),
    'ITP': ('Introductory Two-Player Set',),
    'JOU': ('Journey into Nyx',),
    'JRW': ('Judge Rewards', 'Judge Gift Cards', 'Judge Gift Program', 'Judge Promo Cards', 'pJGP',),
    'JSS': ('Junior Super Series', 'Junior Series Promos', 'Junior Super Series (JSS)', 'Super Series',),
    'JUD': ('Judgment', 'JU', 'Judgement',),
    'KLD': ('Kaladesh',),
    'KTK': ('Khans of Tarkir',),
    'LEA': ('Limited Edition Alpha', 'Alpha', 'Alpha Edition', 'A'),
    'LEB': ('Limited Edition Beta', 'Beta', 'Beta Edition',),
    'LEG': ('Legends',),
    'LGN': ('Legions',),
    'LND': ('Alternate Art Lands',),
    'LRW': ('Lorwyn', 'LW', 'LOR',),
    'M10': ('Magic 2010', '2010 Core Set', 'Magic 2010 Core Set', 'Magic 2010 (M10)',),
    'M11': ('Magic 2011', '2011 Core Set', 'Magic 2011 Core Set', 'Magic 2011 (M11)',),
    'M12': ('Magic 2012', '2012 Core Set', 'Magic 2012 Core Set', 'Magic 2012 (M12)',),
    'M13': ('Magic 2013', '2013 Core Set', 'Magic 2013 Core Set', 'Magic 2013 (M13)',),
    'M14': ('Magic 2014', '2014 Core Set', 'Magic 2014 Core Set', 'Magic 2014 (M14)',),
    'M15': ('Magic 2015', '2015 Core Set', 'Magic 2015 Core Set', 'Magic 2015 (M15)',),
    'MBP': ('Media Inserts', 'Media Promos', 'pMEI',),
    'MBS': ('Mirrodin Besieged',),
    'MD1': ('Modern Event Deck', 'Modern Event Deck 2014', 'Magic Modern Event Deck',),
    'MGB': ('Multiverse Gift Box',),
    'MGD': ('Magic Game Day Cards', 'Magic Game Day', 'Game Day', 'Game Day Promos', 'pMGD', 'Game Day',),
    'MIR': ('Mirage',),
    'MM2': ('Modern Masters 2015', 'Modern Masters 2015 Edition',),
    'MM3': ('Modern Masters 2017', 'Modern Masters 2017 Edition',),
    'MMA': ('Modern Masters',),
    'MMQ': ('Mercadian Masques', 'MM',),
    'MOR': ('Morningtide', 'MT',),
    'MPH': ('Magic Premiere Shop',),
    'MPR': ('Magic Player Rewards', 'Reward cards', 'Textless Player Rewards', 'Player Rewards', 'pMPR',),
    'MPS': ('Amonkhet Invocations',),
    'MRD': ('Mirrodin',),
    'MS1': ('Masterpiece Series: Kaladesh Inventions', 'Kaladesh Inventions', 'MPS_KLD',),
    'MSP': ('Misc Promos', 'Stores Promos', 'Convention Promos', 'Comic Inserts', 'Full Box Promotion', 'Box Topper Cards', 'Magazine Inserts', 'Book Inserts', 'Video Game Promos', 'Other Cards', 'WotC Online Store', 'Buy-a-Box Promos', 'Draft Weekend Promos', 'Open House Promos', 'Standard Showdown Promos', 'Store Championship Promos',),
    'NEM': ('Nemesis', 'NE', 'NMS',),
    'NPH': ('New Phyrexia',),
    'ODY': ('Odyssey', 'OD',),
    'OGW': ('Oath of the Gatewatch',),
    'ONS': ('Onslaught', 'ON',),
    'ORI': ('Magic Origins', 'Origins',),
    'OVS': ('Oversized Cards',),
    'P96': ('1996 Pro Tour Decks',),
    'PC2': ('Planechase 2012', 'Planechase 2012 Edition',),
    'PCA': ('Planechase Anthology',),
    'PCY': ('Prophecy', 'PY', 'PR',),
    'PD2': ('Premium Deck Series: Fire and Lightning', 'Premium Deck Series: Fire & Lightning',),
    'PD3': ('Premium Deck Series: Graveborn',),
    'PLC': ('Planar Chaos', 'PC', 'PCH',),
    'PLS': ('Planeshift', 'PS',),
    'PO2': ('Portal: Second Age', 'Portal Second Age',),
    'POR': ('Portal',),
    'PRL': ('Prerelease, Release & Launch Party Cards', 'Prerelease & Release Cards', 'Prerelease Events', 'Release Events', 'Prerelease Promos', 'Release & Launch Parties Promos', 'Magic: The Gathering Launch Parties', 'PreRelease', 'Release', 'Launch Party', 'pPRE', 'pLPA', 'pREL',),
    'PRO': ('Pro Tour Promos', 'Pro Tour',),
    'PTK': ('Portal: Three Kingdoms', 'Portal Three Kingdoms',),
    'RAV': ('Ravnica: City of Guilds', 'Ravnica', 'RA',),
    'RED': ('Redemption Program Cards',),
    'REN': ('Renaissance',),
    'RIX': ('Rivals of Ixalan',),
    'ROE': ('Rise of the Eldrazi',),
    'RSM': ('Revised Edition (Summer Magic)',),
    'RTR': ('Return to Ravnica', 'Retun to Ravnica',),
    'S00': ('Starter 2000',),
    'S11': ('Salvat 2011', 'Salvat Magic Encyclopedia',),
    'S99': ('Starter 1999', 'Starter',),
    'SCG': ('Scourge', 'SC',),
    'SHM': ('Shadowmoor', 'SM',),
    'SOI': ('Shadows over Innistrad',),
    'SOK': ('Saviors of Kamigawa', 'SK',),
    'SOM': ('Scars of Mirrodin',),
    'STH': ('Stronghold', 'SH',),
    'SUM': ('Summer of Magic Promos', 'Summer of Magic', 'pSUM',),
    'TDP': ('Tarkir Dragonfury Promos',),
    'THG': ('Two-Headed Giant Promos', '2HG', 'Two-Headed Giant Tournament',),
    'THS': ('Theros',),
    'TMP': ('Tempest', 'TE',),
    'TOR': ('Torment', 'TO', 'TR',),
    'TSP': ('Time Spiral', 'TS',),
    'TST': ('Time Spiral Timeshifted', 'TSTS', 'Timeshifted',),
    'UDS': ("Urza's Destiny", 'UD',),
    'UGF': ("Ugin's Fate Promos", "Ugin's Fate", 'FRF_UGIN'),
    'UGL': ('Unglued',),
    'ULG': ("Urza's Legacy", 'UL',),
    'UNH': ('Unhinged', 'UH',),
    'URC': ('Ultra Rare Cards',),
    'USG': ("Urza's Saga", 'US',),
    'UST': ('Unstable',),
    'V09': ('From the Vault: Exiled', 'FTV: Exiled',),
    'V10': ('From the Vault: Relics', 'FTV: Relics',),
    'V11': ('From the Vault: Legends', 'FTV: Legends', 'FVL',),
    'V12': ('From the Vault: Realms', 'FTV: Realms',),
    'V13': ('From the Vault: Twenty', 'FTV: Twenty',),
    'V14': ('From the Vault: Annihilation', 'FTV: Annihilation',),
    'V15': ('From the Vault: Angels', 'FTV: Angels',),
    'V16': ('From the Vault: Lore', 'FTV: Lore',),
    'V17': ('From the Vault: Transform',),
    'VIS': ('Visions', 'VI',),
    'VNG': ('Vanguard',),
    'W00': ('2000 World Championship Decks',),
    'W01': ('2001 World Championship Decks',),
    'W02': ('2002 World Championship Decks',),
    'W03': ('2003 World Championship Decks',),
    'W04': ('2004 World Championship Decks',),
    'W16': ('Welcome Deck 2016',),
    'W17': ('Welcome Deck 2017',),
    'W97': ('1997 World Championship Decks',),
    'W98': ('1998 World Championship Decks',),
    'W99': ('1999 World Championship Decks',),
    'WLD': ('Championships Prizes',),
    'WMC': ('World Magic Cup Qualifiers Promos', 'World Magic Cup Qualifiers', 'WMCQ', 'pWCQ',),
    'WPN': ('WPN\\Gateway', 'WPN/Gateway', 'Gateway & WPN Promos', 'Wizards Play Network', 'Gateway', 'Gateway Promo', 'pWPN', 'pGTW',),
    'WTH': ('Weatherlight', 'WL',),
    'WWK': ('Worldwake',),
    'XLN': ('Ixalan',),
    'ZEN': ('Zendikar',),
}

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
        'Duel Decks: Elves vs. Inventors',
        'Duel Decks: Garruk vs. Liliana',
        'Duel Decks: Merfolk vs. Goblins',
        'Duel Decks: Mind vs. Might',
        'Duels of the Planeswalkers',
        'Fallen Empires',
        'Fate Reforged Clash Pack',
        'From the Vault: Annihilation',
        'From the Vault: Dragons',
        'From the Vault: Exiled',
        'From the Vault: Legends',
        'From the Vault: Realms',
        'From the Vault: Relics',
        'From the Vault: Transform',
        'From the Vault: Twenty',
        'Grand Prix Promos',
        'Happy Holidays Promos',
        'Iconic Masters',
        'Intro Pack Promos',
        'Limited Edition Alpha',
        'Limited Edition Beta',
        'Magic 2015 Clash Pack',
        'Magic Player Rewards',
        'Masterpiece Series: Kaladesh Inventions',
        'Masters 25',
        'Modern Event Deck',
        'Modern Masters 2015',
        'Modern Masters 2017',
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
        'Zendikar Expeditions',
    )
}

NAME_CHARACTERS = core.language.LOWERCASE_LETTERS_ENGLISH | core.language.LOWERCASE_LETTERS_RUSSIAN | set(string.digits)


def getNameKey(setNameString):
    return ''.join(c for c in setNameString.lower() if c in NAME_CHARACTERS)

_SETS = tools.dict.expandMapping(_SET_ABBREVIATIONS_SOURCE, getNameKey)


def getFullName(setAbbrv):
    return _SET_ABBREVIATIONS_SOURCE[setAbbrv][0]


def tryGetAbbreviation(setNameString, quiet=False):
    result = _SETS.get(getNameKey(setNameString), None)
    if result is None and not quiet:
        _logger.warning('Unable to recognize set "{}"'.format(setNameString))
        _logger.warning(''.join(traceback.format_stack()))
    return result


SINGLE_LANGUAGE_SETS = {}
for language, setStrings in _SINGLE_LANGUAGE_SETS_DATA.items():
    for setId in setStrings:
        abbrv = tryGetAbbreviation(setId)
        if abbrv is None:
            print('Unknown card set "{}"'.format(setId))
        SINGLE_LANGUAGE_SETS[abbrv] = language
