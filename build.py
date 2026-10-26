"""Build Hu Luo's single-page academic CV: python build.py."""
import json, re
from html import escape as e
from pathlib import Path
ROOT = Path(__file__).resolve().parent
D = json.loads((ROOT / 'content.json').read_text(encoding='utf-8'))
OUT = ROOT / 'site'
OUT.mkdir(exist_ok=True)
P = D['profile']
T = D['section_titles']
LIMIT = D.get('display', {}).get('initial_items', 10)
assert isinstance(LIMIT, int) and not isinstance(LIMIT, bool) and LIMIT > 0, 'initial_items must be a positive integer.'
def link(url,label,cls=''):
    return f'<a class="{cls}" href="{e(url,quote=True)}">{label}</a>'

def intro_text(text):
    # Only paired **bold** markers are supported; user HTML remains literal text.
    return re.sub(r'\*\*([^*\n]+)\*\*', r'<strong>\1</strong>', e(text))
def section_head(number,label,title):
    return f'<div class="section-heading"><span class="section-number">{number}</span><div><p class="eyebrow">{label}</p><h2>{title}</h2></div></div>'
def institution(x):
    logo=f'<img src="{e(x["logo"])}" alt="{e(x["institution"])} logo" class="{e(x["logo_kind"])}">'
    if x['logo'].endswith('.svg'):
        logo=(OUT/x['logo']).read_text(encoding='utf-8').replace('<svg ',f'<svg class="{e(x["logo_kind"])}" role="img" aria-label="{e(x["institution"])} logo" ',1)
    intro=f'<p class="institution-intro">{e(x["intro"])}</p>' if x.get('intro') else ''
    return f'''<article class="institution-row"><a class="institution-logo" href="{e(x['url'])}" aria-label="{e(x['institution'])} official website">{logo}</a><div class="institution-content"><div class="institution-heading"><h3>{link(x['url'],e(x['institution']))}<span lang="zh-CN">{e(x['institution_zh'])}</span></h3><span class="period">{e(x['period'])}</span></div><p class="role">{e(x['role'])}</p><p class="department">{e(x['department'])}</p>{intro}<p class="institution-detail">{e(x['detail'])}</p></div></article>'''

def institution_compact(x):
    if x['logo'].endswith('.svg'):
        logo=(OUT/x['logo']).read_text(encoding='utf-8').replace('<svg ',f'<svg role="img" aria-label="{e(x["institution"])} logo" ',1)
    else:
        logo=f'<img src="{e(x["logo"])}" alt="{e(x["institution"])} logo">'
    chinese=f'<span class="compact-chinese" lang="zh-CN">{e(x["institution_zh"])}</span>'
    return f'''<article class="background-entry"><a class="compact-logo {e(x['logo_kind'])}" href="{e(x['url'])}" aria-label="{e(x['institution'])} official website">{logo}</a><div class="background-entry-copy"><h3>{link(x['url'],e(x['institution']))}</h3>{chinese}<div class="compact-role-row"><p>{e(x['role'])}</p><span class="period">{e(x['period'])}</span></div></div></article>'''

def institution_details(x):
    intro=f'<p>{e(x["intro"])}</p>' if x.get('intro') else ''
    return f'<article class="background-detail"><h4>{e(x["institution"])}</h4><p class="department">{e(x["department"])}</p>{intro}<p>{e(x["detail"])}</p></article>'
def publication(p):
    url='https://doi.org/'+p['doi'] if p.get('doi') else p.get('url','')
    title=link(url,e(p['title'])) if url else e(p['title'])
    authors=re.sub(r'\bLuo,? H(?:\.|(?=[,\s]|$))',r'<strong class="author">\g<0></strong>',e(p['authors']))
    actions=link(url,'Paper ↗','text-link') if url else ''
    if p.get('project_url'): actions+=' '+link(p['project_url'],'Project ↗','text-link')
    summary=f'<p class="paper-summary">{e(p["summary"])}</p>' if p.get('summary') else ''
    expertise=f'<p class="expertise">{e(p["expertise"])}</p>' if p.get('expertise') else ''
    display_image = p.get('selected', False) is True
    cls='featured' if display_image else 'compact'
    role='First author' if p.get('first_author', False) else ''
    if display_image:
        path=OUT/p['image']
        # Inline SVG avoids operating-system MIME differences during local preview.
        visual=path.read_text(encoding='utf-8').replace('<svg ',f'<svg role="img" aria-label="{e(p["image_alt"],quote=True)}" ',1) if path.suffix=='.svg' else f'<img src="{e(p["image"])}" alt="{e(p["image_alt"])}" loading="lazy">'
        side=f'<figure class="paper-figure">{link(url,visual)}<figcaption>{e(p.get("image_caption", "Research schematic"))}</figcaption></figure>'
    else:
        in_review = p.get("status", "").casefold() in {"major revision", "minor revision", "under review", "in review"}
        if in_review:
            side='<div class="publication-meta"><span class="badge">In Review</span></div>'
        else:
            year_label = f'<span>{e(str(p["year"]))}</span>' if p.get("year") is not None else ""
            side=f'<div class="publication-meta">{year_label}<span class="badge">{e(p["status"])}</span></div>'
    author_line='' if p.get('key_manuscript') else f'<p class="paper-authors">{authors.rstrip(".")}.</p>'
    role_line=f'<span class="author-role">{role}</span>' if role else ''
    return f'<li class="publication {cls}" data-id="{p["id"]}" data-status="{e(p["status"])}">{side}<div class="paper-content"><p class="paper-venue">{e(p["display_venue"])} {role_line}</p><h3 class="paper-title">{title}</h3>{author_line}{summary}{expertise}<div class="paper-actions">{actions}</div></div></li>'

