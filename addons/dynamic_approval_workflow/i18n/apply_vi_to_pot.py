from pathlib import Path
import polib

base = Path('/mnt/extra-addons/dynamic_approval_workflow/i18n')
po_path = base / 'vi.po'
pot_path = base / 'dynamic_approval_workflow.pot'

po = polib.pofile(str(po_path))
pot = polib.pofile(str(pot_path))

translations = {e.msgid: e.msgstr for e in po if e.msgstr}

for entry in pot:
    if entry.msgid in translations:
        entry.msgstr = translations[entry.msgid]

# Header cleanup for Vietnamese locale
pot.metadata['Language'] = 'vi_VN'
pot.metadata['Language-Team'] = 'Vietnamese'
pot.metadata['Content-Transfer-Encoding'] = '8bit'
pot.metadata['Plural-Forms'] = 'nplurals=1; plural=0;'

pot.save(str(pot_path))
print(f'Updated: {pot_path}')
print(f'Translated entries: {sum(1 for e in pot if e.msgstr)} / {len(pot)}')
