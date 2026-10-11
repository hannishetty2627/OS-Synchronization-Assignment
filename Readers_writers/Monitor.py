import threading
import time
import random
import json
import os
import webbrowser
from pathlib import Path


# ==========================================
# READERS-WRITERS PROBLEM: MONITOR APPROACH
# ==========================================

class ReadersWritersMonitor:

    def __init__(self):
        # Condition combines a lock and waiting mechanism
        self.condition = threading.Condition()

        self.read_count = 0
        self.writer_active = False
        self.waiting_writers = 0
        self.shared_data = 0

        # Execution event recording
        self.events = []
        self.active_readers = set()
        self.active_writers = set()

        self.start_time = time.perf_counter()

    def log_event(self, name, action, message):
        """Record execution events while holding the monitor lock."""
        self.events.append({
            "time": round(time.perf_counter() - self.start_time, 3),
            "name": name,
            "action": action,
            "message": message,
            "readers": sorted(self.active_readers),
            "writers": sorted(self.active_writers),
            "data": self.shared_data
        })

    def start_read(self, name):
        """Enter the monitor and acquire permission to read."""
        with self.condition:

            self.log_event(
                name, "waiting",
                f"{name} is waiting to read"
            )

            # Waiting writers get priority over newly arriving readers
            while self.writer_active or self.waiting_writers > 0:
                self.condition.wait()

            self.read_count += 1
            self.active_readers.add(name)

            self.log_event(
                name, "reading",
                f"{name} started reading"
            )

    def finish_read(self, name):
        """Finish reading and notify waiting threads if necessary."""
        with self.condition:

            self.read_count -= 1
            self.active_readers.discard(name)

            self.log_event(
                name, "finished",
                f"{name} finished reading"
            )

            # Notify writers when the last reader leaves
            if self.read_count == 0:
                self.condition.notify_all()

    def start_write(self, name):
        """Wait until exclusive access to the resource is available."""
        with self.condition:

            self.waiting_writers += 1

            self.log_event(
                name, "waiting",
                f"{name} is waiting to write"
            )

            try:
                while self.writer_active or self.read_count > 0:
                    self.condition.wait()

                self.writer_active = True
                self.active_writers.add(name)

                self.log_event(
                    name, "writing",
                    f"{name} started writing"
                )

            finally:
                # Decrement even if an exception occurs
                self.waiting_writers -= 1

    def finish_write(self, name):
        """Update shared data and release the monitor."""
        with self.condition:

            self.shared_data += 1

            self.log_event(
                name, "updated",
                f"{name} updated shared data to {self.shared_data}"
            )

            self.active_writers.discard(name)
            self.writer_active = False

            self.log_event(
                name, "finished",
                f"{name} finished writing"
            )

            # Wake waiting readers and writers
            self.condition.notify_all()


# Create the monitor
monitor = ReadersWritersMonitor()


# ==========================================
# READER THREAD
# ==========================================

def reader(reader_id):
    name = f"Reader {reader_id}"

    monitor.start_read(name)

    try:
        # Simulate reading while holding reader permission
        time.sleep(random.uniform(0.5, 1.0))

        with monitor.condition:
            value = monitor.shared_data

            monitor.log_event(
                name, "read",
                f"{name} read shared data = {value}"
            )

    finally:
        monitor.finish_read(name)


# ==========================================
# WRITER THREAD
# ==========================================

def writer(writer_id):
    name = f"Writer {writer_id}"

    monitor.start_write(name)

    try:
        # Simulate a write operation
        time.sleep(random.uniform(0.5, 0.8))

    finally:
        monitor.finish_write(name)


# ==========================================
# HTML SIMULATION GENERATOR
# ==========================================

def generate_html(filename):
    """Generate a browser simulation from recorded execution events."""

    event_json = json.dumps(monitor.events).replace("</", "<\\/")

    page = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>Readers-Writers Monitor Simulation</title>

<style>
body {
    font-family: Arial, sans-serif;
    background: #eef2f7;
    color: #183153;
    margin: 0;
    padding: 24px;
}

h1 { text-align: center; }

.subtitle {
    text-align: center;
    color: #52647a;
}

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

.progress-bg {
    background: #ddd;
    border-radius: 8px;
}

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
<p class="subtitle">Monitor-Based Synchronization Simulation</p>

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


# ==========================================
# MAIN PROGRAM
# ==========================================

def main():
    print("=" * 50)
    print("READERS-WRITERS: MONITOR APPROACH")
    print("=" * 50)

    # Reset the start time before execution
    monitor.start_time = time.perf_counter()

    threads = []

    # Create four readers
    for i in range(1, 5):
        threads.append(
            threading.Thread(target=reader, args=(i,))
        )

    # Create three writers
    for i in range(1, 4):
        threads.append(
            threading.Thread(target=writer, args=(i,))
        )

    # Randomize thread start order
    random.shuffle(threads)

    # Start the threads
    for thread in threads:
        thread.start()
        time.sleep(0.08)

    # Wait for every thread to finish
    for thread in threads:
        thread.join()

    # Generate HTML beside this Python file
    output_file = (
        Path(__file__).resolve().parent
        / "readers_writers_monitor.html"
    )

    generate_html(str(output_file))

    print("\nExecution completed successfully.")
    print("Final shared data:", monitor.shared_data)
    print("Total events recorded:", len(monitor.events))

    # Open the simulation in the default browser
    webbrowser.open(output_file.as_uri())


if __name__ == "__main__":
    main()