def collection(items, renderer, kind, label):
    limit=D.get('display', {}).get(kind+'s_initial_items', LIMIT)
    assert isinstance(limit, int) and not isinstance(limit, bool) and limit > 0, kind+'s_initial_items must be a positive integer.'
    first=f'<ol class="{kind}-list">'+''.join(renderer(x) for x in items[:limit])+'</ol>'
    if len(items)<=limit: return first
    remaining=len(items)-limit
    more=T.get(kind+'s_more', 'More '+label)
    less=T.get('show_fewer', 'Show fewer')
    count=T.get('additional_entries', '{count} additional entries').replace('{count}', str(remaining))
    return first+f'<details class="more-items" id="more-{kind}"><summary><span class="when-closed">{e(more)} <span aria-hidden="true">↗</span></span><span class="when-open">{e(less)} <span aria-hidden="true">−</span></span><span class="more-count">{e(count)}</span></summary><ol class="{kind}-list" start="{limit+1}">'+''.join(renderer(x) for x in items[limit:])+'</ol></details>'

bio=''.join(f'<p class="hero-bio">{intro_text(p)}</p>' for p in D['intro_paragraphs'])
wechat=f'<details class="wechat"><summary>WeChat <span aria-hidden="true">+</span></summary><div class="wechat-card"><span>WeChat ID</span><strong>{e(D["wechat"])}</strong></div></details>'
hero=f'''<section class="hero"><div class="hero-copy"><p class="eyebrow"><span class="dot"></span> {e(P["research_tagline"])}</p><h1>{e(D['name'])}</h1><p class="affiliation">{e(P["role"])} · {e(P["affiliation"])} <span lang="zh-CN">{e(P["affiliation_zh"])}</span></p>{bio}<div class="contact-links">{link('mailto:'+D['email'],e(D['email'])+' ↗')}{link(D['scholar'],'Google Scholar ↗')}{link(D['github'],'GitHub ↗')}{wechat}</div></div><figure class="portrait"><div class="portrait-frame"><img src="{e(P["portrait"],quote=True)}" alt="{e(P["portrait_alt"],quote=True)}" width="300" height="375"></div></figure></section>'''
experience=f'''<section class="background-section" id="experience" aria-label="Education and experience"><div class="background-card"><div class="background-columns"><div class="background-column"><h2>{e(T["education"])} <span lang="zh-CN">{e(T["education_zh"])}</span></h2>{''.join(institution_compact(x) for x in D['education'])}</div><div class="background-column"><h2>{e(T["experience"])} <span lang="zh-CN">{e(T["experience_zh"])}</span></h2>{''.join(institution_compact(x) for x in D['experience'])}</div></div><details class="background-more"><summary><span class="background-show">{e(T["background_more"])}</span><span class="background-hide">{e(T["background_less"])}</span><span class="background-plus" aria-hidden="true">+</span></summary><div class="background-columns"><div>{''.join(institution_details(x) for x in D['education'])}</div><div>{''.join(institution_details(x) for x in D['experience'])}</div></div></details></div></section>'''
by_id={p['id']:p for p in D['publications']}
assert len(by_id)==len(D['publications']), 'Publication IDs must be unique.'
assert len(D['publication_order'])==len(by_id) and set(D['publication_order'])==set(by_id), 'publication_order must contain every publication ID exactly once.'
ordered=[by_id[i] for i in D['publication_order']]
publications=f'''<section class="cv-section" id="publications">{section_head('02',e(T['publications_label']),e(T['publications']))}<p class="section-intro">{e(T["publications_intro"])} <span class="collection-total">{len(ordered)} entries</span></p>{collection(ordered,publication,'publication','publications & manuscripts')}</section>'''

