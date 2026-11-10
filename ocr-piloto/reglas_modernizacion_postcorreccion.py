# Adapted from https://github.com/vegafabianr/early-modern-spanish-ocr-baseline (modernizacion/reglas.py,
# commit c4e1b71), whose rules were written for 16th-18th century prints. Changes for this corpus of
# 19th and 20th century editions, where these words are usually already right and the rules made them wrong:
# - "estas" and "aun" no longer get an accent ("estás", "aún"): "en estas sagradas", "y aun el soldado".
# - "el" before "mismo" stays an article: "en el mismo sentido", not "en él mismo sentido".
# - "dél" becomes "de él" instead of "del", which changed the meaning.
# - Past tense in "-steis" keeps no accent: "tuvisteis", not "tuvistéis".
# Added: postcorregir(), a second step that uses the vocabulary of the whole corpus (see its section at the end).
# Made more prudent after checking every change in "La perfecta casada", where about 25 of 433 changes
# turned a right word into a wrong one:
# - Missing accents: only accents that current spelling requires ("dió", "imágen", "procurarémos" were 19th-century
#   accents taken from the corpus), and never on the last syllable of a word ending in -a, -e, -o, -an, -en, -as or
#   -es, because both forms are verbs ("ni sacara" / "sacará", "al mando" / "mandó", "que apunte" / "apunté").
# - "gue"/"gui" take "ü", not "ú" ("vergüenza"). Printed without a mark ("verguenza", "antiguedad"), they take "ü" if
#   only the form with "ü" is in the Spanish dictionary (_dieresis()).
# - "sc" -> "c" is not applied to capitalized words, mostly names ("Scila").
# - Glued words are split only in step 5, if the two words appear together in the corpus at least 3 times and 20 times
#   more often than the glued form; pronoun groups ("Olvidósele") and verb endings after -r ("compraren") are kept.
# - Step 5 needs the corrected word next to the same neighbor at least twice, not once ("asear" -> "afear").
# - Latin passages (found as in modernizar()) get no accents from the corpus ("est anima mea", not "ánima").
# - Abbreviations and tokens with digits are left as printed (see procesar_linea()): "Génes.", "cap.", "x1v".
# - A word changed by modernizar() into a form found in fewer than DROP_BOOKS books of the corpus stays as printed
#   (modernizar_prudente()): "distin" (half of a word cut at the end of a line) is not "distín", "Hymnus" is not
#   "Himnus".
# - Step 5 also corrects frequent OCR errors ("eon" -> "con", "esle" -> "este", in 3 books or more): a word that is
#   not in the Spanish dictionary of LibreOffice (Hunspell es_ES, RLA-ES project; github.com/LibreOffice/dictionaries,
#   es/es_ES.dic and es_ES.aff, commit 762abe7 of 2025-02-13, copied to ocr-piloto/diccionario-es/ with its license
#   and README, read with the spylls package; see errores_frecuentes()) and is one OCR confusion
#   away from a word 50 times more frequent, if the corrected word appears next to the same neighbors at least 3
#   times and 20 times more often than the printed one. Words of the dictionary ("lodo", "fino", "ciclo") are never
#   corrected. Latin passages of two words or more are not touched. modernizar() leaves these forms as printed.
# - Step 5 also corrects an unknown word (5 letters or more) without neighbor support when it has a single clear
#   candidate: one OCR confusion away (adding a/u, o/e, n/a and J/l), in 10 books or more, 30 occurrences or more and
#   10 times more frequent than the second candidate (see _clear_candidate()).
# - A frequent OCR error with a single correction (4 letters or more) is corrected even without neighbor
#   support ("consideren” mueho tres" -> "mucho"); frequent errors need a correction 20 times more frequent, not 50
#   ("eruz" -> "cruz"); "ñ" read for "n" is one more OCR confusion ("mañeras" -> "maneras"). Drop caps at the
#   beginning of a line (capitulares()), punctuation at the beginning of a line (_puntuacion_inicial()) and the
#   register of changes (_anotar()) were also added. After reading that register for three books: glued
#   words are not split if the word is in the Spanish dictionary ("decrecer" is not "de crecer"), and step 5 without
#   a neighbor leaves alone capitalized words ("Tamba", a province of Japan, is not "Tumba") and words of the
#   dictionary ("alojan" is not "alejan"). Latin: a piece of line with a third of its words Latin
#   (3 or more) is left whole as printed ("charitatis" stayed, "quasi" no longer becomes "cuasi"); accents read by the
#   OCR on Latin words and inscriptions in capitals with V for U ("OMNIVM") are recognized as Latin. Passages marked
#   as Latin or Italian by the last cell of 5-limpieza (<foreign xml:lang="la">) are left whole (patron_protegido()).
# -*- coding: utf-8 -*-
"""Spelling modernization of Spanish prints, 16th-18th centuries.

Criterion: modern editions of Golden Age drama. Only what is purely graphic is modernized (u/v, i/j/y, b/v, h, x>j, ç,
z/c, qu/cu, ph, th, ch=k, double letters, g/j) and the accents (RAE 2010). Forms with a phonetic or morphological value
of their own stay (agora, mesmo, propria, efeto, escusar...). Punctuation and capitals are not touched. Latin is left
alone as far as possible.

Use: modernizar(line) -> str   (only re and unicodedata)
"""
import re
import unicodedata

# ---------------------------------------------------------------------------
# Constantes básicas
# ---------------------------------------------------------------------------
V = 'aeiouáéíóúàèìòùâêîôûäëïöü'           # Vowels, with their marks
VCLASS = '[' + V + ']'
STRONG = set('aeoáéóàèòâêô')
ACUTE = {'a': 'á', 'e': 'é', 'i': 'í', 'o': 'ó', 'u': 'ú'}
UNACC = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u'}
VOW_PLAIN = 'aeiouáéíóúü'


def _strip_acc(s):
    return ''.join(UNACC.get(c, c) for c in s)


# ---------------------------------------------------------------------------
# Latín
# ---------------------------------------------------------------------------
LAT_STRONG = set("""
et est sunt non quod quae quam quia quoniam enim autem vero ut cum ad ab atque ac
nec neque sicut ego mihi tibi sibi nobis vobis eius ejus eorum earum ipse ipsa ipsum
ipsi hoc haec hic ille illa illud illi illum illo omnis omnes omnia omnibus deus dei
deo deum domine dominus domini domino dominum christi christus christum sancti
sanctus sanctum sanctorum spiritus spiritu spiritui filius filii filio filium patris
patri patrem pater mater verbum factum erat esse fuit sit dixit dicit dicens dicitur
ait inquit ibi ubi tamen etiam igitur itaque nunc tunc semper quis quid quo cuius
cujus eam eum eos eas apud secundum propter sub inter per ecce beati beatus beata
qui quoque quidem nisi sine aut vel gratia gratiae plena benedicta benedictus
mulieribus fructus ventris tui tuae tuum meum meus mea tua sua suis suo suum sui
nostri nostra nostrum noster vestri vester vestra coeli caeli coelum caelum coelo
caelo terrae regnum nomen voluntas panem hodie debita dimittimus debitoribus
tentationem saecula saeculorum secula seculorum in ex eo super magis tempore ibid
ibidem psal psalm cap lib vers ergo idest scilicet videlicet libera liberanos
""".split())
LAT_WEAK = set("""de me te a e o si nos vos tu pro contra ora amen alleluia gloria
caro malo terra sed id ea in iesu iesus maria mariae ave sancta sancto""".split())
LAT_NOT = set("""jesus iesus venus virus cae trae decae recae atrae contrae distrae
retrae sustrae extrae item""".split())


def _is_latin_strong(tok):
    t = _strip_acc(tok.lower())  # OCR accents on Latin: "quía", "Ením"
    if tok.isupper() and len(tok) > 1 and 'v' in t and _is_latin_strong(t.replace('v', 'u')):
        return True  # Inscriptions in capitals with V for U: "OMNIVM", "SVSPENSVS"
    if t in LAT_STRONG:
        return True
    if t in LAT_NOT:
        return False
    if len(t) >= 5 and re.search(r'(orum|arum|ibus|ntur|bant|atis|itis|inis|onis|oris)$', t):
        return True
    if tok[:1].islower() and len(t) >= 4 and re.search(
            r'(um|us|ae|ii|tur|mus|it|unt|ent|at|et|am|em|bat|unt)$', t):
        if t.endswith('ae') and re.search(r'[cr]ae$', t) and len(t) < 5:
            return False
        return True
    return False


LATIN_SHARE = 1 / 3  # A line (or piece) with a third of its words Latin, 3 or more, is all Latin


def _latin_mask(words):
    n = len(words)
    strong = [_is_latin_strong(w) for w in words]
    weak = [w.lower() in LAT_WEAK for w in words]
    if sum(strong) >= 3 and sum(strong) >= LATIN_SHARE * n:
        return [True] * n  # "et charitatis affectu", "posse sustineri. Enim vero": words the lists do not know
    mask = [False] * n
    idx = [i for i in range(n) if strong[i]]
    groups, cur = [], []
    for i in idx:
        if cur and i - cur[-1] - 1 > 2:
            groups.append(cur)
            cur = []
        cur.append(i)
    if cur:
        groups.append(cur)
    for g in groups:
        if len(g) >= 2:
            a, b = g[0], g[-1]
            while a - 1 >= 0 and (weak[a - 1] or strong[a - 1]):
                a -= 1
            while b + 1 < n and (weak[b + 1] or strong[b + 1]):
                b += 1
            for k in range(a, b + 1):
                mask[k] = True
        else:
            mask[g[0]] = True
    return mask


# ---------------------------------------------------------------------------
# Step 1: u/v, i/j/y (one-to-one substitutions, positions stay)
# ---------------------------------------------------------------------------
JE_STEMS = ('iesu', 'ierusal', 'ieronim', 'ierich', 'ieric', 'ieremi', 'iehov',
            'ierarq', 'ieroglif', 'iezabel', 'iebus', 'iesse', 'iepht', 'iefte',
            'ieroboam', 'iesuit')
Y_CAP_OK = ('ygles', 'ygna', 'ysab', 'ysid', 'ytal', 'yndi', 'ymag', 'ydol', 'yglesia',
            'ynqui', 'ynoc', 'ylust', 'ysla', 'yrlan', 'ynglat', 'yerusal', 'ymperi',
            'ynfier', 'ynmacul', 'ynmac', 'yspan')
