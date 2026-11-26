"use strict";

/**
 * StudySpace staff admin: add a room, list the catalogue, cancel any booking.
 *
 * The page talks to the same JSON API as the booking page; the server remains
 * the authority for every rule.
 */

const elements = {
  roomForm: document.getElementById("room-form"),
  roomId: document.getElementById("room-id"),
  roomName: document.getElementById("room-name"),
  roomBuilding: document.getElementById("room-building"),
  roomCapacity: document.getElementById("room-capacity"),
  roomFeatures: document.getElementById("room-features"),
  roomStatus: document.getElementById("room-status"),
  roomTable: document.getElementById("room-table"),
  allStatus: document.getElementById("all-status"),
  allTable: document.getElementById("all-table"),
  waitlistStatus: document.getElementById("waitlist-status"),
  waitlistTable: document.getElementById("waitlist-table"),
};

function setStatus(element, message, isError = false) {
  element.textContent = message;
  element.classList.toggle("error", isError);
}

async function requestJson(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (response.status === 204) {
    return null;
  }
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = payload.error || {};
    throw new Error(error.message || `Request failed with status ${response.status}.`);
  }
  return payload;
}

function buildTable(headers, rows) {
  const table = document.createElement("table");
  table.className = "data-table";
  const head = document.createElement("thead");
  const headRow = document.createElement("tr");
  for (const label of headers) {
    const th = document.createElement("th");
    th.textContent = label;
    headRow.append(th);
  }
  head.append(headRow);
  const body = document.createElement("tbody");
  for (const row of rows) {
    const tr = document.createElement("tr");
    for (const value of row) {
      const td = document.createElement("td");
      if (value instanceof Node) {
        td.append(value);
      } else {
        td.textContent = value;
      }
      tr.append(td);
    }
    body.append(tr);
  }
  table.append(head, body);
  return table;
}

function cancelButton(booking) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "ghost-button";
  button.textContent = "Cancel";
  button.addEventListener("click", async () => {
    if (!window.confirm(`Cancel the booking for ${booking.name}?`)) {
      return;
    }
    try {
      const result = await requestJson(`/api/bookings/${booking.id}`, {
        method: "DELETE",
      });
      await loadAll();
      await loadWaitlist();
      if (result && result.promoted) {
        setStatus(
          elements.allStatus,
          `${result.promoted.name} was promoted to ${result.promoted.start.slice(11, 16)}–${result.promoted.end.slice(11, 16)}.`
        );
      }
    } catch (error) {
      setStatus(elements.allStatus, error.message, true);
    }
  });
  return button;
}

async function loadRooms() {
  try {
    const payload = await requestJson("/api/rooms");
    elements.roomTable.replaceChildren(
      buildTable(
        ["Room", "Name", "Building", "Capacity", "Features"],
        payload.rooms.map((room) => [
          room.id,
          room.name,
          room.building,
          String(room.capacity),
          room.features.length ? room.features.join(", ") : "—",
        ])
      )
    );
  } catch (error) {
    setStatus(elements.roomStatus, error.message, true);
  }
}

async function loadWaitlist() {
  try {
    const payload = await requestJson("/api/waitlist");
    if (!payload.entries.length) {
      elements.waitlistTable.textContent = "Nobody is waiting.";
      return;
    }
    elements.waitlistTable.replaceChildren(
      buildTable(
        ["Position", "Room", "Date", "Time", "Name", "Email"],
        payload.entries.map((entry, index) => [
          String(index + 1),
          entry.room_id,
          entry.start.slice(0, 10),
          `${entry.start.slice(11, 16)}–${entry.end.slice(11, 16)}`,
          entry.name,
          entry.email,
        ])
      )
    );
  } catch (error) {
    setStatus(elements.waitlistStatus, error.message, true);
  }
}

async function loadAll() {
  try {
    const payload = await requestJson("/api/bookings?all=1");
    if (!payload.bookings.length) {
      elements.allTable.textContent = "No bookings yet.";
      return;
    }
    elements.allTable.replaceChildren(
      buildTable(
        ["Date", "Time", "Room", "Name", "Email", ""],
        payload.bookings.map((booking) => [
          booking.start.slice(0, 10),
          `${booking.start.slice(11, 16)}–${booking.end.slice(11, 16)}`,
          booking.room_id,
          booking.name,
          booking.email,
          cancelButton(booking),
        ])
      )
    );
    setStatus(elements.allStatus, `${payload.count} booking${payload.count === 1 ? "" : "s"} in total.`);
  } catch (error) {
    setStatus(elements.allStatus, error.message, true);
  }
}

async function addRoom(event) {
  event.preventDefault();
  const features = elements.roomFeatures.value
    .split(",")
    .map((feature) => feature.trim())
    .filter(Boolean);
  const payload = {
    id: elements.roomId.value.trim(),
    name: elements.roomName.value.trim(),
    building: elements.roomBuilding.value.trim(),
    capacity: Number(elements.roomCapacity.value),
    features,
  };
  try {
    await requestJson("/api/rooms", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    elements.roomForm.reset();
    elements.roomCapacity.value = "4";
    setStatus(elements.roomStatus, `Room ${payload.id} added.`);
    await loadRooms();
  } catch (error) {
    setStatus(elements.roomStatus, error.message, true);
  }
}

elements.roomForm.addEventListener("submit", addRoom);

function initialise() {
  loadRooms();
  loadWaitlist();
  loadAll();
}

document.addEventListener("DOMContentLoaded", initialise);
