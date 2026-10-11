
import threading
import time
import random
import json
import webbrowser
from pathlib import Path

N = 4
chopsticks = [threading.Semaphore(1) for _ in range(N)]
room = threading.Semaphore(N - 1)

states = ["Thinking"] * N
events = []
event_lock = threading.Lock()
start_time = time.perf_counter()


def record(i, action, message):
    with event_lock:
        events.append({
            "time": round(time.perf_counter() - start_time, 3),
            "philosopher": i,
            "action": action,
            "message": message,
            "states": states.copy()
        })


def philosopher(i):
    left = i
    right = (i + 1) % N
    name = f"Philosopher {i + 1}"

    for round_no in range(1, 3):
        states[i] = "Thinking"
        record(i, "thinking", f"{name} is thinking")
        time.sleep(random.uniform(0.3, 0.7))

        states[i] = "Hungry"
        record(i, "hungry", f"{name} is hungry and waiting")
        room.acquire()

        chopsticks[left].acquire()
        states[i] = "Has left chopstick"
        record(i, "left", f"{name} picked up chopstick {left + 1}")

        chopsticks[right].acquire()
        states[i] = "Eating"
        record(i, "eating", f"{name} is eating")
        time.sleep(random.uniform(0.3, 0.6))

        chopsticks[right].release()
        chopsticks[left].release()
        room.release()

        states[i] = "Thinking"
        record(i, "finished", f"{name} finished eating")
        time.sleep(0.2)


def generate_html(filename):
    data = json.dumps(events).replace("</", "<\\/")

    page = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Dining Philosophers - Semaphore</title>
<style>
body{font-family:Arial;background:#eef2f7;color:#183153;padding:20px}
.card{background:white;padding:18px;margin:12px 0;border-radius:12px}
button{padding:10px;margin:4px;background:#1769aa;color:white;border:0;cursor:pointer}
table{width:100%;border-collapse:collapse}
td,th{border:1px solid #ccc;padding:8px;text-align:left}
svg{width:100%;max-width:450px;display:block;margin:auto}
</style>
</head>
<body>
<h1>Dining Philosophers - Semaphore Solution</h1>
<div class="card">
<h2 id="message">Press Play to start</h2>
<p id="counter">Event 0</p>
<p id="states"></p>
<button onclick="play()">Play</button>
<button onclick="pause()">Pause</button>
<button onclick="next()">Next Event</button>
<button onclick="reset()">Reset</button>
<div style="background:#ddd;height:10px"><div id="progress" style="background:#1769aa;height:10px;width:0%"></div></div>
</div>
<div class="card">
<h2>Table Visualization</h2>
<svg viewBox="0 0 400 400">
<circle cx="200" cy="200" r="95" fill="#f5e5c8" stroke="#c6a56b" stroke-width="3"/>
<g id="sticks"></g><g id="people"></g>
</svg>
</div>
<div class="card">
<h2>Execution Log</h2>
<table><thead><tr><th>Time</th><th>Philosopher</th><th>Event</th></tr></thead>
<tbody id="logs"></tbody></table>
</div>
<script>
const events=EVENT_DATA;
const positions=[[200,65],[335,200],[200,335],[65,200]];
const stickPositions=[[270,120],[280,270],[120,280],[120,120]];
let index=0,timer=null;

function draw(states){
 document.getElementById("people").innerHTML=states.map((s,i)=>{
  let [x,y]=positions[i];
  let c=s==="Eating"?"#39a96b":s==="Hungry"||s==="Has left chopstick"?"#efb447":"#528fd1";
  return `<g><circle cx="${x}" cy="${y}" r="30" fill="${c}" stroke="#183153" stroke-width="2"/><text x="${x}" y="${y-2}" text-anchor="middle" font-size="12" fill="white">P${i+1}</text><text x="${x}" y="${y+12}" text-anchor="middle" font-size="8" fill="white">${s}</text></g>`;
 }).join("");
 document.getElementById("sticks").innerHTML=stickPositions.map(([x,y],i)=>
 `<g><rect x="${x-5}" y="${y-16}" width="10" height="32" rx="3" fill="#a87945" transform="rotate(45 ${x} ${y})"/><text x="${x}" y="${y+25}" text-anchor="middle" font-size="10">C${i+1}</text></g>`
 ).join("");
 document.getElementById("states").textContent=states.map((s,i)=>`P${i+1}: ${s}`).join(" | ");
}
function show(){
 if(index>=events.length){pause();return}
 let e=events[index++];
 document.getElementById("message").textContent=e.message;
 document.getElementById("counter").textContent=`Event ${index}/${events.length} · ${e.time}s`;
 draw(e.states);
 document.getElementById("progress").style.width=(index/events.length*100)+"%";
 let row=document.createElement("tr");
 [e.time,"Philosopher "+(e.philosopher+1),e.message].forEach(v=>{let td=document.createElement("td");td.textContent=v;row.appendChild(td)});
 document.getElementById("logs").appendChild(row);
}
function play(){if(timer===null&&index<events.length)timer=setInterval(show,700)}
function pause(){clearInterval(timer);timer=null}
function next(){pause();show()}
function reset(){pause();index=0;document.getElementById("logs").innerHTML="";document.getElementById("message").textContent="Press Play to start";document.getElementById("counter").textContent="Event 0";document.getElementById("progress").style.width="0%";draw(["Thinking","Thinking","Thinking","Thinking"])}
draw(["Thinking","Thinking","Thinking","Thinking"]);
</script>
</body>
</html>"""

    Path(filename).write_text(data and page.replace("EVENT_DATA", data)
                              or page.replace("EVENT_DATA", "[]"),
                              encoding="utf-8")
    print("HTML generated:", Path(filename).resolve())


def main():
    global start_time
    start_time = time.perf_counter()

    threads = [
        threading.Thread(target=philosopher, args=(i,))
        for i in range(N)
    ]

    random.shuffle(threads)

    for t in threads:
        t.start()
        time.sleep(0.05)

    for t in threads:
        t.join()

    output = Path(__file__).resolve().parent / "dining_semaphore.html"
    generate_html(str(output))
    print("Simulation finished. Events:", len(events))
    webbrowser.open(output.as_uri())


if __name__ == "__main__":
    main()