Y_EXC = {'ayllu', 'ayllus'}
MID_Y = {'maior': 'mayor', 'maiores': 'mayores', 'maioral': 'mayoral', 'suio': 'suyo',
         'suia': 'suya', 'suios': 'suyos', 'suias': 'suyas', 'tuio': 'tuyo',
         'tuia': 'tuya', 'tuios': 'tuyos', 'tuias': 'tuyas', 'cuio': 'cuyo',
         'cuia': 'cuya', 'cuios': 'cuyos', 'cuias': 'cuyas', 'aiuda': 'ayuda',
         'aiudar': 'ayudar', 'aiudo': 'ayudo', 'raio': 'rayo', 'raios': 'rayos',
         'maio': 'mayo', 'oiendo': 'oyendo', 'leies': 'leyes', 'reies': 'reyes',
         'aiuno': 'ayuno', 'aiunos': 'ayunos', 'aiunar': 'ayunar', 'huio': 'huyo'}


def _uv_ij(w, cap):
    if re.match(r'^i[uv]' + VCLASS, w):
        w = 'j' + w[1:]
    # v as a vowel (not followed by a vowel) -> u
    w = re.sub(r'v(?!' + VCLASS + ')', 'u', w)
    # u entre vocales -> v
    w = re.sub(r'(?<=' + VCLASS + ')u(?=' + VCLASS + ')', 'v', w)
    # Vowel + l/r + u + vowel -> v (obseruar, saluo, cieruo)
    if not re.match(r'^(baluart|valuart|peruan|ceruleo)', w):
        w = re.sub(r'(?<=' + VCLASS + r')([lr])u(?=' + VCLASS + ')', r'\1v', w)
    # Prefixes with consonantal u
    w = re.sub(r'^(con|in|en|sin)u(?=[aeioáéíó])', r'\1v', w)
    if not w.startswith('aduan'):
        w = re.sub(r'^adu(?=[aeioáéíó])', 'adv', w)
    w = re.sub(r'^obu(?=[aeioáéíó])', 'obv', w)
    # i inicial consonántica
    if w in ('ia', 'io'):
        return 'y' + w[1:]
    if re.match(r'^i' + VCLASS, w) and len(w) > 2:
        if w.startswith('ie') or w.startswith('ié') or w.startswith('iè'):
            if w.startswith(JE_STEMS):
                w = 'j' + w[1:]
            else:
                w = 'y' + w[1:]
        elif re.match(r'^ia[zc]', w) or w.startswith('iug'):
            w = 'y' + w[1:]
        else:
            w = 'j' + w[1:]
    # y as a vowel before a consonant -> i
    if w not in Y_EXC and (not cap or w.startswith(Y_CAP_OK) or re.search(r'y[^aeiouáéíóú]', w[1:] if not w.startswith('y') else '')):
        if not cap or w.startswith(Y_CAP_OK) or not w.startswith('y'):
            w = re.sub(r'y(?=[bcdfgjklmnñpqrstvxz])', 'i', w)
    if w in MID_Y:
        w = MID_Y[w]
    return w


# ---------------------------------------------------------------------------
# Paso 2: grafías consonánticas
# ---------------------------------------------------------------------------
GRAPHIC_EXACT = {
    'oy': 'hoy', 'ombre': 'hombre', 'ombres': 'hombres', 'aora': 'ahora',
    'onra': 'honra', 'onras': 'honras', 'onrar': 'honrar', 'onrado': 'honrado',
    'onrada': 'honrada', 'onrados': 'honrados', 'onroso': 'honroso',
    'onesto': 'honesto', 'onesta': 'honesta', 'onestidad': 'honestidad',
    'umilde': 'humilde', 'umildes': 'humildes', 'umildad': 'humildad',
    'umano': 'humano', 'umana': 'humana', 'umanos': 'humanos', 'umanas': 'humanas',
    'umanidad': 'humanidad', 'ermano': 'hermano', 'ermana': 'hermana',
    'ermanos': 'hermanos', 'ermanas': 'hermanas', 'ermosura': 'hermosura',
    'ermoso': 'hermoso', 'ermosa': 'hermosa', 'ijo': 'hijo', 'ija': 'hija',
    'ijos': 'hijos', 'ijas': 'hijas', 'eredero': 'heredero', 'eredad': 'heredad',
    'erencia': 'herencia', 'ospital': 'hospital', 'ostia': 'hostia',
    'ostias': 'hostias', 'istoria': 'historia', 'istorias': 'historias', 'acia': 'hacia',
    'uir': 'huir', 'ayan': 'hayan', 'ayamos': 'hayamos',
    'hechar': 'echar', 'hecharon': 'echaron', 'hechando': 'echando',
    'hechava': 'echava', 'hechaba': 'echaba',
    'boz': 'voz', 'bozes': 'vozes', 'choro': 'coro', 'choros': 'coros',
    'chaos': 'caos', 'anna': 'ana',
    'proximo': 'proximo', 'huve': 'hube',
}
CONM = ('commov', 'commemor', 'commut', 'commiser', 'commigo', 'commin', 'commoc',
        'commen', 'commixt')
NN_FIX = [('annunci', 'anunci'), ('connex', 'conex'), ('annex', 'anex'),
          ('annual', 'anual'), ('annal', 'anal'), ('tyrann', 'tyran'),
          ('tirann', 'tiran'), ('innocen', 'inocen'), ('annot', 'anot'),
          ('annul', 'anul'), ('annihil', 'aniquil')]
X_KEEP = ('proxim', 'maxim', 'auxili', 'sexo', 'sexu', 'anex', 'nexo', 'flexi',
          'reflexion', 'complexion', 'conexion', 'connexion', 'inflexi', 'axiom',
          'doxo', 'doxa', 'doxia', 'toxic', 'oxid', 'laxo', 'laxa', 'inexo', 'inexa',
          'inexh', 'taxat', 'elixir', 'exhal', 'exhort', 'exhib', 'exhum', 'mexic')
X_CAP_J = ('xavier', 'ximen', 'xerez', 'alexandr', 'quixot', 'guadalaxar', 'xativa',
           'xuarez', 'xeronim', 'xerusal', 'mexia', 'xaen', 'xalisc', 'truxill',
           'badaxoz', 'aranxuez', 'xaraquemad', 'ximenez')
Z_KEEP = ('ezequiel', 'ezequias', 'zebedeo', 'zenon', 'zeus', 'zenobi', 'zeuxis',
          'zigzag', 'zinc', 'zeta', 'zebulon', 'zelot', 'zelan', 'zefora')
CH_K = [('archang', 'arcang'), ('eucharist', 'eucarist'), ('zachar', 'zacar'),
        ('zacheo', 'zaqueo'), ('chimera', 'quimera'), ('machina', 'maquina'),
        ('mechanic', 'mecanic'), ('catechism', 'catecism'), ('catechumen', 'catecumen'),
        ('ezechi', 'ezequi'), ('melchised', 'melquised'), ('antiochi', 'antioqui'),
        ('rachel', 'raquel'), ('cherubin', 'querubin'), ('joachin', 'joaquin'),
        ('chanane', 'canane'), ('chanaan', 'canaan'), ('achab', 'acab'),
        ('chimic', 'quimic'), ('schola', 'escola'), ('scholast', 'escolast'),
        ('character', 'caracter'), ('charism', 'carism'), ('achaz', 'acaz'),
        ('ochozias', 'ocozias'), ('jechonias', 'jeconias'), ('chore', 'core'),
        ('anchora', 'ancora'), ('stomach', 'stomac'), ('estomach', 'estomag'),
        ('cholera', 'colera'), ('melancholi', 'melancoli'), ('chaldeo', 'caldeo'),
        ('chaldea', 'caldea'), ('charid', 'carid'), ('charit', 'carit'), ('chersones', 'quersones'), ('chirurg', 'cirug')]