def patent_partners(p):
    catalog=D.get('patent_organizations', {})
    labels=D.get('patent_labels', {})
    cards=[]
    for item in p.get('partnerships', []):
        relationship=item['type']
        assert relationship in ('commercialized','collaboration'), 'Patent partnership type must be commercialized or collaboration.'
        org=catalog[item['organization']]
        assert org.get('name'), 'Fill the patent organization name before linking it to a patent.'
        logo=''
        if org.get('logo'):
            path=OUT/org['logo']
            assert path.is_file(), 'Patent organization logo not found: '+org['logo']
            visual=path.read_text(encoding='utf-8').replace('<svg ',f'<svg role="img" aria-label="{e(org["name"])} logo" ',1) if path.suffix.lower()=='.svg' else f'<img src="{e(org["logo"])}" alt="{e(org["name"])} logo" loading="lazy">'
            logo=f'<span class="patent-org-logo">{visual}</span>'
        name=f'<span class="patent-org-name">{e(org["name"])}'
        if org.get('name_zh'): name+=f'<span lang="zh-CN">{e(org["name_zh"])}</span>'
        name+='</span>'
        identity=logo+name
        identity=link(org['url'],identity,'patent-org') if org.get('url') else f'<span class="patent-org">{identity}</span>'
        label=labels.get(relationship, 'Commercialized' if relationship=='commercialized' else 'Collaboration')
        note=f'<span class="patent-partner-note">{e(item["note"])}</span>' if item.get('note') else ''
        cards.append(f'<div class="patent-partner {relationship}"><span class="relationship-label">{e(label)}</span>{identity}{note}</div>')
    return '<div class="patent-partners">'+''.join(cards)+'</div>' if cards else ''

def patent(p):
    number=link('https://patents.google.com/patent/'+p['number']+'/en',e(p['number'])+' ↗','text-link') if p['number'].startswith('CN') else e('Application '+p['number'])
    summary=f'<p class="patent-summary">{e(p["summary"])}</p>' if p.get('summary') else ''
    inventors=e(p['inventors']).replace('Luo Hu','<strong class="author">Luo Hu</strong>')
    return f'<li class="patent" data-number="{p["number"]}"><div class="patent-meta">{patent_partners(p)}</div><div class="patent-content"><h3>{e(p["title"])}</h3><p>{inventors}</p>{summary}<div class="patent-reference"><span class="badge">{e(p["status"])}</span><span class="patent-number">{number}</span></div></div></li>'
patents=f'<section class="cv-section" id="patents">{section_head("03",e(T["patents_label"]),e(T["patents"]))}<p class="section-intro">{e(T["patents_intro"])} <span class="collection-total">{len(D["patents"])} entries</span></p>{collection(D["patents"],patent,"patent","patents & applications")}</section>'
awards=f'<section class="cv-section" id="awards">{section_head("04",e(T["awards_label"]),e(T["awards"]))}{collection(D["awards"],lambda x:f"<li>{e(x)}</li>","award","awards")}</section>'
description=P['page_description']
html=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=1200"><title>{e(P["page_title"])}</title><meta name="description" content="{e(description)}"><meta name="theme-color" content="#193e38"><meta property="og:title" content="{e(P["page_title"],quote=True)}"><meta property="og:description" content="{e(description)}"><meta property="og:type" content="profile"><link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/style.css"></head><body><a class="skip" href="#main">Skip to content</a><div class="page-top"><span>{e(D["name"].upper())}</span><span>{e(P["top_label"])}</span></div><main id="main">{hero}{experience}{publications}{patents}{awards}</main><footer><span>© 2026 {e(D["name"])} · Updated {e(D['updated'])}</span>{link('mailto:'+D['email'],e(D['email'])+' ↗')}</footer></body></html>'''
(OUT/'index.html').write_text(html,encoding='utf-8')
# Previously shared addresses redirect into the single page.
for filename,anchor in [('experience.html','experience'),('publications.html','publications'),('patents.html','patents'),('cv.html','main')]:
    target='index.html#'+anchor
    (OUT/filename).write_text(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={target}"><title>{e(P["page_title"])}</title><link rel="canonical" href="{e(D["site_url"])}/"></head><body><p><a href="{target}">Continue to Hu Luo’s academic profile</a></p></body></html>',encoding='utf-8')
(OUT/'404.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Page not found | Hu Luo</title></head><body><h1>Page not found</h1><p><a href="index.html">Return to Hu Luo’s academic profile</a></p></body></html>',encoding='utf-8')
(OUT/'.nojekyll').touch()
(OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+D['site_url']+'/sitemap.xml\n',encoding='utf-8')
(OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+e(D['site_url'])+'/</loc></url></urlset>',encoding='utf-8')
print('Built single-page academic CV and legacy URL redirects.')
