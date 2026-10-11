
import threading
import time
import random
import json
import os
import webbrowser
from pathlib import Path

# ==========================================
# READERS-WRITERS PROBLEM: SEMAPHORE APPROACH
# ==========================================

read_count = 0
shared_data = 0

# Semaphores for synchronization
mutex = threading.Semaphore(1)
resource = threading.Semaphore(1)

# Event recording
events = []
event_lock = threading.Lock()

active_readers = set()
active_writers = set()

start_time = time.perf_counter()


def log_event(name, action, message):
    """Record the current execution state safely."""
    with event_lock:
        events.append({
            "time": round(time.perf_counter() - start_time, 3),
            "name": name,
            "action": action,
            "message": message,
            "readers": sorted(active_readers),
            "writers": sorted(active_writers),
            "data": shared_data
        })


def reader(reader_id):
    """Reader process: multiple readers can read simultaneously."""
    global read_count

    name = f"Reader {reader_id}"

    log_event(name, "waiting", f"{name} is waiting to read")

    # Protect the reader count
    mutex.acquire()
    read_count += 1

    # First reader blocks writers
    if read_count == 1:
        resource.acquire()

    with event_lock:
        active_readers.add(name)
        events.append({
            "time": round(time.perf_counter() - start_time, 3),
            "name": name,
            "action": "reading",
            "message": f"{name} started reading",
            "readers": sorted(active_readers),
            "writers": sorted(active_writers),
            "data": shared_data
        })

    mutex.release()

    # Simulate reading
    time.sleep(random.uniform(0.5, 1.0))

    # Record the value actually read
    with event_lock:
        value = shared_data
        events.append({
            "time": round(time.perf_counter() - start_time, 3),
            "name": name,
            "action": "read",
            "message": f"{name} read shared data = {value}",
            "readers": sorted(active_readers),
            "writers": sorted(active_writers),
            "data": value
        })

    # Update the reader count
    mutex.acquire()
    read_count -= 1

    with event_lock:
        active_readers.discard(name)

    # Last reader allows writers to proceed
    if read_count == 0:
        resource.release()

    mutex.release()

    log_event(name, "finished", f"{name} finished reading")


def writer(writer_id):
    """Writer process: only one writer can access the resource."""
    global shared_data

    name = f"Writer {writer_id}"

    log_event(name, "waiting", f"{name} is waiting to write")

    # Exclusive access to the shared resource
    resource.acquire()

    with event_lock:
        active_writers.add(name)
        events.append({
            "time": round(time.perf_counter() - start_time, 3),
            "name": name,
            "action": "writing",
            "message": f"{name} started writing",
            "readers": sorted(active_readers),
            "writers": sorted(active_writers),
            "data": shared_data
        })

    # Simulate writing
    time.sleep(random.uniform(0.5, 0.8))

    shared_data += 1

    with event_lock:
        events.append({
            "time": round(time.perf_counter() - start_time, 3),
            "name": name,
            "action": "updated",
            "message": f"{name} updated shared data to {shared_data}",
            "readers": sorted(active_readers),
            "writers": sorted(active_writers),
            "data": shared_data
        })
        active_writers.discard(name)

    log_event(
        name,
        "finished",
        f"{name} finished writing; shared data = {shared_data}"
    )

    resource.release()


def generate_html(filename):
    """Generate a browser simulation from actual execution events."""

    # JSON encoding safely embeds the recorded events in JavaScript
    event_json = json.dumps(events).replace("</", "<\\/")

    page = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Readers-Writers Semaphore Simulation</title>

