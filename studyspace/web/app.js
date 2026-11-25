"use strict";

/**
 * StudySpace front-end.
 *
 * The browser never decides whether a booking is valid: it asks the server and
 * renders the server's answer. That keeps the JSON API the single source of
 * truth for the booking rules (SPEC engineering issue 2).
 */

const state = {
  date: "",
  start: "",
  end: "",
  rooms: [],
  selectedRoom: null,
};

const elements = {
  searchForm: document.getElementById("search-form"),
  date: document.getElementById("search-date"),
  start: document.getElementById("search-start"),
  end: document.getElementById("search-end"),
  capacity: document.getElementById("search-capacity"),
  building: document.getElementById("search-building"),
  searchStatus: document.getElementById("search-status"),
  results: document.getElementById("room-results"),
  bookingsDate: document.getElementById("bookings-date"),
  bookingsStatus: document.getElementById("bookings-status"),
  bookingList: document.getElementById("booking-list"),
  dialog: document.getElementById("booking-dialog"),
  dialogRoomName: document.getElementById("dialog-room-name"),
  dialogSlot: document.getElementById("dialog-slot"),
  bookingForm: document.getElementById("booking-form"),
  bookingName: document.getElementById("booking-name"),
  bookingEmail: document.getElementById("booking-email"),
  dialogError: document.getElementById("dialog-error"),
  dialogCancel: document.getElementById("dialog-cancel"),
};

function localDateString(date) {
  const pad = (value) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function tomorrow() {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  return date;
}

function toIso(date, time) {
  return `${date}T${time}:00`;
}

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

function renderRooms(rooms) {
  elements.results.replaceChildren();
  if (!rooms.length) {
    elements.results.textContent = "No free rooms match this search.";
    return;
  }
  for (const room of rooms) {
    const card = document.createElement("article");
    card.className = "room-card";

    const title = document.createElement("h3");
    title.textContent = room.name;

    const details = document.createElement("p");
    details.textContent = `${room.building} building · capacity ${room.capacity}`;

    const features = document.createElement("p");
    features.className = "muted";
    features.textContent = room.features.length
      ? room.features.join(", ")
      : "No listed features";

    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "Book this room";
    button.addEventListener("click", () => openBookingDialog(room));

    card.append(title, details, features, button);
    elements.results.append(card);
  }
}

async function search() {
  const date = elements.date.value;
  const start = elements.start.value;
  const end = elements.end.value;
  const capacity = Number(elements.capacity.value);

  if (!date || !start || !end) {
    setStatus(elements.searchStatus, "Choose a date and a start and end time.", true);
    return;
  }
  if (end <= start) {
    setStatus(elements.searchStatus, "The end time must be after the start time.", true);
    return;
  }

  state.date = date;
  state.start = start;
  state.end = end;
  setStatus(elements.searchStatus, "Searching…");
  try {
    const query = new URLSearchParams({
      start: toIso(date, start),
      end: toIso(date, end),
      min_capacity: String(capacity),
    });
    if (elements.building.value) {
      query.set("building", elements.building.value);
    }
    const payload = await requestJson(`/api/rooms?${query.toString()}`);
    state.rooms = payload.rooms;
    setStatus(
      elements.searchStatus,
      `${payload.count} room${payload.count === 1 ? "" : "s"} free for this window.`
    );
    renderRooms(payload.rooms);
    await loadBookings();
  } catch (error) {
    setStatus(elements.searchStatus, error.message, true);
  }
}

function renderBookings(bookings) {
  elements.bookingList.replaceChildren();
  if (!bookings.length) {
    elements.bookingList.textContent = "No bookings for this date yet.";
    return;
  }
  const list = document.createElement("ul");
  list.className = "booking-list";
  for (const booking of bookings) {
    const item = document.createElement("li");

    const label = document.createElement("span");
    label.textContent =
      `${booking.start.slice(11, 16)}–${booking.end.slice(11, 16)} · ` +
      `${booking.room_id} · ${booking.name}`;

    const cancelButton = document.createElement("button");
    cancelButton.type = "button";
    cancelButton.textContent = "Cancel";
    cancelButton.addEventListener("click", () => cancelBooking(booking));

    item.append(label, cancelButton);
    list.append(item);
  }
  elements.bookingList.append(list);
}

async function loadBookings() {
  if (!state.date) {
    return;
  }
  elements.bookingsDate.textContent = state.date;
  try {
    const payload = await requestJson(
      `/api/bookings?date=${encodeURIComponent(state.date)}`
    );
    renderBookings(payload.bookings);
    setStatus(elements.bookingsStatus, "");
  } catch (error) {
    setStatus(elements.bookingsStatus, error.message, true);
  }
}

async function cancelBooking(booking) {
  const confirmed = window.confirm(
    `Cancel the booking for ${booking.name} at ${booking.start.slice(11, 16)}?`
  );
  if (!confirmed) {
    return;
  }
  try {
    await requestJson(`/api/bookings/${booking.id}`, { method: "DELETE" });
    await search();
  } catch (error) {
    setStatus(elements.bookingsStatus, error.message, true);
  }
}

function openBookingDialog(room) {
  state.selectedRoom = room;
  elements.dialogRoomName.textContent = room.name;
  elements.dialogSlot.textContent = `${state.date}, ${state.start}–${state.end}`;
  elements.dialogError.textContent = "";
  elements.dialog.showModal();
  elements.bookingName.focus();
}

function closeBookingDialog() {
  elements.dialog.close();
  elements.dialogError.textContent = "";
}

async function submitBooking() {
  if (!state.selectedRoom) {
    return;
  }
  elements.dialogError.textContent = "";
  try {
    await requestJson("/api/bookings", {
      method: "POST",
      body: JSON.stringify({
        room_id: state.selectedRoom.id,
        name: elements.bookingName.value.trim(),
        email: elements.bookingEmail.value.trim(),
        start: toIso(state.date, state.start),
        end: toIso(state.date, state.end),
      }),
    });
    closeBookingDialog();
    await search();
  } catch (error) {
    setStatus(elements.dialogError, error.message, true);
  }
}

elements.searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  search();
});

elements.dialogCancel.addEventListener("click", closeBookingDialog);
elements.bookingForm.addEventListener("submit", (event) => {
  event.preventDefault();
  submitBooking();
});

function initialise() {
  elements.date.value = localDateString(tomorrow());
  search();
}

document.addEventListener("DOMContentLoaded", initialise);
