from pathlib import Path
import re
import polib
from deep_translator import GoogleTranslator

base = Path(__file__).resolve().parent
po_path = base / 'vi.po'
po = polib.pofile(str(po_path))
translator = GoogleTranslator(source='en', target='vi')

pattern_printf = re.compile(r'%\([^)]+\)[sd]')
pattern_jinja = re.compile(r'\{\{[^}]+\}\}')


def protect(text: str):
    tokens = {}
    idx = 0

    def sub(regex, t):
        nonlocal idx

        def repl(m):
            nonlocal idx
            key = f'__TK{idx}__'
            idx += 1
            tokens[key] = m.group(0)
            return key

        return regex.sub(repl, t)

    t = text
    t = sub(pattern_printf, t)
    t = sub(pattern_jinja, t)
    return t, tokens


def restore(text: str, tokens):
    t = text
    for k, v in tokens.items():
        t = t.replace(k, v)
    return t


updated = 0
for e in po:
    if e.msgid == '' or e.msgstr.strip():
        continue

    src = e.msgid
    protected, tokens = protect(src)

    try:
        translated = translator.translate(protected)
        translated = restore(translated, tokens)
        e.msgstr = translated
        updated += 1
    except Exception:
        pass

po.metadata['Language'] = 'vi_VN'
po.metadata['Language-Team'] = 'Vietnamese'
po.metadata['Content-Transfer-Encoding'] = '8bit'
po.metadata['Plural-Forms'] = 'nplurals=1; plural=0;'
po.save(str(po_path))

remaining = sum(1 for e in po if e.msgid and not e.msgstr.strip())
print('updated', updated)
print('remaining', remaining)
print('file', po_path)
