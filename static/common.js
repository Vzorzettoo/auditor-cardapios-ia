const $ = (id) => document.getElementById(id);
const esc = (value) => String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function post(path, data) {
  const response = await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  const value = await response.json();
  if(!response.ok) throw new Error(typeof value.detail === 'string' ? value.detail : JSON.stringify(value.detail));
  return value;
}
async function busy(action) {
  const button = $('run'); button.disabled=true; $('result').innerHTML='<p>Processando...</p>';
  try { await action(); } catch(e) { $('result').innerHTML=`<p class="error">${esc(e.message)}</p>`; }
  finally {button.disabled=false;}
}