def _graphic(w, cap, keepx=False):
    if w in GRAPHIC_EXACT:
        return GRAPHIC_EXACT[w]
    w = re.sub(r'^scien', 'cien', w)
    # ç
    w = re.sub(r'ç(?=[eiéí])', 'c', w).replace('ç', 'z')
    # ph, th, rh
    w = w.replace('ph', 'f').replace('th', 't').replace('rh', 'r')
    # ch = k
    for a, b in CH_K:
        if a in w:
            w = w.replace(a, b)
    w = re.sub(r'ch(?=[rl])', 'c', w)
    w = re.sub(r'rchi(a|as)$', r'rqui\1', w)
    w = re.sub(r'rcha(s)?$', r'rca\1', w)
    if len(w) > 3:
        w = re.sub(r'ch$', 'c', w)
    # qu / cu
    w = w.replace('qü', 'cu')
    w = re.sub(r'qu(?=[aoáóàò])', 'cu', w)
    w = re.sub(r'(fre|elo|conse|subse|delin)quen', r'\1cuen', w)
    w = re.sub(r'^sequenc', 'secuenc', w)
    w = re.sub(r'^questi', 'cuesti', w)
    w = re.sub(r'quinquag', 'quincuag', w)
    w = re.sub(r'^equestr', 'ecuestr', w)
    # x -> j
    if not keepx and not (cap and not w.startswith(X_CAP_J)):
        if not w.startswith(X_KEEP) and not any(k in w for k in X_KEEP):
            w = re.sub(r'^ex(?=empl|erc|ecu|ido)', 'ej', w)
            # x between vowels, not the initial 'ex-'
            def _xj(m):
                i = m.start()
                if i == 1 and w[0] == 'e':
                    return 'x'
                if i >= 3 and w[i - 3:i - 1] == 'in' and w[i - 1] == 'e':
                    return 'x'
                return 'j'
            w = re.sub(r'(?<=' + VCLASS + ')x(?=' + VCLASS + ')', _xj, w)
            w = re.sub(r'^x(?=' + VCLASS + ')', 'j', w)
            if not cap:
                w = re.sub(r'(?<=' + VCLASS + ')x$', 'j', w)
    # g -> j
    w = re.sub(r'^muger', 'mujer', w)
    w = re.sub(r'^magest', 'majest', w)
    w = re.sub(r'^agen(o|a|os|as)$', r'ajen\1', w)
    w = re.sub(r'hereg([eií])', r'herej\1', w)
    if len(w) >= 5:
        w = re.sub(r'age(s)?$', r'aje\1', w)
    if 'exager' not in w:
        w = re.sub(r'ager(o|a|os|as)$', r'ajer\1', w)
    w = re.sub(r'^(e[sx]trang)(er)', lambda m: m.group(1)[:-1] + 'j' + m.group(2), w)
    w = re.sub(r'^consegero', 'consejero', w)
    w = re.sub(r'^vegez', 'vejez', w)
    w = re.sub(r'^lisong', 'lisonj', w)
    w = re.sub(r'^monge', 'monje', w)
    w = re.sub(r'^suget', 'sujet', w)
    w = re.sub(r'^sugeci', 'sujeci', w)
    w = re.sub(r'^gef([ea])', r'jef\1', w)
    w = re.sub(r'^(ge|hie)ronim', 'jeronim', w)
    w = re.sub(r'^gerusal', 'jerusal', w)
    # z before e/i -> c
    if not w.startswith(Z_KEEP):
        w = re.sub(r'z(?=[eiéíèì])', 'c', w)
    # consonantes dobles
    w = w.replace('ss', 's').replace('ff', 'f').replace('pp', 'p').replace('tt', 't')
    w = w.replace('bb', 'b').replace('dd', 'd').replace('gg', 'g')
    w = w.replace('succe', 'suce')
    w = re.sub(r'cc(?=[aouáóúlr]|$)', 'c', w)
    if w.startswith('comm'):
        w = ('conm' if w.startswith(CONM) else 'com') + w[4:]
    w = w.replace('imm', 'inm').replace('summ', 'sum').replace('mm', 'm')
    for a, b in NN_FIX:
        if a in w:
            w = w.replace(a, b)
    # h
    w = re.sub(r'^ue', 'hue', w)
    w = re.sub(r'^h?av(er|ia|ian|ias|iamos|iendo|ido|ida|idos|idas|emos|eis|ra|ras|'
               r'ran|re|ria|rian|rias|riamos|ramos|reis|ieis)$', r'hab\1', w)
    w = re.sub(r'^h?[uv][uvb](o|imos|isteis|iste|ieron|iera|ieras|ieran|ieramos|iese|'
               r'ieses|iesen|iere|ieren|iesemos)$', r'hub\1', w)
    # b / v
    if not re.search(r'(octav|esclav|eslav|brav|^lav|^clav|enclav|agrav|^grav|^cav|'
                     r'excav|^nav|deprav|^bav|^slav|^ochav)(a|as|an|amos|ais)$', w):
        w = re.sub(r'(?<=[a-zñ])av(a|as|an|amos|ais)$', r'ab\1', w)
    w = re.sub(r'^dev(e|es|en|emos|eis|er|eres|ia|ian|ias|iamos|ido|ida|idos|idas|'
               r'idamente|io|iendo|iera|ieran|ieras|iese|iesen|iere|ieren|o|a|as|an|'
               r'amos|ais|eria|erian|era)$', r'deb\1', w)
    w = re.sub(r'^bev(?=[aeiou])', 'beb', w)
    w = w.replace('escriv', 'escrib')
    w = re.sub(r'^embi(?=[aeoáéó])', 'envi', w)
    w = re.sub(r'(rec|perc|conc|aperc)([ei])v', r'\1\2b', w)
    w = w.replace('caval', 'cabal')
    w = re.sub(r'gov(e|ie)rn', r'gob\1rn', w)
    w = re.sub(r'^(re|de|en|des)?bolv', r'\1volv', w)
    w = re.sub(r'^(re|de|en|des)?buel(v|t)', r'\1vuel\2', w)
    if not w.startswith('bivor'):
        w = re.sub(r'^(re|con|sobre)?biv', r'\1viv', w)
    w = re.sub(r'^(a|com|re|des)?prov(ar|ad|ado|ada|ados|adas|aba|aban|o|amos|aron|'
               r'ando|aria|arian|are|aremos|ase|asen|ara|aran|e|es|en|emos|ais|eis|'
               r'acion|anza)$', r'\1prob\2', w)
    w = re.sub(r'^(a|com|re)?pruev', r'\1prueb', w)
    w = w.replace('cordova', 'cordoba').replace('cristoval', 'cristobal')
    return w


# ---------------------------------------------------------------------------
# Paso 3: acentuación
# ---------------------------------------------------------------------------
def _vowel_pos(w):
    res = []
    for i, c in enumerate(w):
        if c in VOW_PLAIN:
            if c == 'u' and i > 0 and w[i - 1] in 'qg' and i + 1 < len(w) and w[i + 1] in 'eiéí':
                continue
            res.append(i)
    return res


def _nuclei(w, stressed=None):
    groups = []
    for p in _vowel_pos(w):
        if groups and groups[-1][-1] == p - 1:
            a, b = w[p - 1], w[p]
            sa, sb = a in STRONG, b in STRONG
            acc_a = a in 'íú' or (p - 1 == stressed and _strip_acc(a) in 'iu')
            acc_b = b in 'íú' or (p == stressed and _strip_acc(b) in 'iu')
            if (sa and sb) or acc_a or acc_b:
                groups.append([p])
            else:
                groups[-1].append(p)
        else:
            groups.append([p])
    return groups


def _needs_tilde(w, p):
    groups = _nuclei(w, p)
    gi = next((i for i, g in enumerate(groups) if p in g), None)
    if gi is None:
        return False
    c = w[p]
    if c in 'iu':
        nb = []
        for d in (-1, 1):
            q = p + d
            if 0 <= q < len(w) and w[q] == 'h':
                q += d
            if 0 <= q < len(w):
                nb.append(w[q])
        if any(x in STRONG for x in nb) and len(groups[gi]) == 1:
            return True
    n = len(groups)
    if n == 1:
        return False
    k = n - 1 - gi
    last = w[-1]
    ends_vns = last in 'aeiou' or (last in 'ns' and len(w) > 1 and w[-2] in 'aeiou')
    if k == 0:
        return ends_vns
    if k == 1:
        return not ends_vns
    return True


def _put(w, p):
    return w[:p] + ACUTE.get(w[p], w[p]) + w[p + 1:]


def _syll(w):
    return len(_nuclei(w))


# Dictionary of accents (modern forms)
_ACC_LIST = """
también además después aquí allí ahí allá acá acullá así jamás quizá quizás según
algún ningún común demás atrás detrás adiós
día días maría río ríos tío tía tíos tías vía vías mío mía míos mías frío fría fríos
judío judía judíos judías albedrío señorío navío navíos gentío vacío vacía desafío
oído oídos país países raíz maíz baúl raúl saúl esaú caín laúd ataúd búho mesías
envío
están estén estés estáis
será serán serás habrá habrán habrás podrá podrán podrás tendrá tendrán tendrás
hará harán harás dirá dirán dirás sabrá sabrán sabrás querrá querrán saldrá saldrán
pondrá pondrán vendrá vendrán valdrá estará estarán dará darán verán irán
seré habré tendré haré diré querré saldré pondré vendré estaré daré
seréis habréis podréis tendréis haréis diréis sabréis vendréis estaréis daréis veréis
iréis queréis
decís venís vivís oís salís pedís servís sentís seguís subís abrís recibís escribís
partís morís
ángel ángeles árbol árboles cárcel cárceles mártir mártires fácil difícil útil inútil
débil hábil dócil frágil ágil cáliz azúcar carácter mármol néctar ámbar huésped
huéspedes alférez lápiz apóstol apóstoles espíritu espíritus ímpetu
último última últimos últimas único única únicos únicas próximo próxima ánima ánimas
ánimo lágrima lágrimas sábado sábados título títulos capítulo capítulos artículo
artículos mérito méritos súbdito súbditos príncipe príncipes pontífice pontífices
sacrílego sacrílegos clérigo clérigos párroco púlpito púlpitos hábito hábitos límite
límites época fábula fábulas parábola parábolas discípulo discípulos discípula
vírgenes órdenes imágenes orígenes jóvenes márgenes crímenes exámenes pájaro pájaros
género géneros número números término términos cántico cánticos cátedra diácono
diáconos música médico médicos óleo océano héroe héroes lícito lícita ilícito
ilícita íntimo íntima prójimo prójimos república público pública públicos públicas
católico católica católicos católicas método período ídolo ídolos bárbaro bárbaros
cántaro lámpara lámparas plática pláticas víspera vísperas célebre célebres cómplice
mínimo máximo pésimo óptimo décimo séptimo sétimo pacífico magnífico magnífica
benévolo pródigo fértil estéril túnica túnicas círculo obstáculo oráculo espectáculo
cúmulo sílaba índice ínfimo ínclito cónyuge máquina máquinas cólera crédito
cristóbal córdoba ángela mónica bárbara águeda úrsula lázaro jerónimo
áspid cálices cálix sacrílega epístola epístolas evangélico tránsito ánade
pública súplica súplicas cuádruple sátira páramo tálamo cáñamo
hipócrita hipócritas cándido cándida lúcido plácido pálido pálida
teología filosofía alegría compañía cortesía osadía valentía porfía fantasía herejía
herejías idolatría profecía profecías geometría melancolía agonía armonía sabiduría
señoría policía monarquía jerarquía eucaristía letanía letanías sacristía tiranía
villanía cobardía hidalguía mayoría minoría simpatía travesía abadía cofradía
cofradías mercadería mercaderías hechicería energía guía guías vigía lejía
andalucía lucía etiopía hungría turquía
isaías elías jeremías matías tobías zacarías ananías ezequías josías ozías nehemías
abdías sofonías malaquías jeconías ocozías
adán jordán capitán capitanes afán galán alacrán satán tucumán yucatán sebastián
julián iván holgazán sacristán refrán desván ademán gavilán guardián faisán huracán
rufián catalán alemán musulmán alcorán corán fernán abrahán solimán canaán
belén jerusalén almacén andén desdén sostén rehén vaivén parabién edén rubén efrén
matusalén
moisés inés andrés francés inglés portugués marqués interés través revés aragonés
genovés holandés japonés montañés burgués ciprés envés ginés eclesiastés
satanás barrabás nicolás caifás anás compás jonás amós
jesús emaús
aquí allí perú belcebú bambú tabú
noé josué josé café bernabé bartolomé
jehová alcalá panamá bogotá maná judá
jericó
maravedí maravedís sinaí jabalí carmesí rubí alhelí frenesí baladí borceguí leví
neftalí
varón ladrón patrón padrón aarón nerón hebrón barón cimarrón cicerón calderón
sánchez fernández martínez gonzález rodríguez gómez lópez pérez díaz hernández
álvarez gutiérrez ramírez jiménez vázquez velázquez suárez domínguez núñez benítez
méndez ordóñez ibáñez yáñez juárez chávez
méxico américa áfrica ávila álava cádiz málaga mérida úbeda écija
"""
ACCENT = {}
for _w in _ACC_LIST.split():
    ACCENT.setdefault(_strip_acc(_w), _w)

