/* Maps API responses to the shapes used by the render functions, and loads shared data. */
const initial = s => Array.from(String(s || '').trim())[0] || '؟';

function mapCard(c) { return { id: Number(c.id), n: c.name, s: c.subject || '', r: c.rating, c: c.reviewCount || 0, rec: c.recommendPercent, st: c.style || '', lv: c.level || '', tags: Array.isArray(c.tags) ? c.tags : [], img: c.photoUrl || '', e: initial(c.name) } }
function reg(card) { const t = Object.assign(TM.get(card.id) || {}, card); TM.set(t.id, t); return t }
function mapProfile(p) {
    const t = reg(mapCard(p)), b = p.bio;
    t.b = b ? { cls: b.classStyle, way: b.method, lvl: b.levelText, tst: b.problemSolving, edu: b.education, exp: b.experience, note: b.note } : null; return t
}
const mapReview = r => ({ id: r.id, w: r.reviewerLabel || 'دانش‌آموز', s: r.stars, t: r.body });
const mapCourses = list => (list || []).map(c => [c.title, c.description || '']);

async function loadSubjects() {
    const d = await API.subjects();
    TOP = ['همه', ...d.top];
    G = d.groups.map(x => [x.name, x.options.map(o => [o.label, o.subject])]);
}
async function loadPopular() {
    const d = await API.popular();
    P = d.items.map(i => { reg(mapCard(i.a)); reg(mapCard(i.b)); return [i.a.id, i.b.id, i.label] });
}