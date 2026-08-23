let sessionId=null;
const messages=document.querySelector('#messages');
const input=document.querySelector('#message');
const send=document.querySelector('#send');
const error=document.querySelector('#error');

function addMessage(text,who){
  const el=document.createElement('div'); el.className='msg '+who; el.textContent=text;
  messages.appendChild(el); messages.scrollTop=messages.scrollHeight; return el;
}
function renderFacts(body){
  const rows=[...(body.products||[]),...(body.offers||[]),...(body.trends||[])];
  const unique=[...new Map(rows.map(row=>[row.product_id,row])).values()];
  if(!unique.length)return;
  const card=document.createElement('div'); card.className='facts';
  unique.forEach(item=>{
    const row=document.createElement('article'); row.className='fact';
    const offer=item.offer ? `<span class="offer">Offer: ${item.offer.offer_price} ${item.currency}</span>` : '';
    const trend=item.trend_label ? `<span class="trend">${item.trend_label}</span>` : '';
    const link=item.product_url ? `<a href="${item.product_url}" target="_blank" rel="noreferrer">View product</a>` : '';
    row.innerHTML=`<strong>${item.name||'Product'}</strong><span>${item.price==null?'Price unavailable':`${item.price} ${item.currency}`}</span><span>${item.availability||'Availability unknown'}</span>${offer}${trend}${link}`;
    card.appendChild(row);
  });
  messages.appendChild(card); messages.scrollTop=messages.scrollHeight;
}
document.querySelector('#chat-form').onsubmit=async event=>{
  event.preventDefault(); const text=input.value.trim(); if(!text||send.disabled)return;
  addMessage(text,'user'); input.value=''; error.textContent=''; send.disabled=true; send.textContent='…';
  const loading=addMessage('Checking HIGHBASE data…','assistant loading');
  try{
    const response=await fetch('/api/v1/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text,session_id:sessionId})});
    if(!response.ok)throw new Error('The assistant could not answer right now.');
    const body=await response.json(); sessionId=body.session_id; loading.remove(); addMessage(body.response,'assistant'); renderFacts(body);
  }catch(exception){loading.remove(); error.textContent=exception.message; addMessage('Please try again in a moment.','assistant error');}
  finally{send.disabled=false; send.textContent='Send'; input.focus();}
};
document.querySelector('#reset').onclick=async()=>{if(sessionId)await fetch('/api/v1/chat/session/'+sessionId,{method:'DELETE'});sessionId=null;messages.innerHTML='';error.textContent='';input.focus();};