# imperfectos/condicionales -ía
_IA_STEMS = """hab ten dec pod quer deb viv ven sal o ve cre le tra ca sent ped serv segu
conoc parec suced ofrec merec padec recib escrib pertenec sol entend respond pon com beb
mov volv perd sufr mor dorm cumpl tem corr venc nac crec conven permit imped advert acud
asist consist exist hu re obedec aparec convert part sub un reg dirig eleg fing aflig ard
cab val dol exced conced proced promet met comet somet escog cog recog atend pretend
defend ofend encend descend vend comprend aprend extend abr cubr descubr resplandec
florec enriquec agradec favorec conven contradec bendec maldec decid divid persuad
prevén prevenx trat""".split()
_IA_IRREG = 'habr podr tendr har dir sabr querr saldr pondr vendr valdr cabr'.split()
for _s in _IA_STEMS + _IA_IRREG:
    for _suf in ('ía', 'ían', 'ías', 'íamos', 'íais'):
        if _s in ('sab', 'hac', 'ser'):
            continue
        ACCENT.setdefault(_strip_acc(_s + _suf), _s + _suf)
for _x in ('sabían', 'sabíamos', 'hacían', 'hacías', 'hacíamos', 'serían', 'seríamos'):
    ACCENT[_strip_acc(_x)] = _x
for _s in _IA_IRREG:
    pass
# Plurals of nouns in -ía
for _k, _v in list(ACCENT.items()):
    if _v.endswith('ía') and not _k.endswith(('ia',)) is False and _k not in ('maria', 'lucia'):
        ACCENT.setdefault(_k + 's', _v + 's')

CAP_ACCENT = {'tomas': 'tomás', 'paris': 'parís', 'angel': 'ángel', 'cesar': 'césar',
              'felix': 'félix', 'hector': 'héctor', 'victor': 'víctor', 'agueda': 'águeda',
              'jose': 'josé', 'leon': 'león', 'simon': 'simón', 'ruben': 'rubén'}
INTERROG = {'que': 'qué', 'quien': 'quién', 'quienes': 'quiénes', 'cual': 'cuál',
            'cuales': 'cuáles', 'como': 'cómo', 'donde': 'dónde', 'adonde': 'adónde',
            'cuando': 'cuándo', 'cuanto': 'cuánto', 'cuanta': 'cuánta',
            'cuantos': 'cuántos', 'cuantas': 'cuántas', 'cuan': 'cuán'}
DIACR_MONO = {'si', 'mi', 'tu', 'el', 'se', 'de', 'te', 'mas', 'que', 'quien', 'cual', 'cuan'}

PATTERNS = [
    (r'isim(o|a|os|as)$', r'ísim\1'), (r'esim(o|a|os|as)$', r'ésim\1'),
    (r'olog(o|a|os|as)$', r'ólog\1'), (r'olic(o|a|os|as)$', r'ólic\1'),
    (r'elic(o|a|os|as)$', r'élic\1'), (r'astic(o|a|os|as)$', r'ástic\1'),
    (r'etic(o|a|os|as)$', r'étic\1'), (r'atic(o|a|os|as)$', r'átic\1'),
    (r'itic(o|a|os|as)$', r'ític\1'), (r'onic(o|a|os|as)$', r'ónic\1'),
    (r'istic(o|a|os|as)$', r'ístic\1'), (r'oric(o|a|os|as)$', r'óric\1'),
    (r'ifer(o|a|os|as)$', r'ífer\1'),
    (r'(log|sof|graf|nom|rqu|pat|fon|latr)ia(s)?$', r'\1ía\2'),
    (r'([aeo])id(o|a|os|as)$', r'\1íd\2'),
    (r'([aeo])ir$', r'\1ír'),
    (r'a(ndo(?:le|la|lo|les|las|los|me|te|se|nos|os)(?:le|la|lo|les|las|los|me|te|se)?)$', r'á\1'),
    (r'e(ndo(?:le|la|lo|les|las|los|me|te|se|nos|os)(?:le|la|lo|les|las|los|me|te|se)?)$', r'é\1'),
]
VERB_IO = [r'[^p]recio$', r'(?<=..)necio$', r'[dt]ecio$', r'quecio$', r'nocio$',
           r'ndio$', r'ibio$', r'rtio$', r'ntio$', r'olvio$', r'cedio$', r'pidio$',
           r'rdio$', r'guio$', r'rrio$', r'etio$', r'itio$', r'rvio$', r'trevio$']
VERB_IO_EXC = {'indio', 'incendio', 'compendio', 'dispendio', 'estipendio', 'barrio',
               'sitio', 'necio', 'precio', 'desprecio', 'aprecio', 'socio', 'negocio',
               'sacerdocio', 'ocio', 'decio', 'arrio', 'patio', 'lucrecio', 'previo'}
VERB_IO_EXACT = {'murio', 'salio', 'valio', 'cumplio', 'subio', 'vivio', 'movio',
                 'conmovio', 'removio', 'promovio', 'temio', 'gimio', 'comio', 'bebio',
                 'nacio', 'renacio', 'yacio', 'complacio', 'sobresalio', 'sufrio',
                 'abrio', 'cubrio', 'descubrio', 'unio', 'reunio', 'rompio', 'dirigio',
                 'eligio', 'fingio', 'afligio', 'ardio', 'cupo', 'huyo', 'oyo', 'creyo',
                 'leyo', 'cayo', 'decidio', 'dividio', 'persuadio', 'resplandecio',
                 'acudio', 'asistio', 'consistio', 'existio', 'insistio', 'resistio',
                 'escogio', 'cogio', 'recogio', 'acogio', 'exigio', 'corrigio',
                 'convirtio', 'mintio', 'sintio', 'pidio', 'midio'}


def _accent_unmarked(w, cap):
    if any(c in w for c in 'áéíóú'):
        return w
    if cap and w in CAP_ACCENT:
        return CAP_ACCENT[w]
    if w in ACCENT:
        return ACCENT[w]
    if w.endswith('mente') and len(w) >= 9:
        base = _accent_unmarked(w[:-5], cap)
        return base + 'mente'
    for pat, rep in PATTERNS:
        if re.search(pat, w):
            nw = re.sub(pat, rep, w)
            if _syll(w) >= 2:
                return nw
    n = _syll(w)
    # Past tenses in -ió
    if n >= 2 and w.endswith('io') and w not in VERB_IO_EXC:
        if w in VERB_IO_EXACT or any(re.search(p, w) for p in VERB_IO):
            return w[:-1] + 'ó'
    if w in VERB_IO_EXACT and w.endswith(('yo',)):
        return w[:-1] + 'ó'
    # Words stressed on the last syllable in -on (not -ron), -in, -un
    if n >= 2 and w not in ('canon',):
        if w.endswith('on') and not w.endswith('ron'):
            return w[:-2] + 'ón'
        if w.endswith('in') and w[-3] not in 'aeou':
            return w[:-2] + 'ín'
        if w.endswith('un') and w[-3] not in 'aeio':
            return w[:-2] + 'ún'
    # -ais/-eis of the second person plural (amáis, tenéis)
    if n >= 2 and re.search(r'[aeo]?[^aeiou](ais|eis)$', w) and \
            not re.search(r'(bais|rais|reis|seis|iais|ieis|steis)$', w):
        p = len(w) - 3
        return _put(w, p)
    # Surnames in -ez, stressed on the second-to-last syllable
    if cap and n >= 2 and w.endswith('ez') and w not in ('jerez', 'xerez', 'ajedrez'):
        g = _nuclei(w)
        pen = g[-2]
        p = next((q for q in pen if w[q] in 'aeo'), pen[-1])
        return _put(w, p)
    return w


# ---------------------------------------------------------------------------
# Whole word
# ---------------------------------------------------------------------------
ROMAN = re.compile(r'^[IVXLCDM]+$')
ROMAN_LOW_J = re.compile(r'^[ivxlcdm]+j$')


def _decompose(w):
    """-> (plain lowercase text, {position: 'acute'|'grave'|'circ'})"""
    nfd = unicodedata.normalize('NFD', w.lower())
    out, marks = [], {}
    for ch in nfd:
        o = ord(ch)
        if o in (0x300, 0x301):
            if out:
                marks[len(out) - 1] = 'stress'
        elif o == 0x302:
            if out:
                marks[len(out) - 1] = 'circ'
        elif o == 0x308:
            if out and out[-1] == 'u':
                out[-1] = 'ü'
        elif o == 0x303 and out and out[-1] == 'n':
            out[-1] = 'ñ'
        elif o == 0x327 and out and out[-1] == 'c':
            out[-1] = 'ç'
        elif unicodedata.combining(ch):
            continue
        else:
            out.append(ch)
    # "gúe", "gúi": many 19th-century prints (and the OCR) put an acute accent where "ü" goes ("ungúento", "vergúenza");
    # without this the accent was dropped ("unguento").
    for p, t in list(marks.items()):
        if t == 'stress' and out[p] == 'u' and 0 < p < len(out) - 1 and out[p - 1] == 'g' and out[p + 1] in 'ei':
            out[p] = 'ü'
            del marks[p]
    return ''.join(out), marks


def _recase(orig, new):
    if len(orig) > 1 and orig.isupper():
        return new.upper()
    if orig[:1].isupper():
        return new[:1].upper() + new[1:]
    return new


def _modernize_word(word):
    if ROMAN.match(word) or ROMAN_LOW_J.match(word):
        return word
    cap = word[:1].isupper()
    plain, marks = _decompose(word)
    if cap and re.search(r'tl|tz', plain):
        return word
    if plain.endswith('mente') and len(plain) >= 9 and not marks:
        base = _modernize_word(word[:-5])
        return base + _recase(word[-5:], 'mente') if not word[-5:].isupper() else base + 'MENTE'
    w = _uv_ij(plain, cap)
    keepx = any(t == 'circ' and p > 0 and w[p - 1] == 'x' for p, t in marks.items())
    stress = [p for p, t in marks.items() if t == 'stress' and p < len(w) and w[p] in 'aeiou']
    vp_before = _vowel_pos(w)
    idx = None
    if stress:
        p = max(stress)
        if p in vp_before:
            idx = len(vp_before) - 1 - vp_before.index(p)
    base_w = w
    w = _graphic(w, cap, keepx)
    if idx is not None:
        vp = _vowel_pos(w)
        if len(vp) == len(vp_before):
            p = vp[len(vp) - 1 - idx]
            if _syll(w) == 1 and not (w[p] in 'iu' and _needs_tilde(w, p)):
                if w in DIACR_MONO:
                    w = _put(w, p)
            elif w in INTERROG:
                w = INTERROG[w]
            elif _needs_tilde(w, p):
                w = _put(w, p)
        else:
            w = _accent_unmarked(w, cap)
    else:
        w = _accent_unmarked(w, cap)
    return _recase(word, w)


