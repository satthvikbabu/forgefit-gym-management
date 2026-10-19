const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
let membersCache = [];
let toastTimer;
function showToast(message, error=false){const t=$('#toast');t.textContent=message;t.classList.toggle('error',error);t.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.classList.remove('show'),3600)}
async function api(url, options={}){const response=await fetch(url,{headers:{'Content-Type':'application/json'},...options});let data={};try{data=await response.json()}catch{}if(!response.ok)throw new Error(data.error||'Request failed. Please try again.');return data}
function initials(name='Member'){return name.trim().split(/\s+/).slice(0,2).map(p=>p[0]).join('').toUpperCase()}
function prettyDate(value){if(!value)return '—';const d=new Date(value+'T00:00:00');return Number.isNaN(d.getTime())?value:d.toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric'})}
function prettyDateTime(value){if(!value)return '—';const d=new Date(value.replace(' ','T'));return Number.isNaN(d.getTime())?value:d.toLocaleString('en-IN',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'})}
function badge(status){return `<span class="badge ${String(status||'').toLowerCase()}">${status||'unknown'}</span>`}
function memberRow(m,compact=false){return compact?`<tr><td><div class="member-cell"><span class="member-avatar">${initials(m.name)}</span><span><span class="member-name">${escapeHtml(m.name)}</span><span class="member-sub">Member #${m.id}</span></span></div></td><td>${escapeHtml(m.fitness_goal||'—')}</td><td style="text-transform:capitalize">${escapeHtml(m.plan||'—')}</td><td>${badge(m.membership_status)}</td></tr>`:`<tr><td>#${m.id}</td><td><div class="member-cell"><span class="member-avatar">${initials(m.name)}</span><span><span class="member-name">${escapeHtml(m.name)}</span><span class="member-sub">${escapeHtml(m.fitness_goal||'')}</span></span></div></td><td>${escapeHtml(String(m.age||'—'))} / ${escapeHtml(m.gender||'—')}</td><td>${escapeHtml(m.fitness_goal||'—')}</td><td style="text-transform:capitalize">${escapeHtml(m.plan||'—')}</td><td>${prettyDate(m.membership_end)}</td><td>${badge(m.membership_status)}</td></tr>`}
function escapeHtml(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function loadMembers(){const q=$('#memberSearch')?.value.trim()||'';const status=$('#statusFilter')?.value||'';const params=new URLSearchParams();if(q)params.set('q',q);if(status)params.set('status',status);const data=await api('/api/members?'+params.toString());membersCache=data.members||[];const body=$('#membersTable');if(body)body.innerHTML=membersCache.length?membersCache.map(m=>memberRow(m)).join(''):'<tr><td colspan="7" class="empty">No members found. Try a different search or add a member.</td></tr>';const recent=$('#recentMembers');if(recent){const all=await api('/api/members');const latest=(all.members||[]).slice(0,5);recent.innerHTML=latest.length?latest.map(m=>memberRow(m,true)).join(''):'<tr><td colspan="4" class="empty">No members yet. Add your first member.</td></tr>';membersCache=all.members||[];}populateMemberSelects();}
function populateMemberSelects(){['#attendanceMember','#workoutMember'].forEach(sel=>{const el=$(sel);if(!el)return;const previous=el.value;el.innerHTML='<option value="">Choose a member…</option>'+membersCache.map(m=>`<option value="${m.id}">${escapeHtml(m.name)} (#${m.id})</option>`).join('');if(previous)el.value=previous})}
async function loadDashboard(){const [analytics]=await Promise.all([api('/api/analytics')]);const s=analytics.summary||{};$('#totalMembers').textContent=s.total_members??0;$('#activeMembers').textContent=s.active_members??0;$('#todayAttendance').textContent=s.attendance_today??0;$('#totalRevenue').textContent='₹'+Number(s.total_recorded_revenue||0).toLocaleString('en-IN',{maximumFractionDigits:2});$('#expiringSoon').textContent=s.memberships_expiring_within_7_days??0;$('#attendanceSnapshot').textContent=s.attendance_today??0;$('#newThisMonth').textContent=s.new_registrations_this_month??0;$('#expiredMembers').textContent=s.expired_memberships??0;$('#workoutCompletions').textContent=s.completed_workout_logs??0;$('#analyticsExpiring').textContent=s.memberships_expiring_within_7_days??0;renderBars('#registrationChart',analytics.member_growth_by_month||[],'registrations','month');renderBars('#attendanceChart',analytics.attendance_by_month||[],'visits','month');renderPopular(analytics.popular_workouts||[]);}
function renderBars(target,items,valueKey,labelKey){const el=$(target);if(!el)return;if(!items.length){el.innerHTML='<div class="empty" style="width:100%">No data available yet.</div>';return}const data=items.slice(-7);const max=Math.max(...data.map(x=>Number(x[valueKey])||0),1);el.innerHTML=data.map(item=>{const val=Number(item[valueKey])||0;const h=Math.max(3,Math.round(val/max*100));const label=String(item[labelKey]||'').slice(5)===''?item[labelKey]:String(item[labelKey]||'').replace(/^\d{4}-/,'');return `<div class="bar-column"><span class="bar-value">${val}</span><div class="bar" style="height:${h}%" title="${val}"></div><span class="bar-label">${escapeHtml(label)}</span></div>`}).join('')}
function renderPopular(items){const el=$('#popularWorkouts');if(!el)return;if(!items.length){el.innerHTML='<div class="empty">No workout assignments yet.</div>';return}const max=Math.max(...items.map(x=>Number(x.assignments)||0),1);el.innerHTML=items.slice(0,7).map(x=>`<div class="popular-row"><span>${escapeHtml(x.exercise_name)}</span><div class="progress-track"><div class="progress-fill" style="width:${Math.max(3,(Number(x.assignments)||0)/max*100)}%"></div></div><strong>${x.assignments}</strong></div>`).join('')}
async function loadAttendance(){const data=await api('/api/attendance');const rows=data.attendance||[];$('#attendanceTable').innerHTML=rows.length?rows.slice(0,40).map(a=>`<tr><td><div class="member-cell"><span class="member-avatar">${initials(a.member_name)}</span><span class="member-name">${escapeHtml(a.member_name||'Member')}</span></div></td><td>${prettyDateTime(a.attended_at)}</td><td>${escapeHtml(a.notes||'—')}</td></tr>`).join(''):'<tr><td colspan="3" class="empty">No attendance records yet.</td></tr>'}
async function loadWorkouts(){const data=await api('/api/workouts');const rows=data.workouts||[];$('#workoutList').innerHTML=rows.length?rows.slice(0,25).map(w=>`<div class="workout-item"><div class="workout-symbol">↗</div><div><b>${escapeHtml(w.exercise_name)}</b><small>${escapeHtml(w.member_name||('Member #'+w.member_id))} · ${w.sets} sets × ${w.repetitions} reps</small><small>${escapeHtml(w.trainer_name||'Trainer not specified')}</small></div><div class="workout-meta">${w.duration_minutes||0} min</div></div>`).join(''):'<div class="empty">No workouts assigned yet.</div>'}
function showView(name){$$('.view').forEach(v=>v.classList.toggle('active',v.id==='view-'+name));$$('.nav-item').forEach(b=>b.classList.toggle('active',b.dataset.view===name));$('#breadcrumb').textContent=name.charAt(0).toUpperCase()+name.slice(1);if(name==='members')loadMembers().catch(e=>showToast(e.message,true));if(name==='attendance'){loadAttendance().catch(e=>showToast(e.message,true));loadMembers().catch(e=>showToast(e.message,true))}if(name==='workouts'){loadWorkouts().catch(e=>showToast(e.message,true));loadMembers().catch(e=>showToast(e.message,true))}if(name==='analytics')loadDashboard().catch(e=>showToast(e.message,true));}
$$('[data-view]').forEach(btn=>btn.addEventListener('click',()=>showView(btn.dataset.view)));
$$('[data-open]').forEach(btn=>btn.addEventListener('click',()=>$('#'+btn.dataset.open).classList.add('open')));
$$('[data-close]').forEach(btn=>btn.addEventListener('click',()=>$('#'+btn.dataset.close).classList.remove('open')));
$$('.modal-backdrop').forEach(backdrop=>backdrop.addEventListener('click',e=>{if(e.target===backdrop)backdrop.classList.remove('open')}));
$('#memberForm').addEventListener('submit',async e=>{e.preventDefault();const form=e.currentTarget;const raw=Object.fromEntries(new FormData(form));const payload={...raw,age:Number(raw.age),weight:Number(raw.weight)};if(raw.amount==='')delete payload.amount;else payload.amount=Number(raw.amount);try{await api('/api/members',{method:'POST',body:JSON.stringify(payload)});form.reset();$('#memberModal').classList.remove('open');await Promise.all([loadMembers(),loadDashboard()]);showToast('Member registered successfully.')}catch(err){showToast(err.message,true)}});
$('#attendanceForm').addEventListener('submit', async e => {
    e.preventDefault();

    const form = e.currentTarget;
    const raw = Object.fromEntries(new FormData(form));
    const payload = {
        member_id: Number(raw.member_id)
    };

    if (raw.notes.trim()) {
        payload.notes = raw.notes.trim();
    }

    try {
        await api('/api/attendance', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        form.reset();

        await Promise.all([
            loadAttendance(),
            loadDashboard()
        ]);

        showToast('Attendance recorded successfully.');
    } catch (err) {
        showToast(err.message, true);
    }
});
$('#workoutForm').addEventListener('submit', async e => {
    e.preventDefault();

    const form = e.currentTarget;
    const raw = Object.fromEntries(new FormData(form));

    const payload = {
        member_id: Number(raw.member_id),
        exercise_name: raw.exercise_name,
        sets: Number(raw.sets),
        repetitions: Number(raw.repetitions),
        duration_minutes: Number(raw.duration_minutes || 0),
        trainer_name: raw.trainer_name,
        trainer_notes: raw.trainer_notes
    };

    try {
        await api('/api/workouts', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        form.reset();

        await Promise.all([
            loadWorkouts(),
            loadDashboard()
        ]);

        showToast('Workout assigned successfully.');
    } catch (err) {
        showToast(err.message, true);
    }
});
$('#memberSearch').addEventListener('input',()=>{clearTimeout(window.searchTimer);window.searchTimer=setTimeout(()=>loadMembers().catch(e=>showToast(e.message,true)),250)});
$('#statusFilter').addEventListener('change',()=>loadMembers().catch(e=>showToast(e.message,true)));
$('#refreshAttendance').addEventListener('click',()=>loadAttendance().catch(e=>showToast(e.message,true)));
$('#refreshWorkouts').addEventListener('click',()=>loadWorkouts().catch(e=>showToast(e.message,true)));
$('#refreshAnalytics').addEventListener('click',()=>Promise.all([loadDashboard(),loadMembers()]).then(()=>showToast('Analytics refreshed.')).catch(e=>showToast(e.message,true)));
$('#todayLabel').textContent=new Date().toLocaleDateString('en-IN',{weekday:'short',day:'2-digit',month:'short',year:'numeric'});
(async function init(){try{await Promise.all([loadMembers(),loadDashboard()]);}catch(e){showToast('Could not load dashboard: '+e.message,true)}})();
