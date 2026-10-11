
import threading
import time
import random
import json
import webbrowser
from pathlib import Path

N = 4


class DiningMonitor:
    def __init__(self):
        self.condition = threading.Condition()
        self.states = ["Thinking"] * N
        self.events = []
        self.start_time = time.perf_counter()

    def record(self, i, action, message):
        self.events.append({
            "time": round(time.perf_counter() - self.start_time, 3),
            "philosopher": i,
            "action": action,
            "message": message,
            "states": self.states.copy()
        })

    def can_eat(self, i):
        left = (i - 1) % N
        right = (i + 1) % N
        return (
            self.states[i] == "Hungry"
            and self.states[left] != "Eating"
            and self.states[right] != "Eating"
        )

    def pickup(self, i):
        with self.condition:
            self.states[i] = "Hungry"
            self.record(i, "hungry", f"Philosopher {i+1} is hungry")

            while not self.can_eat(i):
                self.condition.wait()

            self.states[i] = "Eating"
            self.record(i, "eating", f"Philosopher {i+1} is eating")

    def putdown(self, i):
        with self.condition:
            self.states[i] = "Thinking"
            self.record(
                i, "finished",
                f"Philosopher {i+1} finished eating and released chopsticks"
            )
            self.condition.notify_all()


monitor = DiningMonitor()


def philosopher(i):
    for round_no in range(2):
        with monitor.condition:
            monitor.record(
                i, "thinking",
                f"Philosopher {i+1} is thinking"
            )

        time.sleep(random.uniform(0.3, 0.7))
        monitor.pickup(i)
        time.sleep(random.uniform(0.3, 0.6))
        monitor.putdown(i)


def generate_html(filename):
    data = json.dumps(monitor.events).replace("</", "<\\/")

    page = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Dining Philosophers - Monitor</title>
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
<h1>Dining Philosophers - Monitor Solution</h1>
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
  let c=s==="Eating"?"#39a96b":s==="Hungry"?"#efb447":"#528fd1";
  return `<g><circle cx="${x}" cy="${y}" r="30" fill="${c}" stroke="#183153" stroke-width="2"/><text x="${x}" y="${y-2}" text-anchor="middle" font-size="12" fill="white">P${i+1}</text><text x="${x}" y="${y+12}" text-anchor="middle" font-size="9" fill="white">${s}</text></g>`;
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

    Path(filename).write_text(page.replace("EVENT_DATA", data), encoding="utf-8")
    print("HTML generated:", Path(filename).resolve())


def main():
    monitor.start_time = time.perf_counter()
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

    output = Path(__file__).resolve().parent / "dining_monitor.html"
    generate_html(str(output))
    print("Simulation finished. Events:", len(monitor.events))
    webbrowser.open(output.as_uri())


if __name__ == "__main__":
    main()