# ---------------------------------------------------------------------------
# Contexto
# ---------------------------------------------------------------------------
PREPS = {'a', 'de', 'para', 'por', 'en', 'sin', 'contra', 'sobre', 'entre', 'hacia',
         'desde', 'hasta', 'con', 'ante', 'tras'}
PRON_NEXT = {'y', 'e', 'ni', 'o', 'u', 'mismo', 'misma', 'mismos', 'mismas', 'mesmo',
             'mesma', 'solo', 'sola', 'propio', 'propia', 'proprio', 'propria'}
PARTIC = {'sido', 'dado', 'ido', 'oído', 'visto', 'dicho', 'hecho', 'puesto', 'escrito',
          'muerto', 'abierto', 'vuelto', 'cubierto', 'roto', 'satisfecho', 'traído',
          'caído', 'leído', 'creído'}
PARTIC_EXC = {'lado', 'grado', 'prado', 'nado', 'vado', 'cuidado', 'modo', 'menudo',
              'grito', 'vestido', 'sentido', 'partido', 'olvido', 'nido', 'ruido',
              'marido', 'pecado', 'estado', 'cargo', 'mandado', 'recado', 'bocado'}
INTERR_KEYS = set(INTERROG)
LEAD_CONJ = {'y', 'e', 'o', 'pues', 'pero', 'mas', 'ni'}


def _is_partic(t):
    t = t.lower()
    if t in PARTIC:
        return True
    if t in PARTIC_EXC:
        return False
    return bool(re.match(r'^[a-zñ]{2,}[ai]do$', t))


def _context(words, seps, latin):
    n = len(words)
    low = [w.lower() for w in words]

    def only_space(s):
        return s.strip() == ''
    for i in range(n):
        if latin[i]:
            continue
        w = low[i]
        nxt = low[i + 1] if i + 1 < n else None
        sep_after = seps[i + 1]
        sep_before = seps[i]
        # a / e / an / as / emos + participio -> ha / he / han / has / hemos
        if w in ('a', 'e', 'an', 'as', 'emos') and nxt and only_space(sep_after) \
                and not latin[i + 1] and _is_partic(nxt):
            words[i] = _recase(words[i], 'h' + w)
            continue
        # i conjunción
        if words[i] == 'i':
            words[i] = 'y'
            continue
        # Stressed pronouns after a preposition
        if w in ('mi', 'el', 'si', 'tu') and i > 0 and low[i - 1] in PREPS and only_space(sep_before) \
                and not (w == 'el' and nxt in ('mismo', 'misma', 'mismos', 'mismas', 'mesmo', 'mesma')):
            punct_after = bool(re.match(r'\s*[,.;:?!)\]]', sep_after)) or (nxt is None and sep_after.strip() != '')
            if punct_after or (nxt in PRON_NEXT and only_space(sep_after)):
                words[i] = _recase(words[i], {'mi': 'mí', 'el': 'él', 'si': 'sí', 'tu': 'tú'}[w])
                continue
        if w == 'si' and nxt in ('mismo', 'misma', 'mismos', 'mismas', 'mesmo', 'mesma') \
                and only_space(sep_after):
            words[i] = _recase(words[i], 'sí')
            continue
        if w == 'tu' and re.match(r'\s*[,.;:?!]', sep_after):
            words[i] = _recase(words[i], 'tú')
    # interrogativos / exclamativos
    for i in range(n):
        if latin[i]:
            continue
        # Look for the end of the segment
        j = i
        end = None
        while j < n:
            m = re.search(r'[.;:?!]', seps[j + 1])
            if m:
                end = m.group(0)
                break
            j += 1
        if end not in ('?', '!'):
            continue
        # Start of a segment?
        before = seps[i]
        starts = bool(re.search(r'[¿¡]\s*$', before)) or bool(re.search(r'[.;:?!]\s*$', before)) \
            or (i == 0 and words[i][:1].isupper())
        if not starts:
            continue
        k = i
        if low[k] in LEAD_CONJ and k + 1 < n and only_space(seps[k + 1]):
            k += 1
        if low[k] == 'por' and k + 1 < n and low[k + 1] == 'que':
            k += 1
        if low[k] in INTERR_KEYS and not latin[k]:
            words[k] = _recase(words[k], INTERROG[low[k]])
    return words


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
def _prenorm(s):
    s = unicodedata.normalize('NFD', s)
    s = re.sub(r'([qQ])̃', lambda m: m.group(1) + ('UE' if m.group(1) == 'Q' and False else 'ue'), s)

    def _nasal(m):
        v, nxt = m.group(1), m.group(2)
        cons = 'm' if nxt and nxt.lower() in 'pb' else 'n'
        if v.isupper():
            cons = cons.upper()
        return v + cons + (nxt or '')
    s = re.sub(r'([aeiouAEIOU])̃(.?)', _nasal, s)
    return unicodedata.normalize('NFC', s)


def modernizar(linea: str) -> str:
    s = _prenorm(linea)
    s = re.sub(r'\b([Dd])él\b', r'\1e él', s)  # "dél" -> "de él"
    parts = re.split(r'([^\W\d_]+)', s)
    words = parts[1::2]
    seps = parts[0::2]          # seps[i] precede a words[i]; seps[-1] final
    if not words:
        return s
    latin = _latin_mask(words)
    out = []
    for w, lat in zip(words, latin):
        if lat:
            out.append(w)
        else:
            try:
                out.append(_modernize_word(w))
            except Exception:
                out.append(w)
    out = _context(out, seps, latin)
    res = []
    for i, w in enumerate(out):
        res.append(seps[i])
        res.append(w)
    res.append(seps[-1])
    return ''.join(res)


# ---------------------------------------------------------------------------
# Post-correction with the vocabulary of the corpus
# ---------------------------------------------------------------------------
# After modernizar(), each line goes through postcorregir(), which uses the vocabulary of the whole corpus:
# a word "exists" if it appears in KNOWN_BOOKS books or more. Steps, in this order:
# 1. Old contractions, from a fixed table: "dello" -> "de ello", "deste" -> "de este".
# 2. Old "sc" before e/i: "obedescer" -> "obedecer", only if the new form is much more frequent in the corpus.
# 3. Missing accents: "temerian" -> "temerían", only if the accented form is more frequent in the corpus.
#    Words whose meaning changes with the accent (mas/más, sabia/sabía) are never touched; only accents current
#    spelling requires are added, and none on a last syllable that would turn one verb form into another.
# 4. Words the OCR glued together, split in step 5: an unknown word (in fewer than DROP_BOOKS books) that splits into
#    two common words ("madresque" -> "madres que"), only if the two words appear together in the corpus at least 3
#    times and 20 times more often than the glued form. Each half has 4 letters or more or is a short Spanish word
#    ("de", "que"), so that OCR junk ("as", "re") does not count; and a verb keeps its pronoun ("débenlo",
#    "componernos", "olvidósele") and its ending ("compraren").
#    A short function word glued to the next one ("enesto" -> "en esto", "porla" -> "por la") is split in step 5,
#    because it needs the pairs of words of the corpus: only if "en esto" is 20 times more frequent than "enesto"
#    (which repeats in 13 books). "a" is left out: too many real words start with it ("adeuda", "ajuntando").
# 4b. Conditional verbs in "-rian" without accent: "temerian" -> "temerían" (lowercase only, so that names stay).
#    Not every "-ian": "estudian", "precian" have no accent.
# 5. OCR errors, with corregir_ocr(), a separate pass: a word still unknown (in fewer than DROP_BOOKS books) is
#    replaced by a common word one typical OCR confusion away ("liermosas" -> "hermosas", "homnbres" -> "hombres"),
#    if that word appears in the corpus next to the same neighbor, before or after, at least twice. Nothing is removed.
# 6. No space before punctuation: "de todos ," -> "de todos,".
import os
from collections import Counter

KNOWN_BOOKS = 10   # A word in 10 books or more exists
DROP_BOOKS = 3     # A word in fewer than 3 books is unknown: steps 4 and 5 try to fix it
RATIO = 5          # A replacement for a known word must be 5 times more frequent than it
COMMON_BOOKS = 100 # Each half of a glued word must be a common word, in 100 books or more
# Short words the OCR often glues to the next one, longest first so that "por" is tried before "po":
FUNCTION_WORDS = ['por', 'con', 'que', 'del', 'los', 'las', 'sin', 'en', 'de', 'la', 'el', 'lo', 'se', 'no', 'y']
# Short Spanish words that may be half of a glued pair; any other half needs 4 letters or more:
SHORT_WORDS = set('''a y e o u de en el la lo le se no su tu mi si ya es al un ha he me te os va da ve fe ni por con
que del los las sin sus mas una uno muy hoy fue era son dos ser ver dar ir hay han has mis tus nos les sea él sí'''.split())
# Pronouns attached to a verb ("débenlo", "dejarle"): never split off.
CLITICS = {'lo', 'la', 'le', 'los', 'las', 'les', 'nos', 'se', 'me', 'te', 'os',
           'sele', 'selo', 'sela', 'seles', 'selos', 'selas', 'melo', 'mela', 'telo', 'tela', 'nosla', 'noslo'}
# After a piece ending in -r these are verb endings, not words: "compraren", "hallare", "dieres".
VERB_ENDINGS = {'a', 'as', 'an', 'e', 'es', 'en'}
# Accents on the last syllable of words with these endings are not added: both forms are usually verbs.
VERB_FINAL = ('a', 'e', 'o', 'an', 'en', 'as', 'es')


def _whole(piece):
    return len(piece) >= 4 or piece in SHORT_WORDS


# Register of changes: while a book is processed, every changed word is noted as (line, before, after, rule), so that
# false corrections can be found by rule. _CAMBIOS is None outside modernizar_libro() and corregir_libro().
# Step 6 (space before punctuation) is not noted.
_CAMBIOS = None
_LINEA = 0
FIX_RULES = ('contracción', 'sc', 'tilde')


def _anotar(antes, despues, regla):
    if _CAMBIOS is not None and antes != despues:
        _CAMBIOS.append((_LINEA, antes, despues, regla))


def _anotar_tramos(antes, despues, regla):
    """Notes the differing stretches of two word lists ("dél" -> "de él")."""
    import difflib
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=antes, b=despues, autojunk=False).get_opcodes():
        if op != 'equal':
            _anotar(' '.join(antes[i1:i2]), ' '.join(despues[j1:j2]), regla)

