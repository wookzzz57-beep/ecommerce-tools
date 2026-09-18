const task=document.querySelector("#task"),agnes=document.querySelector("#agnes"),hermes=document.querySelector("#hermes"),result=document.querySelector("#result");
document.querySelector("#route").addEventListener("click",()=>{if(!task.value.trim()){result.textContent="BLOCKED\nTask cannot be empty.";return}
if(agnes.checked){result.textContent="$0 GUARD: PASS\nLANE: agnes-free\nSTATE: task.json → checkpoint.json\nNEXT: run Agnes Recipe\nDONE GATE: evidence required";return}
if(hermes.checked){result.textContent="$0 GUARD: PASS\nLANE: hermes-local\nSTATE: task.json → checkpoint.json\nNEXT: use saved Hermes managed Local Model\nDONE GATE: evidence required";return}
result.textContent="$0 GUARD: BLOCKED\nNo explicitly verified free/local lane is ready.\nFirstWindow will not silently fall back to paid/unknown-cost inference.";});
