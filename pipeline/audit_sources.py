"""Read-only inventory of registered ship sources and utility model coverage."""
import json
from pathlib import Path
import ini
from run import BASE, dump, f, low

def audit(cfg):
    ini.ROOT = root = Path(cfg['game'])
    data = root/'DATA'
    registered = [(k.lower(), str(v[0]).replace('\\', '/').lower())
                  for s in ini.ini(root/'EXE/freelancer.ini') if low(s['section']) == 'data'
                  for k, v in s['entries'] if v]
    sources = {}
    ships = []
    for path in sorted((data/'SHIPS').glob('*.ini')):
        sections = ini.ini(path)
        records = [s for s in sections if low(s['section']) in ('ship', 'loadout')]
        sources[path.name] = {'registered': any(p == 'ships/'+path.name.lower() for _, p in registered),
                              'records': len(records), 'models': sorted({f(s, 'DA_archetype') for s in records if f(s, 'DA_archetype')}),
                              'inheritance': [s for s in records if f(s, 'inherit')]}
        ships.extend(s for s in records if low(s['section']) == 'ship')
    utility = []
    for path in sorted((data/'SHIPS/UTILITY').rglob('*')):
        if path.suffix.lower() not in ('.cmp', '.3db'): continue
        rel = str(path.relative_to(data)).replace('\\', '/').lower()
        utility.append({'model': rel, 'ship_archetypes': [f(s, 'nickname') for s in ships
                        if low(f(s, 'DA_archetype')).replace('\\', '/') == rel]})
    loadouts = [{f(s,'nickname'):s['entries'] for s in ini.ini(data/'SHIPS'/name)}
                for name in ('loadouts.ini','loadouts_regen.ini')]
    active, regen = loadouts
    regen_changes = [{'nickname':n, 'added':[e for e in regen.get(n,[]) if e not in active[n]],
                      'removed':[e for e in active[n] if e not in regen.get(n,[])]}
                     for n in sorted(active) if active[n] != regen.get(n)]
    result = {'game': str(root), 'sources': sources, 'utility': utility, 'regen_changes':regen_changes}
    dump(BASE/'reports/source-audit.json', result)
    print(json.dumps({'sources': {k: {x: v[x] if x != 'models' else len(v[x]) for x in ('registered','records','models','inheritance')} for k,v in sources.items()},
                      'utility_models': len(utility), 'utility_registered_models': sum(bool(x['ship_archetypes']) for x in utility)}, indent=2))
    return result

if __name__ == '__main__':
    audit(json.loads((BASE/'config.json').read_text()))