CONTRACTIONS = {
    'dello': 'de ello', 'dellos': 'de ellos', 'della': 'de ella', 'dellas': 'de ellas',
    'deste': 'de este', 'desta': 'de esta', 'destos': 'de estos', 'destas': 'de estas', 'desto': 'de esto',
    'dese': 'de ese', 'desos': 'de esos', 'desas': 'de esas', 'deso': 'de eso',
    'daquel': 'de aquel', 'daquella': 'de aquella', 'daquellos': 'de aquellos', 'daquellas': 'de aquellas',
    'estotro': 'este otro', 'estotra': 'esta otra', 'estotros': 'estos otros', 'estotras': 'estas otras',
    'esotro': 'ese otro', 'esotra': 'esa otra',
}
# Words whose meaning changes with the accent: left as printed.
AMBIGUOUS = set('''mas mas esta este estas estos ese esa esos esas aquel aquella aquellos aquellas solo aun
el tu mi si se te de que quien quienes cual cuales como cuando donde adonde cuanto cuanta cuantos cuantas porque
sabia hacia hacian continuo publico practica practico ultimo termino animo habito limite deposito transito
titulo numero genero valido perdida ejercito estan esten seria serian sera seras era eras amo ame ames
hable hablo canto llamo tomo paso pase pasa lloro entro gusto cambio anuncio estimulo vinculo circulo
deposito liquido rapido solido intimo legitimo ultima ultimas publica publicas cantara cantaras fuera
fueras diera dieras tenia tenias venia venias decia decias hacia sabia sabias vivia continua continuas'''.split())

_WORD = re.compile(r'[^\W\d_]+')
_ACUTE = {'a': 'á', 'e': 'é', 'i': 'í', 'o': 'ó', 'u': 'ú'}


def plain(word):
    return _strip_acc(word.lower())


def contar_vocabulario(carpeta, excluir=()):
    """Counts every word of the corpus: occurrences and books, as printed (lowercase) and without accents; and the
    abbreviations (see _abreviaturas())."""
    freq, books, plain_books = Counter(), Counter(), Counter()
    total, dotted, dotted_books = Counter(), Counter(), Counter()
    for nombre in sorted(os.listdir(carpeta)):
        if not nombre.endswith('.txt') or any(x in nombre for x in excluir):
            continue
        with open(os.path.join(carpeta, nombre), encoding='utf-8') as f:
            texto = re.sub(r'<[^>]+>', ' ', f.read())
        palabras = [w.lower() for w in _WORD.findall(texto)]
        freq.update(palabras)
        unicas = set(palabras)
        books.update(unicas)
        plain_books.update(set(_strip_acc(w) for w in unicas))
        con_punto = set()
        for m in _TOKEN_DOT.finditer(texto):
            total[m.group(1)] += 1
            if m.group(2):
                dotted[m.group(1)] += 1
                con_punto.add(m.group(1))
        dotted_books.update(con_punto)
    return {'freq': freq, 'books': books, 'plain': plain_books,
            'abrev': _abreviaturas(total, dotted, dotted_books)}


# Abbreviations: a form of 2 letters or more that carries a period in at least 80% of its 5 or more appearances, in
# 3 books or more ("cap.", "Psalm.", "Génes.", "pág."). About 490 forms. Words of titles in capitals that end a
# heading ("PRIMERO.") and "Amen." are not abbreviations. One letter and a period ("V.", "S.") always counts.
_TOKEN_DOT = re.compile(r'(?<![\w.])([^\W\d_]{1,8})(\.?)')
NOT_ABBREVIATIONS = {'amen', 'amén'}


def _abreviaturas(total, dotted, dotted_books):
    return {w for w in dotted if len(w) > 1 and total[w] >= 5 and dotted[w] >= 0.8 * total[w]
            and dotted_books[w] >= 3 and w.lower() not in NOT_ABBREVIATIONS and not (w.isupper() and len(w) > 4)}


# Latin words outside the marked passages (short quotes, passages lingua did not mark): words found at least
# LATIN_MIN times inside <foreign xml:lang="la"> and at least as often there as outside, with 3 letters or more, not in
# the Spanish dictionary and not a frequent OCR error of a Spanish word ("dei" is mostly "del"). They are left as
# printed wherever they appear (patron_protegido()).
LATIN_MIN = 5


def lexico_latino(carpeta, voc, ruta_diccionario):
    """Latin words of the corpus, by where they appear; see LATIN_MIN."""
    from spylls.hunspell import Dictionary
    dentro, fuera = Counter(), Counter()
    marcado = re.compile(r'<foreign xml:lang="la">(.*?)</foreign>')
    for nombre in os.listdir(carpeta):
        with open(os.path.join(carpeta, nombre), encoding='utf-8') as f:
            for linea in f:
                for m in marcado.finditer(linea):
                    dentro.update(w.lower() for w in _WORD.findall(m.group(1)))
                resto = re.sub(r'<[^>]+>', ' ', re.sub(r'<foreign[^>]*>.*?</foreign>', ' ', linea))
                fuera.update(w.lower() for w in _WORD.findall(resto))
    diccionario = Dictionary.from_files(ruta_diccionario)
    return {w for w, n in dentro.items() if n >= LATIN_MIN and n >= fuera[w] and len(w) >= 3
            and w not in voc.get('frecuentes', {}) and not diccionario.lookup(w)}


def patron_protegido(voc):
    """What is left as printed: Latin words of lexico_latino(), passages in Latin or Italian marked by 5-limpieza (<foreign xml:lang="la">...
    </foreign>, with their content), tags (<pb n="N"/>, <head>), abbreviations with their period, one letter and a
    period, and tokens with digits ("x1v", "32")."""
    abrevs = '|'.join(re.escape(w) for w in sorted(voc['abrev'], key=len, reverse=True))
    latinas = '|'.join(re.escape(w) for w in sorted(voc.get('latin', ()), key=len, reverse=True)) or '(?!)'
    return re.compile(r'(<foreign[^>]*>.*?</foreign>|<[^>]+>|(?<![\w.])(?:' + abrevs + r'|[^\W\d_])\.|\w*\d\w*'
                      r'|(?<!\w)(?i:' + latinas + r')(?!\w))')


def procesar_linea(linea, patron, funcion):
    """Applies funcion() to the pieces of the line between protected tokens."""
    partes = patron.split(linea)
    for i in range(0, len(partes), 2):
        partes[i] = funcion(partes[i])
    return ''.join(partes)


def _case_like(orig, new):
    if orig.isupper() and len(orig) > 1:
        return new.upper()
    if orig[:1].isupper():
        return new[:1].upper() + new[1:]
    return new


def _better(w, cand, voc):
    """cand replaces w if it is much more frequent (w known) or simply more frequent (w rare, cand in 3+ books)."""
    if voc['books'][w] >= KNOWN_BOOKS:
        return voc['books'][cand] >= KNOWN_BOOKS and voc['freq'][cand] >= RATIO * voc['freq'][w]
    return voc['books'][cand] >= DROP_BOOKS and voc['freq'][cand] > voc['freq'][w]


def _fix_word(word, voc, stats):
    low = word.lower()
    if low in CONTRACTIONS:
        stats['contracción'] += 1
        return _case_like(word, CONTRACTIONS[low])
    if 'sc' in low and not word[:1].isupper():
        cand = re.sub(r'sc(?=[eiéí])', 'c', low)
        if cand != low and _better(low, cand, voc):
            stats['sc'] += 1
            low, word = cand, _case_like(word, cand)
    if low == _strip_acc(low) and low not in AMBIGUOUS and len(low) > 2:
        best = None
        for i, c in enumerate(low):
            if c in _ACUTE:
                if c == 'u' and 0 < i < len(low) - 1 and low[i - 1] == 'g' and low[i + 1] in 'ei':
                    cand = low[:i] + 'ü' + low[i + 1:]
                elif not _needs_tilde(low, i):
                    continue  # An accent current spelling does not write
                elif len(_nuclei(low, i)) - 1 == next(k for k, g in enumerate(_nuclei(low, i)) if i in g)                         and low.endswith(VERB_FINAL):
                    continue  # Last syllable: "sacara" / "sacará"
                else:
                    cand = low[:i] + _ACUTE[c] + low[i + 1:]
                if _better(low, cand, voc) and (best is None or voc['freq'][cand] > voc['freq'][best]):
                    best = cand
        if best:
            stats['tilde'] += 1
            low, word = best, _case_like(word, best)
    if low.endswith('rian') and len(low) >= 6 and word.islower():
        stats['tilde'] += 1
        return word[:-3] + 'ían'
    return word


def _glued_split(w, voc):
    """Glued words: two common words ("madres" + "que"); the split whose rarer half is most frequent. Checked in step 5
    against the corpus."""
    low = w.lower()
    if voc['plain'][plain(low)] >= DROP_BOOKS:
        return None
    best = None
    for i in range(1, len(low)):
        left, right = low[:i], low[i:]
        if not (_whole(left) and _whole(right)) or right in CLITICS:
            continue
        if left.endswith('r') and right in VERB_ENDINGS:
            continue
        if voc['plain'][plain(left)] >= COMMON_BOOKS and voc['plain'][plain(right)] >= COMMON_BOOKS:
            score = min(voc['freq'][left], voc['freq'][right])
            if best is None or score > best[0]:
                best = (score, i)
    return best[1] if best else None


# Typical OCR confusions of letters that look alike: "rn" read for "m", "li" for "h", "c" for "e", and so on,
# plus a letter read twice ("acrecentamiiento"). Only these: a free change of any letter turned rare real words
# into common ones ("tinturas" -> "pinturas", "comedoras" -> "comedores").
OCR_CONFUSIONS = [('rn', 'm'), ('m', 'rn'), ('ni', 'm'), ('in', 'm'), ('li', 'h'), ('cl', 'd'), ('ii', 'u'),
                  ('c', 'e'), ('e', 'c'), ('l', 't'), ('t', 'l'), ('h', 'b'), ('b', 'h'), ('n', 'u'), ('u', 'n'),
                  ('f', 's'), ('s', 'f'), ('l', 'i'), ('i', 'l'), ('J', 'I'), ('I', 'l'), ('ñ', 'n')]