<style>
body {
    font-family: Arial, sans-serif;
    background: #eef2f7;
    color: #183153;
    margin: 0;
    padding: 24px;
}
h1 { text-align: center; }
.subtitle { text-align: center; color: #52647a; }
.card {
    background: white;
    padding: 20px;
    margin: 18px 0;
    border-radius: 12px;
    box-shadow: 0 3px 10px #00000012;
}
button {
    padding: 10px 16px;
    margin: 5px;
    border: none;
    border-radius: 6px;
    background: #1769aa;
    color: white;
    cursor: pointer;
}
button:hover { background: #0e4e83; }
.reader {
    display: inline-block;
    background: #d5f5e3;
    color: #145a32;
    padding: 10px;
    margin: 5px;
    border-radius: 7px;
}
.writer {
    display: inline-block;
    background: #fadbd8;
    color: #922b21;
    padding: 10px;
    margin: 5px;
    border-radius: 7px;
}
#progress {
    height: 12px;
    width: 0%;
    background: #1769aa;
    border-radius: 8px;
    transition: width 0.2s;
}
.progress-bg { background: #ddd; border-radius: 8px; }
.table-wrap { overflow-x: auto; }
table {
    border-collapse: collapse;
    width: 100%;
    background: white;
}
th, td {
    border: 1px solid #ddd;
    padding: 10px;
    text-align: left;
}
th { background: #dce6f1; }
.status {
    padding: 10px;
    background: #f4f7fb;
    border-radius: 8px;
}
</style>
</head>

<body>
<h1>Readers-Writers Problem</h1>
<p class="subtitle">Semaphore-Based Synchronization Simulation</p>

<div class="card">
    <h2>Execution Simulation</h2>
    <h3 id="message">Press Play to start</h3>
    <p id="clock">Event: 0</p>
    <p id="data">Shared data: 0</p>
    <p class="status" id="status">Waiting to begin</p>

    <h3>Active Readers</h3>
    <div id="readers">None</div>

    <h3>Active Writers</h3>
    <div id="writers">None</div>

    <br>
    <div class="progress-bg">
        <div id="progress"></div>
    </div>

    <br>
    <button onclick="play()">Play</button>
    <button onclick="pause()">Pause</button>
    <button onclick="nextEvent()">Next Event</button>
    <button onclick="resetSimulation()">Reset</button>
</div>

<div class="card">
    <h2>Execution Event Log</h2>
    <div class="table-wrap">
    <table>
        <thead>
            <tr>
                <th>Time (s)</th>
                <th>Thread</th>
                <th>Action</th>
                <th>Shared Data</th>
            </tr>
        </thead>
        <tbody id="logs"></tbody>
    </table>
    </div>
</div>

<script>
const events = EVENT_DATA;
let index = 0;
let timer = null;

function showEvent() {
    if (index >= events.length) {
        pause();
        document.getElementById("status").textContent =
            "Simulation completed.";
        return;
    }

    const e = events[index];

    document.getElementById("message").textContent = e.message;
    document.getElementById("clock").textContent =
        "Event: " + (index + 1) + " / " + events.length +
        " | Time: " + e.time + " seconds";

    document.getElementById("data").textContent =
        "Shared data: " + e.data;

    document.getElementById("status").textContent =
        "Action: " + e.action;

    document.getElementById("readers").innerHTML =
        e.readers.length
        ? e.readers.map(x =>
            '<span class="reader">' + x + '</span>').join("")
        : "No active readers";

    document.getElementById("writers").innerHTML =
        e.writers.length
        ? e.writers.map(x =>
            '<span class="writer">' + x + '</span>').join("")
        : "No active writers";

    document.getElementById("progress").style.width =
        ((index + 1) / events.length * 100) + "%";

    const row = document.createElement("tr");

    [e.time, e.name, e.message, e.data].forEach(value => {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.appendChild(cell);
    });

    document.getElementById("logs").appendChild(row);

    index++;
}

function play() {
    if (timer === null && index < events.length) {
        timer = setInterval(showEvent, 800);
    }
}

function pause() {
    if (timer !== null) {
        clearInterval(timer);
        timer = null;
    }
}

function nextEvent() {
    pause();
    showEvent();
}

function resetSimulation() {
    pause();
    index = 0;

    document.getElementById("message").textContent =
        "Press Play to start";
    document.getElementById("clock").textContent = "Event: 0";
    document.getElementById("data").textContent = "Shared data: 0";
    document.getElementById("status").textContent = "Waiting to begin";
    document.getElementById("readers").textContent = "None";
    document.getElementById("writers").textContent = "None";
    document.getElementById("progress").style.width = "0%";
    document.getElementById("logs").innerHTML = "";
}
</script>
</body>
</html>"""

    page = page.replace("EVENT_DATA", event_json)

    with open(filename, "w", encoding="utf-8") as file:
        file.write(page)

    print(f"\nHTML simulation generated: {os.path.abspath(filename)}")


def main():
    global start_time

    print("=" * 50)
    print("READERS-WRITERS: SEMAPHORE APPROACH")
    print("=" * 50)

    start_time = time.perf_counter()

    threads = []

    # Create four readers and three writers
    for i in range(1, 5):
        threads.append(
            threading.Thread(target=reader, args=(i,))
        )

    for i in range(1, 4):
        threads.append(
            threading.Thread(target=writer, args=(i,))
        )

    # Randomize the order in which threads are started
    random.shuffle(threads)

    for thread in threads:
        thread.start()
        time.sleep(0.08)

    # Wait for every thread to complete
    for thread in threads:
        thread.join()

    # Generate HTML only after all events have been recorded
    output_file = Path(__file__).resolve().parent / \
        "readers_writers_semaphore.html"

    generate_html(str(output_file))

    print("\nExecution completed successfully.")
    print("Final shared data:", shared_data)
    print("Total events recorded:", len(events))

    # Open the generated simulation in the default browser
    webbrowser.open(output_file.as_uri())


if __name__ == "__main__":
    main()