def _edits(w):
    out = set()
    for a, b in OCR_CONFUSIONS:
        start = w.find(a)
        while start != -1:
            out.add(w[:start] + b + w[start + len(a):])
            start = w.find(a, start + 1)
    for i in range(len(w) - 1):
        if w[i] == w[i + 1] and w[i] not in 'lrc':  # a letter read twice; "ll", "rr", "cc" are Spanish
            out.add(w[:i] + w[i + 1:])
    out.discard(w)
    return out


# Step 5 without a neighbor: an unknown word with a single clear candidate is corrected even if the candidate never
# appears next to the same neighbor ("conclnye" -> "concluye", "dificaltosa" -> "dificultosa"). The candidate may also
# be one of these confusions, seen in the low-quality pages and used only here:
EXTRA_CONFUSIONS = [('a', 'u'), ('u', 'a'), ('o', 'e'), ('e', 'o'), ('n', 'a'), ('J', 'l')]
CLEAR_MIN_LENGTH = 5    # "Tita" (for "Titu") would become "tila"
CLEAR_MIN_FREQ = 30     # "hnego" (for "luego") would become "huego", which appears 10 times
CLEAR_RATIO = 10        # The candidate must be 10 times more frequent than the second best


def _clear_candidate(w, voc):
    """The only common word one OCR confusion away from an unknown word, if there is a clear one; else None."""
    low = w.lower()
    if len(low) < CLEAR_MIN_LENGTH or voc['plain'][plain(low)] >= DROP_BOOKS or low in voc.get('frecuentes', {}):
        return None
    cands = set(_edits(low))
    for a, b in EXTRA_CONFUSIONS:
        start = low.find(a)
        while start != -1:
            cands.add(low[:start] + b + low[start + len(a):])
            start = low.find(a, start + 1)
    cands = sorted([c for c in cands if c != low and voc['books'][c] >= KNOWN_BOOKS], key=lambda c: -voc['freq'][c])
    if not cands or voc['freq'][cands[0]] < CLEAR_MIN_FREQ:
        return None
    if len(cands) > 1 and voc['freq'][cands[0]] < CLEAR_RATIO * voc['freq'][cands[1]]:
        return None
    return cands[0]


FREQUENT_RATIO = 20  # A frequent OCR error: its correction is at least 20 times more frequent
# ("eruz" is 48 times rarer than "cruz")
FREQUENT_MIN_LENGTH = 4  # A frequent error with a single correction is corrected even without neighbors ("mueho")


def errores_frecuentes(voc, ruta_diccionario):
    """Frequent OCR errors: words in DROP_BOOKS books or more, not in the Hunspell dictionary, one OCR confusion away
    from a word FREQUENT_RATIO times more frequent. {word: [corrections]}"""
    from spylls.hunspell import Dictionary
    diccionario = Dictionary.from_files(ruta_diccionario)
    out = {}
    for w, n in voc['freq'].items():
        if voc['books'][w] < DROP_BOOKS or len(w) < 2:
            continue
        cands = [c for c in _edits(w) if voc['freq'][c] >= FREQUENT_RATIO * n and voc['books'][c] >= KNOWN_BOOKS]
        if cands and not diccionario.lookup(w):
            out[w] = cands
    return out


def _candidates(w, voc):
    """Common words (in KNOWN_BOOKS books or more) one OCR confusion away from an unknown word, lowercase."""
    low = w.lower()
    if low in voc.get('frecuentes', {}):
        return voc['frecuentes'][low]
    if len(low) < 4 or voc['plain'][plain(low)] >= DROP_BOOKS:
        return []
    return [c for c in _edits(low) if voc['books'][c] >= KNOWN_BOOKS]


def _neighbors(parts, i):
    """The words before and after parts[i] in the line, lowercase without accents ('' at the edges)."""
    before = plain(parts[i - 2]) if i >= 2 else ''
    after = plain(parts[i + 2]) if i + 2 < len(parts) else ''
    return before, after


def pares_necesarios(linea, voc, necesarios):
    """Adds to `necesarios` the word pairs that corregir_ocr() will need for this line."""
    parts = re.split(r'([^\W\d_]+)', linea)
    for i in range(1, len(parts), 2):
        for short, rest in _function_splits(parts[i], voc):
            necesarios.add((short, plain(rest)))
        k = _glued_split(parts[i], voc)
        if k:
            necesarios.add((plain(parts[i][:k]), plain(parts[i][k:])))
        for c in _candidates(parts[i], voc):
            before, after = _neighbors(parts, i)
            necesarios.add((before, plain(c)))
            necesarios.add((plain(c), after))
            necesarios.add((before, plain(parts[i])))
            necesarios.add((plain(parts[i]), after))


def _function_splits(w, voc):
    """("en", "esto") for "enesto": a function word glued to a common word, if the glued form is not common."""
    low = w.lower()
    if voc['plain'][plain(low)] >= COMMON_BOOKS:
        return []
    return [(short, low[len(short):]) for short in FUNCTION_WORDS
            if low.startswith(short) and _whole(low[len(short):]) and low[len(short):] not in CLITICS
            and voc['plain'][plain(low[len(short):])] >= COMMON_BOOKS]


def contar_pares(carpeta, necesarios, excluir=()):
    """Counts how often each needed pair of neighboring words appears in the corpus."""
    cuenta = Counter()
    for nombre in sorted(os.listdir(carpeta)):
        if not nombre.endswith('.txt') or any(x in nombre for x in excluir):
            continue
        with open(os.path.join(carpeta, nombre), encoding='utf-8') as f:
            for linea in f:
                palabras = [plain(w) for w in _WORD.findall(re.sub(r'<[^>]+>', ' ', linea))]
                for par in zip(palabras, palabras[1:]):
                    if par in necesarios:
                        cuenta[par] += 1
    return cuenta


def _latin_tramos(words):
    """_latin_mask(), without single words: a lone "dei" between Spanish words is "del" misread."""
    mask = _latin_mask(words)
    return [m and ((k > 0 and mask[k - 1]) or (k + 1 < len(mask) and mask[k + 1])) for k, m in enumerate(mask)]


_DICCIONARIO = None
RUTA_DICCIONARIO = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diccionario-es', 'es_ES')


def _en_diccionario(w):
    """True if the word is in the Spanish dictionary (Hunspell es_ES), loaded on first use."""
    global _DICCIONARIO
    if _DICCIONARIO is None:
        from spylls.hunspell import Dictionary
        _DICCIONARIO = Dictionary.from_files(RUTA_DICCIONARIO)
    return _DICCIONARIO.lookup(w) or _DICCIONARIO.lookup(w.lower())


def corregir_ocr(linea, voc, pares, stats=None):
    """Step 5: an unknown word becomes the nearby common word best supported by its neighbors, if any is."""
    if stats is None:
        stats = Counter()
    stats.setdefault('corregidas', [])
    parts = re.split(r'([^\W\d_]+)', linea)
    latin = _latin_tramos(parts[1::2])
    for i in range(1, len(parts), 2):
        if latin[i // 2]:
            continue
        split = None
        for short, rest in _function_splits(parts[i], voc):
            together = pares[(short, plain(rest))]
            if together >= 3 and together >= 20 * voc['freq'][parts[i].lower()]:
                split = len(short)
                break
        k = None if split else _glued_split(parts[i], voc)
        if k:
            together = pares[(plain(parts[i][:k]), plain(parts[i][k:]))]
            if together >= 3 and together >= 20 * voc['freq'][parts[i].lower()]:
                split = k
        if split and _en_diccionario(parts[i]):
            split = None  # "decrecer", "decaer" are words, not "de crecer", "de caer"
        if split:
            stats['pegada'] += 1
            _anotar(parts[i], parts[i][:split] + ' ' + parts[i][split:], 'palabras pegadas')
            parts[i] = parts[i][:split] + ' ' + parts[i][split:]
            continue
        best, best_score = None, 0
        before, after = _neighbors(parts, i)
        for c in _candidates(parts[i], voc):
            score = pares[(before, plain(c))] + pares[(plain(c), after)]
            if score > best_score or (score == best_score and best and voc['freq'][c] > voc['freq'][best]):
                best, best_score = c, score
        frecuente = parts[i].lower() in voc.get('frecuentes', {})
        if frecuente:  # A frequent form: the correction needs much stronger support than the printed word has
            printed = pares[(before, plain(parts[i]))] + pares[(plain(parts[i]), after)]
            if best_score < 3 or best_score < 20 * max(printed, 1):
                best = None
        if best is None and frecuente and len(parts[i]) >= FREQUENT_MIN_LENGTH                 and len(voc['frecuentes'][parts[i].lower()]) == 1:
            stats['corregida'] += 1
            stats['frecuente'] += 1
            nueva = _case_like(parts[i], voc['frecuentes'][parts[i].lower()][0])
            stats['corregidas'].append(parts[i] + ' -> ' + nueva + ' (frecuente)')
            _anotar(parts[i], nueva, 'OCR (frecuente)')
            parts[i] = nueva
            continue
        if best and best_score >= 2:
            stats['corregida'] += 1
            stats['corregidas'].append(parts[i] + ' -> ' + best)
            _anotar(parts[i], _case_like(parts[i], best), 'OCR (vecino)')
            parts[i] = _case_like(parts[i], best)
            continue
        clear = None
        if parts[i][:1].islower():  # Names are left alone: "Tamba", "Fingo" (provinces of Japan)
            clear = _clear_candidate(parts[i], voc)
        if clear and _en_diccionario(parts[i]):
            clear = None  # "alojan", "huchas" are words
        if clear:
            stats['corregida'] += 1
            stats['sin_vecino'] += 1
            stats['corregidas'].append(parts[i] + ' -> ' + clear + ' (sin vecino)')
            _anotar(parts[i], _case_like(parts[i], clear), 'OCR (sin vecino)')
            parts[i] = _case_like(parts[i], clear)
    return ''.join(parts)


def modernizar_prudente(linea, voc):
    """modernizar(), except words it turns into a form found in fewer than DROP_BOOKS books of the corpus, and
    frequent OCR errors, left for step 5 ("eon" would become "eón")."""
    nueva = modernizar(linea)
    antes = _WORD.findall(linea)
    parts = re.split(r'([^\W\d_]+)', nueva)
    if len(antes) != len(parts) // 2:
        _anotar_tramos(antes, _WORD.findall(nueva), 'modernización')
        return nueva  # Words joined or split ("dél" -> "de él"): no word-by-word comparison
    for k in range(len(antes)):
        w = parts[2 * k + 1]
        only_dieresis = re.sub(r'(?<=[gG])[úÚ](?=[eiEI])', lambda m: 'ü' if m.group(0) == 'ú' else 'Ü', antes[k]) == w
        if w != antes[k] and not only_dieresis and (voc['books'][w.lower()] < DROP_BOOKS
                                                   or antes[k].lower() in voc.get('frecuentes', {})):
            parts[2 * k + 1] = antes[k]
        parts[2 * k + 1] = _dieresis(parts[2 * k + 1])
        _anotar(antes[k], parts[2 * k + 1], 'modernización')
    return ''.join(parts)


_GUE_GUI = re.compile(r'(?<=[gG])([uU])(?=[eiéíEIÉÍ])')
_DIERESIS_CACHE = {}


def _dieresis(w):
    """"verguenza" -> "vergüenza", "antiguedad" -> "antigüedad", "arguir" -> "argüir": a "gue"/"gui" printed without
    a mark takes "ü" if the word with "ü" is in the Spanish dictionary and the word without it is not ("guerra",
    "seguir" stay)."""
    if not _GUE_GUI.search(w):
        return w
    if w not in _DIERESIS_CACHE:
        nueva = w
        if not _en_diccionario(w):
            for m in _GUE_GUI.finditer(w):
                prueba = w[:m.start()] + ('ü' if m.group(1) == 'u' else 'Ü') + w[m.end():]
                if _en_diccionario(prueba):
                    nueva = prueba
                    break
        _DIERESIS_CACHE[w] = nueva
    return _DIERESIS_CACHE[w]


def postcorregir(linea, voc, stats=None):
    """Second step, after modernizar(): steps 1-3 and 6, which need the vocabulary of the whole corpus."""
    if stats is None:
        stats = Counter()
    parts = re.split(r'([^\W\d_]+)', linea)
    latin = _latin_mask(parts[1::2])
    for i in range(1, len(parts), 2):
        if latin[i // 2]:
            continue  # Latin: no accents, contractions or splits from the Spanish corpus
        before = [stats[k] for k in FIX_RULES]
        fixed = _fix_word(parts[i], voc, stats)
        _anotar(parts[i], fixed, '+'.join(k for k, n in zip(FIX_RULES, before) if stats[k] > n))
        parts[i] = fixed
    s = ''.join(parts)
    s = re.sub(r'  +', ' ', s)
    s = re.sub(r' +([,;:.?!)\]])', r'\1', s)
    return s


# ---------------------------------------------------------------------------
# A whole book (to run in parallel from 6-modernizacion.ipynb)
# ---------------------------------------------------------------------------
_VOC = None
_TAG = re.compile(r'(<[^>]+>)')


def iniciar(ruta_vocabulario):
    """Loads the corpus vocabulary once in each worker process."""
    global _VOC
    import pickle
    with open(ruta_vocabulario, 'rb') as f:
        _VOC = pickle.load(f)


# Drop caps misread by the OCR ("Eué" for "Fué", "Iijos" for "hijos"): the first word of a line, capitalized, not in
# the Spanish dictionary, in fewer than KNOWN_BOOKS books and not an abbreviation, becomes a word that differs only in
# its first letter and is CAPITAL_RATIO times more frequent. If there are several such words, the one most often
# followed by the next word of the line, relative to its own frequency (at least twice, and 5 times the second):
# "Eué el" -> "Fué el", not "Qué el"; if that does not decide, the one CLEAR_RATIO times more frequent than the rest.
# Words in capitals and words found capitalized inside a line elsewhere (names: "Zola", "Vicencia") are left alone. Latin words are left alone. Only at the beginning
# of a line, where drop caps are.
CAPITAL_RATIO = 100
_FIRST_LETTERS = 'abcdefghijlmnopqrstuvxyzñ'


def capitulares(voc, ruta_diccionario):
    """{misread word: [corrections, most frequent first]} for drop caps; see CAPITAL_RATIO. Once for the corpus."""
    from spylls.hunspell import Dictionary
    abreviaturas = {a.lower() for a in voc['abrev']}
    candidatos = {}
    for w, n in voc['freq'].items():
        if len(w) < 3 or voc['books'][w] >= KNOWN_BOOKS or _is_latin_strong(w) or w in abreviaturas:
            continue
        opts = sorted(((voc['freq'][c], c) for c in (L + w[1:] for L in _FIRST_LETTERS if L != w[0])
                       if voc['books'][c] >= KNOWN_BOOKS and voc['freq'][c] >= CAPITAL_RATIO * n
                       and not _is_latin_strong(c) and not _abreviatura_vocal(w, c)), reverse=True)
        if opts:
            candidatos[w] = [c for _, c in opts]
    diccionario = Dictionary.from_files(ruta_diccionario)
    return {w: c for w, c in candidatos.items() if not diccionario.lookup(w) and not diccionario.lookup(w.capitalize())}


def _abreviatura_vocal(w, c):
    """A three-letter abbreviation without period ("Vra" for "Vuestra") is not a misread vowel ("Era")."""
    vocales = 'aeiouáéíóú'
    return len(w) == 3 and w[0] not in vocales and w[1] not in vocales and c[0] in vocales


def _primera_palabra(linea):
    """The first word of the line and the plain word after it ('' if none)."""
    words = list(_WORD.finditer(linea))
    if not words or words[0].start() != 0:
        return None, ''
    return words[0], (plain(words[1].group(0)) if len(words) > 1 else '')


def pares_capitulares(carpeta, voc):
    """The pairs (correction, next word) that _capitular() needs, from the beginnings of lines of the corpus; and the
    words of voc['capitulares'] found capitalized inside a line, which are names ("Zola", "Vicencia"), not drop caps."""
    necesarios, nombres = set(), set()
    for nombre in os.listdir(carpeta):
        with open(os.path.join(carpeta, nombre), encoding='utf-8') as f:
            for linea in f:
                m, siguiente = _primera_palabra(linea)
                if m and len(voc['capitulares'].get(m.group(0).lower(), [])) > 1:
                    necesarios.update((plain(c), siguiente) for c in voc['capitulares'][m.group(0).lower()])
                for w in _WORD.finditer(linea):
                    if w.start() > 0 and w.group(0)[:1].isupper() and w.group(0).lower() in voc['capitulares']:
                        nombres.add(w.group(0).lower())
    return necesarios, nombres


def _capitular(linea, voc):
    m, siguiente = _primera_palabra(linea)
    if not m or not m.group(0)[:1].isupper() or m.group(0).lower() not in voc.get('capitulares', {})             or linea[m.end():m.end() + 1] == '.' or m.group(0).isupper()             or m.group(0).lower() in voc['nombres_capitulares'] or m.group(0).lower() in voc.get('latin', ()):
        return linea  # "Vra." (Vuestra) is not "Era."; "REMIÓ" (for "PREMIÓ") is not "TEMIÓ"; names stay
    cands = voc['capitulares'][m.group(0).lower()]
    best = cands[0]
    if len(cands) > 1:
        pares = voc['pares_capitulares']
        # Pairs are counted without accents ("qué el" with "que el"), so the frequency is too:
        scores = sorted(((pares[(plain(c), siguiente)] / (voc['freq'][plain(c)] + (voc['freq'][c] if c != plain(c) else 0)), c)
                         for c in cands), reverse=True)
        if pares[(plain(scores[0][1]), siguiente)] >= 2 and scores[0][0] >= 5 * scores[1][0]:
            best = scores[0][1]
        elif voc['freq'][cands[0]] < CLEAR_RATIO * voc['freq'][cands[1]]:
            return linea
    nueva = _case_like(m.group(0), best)
    _anotar(m.group(0), nueva, 'capitular')
    return nueva + linea[m.end():]


# Punctuation at the beginning of a line (", caricias y favores"): the OCR put the mark of the end of the previous line
# on the next one. It goes back to the end of the previous line with text, across page breaks but not across headings
# or other tags, nor after a line ending in a hyphen. Line numbers do not change.
_LEADING_PUNCT = re.compile(r'([,;:.]+) *')


def _puntuacion_inicial(lineas):
    global _LINEA
    for k in range(1, len(lineas)):
        m = _LEADING_PUNCT.match(lineas[k])
        if not m:
            continue
        j = k - 1
        while j >= 0 and (not lineas[j].strip() or lineas[j].startswith('<pb')):
            j -= 1
        if j < 0 or lineas[j].lstrip().startswith('<') or lineas[j].rstrip().endswith(('-', '¬', ',', ';', ':', '.')):
            continue
        lineas[j] = lineas[j].rstrip() + m.group(1)
        lineas[k] = lineas[k][m.end():]
        _LINEA = k + 1
        _anotar(m.group(1), '', f'puntuación al inicio de línea (pasa a la línea {j + 1})')


def _escribir_registro(ruta, libro):
    import csv
    with open(ruta, 'w', encoding='utf-8', newline='') as f:
        csv.writer(f).writerows((libro, n, antes, despues, regla) for n, antes, despues, regla in _CAMBIOS)


def modernizar_libro(rutas):
    """modernizar() and postcorregir() over one book; tags, abbreviations and tokens with digits are left out.
    rutas: (clean text, modernized text, register of changes)."""
    global _CAMBIOS, _LINEA
    entrada, salida, registro = rutas
    stats = Counter()
    with open(entrada, encoding='utf-8') as f:
        lineas = f.read().split('\n')
    _CAMBIOS = []
    _puntuacion_inicial(lineas)
    patron = patron_protegido(_VOC)
    nuevas = []
    for k, linea in enumerate(lineas):
        _LINEA = k + 1
        linea = _capitular(linea, _VOC)
        nuevas.append(procesar_linea(linea, patron, lambda s: postcorregir(modernizar_prudente(s, _VOC), _VOC, stats)))
    libro = os.path.basename(salida)
    _escribir_registro(registro, libro)
    _CAMBIOS = None
    with open(salida + '.part', 'w', encoding='utf-8') as f:
        f.write('\n'.join(nuevas))
    os.replace(salida + '.part', salida)
    return libro, dict(stats)


def corregir_libro(ruta, voc, pares, patron, stats, registro):
    """Step 5 (corregir_ocr()) over one modernized book, in place, with its register of changes."""
    global _CAMBIOS, _LINEA
    with open(ruta, encoding='utf-8') as f:
        lineas = f.read().split('\n')
    _CAMBIOS = []
    for k in range(len(lineas)):
        _LINEA = k + 1
        lineas[k] = procesar_linea(lineas[k], patron, lambda s: corregir_ocr(s, voc, pares, stats))
    _escribir_registro(registro, os.path.basename(ruta))
    _CAMBIOS = None
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lineas))


if __name__ == '__main__':
    import sys
    for ln in sys.stdin:
        sys.stdout.write(modernizar(ln.rstrip('\n')) + '\n')
